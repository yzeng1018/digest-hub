"""
通用 Qwen 评分模块。
system_prompt、batch_size、summary_fn 由各 channel 的 config 传入，
使同一套 API 调用逻辑可服务于不同视角的评分需求。
"""

import json
import os
import re
from collections.abc import Callable

import httpx
import openai as _openai
from openai import OpenAI

QWEN_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
QWEN_MODEL    = "qwen-max"
GATEWAY_URL   = os.environ.get("GATEWAY_URL", "http://localhost:8000/v1")
GATEWAY_API_KEY = os.environ.get("GATEWAY_API_KEY", "dummy")

# GLM 兜底（glm-4-flash 永久免费）
GLM_BASE_URL = "https://open.bigmodel.cn/api/paas/v4"
GLM_MODEL    = "glm-4-flash"

# 模块级 usage 累计器，每次 score_articles 调用前重置
_usage: dict = {"model": "", "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}


def get_usage() -> dict:
    """返回最近一次 score_articles 调用的 token 消耗统计。"""
    return dict(_usage)


def _complete(messages: list, model: str = QWEN_MODEL, **kwargs):
    """
    三级 fallback 链：本地网关 → DashScope 直连 → GLM-4-Flash。
    本地网关请求强制绕过系统代理（trust_env=False），避免 http_proxy 拦截 localhost。
    """
    # 1. 本地网关（绕过系统代理）
    try:
        c = OpenAI(
            api_key=GATEWAY_API_KEY,
            base_url=GATEWAY_URL,
            http_client=httpx.Client(trust_env=False),
        )
        resp = c.chat.completions.create(model="free", messages=messages, **kwargs)
        return resp, "gateway"
    except Exception as e:
        print(f"  [gateway] 不可用 ({type(e).__name__})，切换 DashScope…")

    # 2. DashScope 直连
    try:
        api_key = os.environ.get("QWEN_API_KEY") or os.environ.get("DASHSCOPE_API_KEY", "")
        if api_key:
            c = OpenAI(api_key=api_key, base_url=QWEN_BASE_URL)
            resp = c.chat.completions.create(model=model, messages=messages, **kwargs)
            return resp, "dashscope"
    except Exception as e:
        print(f"  [dashscope] 失败 ({type(e).__name__}: {e})，切换 GLM…")

    # 3. GLM 兜底
    glm_key = os.environ.get("ZHIPU_API_KEY", "")
    if not glm_key:
        raise RuntimeError("所有 provider 均失败，且未配置 ZHIPU_API_KEY（GLM 兜底不可用）")
    print(f"  [glm] 使用 {GLM_MODEL} 兜底…")
    c = OpenAI(api_key=glm_key, base_url=GLM_BASE_URL)
    resp = c.chat.completions.create(model=GLM_MODEL, messages=messages, **kwargs)
    return resp, "glm"

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
    调用结束后可通过 get_usage() 获取 token 消耗。
    """
    global _usage
    _usage = {"model": "", "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

    if summary_fn is None:
        summary_fn = _default_summary_fn

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
            # 记录实际模型名（优先用响应中的，否则用请求参数）
            if not _usage["model"]:
                _usage["model"] = getattr(resp, "model", "") or (
                    "gateway/auto" if backend == "gateway" else QWEN_MODEL
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
