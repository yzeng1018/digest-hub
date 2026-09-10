"""
投资情报二次 enrichment：
1. 首选直接爬取文章正文
2. 降级：DuckDuckGo 搜索
3. Qwen 提取 reason/background/key_players/data_point（投资视角）
"""

import json
import re
import time

import requests
from bs4 import BeautifulSoup

from config import (
    ENRICH_BATCH_SIZE, ENRICH_MIN_SCORE, ENRICH_MAX_COUNT, ENRICH_SYSTEM_PROMPT,
)
from portfolio import portfolio_context

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from common.scorer import call_ai as _complete

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


def _fetch_article_body(url: str) -> str:
    try:
        resp = requests.get(url, timeout=10, headers=_HEADERS)
        if resp.status_code != 200:
            return ""
        html = resp.content.decode(resp.apparent_encoding or "utf-8", errors="replace")
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "noscript", "nav", "footer", "header"]):
            tag.decompose()
        text = " ".join(soup.get_text(separator=" ").split())
        return text[:1200] if len(text) >= 150 else ""
    except Exception:
        return ""


def _ddg_search(query: str, max_results: int = 3) -> list[str]:
    try:
        from ddgs import DDGS
        snippets = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                title = r.get("title", "")
                body  = r.get("body", "")
                if title or body:
                    snippets.append(f"{title}: {body[:200]}")
        return snippets
    except Exception as exc:
        print(f"    [DDG WARN] {exc}")
        return []


def _prepare_enrichment(art: dict, watchlist: list[dict]) -> dict:
    # Google News links often resolve to an interstitial rather than the article.
    # A fresh search gives portfolio stories more independent context.
    body = "" if art.get("platform") in {"Portfolio", "Watchlist"} else _fetch_article_body(art.get("url", ""))

    if body:
        context_label   = "文章正文"
        search_context  = body
    else:
        query = f"{art['title']} {art['source']} 2026 earnings industry analysis"
        snippets = _ddg_search(query)
        time.sleep(1.5)
        context_label  = "网络搜索背景信息"
        search_context = (
            "\n".join(f"- {s}" for s in snippets) if snippets else "（无搜索结果）"
        )

    matches = art.get("portfolio_matches", [])
    relevant_holdings = "、".join(matches)
    if not relevant_holdings:
        relevant_holdings = portfolio_context(watchlist, limit=8)
    return {
        "article": art,
        "payload": {
            "title": art["title"],
            "source": art["source"],
            "lang": art.get("lang", ""),
            "current_summary": (art.get("summary") or "")[:220],
            "related_holdings": relevant_holdings,
            "sector": art.get("portfolio_sector", ""),
            "published_at": art.get("published_at", ""),
            "context_type": context_label,
            "context": search_context,
        },
    }


_ENRICH_FIELDS = (
    "title_zh", "summary_zh", "reason_zh", "background_zh",
    "key_players_zh", "data_point_zh", "portfolio_relevance_zh",
    "investment_angle_zh", "confirmation_signal_zh", "risk_zh",
    "idea_topic_zh", "news_hook_zh",
)


def _apply_enrichment(art: dict, data: dict) -> None:
    for field in _ENRICH_FIELDS:
        value = data.get(field, "")
        if value or field not in {"reason_zh", "title_zh", "summary_zh"}:
            art[field] = value


def _enrich_prepared(prepared: list[dict]) -> None:
    items = []
    for index, item in enumerate(prepared):
        payload = dict(item["payload"])
        payload["id"] = str(index)
        items.append(payload)

    try:
        resp = _complete(
            messages=[
                {"role": "system", "content": ENRICH_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": json.dumps(items, ensure_ascii=False, separators=(",", ":")),
                },
            ],
            max_tokens=max(1536, len(items) * 700),
            usage_stage="enrich",
        )
        raw = re.sub(r"```(?:json)?", "", resp.choices[0].message.content or "[]").strip()
        match = re.search(r"\[.*\]", raw, re.DOTALL)
        results = json.loads(match.group() if match else "[]")
        indexed = {str(result.get("id")): result for result in results}
        if not indexed:
            raise ValueError("empty enrichment response")
        for index, item in enumerate(prepared):
            data = indexed.get(str(index))
            if data:
                _apply_enrichment(item["article"], data)
    except Exception as exc:
        if len(prepared) > 1:
            midpoint = len(prepared) // 2
            print(f"    [ENRICH RETRY] 批次失败，拆分重试: {exc}")
            _enrich_prepared(prepared[:midpoint])
            _enrich_prepared(prepared[midpoint:])
        else:
            art = prepared[0]["article"]
            print(f"    [ENRICH WARN] {art['title'][:40]}: {exc}")


def enrich_articles(articles: list[dict], watchlist: list[dict] | None = None) -> list[dict]:
    watchlist = watchlist or []
    targets = [a for a in articles if a.get("score", 0) >= ENRICH_MIN_SCORE][:ENRICH_MAX_COUNT]

    if not targets:
        for art in articles:
            for field in _ENRICH_FIELDS:
                art.setdefault(field, "")
        return articles

    print(
        f"Enriching {len(targets)} top investment articles "
        f"in batches of {ENRICH_BATCH_SIZE}…"
    )
    prepared = []
    for i, art in enumerate(targets, 1):
        print(f"  准备 [{i}/{len(targets)}] {art['title'][:55]}…")
        prepared.append(_prepare_enrichment(art, watchlist))
    for start in range(0, len(prepared), ENRICH_BATCH_SIZE):
        batch = prepared[start:start + ENRICH_BATCH_SIZE]
        print(f"  分析 [{start + 1}–{start + len(batch)}] …")
        _enrich_prepared(batch)

    for art in articles:
        for field in _ENRICH_FIELDS:
            art.setdefault(field, "")

    return articles
