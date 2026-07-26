"""公共评分模块，以及 DeepSeek V4 Flash / Qwen Max A/B 轮转。"""

import json
import math
import os
import re
import time
from collections.abc import Callable
from datetime import date, datetime
from zoneinfo import ZoneInfo

from openai import OpenAI

DEEPSEEK_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-flash")
QWEN_URL = os.environ.get(
    "QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"
)
QWEN_MODEL = os.environ.get("QWEN_MODEL", "qwen-max")

_CHANNEL_SLOTS = {
    "digest-hub/crypto": 0,
    "digest-hub/investment": 0,
    "digest-hub/ai-info": 1,
    "digest-hub/product-radar": 1,
    "digest-hub/growth-weekly": 0,
    "digest-hub/product-radar-weekly": 1,
}


def select_model(
    channel: str | None = None,
    date_string: str | None = None,
    override: str | None = None,
) -> str:
    """返回 deepseek 或 qwen；参数可注入，便于本地验证轮转表。"""
    channel = channel or os.environ.get("CHANNEL_NAME", "digest-hub")
    date_string = date_string or os.environ.get("MODEL_AB_DATE") or datetime.now(
        ZoneInfo("Asia/Shanghai")
    ).strftime("%Y-%m-%d")
    override = (override or os.environ.get("MODEL_AB_OVERRIDE", "")).lower()
    if override in {"deepseek", "qwen"}:
        return override

    slot = _CHANNEL_SLOTS.get(channel, sum(map(ord, channel)) % 2)
    current = date.fromisoformat(date_string)
    epoch_days = (current - date(1970, 1, 1)).days
    return "deepseek" if (epoch_days + slot) % 2 == 0 else "qwen"


_CHANNEL = os.environ.get("CHANNEL_NAME", "digest-hub")
_AB_DATE = os.environ.get("MODEL_AB_DATE") or datetime.now(
    ZoneInfo("Asia/Shanghai")
).strftime("%Y-%m-%d")
_SELECTED_PROVIDER = select_model(_CHANNEL, _AB_DATE)
_active_provider: str | None = None

_usage: dict = {
    "model": "", "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0,
    "scheduled_provider": _SELECTED_PROVIDER, "experiment_date": _AB_DATE,
}
_metrics: dict = {"batches_total": 0, "batches_parsed": 0}


def get_usage() -> dict:
    return dict(_usage)


def get_metrics(articles: list[dict]) -> dict:
    total = _metrics["batches_total"]
    parsed = _metrics["batches_parsed"]
    parse_rate = parsed / total if total else 0.0
    scores = [a.get("score", 0) for a in articles if a.get("score", 0) > 0]
    if len(scores) >= 2:
        mean = sum(scores) / len(scores)
        score_spread = math.sqrt(sum((s - mean) ** 2 for s in scores) / len(scores))
    else:
        score_spread = 0.0
    translated = sum(
        1 for a in articles if a.get("title_zh") and a["title_zh"] != a.get("title")
    )
    translation_rate = translated / len(articles) if articles else 0.0
    perf_score = round(
        parse_rate * 4
        + min(score_spread / 3, 1) * 3
        + translation_rate * 3,
        2,
    )
    return {
        "parse_rate": round(parse_rate, 3),
        "score_spread": round(score_spread, 2),
        "translation_rate": round(translation_rate, 3),
        "perf_score": perf_score,
        "article_count": len(articles),
    }


def _provider_config(provider: str) -> dict:
    if provider == "deepseek":
        return {
            "provider": provider,
            "base_url": DEEPSEEK_URL,
            "api_key": os.environ.get("DEEPSEEK_API_KEY", ""),
            "model": DEEPSEEK_MODEL,
        }
    return {
        "provider": "qwen",
        "base_url": QWEN_URL,
        "api_key": os.environ.get("QWEN_API_KEY")
        or os.environ.get("DASHSCOPE_API_KEY", ""),
        "model": QWEN_MODEL,
    }


def _call_provider(config: dict, messages: list, **kwargs):
    if not config["api_key"]:
        raise RuntimeError(f"未配置 {config['provider']} API key")
    client = OpenAI(api_key=config["api_key"], base_url=config["base_url"])
    if config["provider"] == "deepseek":
        kwargs["extra_body"] = {"thinking": {"type": "disabled"}}
    return client.chat.completions.create(
        model=config["model"], messages=messages, **kwargs
    )


def _complete(messages: list, **kwargs):
    global _active_provider
    fallback = "qwen" if _SELECTED_PROVIDER == "deepseek" else "deepseek"
    first_error: Exception | None = None
    candidates = (_active_provider,) if _active_provider else (_SELECTED_PROVIDER, fallback)
    print(f"  [A/B] {_AB_DATE} · {_CHANNEL} → {_active_provider or _SELECTED_PROVIDER}")
    for provider in candidates:
        config = _provider_config(provider)
        try:
            response = _call_provider(config, messages, **kwargs)
            if provider != _SELECTED_PROVIDER:
                print(f"  [A/B] {_SELECTED_PROVIDER} 不可用，已降级到 {provider}")
            _active_provider = provider
            return response, provider
        except Exception as exc:
            first_error = first_error or exc
            print(f"  [{provider}] 调用失败: {exc}")
    raise first_error or RuntimeError("DeepSeek 与 Qwen 均不可用")


def call_ai(messages: list, **kwargs):
    response, _ = _complete(messages, **kwargs)
    return response


USER_PROMPT_TEMPLATE = """请对以下 {count} 条内容进行评估。

严格按照以下 JSON 格式返回，不要有任何其他文字，不要有 markdown 代码块：
[
  {{
    "id": "序号，从0开始",
    "score": 评分数字(1-10),
    "reason_zh": "一句话说明价值（20字以内）",
    "title_zh": "中文标题",
    "summary_zh": "中文摘要4-6句，充分展开背景、核心内容和价值，不要过于简短"
  }}
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
    index = {str(r.get("id")): r for r in results}
    for i, art in enumerate(articles):
        result = index.get(str(i))
        if not result:
            art["score"] = art.get("score") or 3
            art["reason_zh"] = art.get("reason_zh") or ""
            art["title_zh"] = art.get("title_zh") or art["title"]
            art["summary_zh"] = art.get("summary_zh") or art["summary"]
            continue
        art["score"] = int(result.get("score", 3))
        art["reason_zh"] = result.get("reason_zh", "")
        art["title_zh"] = result.get("title_zh") or art["title"]
        art["summary_zh"] = result.get("summary_zh") or art["summary"]


def score_articles(
    articles: list[dict],
    system_prompt: str,
    batch_size: int = 10,
    summary_fn: Callable[[dict], str] | None = None,
) -> list[dict]:
    global _usage, _metrics
    _usage = {
        "model": "", "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0,
        "scheduled_provider": _SELECTED_PROVIDER, "experiment_date": _AB_DATE,
    }
    _metrics = {"batches_total": 0, "batches_parsed": 0}
    summary_fn = summary_fn or _default_summary_fn

    for batch_start in range(0, len(articles), batch_size):
        if batch_start:
            time.sleep(2)
        batch = articles[batch_start:batch_start + batch_size]
        print(f"  评分 [{batch_start + 1}–{batch_start + len(batch)}] …")
        items = [
            {
                "id": str(i), "platform": art.get("platform", ""),
                "source": art["source"], "lang": art["lang"],
                "title": art["title"], "summary": summary_fn(art),
            }
            for i, art in enumerate(batch)
        ]
        user_msg = USER_PROMPT_TEMPLATE.format(
            count=len(batch), articles_json=json.dumps(items, ensure_ascii=False, indent=2)
        )
        _metrics["batches_total"] += 1
        try:
            response, backend = _complete(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_msg},
                ],
                max_tokens=8192,
                timeout=120,
            )
            if response.usage:
                _usage["prompt_tokens"] += response.usage.prompt_tokens
                _usage["completion_tokens"] += response.usage.completion_tokens
                _usage["total_tokens"] += response.usage.total_tokens
            if not _usage["model"]:
                _usage["model"] = getattr(response, "model", "") or _provider_config(backend)["model"]
            results = _parse_response(response.choices[0].message.content or "")
            if results:
                _metrics["batches_parsed"] += 1
            _apply_results(batch, results)
        except Exception as exc:
            print(f"  [ERROR] Scoring batch failed: {exc}")
            _apply_results(batch, [])

    if not _usage["model"]:
        _usage["model"] = "gateway/blocked"
    return articles
