"""
上报 token 消耗到 token-management 网关。
使用 stdlib urllib，不引入额外依赖。
"""

import json
import os
import urllib.request
import urllib.error
from datetime import datetime

# GLM 定价补充
_GLM_COST_TABLE: dict[str, tuple[float, float]] = {
    "glm-4-flash":   (0.0, 0.0),   # 永久免费
    "glm-4.7-flash": (0.0, 0.0),
    "glm-z1-flash":  (0.0, 0.0),
    "glm-4-air":     (0.001, 0.001),
    "glm-4":         (0.1, 0.1),
}

GATEWAY_URL = os.environ.get("GATEWAY_URL", "http://localhost:8000")
GATEWAY_API_KEY = os.environ.get("GATEWAY_API_KEY", "")

# qwen-max 单价（USD / 1M tokens），与 token-management/config/providers.yaml 保持一致
_COST_TABLE: dict[str, tuple[float, float]] = {
    "qwen-max":   (0.04,  0.12),
    "qwen-plus":  (0.004, 0.012),
    "qwen-turbo": (0.002, 0.006),
    "qwen-long":  (0.0005, 0.002),
}


_ALL_COST = {**_COST_TABLE, **_GLM_COST_TABLE}


def _calc_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    model_base = next((k for k in _ALL_COST if model.startswith(k)), None)
    rates = _ALL_COST.get(model_base or model)
    if not rates:
        return 0.0
    return (input_tokens / 1_000_000) * rates[0] + (output_tokens / 1_000_000) * rates[1]


def _infer_provider(model: str) -> str:
    if any(model.startswith(k) for k in _GLM_COST_TABLE):
        return "zhipu"
    return "qwen"


def report_to_gateway(usage_info: dict, project: str) -> None:
    """
    将一次 scorer 调用的 token 消耗上报至 token-management 网关。

    usage_info 格式（来自 common.scorer.get_usage()）:
      {"model": str, "prompt_tokens": int, "completion_tokens": int, "total_tokens": int}
    project:
      channel 名称，例如 "digest-hub/ai-info"
    """
    if not usage_info or not usage_info.get("total_tokens"):
        return

    model    = usage_info.get("model") or "qwen-max"
    in_t     = usage_info.get("prompt_tokens", 0)
    out_t    = usage_info.get("completion_tokens", 0)
    cost     = _calc_cost(model, in_t, out_t)
    provider = _infer_provider(model)

    payload = {
        "provider":      provider,
        "model":         model,
        "project":       project,
        "input_tokens":  in_t,
        "output_tokens": out_t,
        "cost_usd":      round(cost, 6),
        "latency_ms":    0,
        "status":        "success",
        "request_id":    datetime.now().strftime("%Y%m%d-%H%M%S"),
    }

    url  = GATEWAY_URL.rstrip("/") + "/api/usage/log"
    data = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if GATEWAY_API_KEY:
        headers["Authorization"] = f"Bearer {GATEWAY_API_KEY}"

    # 强制绕过系统代理（http_proxy 会拦截 localhost 请求）
    no_proxy_handler = urllib.request.ProxyHandler({})
    opener = urllib.request.build_opener(no_proxy_handler)

    try:
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        with opener.open(req, timeout=5) as resp:
            result = json.loads(resp.read())
            print(f"  [token-mgmt] 已上报 {result.get('total_tokens', 0):,} tokens "
                  f"({provider}/{model}) → {project}")
    except urllib.error.URLError as e:
        print(f"  [token-mgmt] 上报失败（网关未启动？）: {e.reason}")
    except Exception as e:
        print(f"  [token-mgmt] 上报失败: {e}")
