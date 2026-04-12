"""
产品雷达专属二次精细化分析。

对高分文章进行深度产品视角解读：
- og_image：文章 OG 封面图 URL
- full_summary_zh：完整中文摘要（比评分阶段更详细）
- product_insight_zh：核心产品洞察
- design_pattern_zh：代表了什么设计模式或产品原则
- crypto_relevance_zh：对加密/交易所产品的借鉴价值
- data_point_zh：文中最有价值的数据
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


ENRICH_SYSTEM = """你是一位在顶级加密交易所（币安）负责产品的资深 PM，有快手/滴滴的超级App产品经验。
给定一篇产品/设计文章的正文，请提取以下5个字段：

1. full_summary_zh：完整中文摘要（5-8句话）。结构：① 背景/作者介绍 ② 核心论点或产品更新内容 ③ 关键数据或案例 ④ 对产品人的启示。要有实质内容，不要废话。
2. product_insight_zh：核心产品洞察，一句话点出底层逻辑（30字以内，要有真正的洞见，有数据优先引用数字）
3. design_pattern_zh：这代表了什么设计模式或产品原则（如：渐进式信息披露、损失厌恶利用、社交证明等，20字以内）
4. crypto_relevance_zh：对加密交易所产品的借鉴价值（如无则填"暂无直接关联"，30字以内）
5. data_point_zh：文中最有价值的一个数字或数据点（如无则留空）

严格以 JSON 格式返回，不要任何其他文字：
{"full_summary_zh": "...", "product_insight_zh": "...", "design_pattern_zh": "...", "crypto_relevance_zh": "...", "data_point_zh": "..."}
"""

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


def _fetch_og_image(url: str) -> str:
    """尝试抓取文章的 OG 封面图 URL，失败返回空字符串。"""
    try:
        resp = requests.get(url, timeout=8, headers=_HEADERS)
        if resp.status_code != 200:
            return ""
        soup = BeautifulSoup(resp.content, "html.parser")
        for prop in ("og:image", "twitter:image", "og:image:url"):
            tag = soup.find("meta", property=prop) or soup.find("meta", attrs={"name": prop})
            if tag and tag.get("content", "").startswith("http"):
                return tag["content"]
        return ""
    except Exception:
        return ""


def _ddg_search(query: str, max_results: int = 3) -> list[str]:
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
    url = art.get("url", "")

    # 并行抓取：正文 + OG 图
    body = _fetch_article_body(url)
    art["og_image"] = _fetch_og_image(url) if url else ""

    if body:
        context_label = "文章正文"
        context = body
    else:
        query = f"{art['title']} {art['source']} product design 2026"
        snippets = _ddg_search(query)
        time.sleep(1.5)
        context_label = "网络搜索背景"
        context = "\n".join(f"- {s}" for s in snippets) if snippets else "（无搜索结果）"

    user_msg = f"""文章标题：{art['title']}
来源：{art['source']}
当前摘要：{(art.get('summary') or '')[:300]}

{context_label}：
{context}
"""
    try:
        resp = _complete(
            messages=[
                {"role": "system", "content": ENRICH_SYSTEM},
                {"role": "user", "content": user_msg},
            ],
            max_tokens=1024,
        )
        raw = resp.choices[0].message.content or "{}"
        raw = re.sub(r"```(?:json)?", "", raw).strip()
        data = json.loads(raw)
        art["full_summary_zh"]     = data.get("full_summary_zh", "")
        art["product_insight_zh"]  = data.get("product_insight_zh", "")
        art["design_pattern_zh"]   = data.get("design_pattern_zh", "")
        art["crypto_relevance_zh"] = data.get("crypto_relevance_zh", "")
        art["data_point_zh"]       = data.get("data_point_zh", "")
    except Exception as exc:
        print(f"    [ENRICH WARN] {art['title'][:40]}: {exc}")
        art["full_summary_zh"]     = ""
        art["product_insight_zh"]  = ""
        art["design_pattern_zh"]   = ""
        art["crypto_relevance_zh"] = ""
        art["data_point_zh"]       = ""


def enrich_articles(articles: list[dict]) -> list[dict]:
    targets = [
        a for a in articles
        if a.get("score", 0) >= ENRICH_MIN_SCORE
    ][:ENRICH_MAX_COUNT]

    if not targets:
        for art in articles:
            art.setdefault("product_insight_zh", "")
            art.setdefault("design_pattern_zh", "")
            art.setdefault("crypto_relevance_zh", "")
            art.setdefault("data_point_zh", "")
        return articles

    print(f"Enriching {len(targets)} top product articles …")
    for i, art in enumerate(targets, 1):
        print(f"  [{i}/{len(targets)}] {art['title'][:55]}…")
        _enrich_one(art)

    for art in articles:
        art.setdefault("og_image", "")
        art.setdefault("full_summary_zh", "")
        art.setdefault("product_insight_zh", "")
        art.setdefault("design_pattern_zh", "")
        art.setdefault("crypto_relevance_zh", "")
        art.setdefault("data_point_zh", "")

    return articles
