"""
投资情报抓取器。
信源：RSS（Crunchbase/TechCrunch/a16z/投资界等）+ Hacker News API（投资关键词过滤）
"""

import re
import time
from datetime import datetime, timezone, timedelta

import feedparser
import requests

from config import SOURCES, HN_TOP_COUNT, TIME_WINDOW_HOURS


_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

_CUTOFF = timedelta(hours=TIME_WINDOW_HOURS)


def _parse_dt(entry) -> datetime | None:
    for attr in ("published_parsed", "updated_parsed"):
        t = getattr(entry, attr, None)
        if t:
            try:
                return datetime(*t[:6], tzinfo=timezone.utc)
            except Exception:
                pass
    return None


def _is_recent(entry) -> bool:
    dt = _parse_dt(entry)
    if dt is None:
        return True  # 无时间信息时保留
    return (datetime.now(timezone.utc) - dt) <= _CUTOFF


def _fetch_rss(source: dict) -> list[dict]:
    articles = []
    try:
        resp = requests.get(source["url"], timeout=15, headers=_HEADERS)
        feed = feedparser.parse(resp.content)
    except Exception as exc:
        print(f"  [WARN] {source['name']}: {exc}")
        return []

    for entry in feed.entries:
        if not _is_recent(entry):
            continue
        title   = getattr(entry, "title", "").strip()
        summary = getattr(entry, "summary", "") or getattr(entry, "description", "")
        url     = getattr(entry, "link", "")
        if not title or not url:
            continue

        # 清理 HTML tags
        summary = re.sub(r"<[^>]+>", " ", summary)
        summary = " ".join(summary.split())[:500]

        articles.append({
            "id":       url,
            "title":    title,
            "summary":  summary,
            "url":      url,
            "source":   source["name"],
            "platform": "News",
            "lang":     source["lang"],
            "priority": source.get("priority", 2),
        })
    return articles


def _fetch_hn() -> list[dict]:
    """抓取 Hacker News top stories，过滤与投资/创业相关的条目。"""
    INVEST_KEYWORDS = {
        "funding", "raises", "raised", "series", "ipo", "acquisition",
        "acquires", "acquired", "merger", "startup", "venture", "billion",
        "million", "valuation", "investor", "投资", "融资", "并购", "上市",
        "estimate", "round",
    }
    articles = []
    try:
        resp = requests.get(
            "https://hacker-news.firebaseio.com/v0/topstories.json",
            timeout=10,
        )
        story_ids = resp.json()[:50]
    except Exception as exc:
        print(f"  [WARN] HN API: {exc}")
        return []

    cutoff = datetime.now(timezone.utc) - _CUTOFF
    count = 0
    for sid in story_ids:
        if count >= HN_TOP_COUNT:
            break
        try:
            item = requests.get(
                f"https://hacker-news.firebaseio.com/v0/item/{sid}.json",
                timeout=8,
            ).json()
        except Exception:
            continue
        if not item or item.get("type") != "story":
            continue

        ts = item.get("time", 0)
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        if dt < cutoff:
            continue

        title = item.get("title", "")
        url   = item.get("url", f"https://news.ycombinator.com/item?id={sid}")

        title_lower = title.lower()
        if not any(kw in title_lower for kw in INVEST_KEYWORDS):
            continue

        articles.append({
            "id":        url,
            "title":     title,
            "summary":   f"HN score: {item.get('score', 0)} · {item.get('descendants', 0)} comments",
            "url":       url,
            "source":    "Hacker News",
            "platform":  "News",
            "lang":      "en",
            "priority":  2,
            "_hn_score": item.get("score", 0),
        })
        count += 1
        time.sleep(0.1)

    return articles


def fetch_all() -> list[dict]:
    articles = []
    for source in SOURCES:
        items = _fetch_rss(source)
        articles.extend(items)
        print(f"  {source['name']}: {len(items)} 条")

    hn_items = _fetch_hn()
    articles.extend(hn_items)
    print(f"  Hacker News (投资相关): {len(hn_items)} 条")

    print(f"共抓取 {len(articles)} 条投资情报。")
    return articles
