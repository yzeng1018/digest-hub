#!/usr/bin/env python3
"""
我的持仓分析 · 每日邮件

只读持仓、行情、新闻与新报送，不调 LLM。判定逻辑全在本地规则里：
触发异动或重点事件的持仓展开，其余一行带过——安静的日子邮件会很短。

用法：
    python main.py               取行情并发送
    python main.py --no-email    只生成 HTML
    python main.py --quiet       安静模式（配合 --no-email 调试）

环境变量：
    PORTFOLIO_HOLDINGS   持仓 JSON（GitHub Secret 注入）
"""

import argparse
import json
import os
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from common.mailer import send_html  # noqa: E402

import config  # noqa: E402
import llm  # noqa: E402
from news import build_news  # noqa: E402
from quotes import fetch_quotes  # noqa: E402
from render import render  # noqa: E402

OUTPUT_DIR = Path(__file__).resolve().parent / "output"


def load_portfolio() -> list[dict]:
    raw = os.environ.get("PORTFOLIO_HOLDINGS", "").strip()
    if not raw:
        local = Path(__file__).resolve().parent / "holdings.sample.json"
        if local.exists():
            raw = local.read_text(encoding="utf-8")
        else:
            raise SystemExit("未设置 PORTFOLIO_HOLDINGS 且无本地样本文件")
    data = json.loads(raw)
    return data.get("holdings", data if isinstance(data, list) else [])


def enrich(holdings: list[dict], quotes: dict, news: dict) -> tuple[list, list, dict]:
    """计算市值盈亏，并判定哪些持仓属于「重点」。"""
    alerts, quiet = [], []
    totals = {"value": 0.0, "cost": 0.0, "dayPnl": 0.0}

    for h in holdings:
        t = h["ticker"]
        q = quotes.get(t)
        if not q or q.get("price") is None:
            quiet.append((h, {"price": "-", "chgPct": 0},
                          {"valueCny": 0, "pnlCny": 0, "costCny": 0,
                           "pnlPct": 0, "news": [], "earnings": [], "filings": []}))
            continue

        fx = config.FX.get(h.get("currency", ""), 1.0)
        price = q["price"]
        prev = q.get("prev") or price
        qty = h["quantity"]
        value_cny = price * qty * fx
        cost_cny = (h.get("avgCost") or 0) * qty * fx
        day_pnl_cny = (price - prev) * qty * fx

        bucket = news.get(t, {})
        info = {
            "valueCny": value_cny,
            "costCny": cost_cny,
            "pnlCny": value_cny - cost_cny if cost_cny else 0.0,
            "pnlPct": (value_cny - cost_cny) / cost_cny * 100 if cost_cny else 0.0,
            "news": bucket.get("news") or [],
            "earnings": bucket.get("earnings") or [],
            "filings": bucket.get("filings") or [],
            "llm": {},
        }
        totals["value"] += value_cny
        totals["cost"] += cost_cny
        totals["dayPnl"] += day_pnl_cny

        pct = q.get("chgPct") or 0.0
        has_earnings = bool(info["earnings"]) or any(
            f.get("isEarnings") for f in info["filings"])
        # 6-K / 8-K 这类杂项公告太频繁，只在已经有别的原因时顺带提一句
        notices = [f for f in info["filings"] if not f.get("isEarnings")]

        reasons = []
        if has_earnings:
            reasons.append("财报")
        if abs(pct) >= config.MOVE_PCT:
            reasons.append("异动")
        if notices and reasons:
            reasons.append("公告")

        (alerts if reasons else quiet).append(
            (h, q, info, reasons) if reasons else (h, q, info))

    return alerts, quiet, totals


def _llm_context(alerts: list) -> list:
    """挑最值得问 LLM 的几只：财报优先，其次按振幅。"""
    ranked = sorted(
        alerts,
        key=lambda a: ("财报" not in a[3], -abs(a[1].get("chgPct") or 0)),
    )[:config.LLM_MAX_ITEMS]
    out = []
    for h, q, info, _ in ranked:
        out.append({
            "name": h["name"],
            "ticker": h["ticker"],
            "market": h["market"],
            "sector": h.get("sector", ""),
            "chgPct": q.get("chgPct") or 0.0,
            "pnlPct": info["pnlPct"],
            "news": info["news"],
            "earnings": info["earnings"],
            "filings": info["filings"],
        })
    return out


def attach_llm(alerts: list, overview_items: list) -> str:
    """给重点持仓补上研判，并生成一段组合总览。失败不影响发信。"""
    provider = config.LLM_PROVIDER
    if not llm.available(provider):
        print("LLM 未配置 key，跳过研判", flush=True)
        return ""
    items = _llm_context(alerts)
    print(f"LLM 分析 {len(items)} 只（{provider}）", flush=True)
    results = llm.analyze(items, provider=provider)
    for _, _, info, _ in alerts:
        info["llm"] = {}
    for h, q, info, _ in alerts:
        info["llm"] = results.get(h["ticker"], {})
    hit = sum(1 for i in results.values() if i.get("verdict"))
    print(f"LLM 研判完成 {hit}/{len(items)}", flush=True)
    return llm.summarize_market(overview_items, provider=provider)


def main() -> None:
    ap = argparse.ArgumentParser(description="我的持仓分析日报")
    ap.add_argument("--no-email", action="store_true")
    ap.add_argument("--no-news", action="store_true", help="跳过新闻与报送（快速调试）")
    ap.add_argument("--no-llm", action="store_true", help="跳过 LLM 研判")
    ap.add_argument("--date", help="覆盖日期，格式 YYYY-MM-DD")
    args = ap.parse_args()

    date_str = args.date or datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d")
    holdings = load_portfolio()
    print(f"持仓 {len(holdings)} 只 · {date_str}", flush=True)

    quotes = fetch_quotes(holdings)
    print(f"行情取到 {len(quotes)}/{len(holdings)}", flush=True)

    news = {} if args.no_news else build_news(holdings, hours=config.NEWS_HOURS)
    if not args.no_news:
        got = sum(1 for v in news.values() if v["news"] or v["filings"])
        print(f"新闻/报送命中 {got} 只", flush=True)

    alerts, quiet, totals = enrich(holdings, quotes, news)
    tally = Counter(r for _, _, _, rs in alerts for r in rs)
    print(f"重点 {len(alerts)} 只 · 无异动 {len(quiet)} 只 · 触发原因 {dict(tally)}",
          flush=True)

    overview = ""
    if not args.no_llm:
        summary_items = []
        for h, q, info in quiet:
            summary_items.append({
                "name": h["name"], "ticker": h["ticker"],
                "chgPct": q.get("chgPct") or 0.0, "headline": "",
            })
        for h, q, info, _ in alerts:
            top = (info.get("earnings") or info.get("news") or [{}])[0]
            summary_items.append({
                "name": h["name"], "ticker": h["ticker"],
                "chgPct": q.get("chgPct") or 0.0,
                "headline": top.get("title", ""),
            })
        overview = attach_llm(alerts, summary_items)

    payload = {
        "date": date_str,
        "count": len(holdings),
        "overview": overview,
        "totalValueCny": totals["value"],
        "totalPnlCny": totals["value"] - totals["cost"],
        "dayPnlCny": totals["dayPnl"],
        "alerts": alerts,
        "quiet": quiet,
    }
    html = render(payload)

    try:
        OUTPUT_DIR.mkdir(exist_ok=True)
    except (FileExistsError, OSError):
        pass
    out_path = OUTPUT_DIR / f"{date_str}.html"
    out_path.write_text(html, encoding="utf-8")
    print(f"HTML → {out_path}", flush=True)

    if not args.no_email:
        send_html(f"我的持仓分析 · {date_str}", html)


if __name__ == "__main__":
    main()
