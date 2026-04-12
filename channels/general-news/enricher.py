"""
Second-pass enrichment for high-score articles.

For each article scoring >= ENRICH_MIN_SCORE:
1. Fetch the article body directly from its URL (primary context)
2. Fall back to DuckDuckGo search snippets if body fetch fails
3. Call Qwen with article + context → richer fields:
   reason_zh, background_zh, key_players_zh, data_point_zh

This keeps costs low: only top articles get the deep treatment.
"""

import json
import re
import time

import requests
from bs4 import BeautifulSoup

from config import ENRICH_MIN_SCORE, ENRICH_MAX_COUNT

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from common.scorer import call_ai as _complete

ENRICH_SYSTEM = """你是一位顶级的科技创业者和风险投资人。
给定一篇新闻文章的完整正文（或网络搜索摘要），请提取以下4个字段：

1. reason_zh：一句话点评，说明这对创业者/投资人的战略意义（30字以内，要有洞见，不要废话）
2. background_zh：1-2句背景介绍，帮助不了解该公司/技术的读者理解上下文
3. key_players_zh：涉及的关键人物或公司名称，逗号分隔（如无则留空）
4. data_point_zh：文中最有价值的一个数字或数据点（如无则留空）

严格以 JSON 格式返回，不要任何其他文字：
{"reason_zh": "...", "background_zh": "...", "key_players_zh": "...", "data_point_zh": "..."}
"""


_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


def _fetch_article_body(url: str) -> str:
    """Fetch and clean article body text. Returns '' on any failure."""
    try:
        resp = requests.get(url, timeout=10, headers=_HEADERS)
        if resp.status_code != 200:
            return ""
        html = resp.content.decode(resp.apparent_encoding or "utf-8", errors="replace")
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "noscript", "nav", "footer", "header"]):
            tag.decompose()
        text = " ".join(soup.get_text(separator=" ").split())
        if len(text) < 150:
            return ""
        return text[:2500]
    except Exception:
        return ""


def _ddg_search(query: str, max_results: int = 3) -> list[str]:
    """Return a list of 'title: snippet' strings from DuckDuckGo."""
    try:
        from ddgs import DDGS
        snippets = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                title = r.get("title", "")
                body = r.get("body", "")
                if title or body:
                    snippets.append(f"{title}: {body[:200]}")
        return snippets
    except Exception as exc:
        print(f"    [DDG WARN] {exc}")
        return []


def _enrich_one(art: dict) -> None:
    """Enrich a single article in-place."""
    # Primary: fetch full article body
    body = _fetch_article_body(art.get("url", ""))

    if body:
        context_label = "文章正文"
        search_context = body
    else:
        # Fallback: DuckDuckGo snippets
        query = f"{art['title']} {art['source']} 2026"
        snippets = _ddg_search(query)
        time.sleep(1.5)   # be gentle with DDG
        context_label = "网络搜索背景信息"
        search_context = (
            "\n".join(f"- {s}" for s in snippets) if snippets else "（无搜索结果）"
        )

    user_msg = f"""文章标题：{art['title']}
来源：{art['source']}
当前摘要：{(art.get('summary') or '')[:300]}

{context_label}：
{search_context}
"""
    try:
        resp = _complete(
            messages=[
                {"role": "system", "content": ENRICH_SYSTEM},
                {"role": "user", "content": user_msg},
            ],
            max_tokens=768,
        )
        raw = resp.choices[0].message.content or "{}"
        raw = re.sub(r"```(?:json)?", "", raw).strip()
        data = json.loads(raw)
        if data.get("reason_zh"):
            art["reason_zh"] = data["reason_zh"]
        art["background_zh"] = data.get("background_zh", "")
        art["key_players_zh"] = data.get("key_players_zh", "")
        art["data_point_zh"] = data.get("data_point_zh", "")
    except Exception as exc:
        print(f"    [ENRICH WARN] {art['title'][:40]}: {exc}")
        art["background_zh"] = ""
        art["key_players_zh"] = ""
        art["data_point_zh"] = ""


def enrich_articles(articles: list[dict]) -> list[dict]:
    """
    Run second-pass enrichment on high-score articles.
    Modifies articles in-place; returns the same list.
    """
    targets = [
        a for a in articles
        if a.get("score", 0) >= ENRICH_MIN_SCORE
    ][:ENRICH_MAX_COUNT]

    if not targets:
        for art in articles:
            art["background_zh"] = ""
            art["key_players_zh"] = ""
            art["data_point_zh"] = ""
        return articles

    print(f"Enriching {len(targets)} top articles with web search…")

    for i, art in enumerate(targets, 1):
        print(f"  [{i}/{len(targets)}] {art['title'][:55]}…")
        _enrich_one(art)

    # ensure all enrichment fields exist on all articles
    for art in articles:
        art.setdefault("background_zh", "")
        art.setdefault("key_players_zh", "")
        art.setdefault("data_point_zh", "")

    return articles
