"""
Fetches articles from RSS feeds and Hacker News API.
Returns a unified list of article dicts.
"""

import time
import re
import html
from datetime import datetime, timezone, timedelta

import urllib3
import feedparser
import requests

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from config import SOURCES, HN_TOP_COUNT, TIME_WINDOW_HOURS

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def _clean_text(text: str) -> str:
    """Strip HTML tags and normalise whitespace."""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    return " ".join(text.split())[:500]


def _parse_time(entry) -> datetime | None:
    """Return a UTC-aware datetime from a feedparser entry, or None."""
    for field in ("published_parsed", "updated_parsed"):
        t = getattr(entry, field, None)
        if t:
            try:
                return datetime(*t[:6], tzinfo=timezone.utc)
            except Exception:
                pass
    return None


def fetch_rss(source: dict, cutoff: datetime) -> list[dict]:
    """Fetch one RSS source; return articles newer than *cutoff*."""
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
            continue  # too old

        title = _clean_text(getattr(entry, "title", ""))
        if not title:
            continue

        summary = _clean_text(
            getattr(entry, "summary", "")
            or getattr(entry, "description", "")
        )
        url = getattr(entry, "link", "")

        articles.append(
            {
                "id": url or title,
                "title": title,
                "title_zh": "",        # filled by scorer
                "summary": summary,
                "summary_zh": "",      # filled by scorer
                "url": url,
                "source": source["name"],
                "lang": source["lang"],
                "category": source["category"],
                "priority": source.get("priority", 1),
                "published": pub.isoformat() if pub else "",
                "score": 0,
                "reason_zh": "",
            }
        )
    return articles


def fetch_hacker_news(count: int, cutoff: datetime) -> list[dict]:
    """Fetch top HN stories via the Firebase API."""
    articles = []
    try:
        resp = requests.get(
            "https://hacker-news.firebaseio.com/v0/topstories.json",
            headers=HEADERS, timeout=10, verify=False
        )
        ids = resp.json()[:count * 2]  # fetch extra in case some are too old
    except Exception as exc:
        print(f"  [WARN] HackerNews top list: {exc}")
        return articles

    fetched = 0
    for story_id in ids:
        if fetched >= count:
            break
        try:
            item = requests.get(
                f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json",
                headers=HEADERS, timeout=8, verify=False,
            ).json()
        except Exception:
            continue

        if not item or item.get("type") != "story":
            continue

        pub_ts = item.get("time")
        pub = datetime.fromtimestamp(pub_ts, tz=timezone.utc) if pub_ts else None
        if pub and pub < cutoff:
            continue

        title = item.get("title", "")
        url = item.get("url", f"https://news.ycombinator.com/item?id={story_id}")
        score_hn = item.get("score", 0)

        articles.append(
            {
                "id": url,
                "title": title,
                "title_zh": "",
                "summary": f"HN points: {score_hn}  |  comments: {item.get('descendants', 0)}",
                "summary_zh": "",
                "url": url,
                "source": "Hacker News",
                "lang": "en",
                "category": "tech",
                "priority": 2,
                "published": pub.isoformat() if pub else "",
                "score": 0,
                "reason_zh": "",
                "_hn_score": score_hn,
            }
        )
        fetched += 1
        time.sleep(0.05)  # be gentle with the API

    return articles


def fetch_all() -> list[dict]:
    """Fetch all sources and return a combined, deduplicated-by-url list."""
    cutoff = datetime.now(tz=timezone.utc) - timedelta(hours=TIME_WINDOW_HOURS)
    all_articles: list[dict] = []
    seen_urls: set[str] = set()

    print(f"Fetching {len(SOURCES)} RSS sources + Hacker News …")

    for source in SOURCES:
        print(f"  → {source['name']}")
        for art in fetch_rss(source, cutoff):
            key = art["url"] or art["title"]
            if key and key not in seen_urls:
                seen_urls.add(key)
                all_articles.append(art)

    print(f"  → Hacker News (top {HN_TOP_COUNT})")
    for art in fetch_hacker_news(HN_TOP_COUNT, cutoff):
        key = art["url"] or art["title"]
        if key and key not in seen_urls:
            seen_urls.add(key)
            all_articles.append(art)

    print(f"Fetched {len(all_articles)} raw articles.")
    return all_articles
