"""
产品雷达专属二次精细化分析。

对高分文章进行深度产品视角解读：
- product_insight_zh：核心产品洞察（这个设计决策背后的逻辑）
- design_pattern_zh：代表了什么设计模式或产品原则
- crypto_relevance_zh：对加密/交易所产品的借鉴价值
- data_point_zh：文中最有价值的数据
"""

import json
import os
import re
import time

import httpx
import requests
from bs4 import BeautifulSoup
from openai import OpenAI

from config import ENRICH_MIN_SCORE, ENRICH_MAX_COUNT

GATEWAY_URL     = os.environ.get("GATEWAY_URL", "http://localhost:8000/v1")
GATEWAY_API_KEY = os.environ.get("GATEWAY_API_KEY", "dummy")
GLM_BASE_URL    = "https://open.bigmodel.cn/api/paas/v4"
GLM_MODEL       = "glm-4-flash"


def _complete(messages: list, **kwargs):
    try:
        c = OpenAI(
            api_key=GATEWAY_API_KEY,
            base_url=GATEWAY_URL,
            http_client=httpx.Client(trust_env=False),
        )
        return c.chat.completions.create(model="free", messages=messages, **kwargs)
    except Exception:
        pass

    glm_key = os.environ.get("ZHIPU_API_KEY", "")
    if not glm_key:
        raise RuntimeError("网关不可用，且未配置 ZHIPU_API_KEY")
    c = OpenAI(api_key=glm_key, base_url=GLM_BASE_URL)
    return c.chat.completions.create(model=GLM_MODEL, messages=messages, **kwargs)


ENRICH_SYSTEM = """你是一位在顶级加密交易所（币安）负责产品的资深 PM，有快手/滴滴的超级App产品经验。
给定一篇产品/设计文章，请从产品经理视角提取以下4个字段：

1. product_insight_zh：核心产品洞察（这个设计决策的底层逻辑是什么？30字以内，要有真正的洞见）
2. design_pattern_zh：这代表了什么设计模式或产品原则？（如：渐进式信息披露、损失厌恶利用、社交证明等，20字以内）
3. crypto_relevance_zh：对加密交易所产品有什么借鉴价值？（如无则填"暂无直接关联"，30字以内）
4. data_point_zh：文中最有价值的数字或数据点（如无则留空）

严格以 JSON 格式返回，不要任何其他文字：
{"product_insight_zh": "...", "design_pattern_zh": "...", "crypto_relevance_zh": "...", "data_point_zh": "..."}
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
    body = _fetch_article_body(art.get("url", ""))

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
            max_tokens=512,
        )
        raw = resp.choices[0].message.content or "{}"
        raw = re.sub(r"```(?:json)?", "", raw).strip()
        data = json.loads(raw)
        art["product_insight_zh"]  = data.get("product_insight_zh", "")
        art["design_pattern_zh"]   = data.get("design_pattern_zh", "")
        art["crypto_relevance_zh"] = data.get("crypto_relevance_zh", "")
        art["data_point_zh"]       = data.get("data_point_zh", "")
    except Exception as exc:
        print(f"    [ENRICH WARN] {art['title'][:40]}: {exc}")
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
        art.setdefault("product_insight_zh", "")
        art.setdefault("design_pattern_zh", "")
        art.setdefault("crypto_relevance_zh", "")
        art.setdefault("data_point_zh", "")

    return articles
