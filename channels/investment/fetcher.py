"""
投资情报抓取器。
信源：RSS（Crunchbase/TechCrunch/a16z/投资界等）+ Hacker News API（投资关键词过滤）
     + X/Twitter KOLs via Nitter RSS（顶级投资人账号）
     + ARK ETF 每日持仓 CSV
     + SEC EDGAR 13F 季度申报 Atom RSS
"""

import csv
import html
import io
import re
import time
from datetime import datetime, timezone, timedelta

import feedparser
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from config import (
    SOURCES, HN_TOP_COUNT, TIME_WINDOW_HOURS,
    NITTER_INSTANCES, TWITTER_HANDLES, TWITTER_MAX_PER_HANDLE,
    ARK_FUND_CSVS, SEC_13F_SOURCES, SEC_13F_WINDOW_DAYS,
)


_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
}

_CUTOFF = timedelta(hours=TIME_WINDOW_HOURS)


def _clean(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    return " ".join(text.split())[:600]


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
        resp = requests.get(source["url"], timeout=15, headers=_HEADERS, verify=False)
        feed = feedparser.parse(resp.content)
    except Exception as exc:
        print(f"  [WARN] {source['name']}: {exc}")
        return []

    for entry in feed.entries:
        if not _is_recent(entry):
            continue
        title   = getattr(entry, "title", "").strip()
        summary = _clean(getattr(entry, "summary", "") or getattr(entry, "description", ""))
        url     = getattr(entry, "link", "")
        if not title or not url:
            continue

        articles.append({
            "id":       url,
            "title":    title,
            "summary":  summary,
            "url":      url,
            "source":   source["name"],
            "platform": source.get("platform", "News"),
            "lang":     source["lang"],
            "priority": source.get("priority", 2),
        })
    return articles


# ─── Twitter/X via Nitter ─────────────────────────────────────────────────────

_PROBE_TIMEOUT = 4


def _probe_nitter_instance(instance: str) -> bool:
    test_url = f"{instance.rstrip('/')}/elonmusk/rss"
    try:
        resp = requests.get(test_url, headers=_HEADERS, timeout=_PROBE_TIMEOUT, verify=False)
        return resp.status_code == 200 and len(resp.content) > 500
    except Exception:
        return False


def _find_live_nitter() -> list[str]:
    live = []
    for inst in NITTER_INSTANCES:
        if _probe_nitter_instance(inst):
            live.append(inst)
            print(f"    ✓ nitter 可用: {inst}")
        else:
            print(f"    ✗ nitter 不可用: {inst}")
    return live


def _fetch_twitter_handle(kol: dict, live: list[str], cutoff: datetime) -> list[dict]:
    handle = kol["handle"]
    name   = kol["name"]
    for instance in live:
        url = f"{instance.rstrip('/')}/{handle}/rss"
        articles = []
        try:
            resp = requests.get(url, headers=_HEADERS, timeout=12, verify=False)
            if resp.status_code != 200:
                continue
            feed = feedparser.parse(resp.content)
        except Exception:
            time.sleep(0.2)
            continue

        count = 0
        for entry in feed.entries:
            if count >= TWITTER_MAX_PER_HANDLE:
                break
            pub = _parse_dt(entry)
            if pub and pub < cutoff:
                continue
            title   = _clean(getattr(entry, "title", ""))
            summary = _clean(getattr(entry, "summary", "") or getattr(entry, "description", ""))
            link    = getattr(entry, "link", "")
            if not title:
                continue
            articles.append({
                "id":       link or title,
                "title":    title,
                "summary":  summary,
                "url":      link,
                "source":   f"{name} (@{handle})",
                "platform": "X",
                "lang":     "en",
                "priority": 3,
            })
            count += 1

        if articles:
            return articles
        time.sleep(0.2)
    return []


def _fetch_twitter(cutoff: datetime) -> list[dict]:
    print(f"  → X/Twitter ({len(TWITTER_HANDLES)} 顶级投资人 via nitter)")
    print("    探测 nitter 实例…")
    live = _find_live_nitter()
    if not live:
        print("    [WARN] 所有 nitter 实例均不可用，跳过 Twitter 抓取")
        return []

    all_articles = []
    for kol in TWITTER_HANDLES:
        arts = _fetch_twitter_handle(kol, live, cutoff)
        all_articles.extend(arts)
        print(f"    @{kol['handle']}: {len(arts)} 条")
        time.sleep(0.3)
    return all_articles


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


# ─── ARK ETF 每日持仓 CSV ──────────────────────────────────────────────────────

def _fetch_ark_csv() -> list[dict]:
    """
    从 ark-funds.com 下载每日持仓 CSV，生成每只基金的持仓摘要文章。
    CSV 格式：date,fund,company,ticker,cusip,shares,market value ($),weight (%)
    """
    articles = []
    for fund in ARK_FUND_CSVS:
        try:
            resp = requests.get(fund["url"], timeout=15, headers=_HEADERS)
            if resp.status_code != 200:
                print(f"  [WARN] ARK {fund['ticker']}: HTTP {resp.status_code}")
                continue

            reader = csv.DictReader(io.StringIO(resp.text))
            rows = [r for r in reader if r.get("company", "").strip()]
            if not rows:
                continue

            filing_date = rows[0].get("date", "").strip()
            top5 = rows[:5]
            holdings_str = " | ".join(
                f"{r.get('company', '?').strip()} ({r.get('ticker', '?').strip()}) "
                f"{r.get('weight (%)', '?').strip()}"
                for r in top5
            )

            articles.append({
                "id":       f"ark-{fund['ticker']}-{filing_date}",
                "title":    f"ARK {fund['ticker']} 持仓更新 ({filing_date})",
                "summary":  f"前5大持仓: {holdings_str}。共持有 {len(rows)} 支股票。",
                "url":      f"https://ark-funds.com/funds/{fund['ticker'].lower()}/",
                "source":   fund["name"],
                "platform": "News",
                "lang":     "en",
                "priority": 3,
            })
            print(f"  ARK {fund['ticker']}: {filing_date}, {len(rows)} 支持仓")
        except Exception as exc:
            print(f"  [WARN] ARK {fund['ticker']}: {exc}")
    return articles


# ─── SEC EDGAR 13F 申报监控 ────────────────────────────────────────────────────

_SEC_EDGAR_BASE = (
    "https://www.sec.gov/cgi-bin/browse-edgar"
    "?action=getcompany&CIK={cik}&type=13F-HR"
    "&dateb=&owner=include&count=5&search_text=&output=atom"
)


def _fetch_sec_13f() -> list[dict]:
    """
    通过 SEC EDGAR Atom RSS 监控顶级机构的 13F 季度申报。
    使用更长的时间窗口（7天）避免漏抓季度申报。
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=SEC_13F_WINDOW_DAYS)
    articles = []

    for source in SEC_13F_SOURCES:
        url = _SEC_EDGAR_BASE.format(cik=source["cik"])
        try:
            resp = requests.get(url, timeout=15, headers=_HEADERS)
            if resp.status_code != 200:
                continue
            feed = feedparser.parse(resp.content)
        except Exception as exc:
            print(f"  [WARN] SEC 13F {source['name']}: {exc}")
            continue

        for entry in feed.entries:
            pub = _parse_dt(entry)
            if pub and pub < cutoff:
                continue
            title   = _clean(getattr(entry, "title", ""))
            summary = _clean(getattr(entry, "summary", ""))
            link    = getattr(entry, "link", "")
            if not title:
                continue
            articles.append({
                "id":       link or title,
                "title":    f"[13F] {source['name']}: {title}",
                "summary":  summary or f"{source['name']} 提交最新季度持仓申报（13F-HR）",
                "url":      link,
                "source":   "SEC EDGAR",
                "platform": "News",
                "lang":     "en",
                "priority": 3,
            })

    print(f"  SEC EDGAR 13F: {len(articles)} 条新申报")
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

    cutoff = datetime.now(timezone.utc) - _CUTOFF
    twitter_items = _fetch_twitter(cutoff)
    articles.extend(twitter_items)

    ark_items = _fetch_ark_csv()
    articles.extend(ark_items)

    sec_items = _fetch_sec_13f()
    articles.extend(sec_items)

    print(f"共抓取 {len(articles)} 条投资情报。")
    return articles
