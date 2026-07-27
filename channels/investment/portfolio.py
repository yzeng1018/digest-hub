"""Load a privacy-safe public-equity watchlist derived from the portfolio project."""

from __future__ import annotations

import json
import os
from collections import defaultdict
from pathlib import Path


_HERE = Path(__file__).resolve().parent
_FALLBACK_PATH = _HERE / "portfolio_watchlist.json"
_DEFAULT_LOCAL_PATH = _HERE.parents[2] / "portfolio" / "data" / "portfolio.json"
_EQUITY_TYPES = {"stock_a", "stock_hk", "stock_us"}
_FX_TO_CNY = {"CNY": 1.0, "HKD": 0.92, "USD": 7.2}


def _read_json(path: Path):
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def _fallback_watchlist() -> list[dict]:
    return _read_json(_FALLBACK_PATH)


def load_portfolio_watchlist() -> list[dict]:
    """
    Prefer the live sibling portfolio locally. CI falls back to a tracked file that
    contains names/tickers only, never quantities, prices, owners, or notes.
    """
    configured = os.environ.get("PORTFOLIO_DATA_PATH", "").strip()
    live_path = Path(configured).expanduser() if configured else _DEFAULT_LOCAL_PATH
    fallback = _fallback_watchlist()
    metadata = {item["ticker"]: item for item in fallback}

    try:
        payload = _read_json(live_path)
    except (OSError, ValueError, TypeError):
        return [dict(item, priority_value=0) for item in fallback]

    grouped: dict[str, dict] = {}
    values: defaultdict[str, float] = defaultdict(float)
    for holding in payload.get("holdings", []):
        ticker = str(holding.get("ticker") or "").strip()
        if not ticker or holding.get("assetType") not in _EQUITY_TYPES:
            continue
        base = metadata.get(ticker, {})
        grouped.setdefault(
            ticker,
            {
                "name": base.get("name") or holding.get("name") or ticker,
                "ticker": ticker,
                "aliases": base.get("aliases") or [holding.get("name") or ticker],
                "exclude_phrases": base.get("exclude_phrases") or [],
                "sector": base.get("sector") or "其他股票",
            },
        )
        quantity = float(holding.get("quantity") or 0)
        current_price = float(holding.get("currentPrice") or 0)
        # The portfolio stores employee options under stock_us. Rank those by
        # intrinsic value rather than pretending every option is one full share.
        if "期权" in str(holding.get("name") or ""):
            unit_value = max(current_price - float(holding.get("buyPrice") or 0), 0)
        else:
            unit_value = current_price
        values[ticker] += (
            quantity * unit_value * _FX_TO_CNY.get(holding.get("currency"), 1.0)
        )

    for ticker, item in grouped.items():
        item["priority_value"] = round(values[ticker], 2)

    # Preserve manually curated coverage if a holding is temporarily absent locally,
    # while letting the actual portfolio determine which names rank first.
    for item in fallback:
        grouped.setdefault(item["ticker"], dict(item, priority_value=0))
    return sorted(grouped.values(), key=lambda x: -x.get("priority_value", 0))


def portfolio_context(watchlist: list[dict], limit: int = 18) -> str:
    return "、".join(
        f'{item["name"]}({item["ticker"]}，{item.get("sector", "")})'
        for item in watchlist[:limit]
    )
