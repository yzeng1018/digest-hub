"""Rolling sent-story history for cross-day deduplication and company rotation."""

from __future__ import annotations

import json
import os
import re
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_PATH = _ROOT / "data" / "digest-history" / "investment.json"
_TRACKING_PARAMS = {"gclid", "fbclid", "ref", "source"}


def _history_path() -> Path:
    configured = os.environ.get("INVESTMENT_HISTORY_PATH", "").strip()
    return Path(configured).expanduser() if configured else _DEFAULT_PATH


def _parse_day(value: str) -> date | None:
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def _canonical_url(value: str) -> str:
    """Drop fragments and common tracking parameters while keeping story identity."""
    if not value:
        return ""
    try:
        parts = urlsplit(value.strip())
        query = [
            (key, val) for key, val in parse_qsl(parts.query, keep_blank_values=True)
            if not key.lower().startswith("utm_") and key.lower() not in _TRACKING_PARAMS
        ]
        path = parts.path.rstrip("/") or "/"
        return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, urlencode(query), ""))
    except ValueError:
        return value.strip()


def _title_tokens(value: str) -> set[str]:
    """Tokenize Latin words and Chinese bigrams so Chinese titles are comparable."""
    text = re.sub(r"\s+-\s+[^-]{1,40}$", "", value.casefold()).strip()
    latin = set(re.findall(r"[a-z0-9]+", text))
    cjk_runs = re.findall(r"[\u4e00-\u9fff]+", text)
    cjk = {
        run[index:index + 2]
        for run in cjk_runs
        for index in range(max(1, len(run) - 1))
        if run[index:index + 2]
    }
    stops = {"a", "an", "the", "in", "of", "to", "and", "for", "on", "with"}
    return (latin - stops) | cjk


def _title_similarity(left: str, right: str) -> float:
    a, b = _title_tokens(left), _title_tokens(right)
    if not a or not b:
        return 0.0
    return 2 * len(a & b) / (len(a) + len(b))


def load_history(retention_days: int, *, today: date | None = None) -> list[dict]:
    today = today or datetime.now().date()
    cutoff = today - timedelta(days=retention_days)
    try:
        payload = json.loads(_history_path().read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return []
    records = payload if isinstance(payload, list) else payload.get("items", [])
    return [item for item in records if (_parse_day(item.get("date", "")) or date.min) >= cutoff]


def filter_seen_articles(
    articles: list[dict], history: list[dict], *, similarity_threshold: float,
    company_cooldown_days: int, today: date | None = None,
) -> list[dict]:
    """Remove already-sent stories and annotate recently featured companies."""
    today = today or datetime.now().date()
    seen_urls = {_canonical_url(item.get("url", "")) for item in history if item.get("url")}
    history_titles = [item.get("title", "") for item in history if item.get("title")]
    company_last_seen: dict[str, int] = {}
    for item in history:
        item_day = _parse_day(item.get("date", ""))
        if not item_day:
            continue
        age = (today - item_day).days
        for company in item.get("companies", []):
            key = str(company).casefold()
            company_last_seen[key] = min(age, company_last_seen.get(key, age))

    kept = []
    removed = 0
    for article in articles:
        url = _canonical_url(article.get("url", ""))
        title = article.get("title", "")
        duplicate = bool(url and url in seen_urls) or any(
            _title_similarity(title, old_title) >= similarity_threshold
            for old_title in history_titles
        )
        if duplicate:
            removed += 1
            continue

        ages = []
        if article.get("platform") in {"Portfolio", "Watchlist"}:
            ages = [
                company_last_seen[name.casefold()]
                for name in article.get("portfolio_matches", [])
                if name.casefold() in company_last_seen
            ]
        if ages:
            age = min(ages)
            if age < company_cooldown_days:
                article["history_penalty"] = round(
                    2.0 * (company_cooldown_days - age) / company_cooldown_days, 2
                )
        kept.append(article)

    print(f"跨日去重：{len(articles)} → {len(kept)} 条（过滤已发 {removed} 条）。")
    return kept


def save_sent_articles(
    articles: list[dict], history: list[dict], retention_days: int,
    *, today: date | None = None,
) -> None:
    today = today or datetime.now().date()
    new_items = [
        {
            "date": today.isoformat(),
            "title": article.get("title", ""),
            "url": _canonical_url(article.get("url", "")),
            "companies": (
                article.get("portfolio_matches", [])
                if article.get("platform") in {"Portfolio", "Watchlist"}
                else []
            ),
        }
        for article in articles
    ]
    cutoff = today - timedelta(days=retention_days)
    retained = [
        item for item in history
        if (_parse_day(item.get("date", "")) or date.min) >= cutoff
    ]
    unique: dict[tuple[str, str], dict] = {}
    for item in retained + new_items:
        unique[(item.get("date", ""), item.get("url") or item.get("title", ""))] = item
    path = _history_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"items": list(unique.values())}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
