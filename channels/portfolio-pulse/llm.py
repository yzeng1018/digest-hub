"""LLM 研判层。

直接走 OpenAI 兼容的 HTTP 接口，不装 SDK：openai 2.x 在本机导入要两分钟以上，
而这个频道每天只发几条短请求，不值得为此拖进整套依赖。

无 key、超时或返回异常时一律静默降级——研判是加分项，不该挡住邮件发出。
"""

import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor

import requests

DEEPSEEK_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-flash")
QWEN_URL = os.environ.get(
    "QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"
)
QWEN_MODEL = os.environ.get("QWEN_MODEL", "qwen-max")

PROVIDERS = {
    "deepseek": {
        "base_url": DEEPSEEK_URL,
        "api_key": os.environ.get("DEEPSEEK_API_KEY", ""),
        "model": DEEPSEEK_MODEL,
    },
    "qwen": {
        "base_url": QWEN_URL,
        "api_key": os.environ.get("QWEN_API_KEY")
        or os.environ.get("DASHSCOPE_API_KEY", ""),
        "model": QWEN_MODEL,
    },
}

MARKET_LABEL = {"US": "美股", "HK": "港股", "A": "A股"}

SYSTEM = """你是一位给个人投资者做持仓复盘的分析师。只依据给出的行情与新闻标题做判断。
要求：中文、克制、具体，不写套话。没有依据就说"信息不足"，绝不编造数字。
只返回 JSON，不要任何解释或代码块外的文字。"""

TEMPLATE = """持仓：{name}（{ticker}，{market}，{sector}）
当日涨跌：{chg}%；相对成本：{pnl}
财报/业绩相关新闻标题：
{earnings}
其他新闻标题：
{news}
官方报送（SEC）：{filings}

请输出：
{{"verdict":"一句话说明今天为什么值得关注，40字内",
 "driver":"个股|行业|大盘|财报|信息不足",
 "earnings":"财报要点：营收、净利、同比、指引，用分号分隔；没有财报信息则空字符串",
 "watch":"接下来该盯什么，30字内"}}"""


def _provider(name: str) -> dict:
    return PROVIDERS.get(name, PROVIDERS["deepseek"])


def available(provider: str = "deepseek") -> bool:
    return bool(_provider(provider)["api_key"])


def _chat(messages: list[dict], provider: str = "deepseek",
          timeout: int = 60, max_tokens: int = 400) -> str:
    cfg = _provider(provider)
    if not cfg["api_key"]:
        raise RuntimeError(f"未配置 {provider} API key")
    body = {
        "model": cfg["model"],
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": max_tokens,
    }
    if provider == "deepseek":
        # 推理型模型默认会先想一大段，这里只要结论
        body["thinking"] = {"type": "disabled"}
    resp = requests.post(
        cfg["base_url"].rstrip("/") + "/chat/completions",
        headers={
            "Authorization": f"Bearer {cfg['api_key']}",
            "Content-Type": "application/json",
        },
        json=body,
        timeout=timeout,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def _parse(text: str) -> dict:
    """尽力从返回里抠出 JSON，抠不出来就把整段当结论。"""
    if not text:
        return {}
    cleaned = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start >= 0 and end > start:
        try:
            data = json.loads(cleaned[start:end + 1])
            if isinstance(data, dict):
                return {k: str(v).strip() for k, v in data.items() if v}
        except json.JSONDecodeError:
            pass
    return {"verdict": cleaned[:200]}


def _fmt_titles(items: list[dict], limit: int = 6) -> str:
    if not items:
        return "（无）"
    return "\n".join(f"- {n.get('title', '')}" for n in items[:limit])


def analyze_one(item: dict, provider: str = "deepseek") -> dict:
    """item 需含 name/ticker/market/sector/chgPct/pnlPct/news/earnings/filings。"""
    filings = item.get("filings") or []
    prompt = TEMPLATE.format(
        name=item.get("name", ""),
        ticker=item.get("ticker", ""),
        market=MARKET_LABEL.get(item.get("market", ""), item.get("market", "")),
        sector=item.get("sector", "未分类"),
        chg=f"{item.get('chgPct') or 0:+.2f}",
        pnl=f"{item.get('pnlPct') or 0:+.1f}%",
        earnings=_fmt_titles(item.get("earnings")),
        news=_fmt_titles(item.get("news")),
        filings="、".join(f"{f['form']} {f['date']}" for f in filings) or "（无）",
    )
    try:
        raw = _chat(
            [{"role": "system", "content": SYSTEM},
             {"role": "user", "content": prompt}],
            provider=provider,
        )
        result = _parse(raw)
    except Exception as exc:
        print(f"[WARN] LLM 分析 {item.get('ticker')} 失败: {exc}", flush=True)
        return {}
    if not result.get("verdict"):
        return {}
    return result


def analyze(items: list[dict], provider: str = "deepseek",
            workers: int = 4) -> dict[str, dict]:
    """并发分析多只持仓，返回 {ticker: 研判结果}。"""
    if not items or not available(provider):
        return {}
    out: dict[str, dict] = {}
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        futures = {
            pool.submit(analyze_one, it, provider): it["ticker"] for it in items
        }
        for fut, ticker in futures.items():
            try:
                res = fut.result()
            except Exception as exc:
                print(f"[WARN] LLM {ticker} 异常: {exc}", flush=True)
                continue
            if res:
                out[ticker] = res
            time.sleep(0)
    return out


def summarize_market(items: list[dict], provider: str = "deepseek") -> str:
    """给整封邮件写一句总览：今天整体是什么行情、哪几只是主线。"""
    if not items or not available(provider):
        return ""
    lines = "\n".join(
        f"- {it['name']}（{it['ticker']}）{it.get('chgPct') or 0:+.2f}%"
        + (f"，{it.get('headline', '')}" if it.get("headline") else "")
        for it in items[:24]
    )
    prompt = (
        "以下是今日个人持仓的涨跌与各自要点。请用两句话写一段总览："
        "第一句说整体（今天是什么行情、组合大致表现），"
        "第二句点出今天真正的主线是哪一两只、因为什么。"
        "中文，80 字内，不要客套。\n\n" + lines
    )
    try:
        return _chat(
            [{"role": "system", "content": SYSTEM},
             {"role": "user", "content": prompt}],
            provider=provider,
            max_tokens=200,
        ).strip()
    except Exception as exc:
        print(f"[WARN] LLM 总览失败: {exc}", flush=True)
        return ""
