#!/usr/bin/env python3
"""
从 portfolio 项目的 portfolio.json 提取实际持仓股票，产出精简 JSON，
供 portfolio-pulse 频道使用。

用法：
    python sync_holdings.py                        打印精简持仓 JSON
    python sync_holdings.py --out holdings.json    写到文件
    python sync_holdings.py --set-secret            直接写入 GitHub Secret

只保留 assetType 为 stock_hk / stock_us / stock_a 且 quantity > 0 的条目；
基金会、货币基金、稳定币、房产、现金一律排除——它们不需要行业跟踪。
同一 ticker 的多条记录（不同券商 / 夫妻共同账户）会合并，数量相加、
成本按数量加权平均。
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

PORTFOLIO_JSON = Path(
    "/Users/zengyan/Desktop/yan-codebase/portfolio/data/portfolio.json"
)
REPO = "yzeng1018/digest-hub"
SECRET_NAME = "PORTFOLIO_HOLDINGS"

STOCK_TYPES = {"stock_hk": "HK", "stock_us": "US", "stock_a": "A"}

# 行业归属，用于分组与「同行业联动」判断。新增持仓时在此补一行即可。
SECTOR = {
    "1024.HK": "互联网 · 短视频",
    "0700.HK": "互联网 · 社交游戏",
    "9988.HK": "互联网 · 电商云",
    "3690.HK": "互联网 · 本地生活",
    "TCOM": "互联网 · 在线旅游",
    "PDD": "互联网 · 电商",
    "DIDIY": "出行 · 网约车",
    "SY": "互联网 · 医美平台",
    "0981.HK": "半导体 · 晶圆代工",
    "1810.HK": "消费电子 · 手机IoT",
    "FIG": "软件 · 设计协作",
    "DUOL": "教育科技",
    "SOFI": "金融科技 · 消费信贷",
    "XYZ": "金融科技 · 支付",
    "LU": "金融科技 · 财富管理",
    "9866.HK": "新能源车 · 整车",
    "002594": "新能源车 · 整车",
    "300750": "新能源 · 动力电池",
    "2252.HK": "医疗器械 · 手术机器人",
    "600030": "金融 · 券商",
    "600036": "金融 · 银行",
    "601318": "金融 · 保险",
    "600519": "消费 · 白酒",
    "9992.HK": "消费 · 潮玩",
}


def normalize_ticker(raw: str, market: str) -> str:
    """港交所代码统一成 4 位 .HK，去掉多余前导零差异。"""
    t = (raw or "").strip().upper()
    if market == "HK":
        code = t.replace(".HK", "")
        code = code.lstrip("0").rjust(4, "0") if code.isdigit() else code
        return f"{code}.HK"
    return t


def load_holdings(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    merged: dict[tuple[str, str], dict] = {}

    for item in data.get("holdings", []):
        market = STOCK_TYPES.get(item.get("assetType", ""))
        if not market:
            continue
        qty = float(item.get("quantity") or 0)
        if qty <= 0:
            continue
        ticker = normalize_ticker(item.get("ticker", ""), market)
        if not ticker:
            continue

        key = (market, ticker)
        cost = float(item.get("buyPrice") or 0)
        cur = merged.get(key)
        if cur is None:
            merged[key] = {
                "ticker": ticker,
                "name": item.get("name", ticker).split("(")[0].split("（")[0].strip(),
                "market": market,
                "sector": SECTOR.get(ticker, "未分类"),
                "quantity": qty,
                "avgCost": cost,
                "currency": item.get("currency", ""),
            }
        else:
            total = cur["quantity"] + qty
            cur["avgCost"] = (
                (cur["avgCost"] * cur["quantity"] + cost * qty) / total
                if total
                else 0
            )
            cur["quantity"] = total

    out = sorted(
        merged.values(),
        key=lambda x: ({"US": 0, "HK": 1, "A": 2}[x["market"]], x["ticker"]),
    )
    for h in out:
        h["quantity"] = round(h["quantity"], 4)
        h["avgCost"] = round(h["avgCost"], 4)
    return out


def set_secret(payload: str) -> None:
    print(f"写入 GitHub Secret {SECRET_NAME} → {REPO}")
    proc = subprocess.run(
        ["gh", "secret", "set", SECRET_NAME, "--repo", REPO, "--body", payload],
        capture_output=True,
        text=True,
        env={
            **__import__("os").environ,
            "https_proxy": "",
            "http_proxy": "",
            "HTTPS_PROXY": "",
            "HTTP_PROXY": "",
        },
    )
    if proc.returncode == 0:
        print("✓ 已更新")
    else:
        print(f"✗ 失败: {proc.stderr.strip()}")
        sys.exit(1)


def main() -> None:
    ap = argparse.ArgumentParser(description="同步持仓到 portfolio-pulse")
    ap.add_argument("--source", default=str(PORTFOLIO_JSON), help="portfolio.json 路径")
    ap.add_argument("--out", help="输出文件路径（默认只打印）")
    ap.add_argument("--set-secret", action="store_true", help="写入 GitHub Secret")
    args = ap.parse_args()

    src = Path(args.source)
    if not src.exists():
        print(f"✗ 找不到 {src}")
        sys.exit(1)

    holdings = load_holdings(src)
    payload = {
        "updated": __import__("datetime").date.today().isoformat(),
        "count": len(holdings),
        "holdings": holdings,
    }
    text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))

    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
        print(f"✓ {len(holdings)} 条已写入 {args.out}")
    elif args.set_secret:
        set_secret(text)
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
