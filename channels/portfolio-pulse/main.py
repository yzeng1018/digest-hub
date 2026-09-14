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
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from common.mailer import send_html  # noqa: E402

import config  # noqa: E402
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


def _is_earnings_news(news: list[dict]) -> bool:
    for n in news:
        low = n["title"].lower()
        if any(k.lower() in low for k in config.EARNINGS_KEYWORDS):
            return True
    return False


def enrich(holdings: list[dict], quotes: dict, news: dict) -> tuple[list, list, dict]:
    """计算市值盈亏，并判定哪些持仓属于「重点」。"""
    alerts, quiet = [], []
    totals = {"value": 0.0, "cost": 0.0, "dayPnl": 0.0}

    for h in holdings:
        t = h["ticker"]
        q = quotes.get(t)
        if not q or q.get("price") is None:
            quiet.append((h, {"price": "-", "chgPct": 0}, {"valueCny": 0, "pnlCny": 0, "costCny": 0}))
            continue

        fx = config.FX.get(h.get("currency", ""), 1.0)
        price = q["price"]
        prev = q.get("prev") or price
        qty = h["quantity"]
        value_cny = price * qty * fx
        cost_cny = (h.get("avgCost") or 0) * qty * fx
        day_pnl_cny = (price - prev) * qty * fx

        info = {
            "valueCny": value_cny,
            "costCny": cost_cny,
            "pnlCny": value_cny - cost_cny if cost_cny else 0.0,
            "news": news.get(t, {}).get("news") or [],
            "filings": news.get(t, {}).get("filings") or [],
        }
        totals["value"] += value_cny
        totals["cost"] += cost_cny
        totals["dayPnl"] += day_pnl_cny

        pct = q.get("chgPct") or 0.0
        reasons = []
        if abs(pct) >= config.MOVE_PCT:
            reasons.append("异动")
        if info["filings"]:
            reasons.append("新报送")
        if _is_earnings_news(info["news"]):
            reasons.append("业绩相关")

        (alerts if reasons else quiet).append((h, q, info, reasons) if reasons else (h, q, info))

    return alerts, quiet, totals


def main() -> None:
    ap = argparse.ArgumentParser(description="我的持仓分析日报")
    ap.add_argument("--no-email", action="store_true")
    ap.add_argument("--no-news", action="store_true", help="跳过新闻与报送（快速调试）")
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
    print(f"重点 {len(alerts)} 只 · 无异动 {len(quiet)} 只", flush=True)

    payload = {
        "date": date_str,
        "count": len(holdings),
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
