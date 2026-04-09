"""
从 RSS 订阅源抓取产品设计相关文章。
"""

import time
import re
import html
from datetime import datetime, timezone, timedelta

import urllib3
import feedparser
import requests

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from config import SOURCES, TIME_WINDOW_HOURS

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def _clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    return " ".join(text.split())[:500]


def _parse_time(entry) -> datetime | None:
    for field in ("published_parsed", "updated_parsed"):
        t = getattr(entry, field, None)
        if t:
            try:
                return datetime(*t[:6], tzinfo=timezone.utc)
            except Exception:
                pass
    return None


def fetch_rss(source: dict, cutoff: datetime) -> list[dict]:
    articles = []
    try:
        resp = requests.get(source["url"], headers=HEADERS, timeout=12, verify=False)
        feed = feedparser.parse(resp.content)
    except Exception as exc:
        print(f"  [WARN] {source['name']}: {exc}")
        return articles

    for entry in feed.entries:
        pub = _parse_time(entry)
        if pub and pub < cutoff:
            continue

        title = _clean_text(getattr(entry, "title", ""))
        if not title:
            continue

        summary = _clean_text(
            getattr(entry, "summary", "")
            or getattr(entry, "description", "")
        )
        url = getattr(entry, "link", "")

        articles.append({
            "id": url or title,
            "title": title,
            "title_zh": "",
            "summary": summary,
            "summary_zh": "",
            "url": url,
            "source": source["name"],
            "lang": source["lang"],
            "category": source["category"],
            "priority": source.get("priority", 1),
            "published": pub.isoformat() if pub else "",
            "score": 0,
            "reason_zh": "",
        })
    return articles


def fetch_all() -> list[dict]:
    cutoff = datetime.now(tz=timezone.utc) - timedelta(hours=TIME_WINDOW_HOURS)
    all_articles: list[dict] = []
    seen_urls: set[str] = set()

    print(f"Fetching {len(SOURCES)} product/design RSS sources …")

    for source in SOURCES:
        print(f"  → {source['name']}")
        for art in fetch_rss(source, cutoff):
            key = art["url"] or art["title"]
            if key and key not in seen_urls:
                seen_urls.add(key)
                all_articles.append(art)

    print(f"Fetched {len(all_articles)} raw articles.")
    return all_articles
