"""
投资情报二次 enrichment：
1. 首选直接爬取文章正文
2. 降级：DuckDuckGo 搜索
3. Qwen 提取 reason/background/key_players/data_point（投资视角）
"""

import json
import os
import re
import time

import requests
from bs4 import BeautifulSoup
from openai import OpenAI

from config import ENRICH_MIN_SCORE, ENRICH_MAX_COUNT, ENRICH_SYSTEM_PROMPT

QWEN_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
QWEN_MODEL = "qwen-plus"

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
        return text[:2500] if len(text) >= 150 else ""
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


def _enrich_one(client: OpenAI, art: dict) -> None:
    body = _fetch_article_body(art.get("url", ""))

    if body:
        context_label   = "文章正文"
        search_context  = body
    else:
        query = f"{art['title']} {art['source']} 2026 funding investment"
        snippets = _ddg_search(query)
        time.sleep(1.5)
        context_label  = "网络搜索背景信息"
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
        resp = client.chat.completions.create(
            model=QWEN_MODEL,
            messages=[
                {"role": "system", "content": ENRICH_SYSTEM_PROMPT},
                {"role": "user",   "content": user_msg},
            ],
            max_tokens=768,
        )
        raw  = re.sub(r"```(?:json)?", "", resp.choices[0].message.content or "{}").strip()
        data = json.loads(raw)
        if data.get("reason_zh"):
            art["reason_zh"] = data["reason_zh"]
        art["background_zh"]  = data.get("background_zh", "")
        art["key_players_zh"] = data.get("key_players_zh", "")
        art["data_point_zh"]  = data.get("data_point_zh", "")
    except Exception as exc:
        print(f"    [ENRICH WARN] {art['title'][:40]}: {exc}")
        art["background_zh"]  = ""
        art["key_players_zh"] = ""
        art["data_point_zh"]  = ""


def enrich_articles(articles: list[dict]) -> list[dict]:
    api_key = os.environ.get("QWEN_API_KEY")
    if not api_key:
        print("[WARN] QWEN_API_KEY not set – skipping enrichment.")
        for art in articles:
            art.setdefault("background_zh", "")
            art.setdefault("key_players_zh", "")
            art.setdefault("data_point_zh", "")
        return articles

    targets = [a for a in articles if a.get("score", 0) >= ENRICH_MIN_SCORE][:ENRICH_MAX_COUNT]

    if not targets:
        for art in articles:
            art.setdefault("background_zh", "")
            art.setdefault("key_players_zh", "")
            art.setdefault("data_point_zh", "")
        return articles

    print(f"Enriching {len(targets)} top investment articles…")
    client = OpenAI(api_key=api_key, base_url=QWEN_BASE_URL)

    for i, art in enumerate(targets, 1):
        print(f"  [{i}/{len(targets)}] {art['title'][:55]}…")
        _enrich_one(client, art)

    for art in articles:
        art.setdefault("background_zh", "")
        art.setdefault("key_players_zh", "")
        art.setdefault("data_point_zh", "")

    return articles
