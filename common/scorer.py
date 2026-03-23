"""
通用 Qwen 评分模块。
system_prompt、batch_size、summary_fn 由各 channel 的 config 传入，
使同一套 API 调用逻辑可服务于不同视角的评分需求。
"""

import json
import os
import re
from collections.abc import Callable

from openai import OpenAI

QWEN_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
QWEN_MODEL = "qwen-max"

USER_PROMPT_TEMPLATE = """请对以下 {count} 条内容进行评估。

严格按照以下 JSON 格式返回，不要有任何其他文字，不要有 markdown 代码块：
[
  {{
    "id": "序号，从0开始",
    "score": 评分数字(1-10),
    "reason_zh": "一句话说明价值（20字以内）",
    "title_zh": "中文标题",
    "summary_zh": "中文摘要2-3句"
  }},
  ...
]

内容列表：
{articles_json}
"""


def _default_summary_fn(art: dict) -> str:
    return (art.get("summary") or "")[:300]


def _parse_response(text: str) -> list[dict]:
    text = re.sub(r"```(?:json)?", "", text).strip()
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if not match:
        return []
    try:
        return json.loads(match.group())
    except json.JSONDecodeError:
        return []


def _apply_results(articles: list[dict], results: list[dict]) -> None:
    index = {r["id"]: r for r in results}
    for i, art in enumerate(articles):
        r = index.get(str(i))
        if not r:
            art.setdefault("score", 3)
            art.setdefault("reason_zh", "")
            art.setdefault("title_zh", art["title"])
            art.setdefault("summary_zh", art["summary"])
            continue
        art["score"] = int(r.get("score", 3))
        art["reason_zh"] = r.get("reason_zh", "")
        art["title_zh"] = r.get("title_zh") or art["title"]
        art["summary_zh"] = r.get("summary_zh") or art["summary"]


def score_articles(
    articles: list[dict],
    system_prompt: str,
    batch_size: int = 15,
    summary_fn: Callable[[dict], str] | None = None,
) -> list[dict]:
    """
    对文章列表评分 + 翻译，修改原列表并返回。
    summary_fn: 从 article dict 提取送给 Qwen 的摘要文本，默认取 summary[:300]。
    """
    if summary_fn is None:
        summary_fn = _default_summary_fn

    api_key = os.environ.get("QWEN_API_KEY")
    if not api_key:
        print("[WARN] QWEN_API_KEY not set – skipping scoring.")
        for art in articles:
            art["score"] = 5
            art["reason_zh"] = ""
            art["title_zh"] = art["title"]
            art["summary_zh"] = art["summary"]
        return articles

    client = OpenAI(api_key=api_key, base_url=QWEN_BASE_URL)

    for batch_start in range(0, len(articles), batch_size):
        batch = articles[batch_start: batch_start + batch_size]
        print(f"  评分 [{batch_start + 1}–{batch_start + len(batch)}] …")

        items = [
            {
                "id": str(i),
                "platform": art.get("platform", ""),
                "source": art["source"],
                "lang": art["lang"],
                "title": art["title"],
                "summary": summary_fn(art),
            }
            for i, art in enumerate(batch)
        ]
        payload = json.dumps(items, ensure_ascii=False, indent=2)
        user_msg = USER_PROMPT_TEMPLATE.format(count=len(batch), articles_json=payload)

        try:
            resp = client.chat.completions.create(
                model=QWEN_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_msg},
                ],
                max_tokens=4096,
                timeout=120,
            )
            results = _parse_response(resp.choices[0].message.content or "")
            _apply_results(batch, results)
        except Exception as exc:
            print(f"  [ERROR] Scoring batch failed: {exc}")
            for art in batch:
                art.setdefault("score", 3)
                art.setdefault("reason_zh", "")
                art.setdefault("title_zh", art["title"])
                art.setdefault("summary_zh", art["summary"])

    return articles
