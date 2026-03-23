"""
对高分内容进行二次 enrichment：
- 普通内容：DuckDuckGo 搜索 + Qwen 生成背景介绍
- 播客内容：直接用转录稿，Qwen 生成 follow-builders 风格的深度摘要
"""

import json
import os
import re
import time

from openai import OpenAI
from config import ENRICH_MIN_SCORE, ENRICH_MAX_COUNT

QWEN_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
QWEN_MODEL = "qwen-plus"

ENRICH_SYSTEM = """你是一位深度关注 AI 领域的分析师。
给定一条 AI 内容和网络搜索背景，请生成：

1. reason_zh：一句话点评，说明对 AI 从业者/创业者的战略意义（30字以内，要有洞见；如有大胆预判或反常识结论，直接以此开头）
2. background_zh：1-2句背景介绍，帮助读者理解上下文。格式：「[职位+全名] 是...，此次...」（例：「Anthropic CEO Dario Amodei 是 Claude 系列模型的核心负责人，此次披露了...」）

严格以 JSON 格式返回，不要任何其他文字：
{"reason_zh": "...", "background_zh": "..."}
"""

PODCAST_ENRICH_SYSTEM = """你是一位深度关注 AI 领域的分析师，正在为忙碌的 AI 从业者提炼播客精华。

给定一段播客转录稿，请生成：

1. reason_zh：一句话点评，说明这期播客对 AI 从业者/创业者的核心价值（30字以内，有洞见；如有反常识观点或大胆预判，直接以此开头）
2. background_zh：200-350字的中文摘要，要求：
   - 第一句点明嘉宾身份：「[嘉宾职位+全名] 在本期讨论了……」
   - 提炼 2-3 个最有价值的观点，优先选反常识、有具体数据、或对行业有直接影响的内容
   - 至少包含一句原文直接引语（翻译成中文）
   - 结尾一句：「最值得关注的是……」
   - 语气：像懂行的朋友转述，不是写报告；文章要能独立成立，不写「在本期节目中…」类自指

严格以 JSON 格式返回，不要任何其他文字：
{"reason_zh": "...", "background_zh": "..."}
"""


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


def _enrich_podcast(client: OpenAI, art: dict) -> None:
    transcript_chunk = art["transcript"][:6000]
    user_msg = f"""播客节目：{art['source']}
集标题：{art['title']}

转录稿（节选）：
{transcript_chunk}
"""
    try:
        resp = client.chat.completions.create(
            model=QWEN_MODEL,
            messages=[
                {"role": "system", "content": PODCAST_ENRICH_SYSTEM},
                {"role": "user",   "content": user_msg},
            ],
            max_tokens=1024,
            timeout=90,
        )
        raw = re.sub(r"```(?:json)?", "", resp.choices[0].message.content or "{}").strip()
        data = json.loads(raw)
        if data.get("reason_zh"):
            art["reason_zh"] = data["reason_zh"]
        art["background_zh"] = data.get("background_zh", "")
    except Exception as exc:
        print(f"    [PODCAST ENRICH WARN] {art['title'][:40]}: {exc}")
        art["background_zh"] = ""


def _enrich_one(client: OpenAI, art: dict) -> None:
    if art.get("platform") == "Podcast" and art.get("transcript"):
        _enrich_podcast(client, art)
        return

    query = f"{art['title']} AI {art['source']}"
    snippets = _ddg_search(query)
    time.sleep(1.5)

    context = "\n".join(f"- {s}" for s in snippets) if snippets else "（无搜索结果）"
    user_msg = f"""内容标题：{art['title']}
来源：{art['source']} ({art.get('platform', '')})
当前摘要：{(art.get('summary') or '')[:300]}

网络背景信息：
{context}
"""
    try:
        resp = client.chat.completions.create(
            model=QWEN_MODEL,
            messages=[
                {"role": "system", "content": ENRICH_SYSTEM},
                {"role": "user", "content": user_msg},
            ],
            max_tokens=512,
            timeout=60,
        )
        raw = re.sub(r"```(?:json)?", "", resp.choices[0].message.content or "{}").strip()
        data = json.loads(raw)
        if data.get("reason_zh"):
            art["reason_zh"] = data["reason_zh"]
        art["background_zh"] = data.get("background_zh", "")
    except Exception as exc:
        print(f"    [ENRICH WARN] {art['title'][:40]}: {exc}")
        art["background_zh"] = ""


def enrich_articles(articles: list[dict]) -> list[dict]:
    api_key = os.environ.get("QWEN_API_KEY")
    if not api_key:
        print("[WARN] QWEN_API_KEY not set – skipping enrichment.")
        for art in articles:
            art.setdefault("background_zh", "")
        return articles

    targets = [a for a in articles if a.get("score", 0) >= ENRICH_MIN_SCORE][:ENRICH_MAX_COUNT]

    if not targets:
        for art in articles:
            art.setdefault("background_zh", "")
        return articles

    print(f"Enriching {len(targets)} 条高分内容…")
    client = OpenAI(api_key=api_key, base_url=QWEN_BASE_URL)

    for i, art in enumerate(targets, 1):
        print(f"  [{i}/{len(targets)}] {art['title'][:55]}…")
        _enrich_one(client, art)

    for art in articles:
        art.setdefault("background_zh", "")
    return articles
