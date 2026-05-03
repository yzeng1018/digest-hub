"""
通用评分模块。
system_prompt、batch_size、summary_fn 由各 channel 的 config 传入，
使同一套 API 调用逻辑可服务于不同视角的评分需求。
"""

import json
import math
import os
import re
import time
from collections.abc import Callable

import httpx
from openai import OpenAI

# Gemini 主力（默认 gemini-2.5-flash，可通过 GitHub Variable PRIMARY_MODEL 覆盖）
GEMINI_URL   = "https://generativelanguage.googleapis.com/v1beta/openai"
GEMINI_MODEL = os.environ.get("PRIMARY_MODEL", "gemini-2.5-flash")

# 智谱 GLM 兜底（默认 glm-4.7-flash，永久免费）
ZHIPU_URL   = "https://open.bigmodel.cn/api/paas/v4"
ZHIPU_MODEL = os.environ.get("FALLBACK_MODEL", "glm-4.7-flash")

# 模块级 usage 累计器，每次 score_articles 调用前重置
_usage: dict = {"model": "", "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

# 模块级 metrics 累计器
_metrics: dict = {
    "batches_total":   0,
    "batches_parsed":  0,  # JSON 解析成功的批次数
}


def get_usage() -> dict:
    """返回最近一次 score_articles 调用的 token 消耗统计。"""
    return dict(_usage)


def get_metrics(articles: list[dict]) -> dict:
    """
    根据已完成评分的文章列表，计算模型表现指标。
    需在 score_articles 调用结束后调用。

    返回：
      parse_rate       — JSON 解析成功率 0-1
      score_spread     — 评分标准差（区分度，目标 ~2.0）
      translation_rate — 有 title_zh 的文章比例
      perf_score       — 综合得分 0-10
        计算公式：parse_rate×4 + min(score_spread/3,1)×3 + translation_rate×3
    """
    total   = _metrics["batches_total"]
    parsed  = _metrics["batches_parsed"]
    parse_rate = (parsed / total) if total > 0 else 0.0

    scores = [a.get("score", 0) for a in articles if a.get("score", 0) > 0]
    if len(scores) >= 2:
        mean = sum(scores) / len(scores)
        variance = sum((s - mean) ** 2 for s in scores) / len(scores)
        score_spread = math.sqrt(variance)
    else:
        score_spread = 0.0

    translated = sum(1 for a in articles if a.get("title_zh") and a["title_zh"] != a.get("title"))
    translation_rate = (translated / len(articles)) if articles else 0.0

    perf_score = round(
        parse_rate * 4.0
        + min(score_spread / 3.0, 1.0) * 3.0
        + translation_rate * 3.0,
        2,
    )

    return {
        "parse_rate":       round(parse_rate, 3),
        "score_spread":     round(score_spread, 2),
        "translation_rate": round(translation_rate, 3),
        "perf_score":       perf_score,
        "article_count":    len(articles),
    }


def call_ai(messages: list, **kwargs):
    """
    公共 AI 调用入口（供 enricher 等模块使用）。
    自动处理 gateway → 火山方舟 fallback，只返回 response 对象。
    """
    resp, _ = _complete(messages, **kwargs)
    return resp


def _complete(messages: list, **kwargs):
    """
    两级直连链：Gemini 2.5 Flash → 智谱 glm-4.7-flash。
    """
    # 1. Gemini 2.5 Flash（高质量，免费 1M tokens/天）
    gemini_key = os.environ.get("GEMINI_API_KEY", "")
    if gemini_key:
        try:
            print(f"  [gemini] 使用 {GEMINI_MODEL}…")
            c = OpenAI(api_key=gemini_key, base_url=GEMINI_URL)
            resp = c.chat.completions.create(model=GEMINI_MODEL, messages=messages, **kwargs)
            return resp, "gemini"
        except Exception as e:
            print(f"  [gemini] 不可用 ({type(e).__name__})，切换智谱…")

    # 2. 智谱 glm-4.7-flash（永久免费兜底）
    zhipu_key = os.environ.get("ZHIPU_API_KEY", "")
    if not zhipu_key:
        raise RuntimeError("所有 AI 服务不可用：未配置 GEMINI_API_KEY 或 ZHIPU_API_KEY")
    print(f"  [zhipu] 使用 {ZHIPU_MODEL} 兜底…")
    c = OpenAI(api_key=zhipu_key, base_url=ZHIPU_URL)
    resp = c.chat.completions.create(model=ZHIPU_MODEL, messages=messages, **kwargs)
    return resp, "zhipu"

USER_PROMPT_TEMPLATE = """请对以下 {count} 条内容进行评估。

严格按照以下 JSON 格式返回，不要有任何其他文字，不要有 markdown 代码块：
[
  {{
    "id": "序号，从0开始",
    "score": 评分数字(1-10),
    "reason_zh": "一句话说明价值（20字以内）",
    "title_zh": "中文标题",
    "summary_zh": "中文摘要4-6句，充分展开背景、核心内容和价值，不要过于简短"
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
            art["score"] = art.get("score") or 3
            art["reason_zh"] = art.get("reason_zh") or ""
            art["title_zh"] = art.get("title_zh") or art["title"]
            art["summary_zh"] = art.get("summary_zh") or art["summary"]
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
    summary_fn: 从 article dict 提取送给模型的摘要文本，默认取 summary[:300]。
    调用结束后可通过 get_usage() 获取 token 消耗，get_metrics() 获取模型表现。
    """
    global _usage, _metrics
    _usage   = {"model": "", "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    _metrics = {"batches_total": 0, "batches_parsed": 0}

    if summary_fn is None:
        summary_fn = _default_summary_fn

    for batch_start in range(0, len(articles), batch_size):
        if batch_start > 0:
            time.sleep(2)  # 避免智谱 429 速率限制
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

        _metrics["batches_total"] += 1
        try:
            resp, backend = _complete(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_msg},
                ],
                max_tokens=4096,
                timeout=120,
            )
            # 累计 token 消耗
            if resp.usage:
                _usage["prompt_tokens"]     += resp.usage.prompt_tokens
                _usage["completion_tokens"] += resp.usage.completion_tokens
                _usage["total_tokens"]      += resp.usage.total_tokens
            # 记录实际模型名（优先用响应中的）
            if not _usage["model"]:
                _usage["model"] = getattr(resp, "model", "") or (
                    GEMINI_MODEL if backend == "gemini" else ZHIPU_MODEL
                )
            results = _parse_response(resp.choices[0].message.content or "")
            if results:
                _metrics["batches_parsed"] += 1
            _apply_results(batch, results)
        except Exception as exc:
            print(f"  [ERROR] Scoring batch failed: {exc}")
            for art in batch:
                art["score"] = art.get("score") or 3
                art["reason_zh"] = art.get("reason_zh") or ""
                art["title_zh"] = art.get("title_zh") or art["title"]
                art["summary_zh"] = art.get("summary_zh") or art["summary"]

    # 兜底：若所有批次均失败，确保 model 字段有值
    if not _usage["model"]:
        _usage["model"] = "gateway/blocked"

    return articles
