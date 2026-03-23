"""
从三类源抓取内容：
  1. X/Twitter KOLs — 通过 nitter 公共实例的 RSS，自动 fallback
  2. 即刻 KOLs      — 通过 RSSHub 公共实例，自动 fallback
  3. Substack/博客  — 直接解析 RSS

所有文章统一为 dict 格式返回。
"""

import html
import re
import time
from datetime import datetime, timedelta, timezone

import feedparser
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from config import (
    BLOG_SOURCES,
    BLOG_TIME_WINDOW_HOURS,
    DEDUP_THRESHOLD,
    JIKE_USERS,
    NITTER_INSTANCES,
    RSSHUB_INSTANCES,
    TIME_WINDOW_HOURS,
    TWITTER_HANDLES,
    TWITTER_MAX_PER_HANDLE,
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
}

TIMEOUT = 12
PROBE_TIMEOUT = 4   # 快速探测超时（秒）


# ─── 工具函数 ─────────────────────────────────────────────────────────────────

def _clean(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    return " ".join(text.split())[:600]


def _parse_time(entry) -> datetime | None:
    for field in ("published_parsed", "updated_parsed"):
        t = getattr(entry, field, None)
        if t:
            try:
                return datetime(*t[:6], tzinfo=timezone.utc)
            except Exception:
                pass
    return None


def _make_article(*, title, summary, url, source, platform, lang, pub) -> dict:
    return {
        "id": url or title,
        "title": title,
        "title_zh": "",
        "summary": summary,
        "summary_zh": "",
        "url": url,
        "source": source,
        "platform": platform,   # "X" | "即刻" | "Blog"
        "lang": lang,
        "published": pub.isoformat() if pub else "",
        "score": 0,
        "reason_zh": "",
        "background_zh": "",
        "priority": 2,
    }


def _parse_feed(feed_url: str, source_name: str, platform: str, lang: str,
                cutoff: datetime, max_items: int = 999) -> list[dict]:
    """通用 RSS 解析器，返回 cutoff 之后的文章。"""
    articles = []
    try:
        resp = requests.get(feed_url, headers=HEADERS, timeout=TIMEOUT, verify=False)
        if resp.status_code != 200:
            return articles
        feed = feedparser.parse(resp.content)
    except Exception as exc:
        print(f"    [WARN] {source_name}: {exc}")
        return articles

    count = 0
    for entry in feed.entries:
        if count >= max_items:
            break
        pub = _parse_time(entry)
        if pub and pub < cutoff:
            continue
        title = _clean(getattr(entry, "title", ""))
        if not title:
            continue
        summary = _clean(
            getattr(entry, "summary", "")
            or getattr(entry, "description", "")
        )
        url = getattr(entry, "link", "")
        articles.append(_make_article(
            title=title, summary=summary, url=url,
            source=source_name, platform=platform, lang=lang, pub=pub,
        ))
        count += 1
    return articles


# ─── Twitter/X via Nitter ─────────────────────────────────────────────────────

def _probe_nitter_instance(instance: str) -> bool:
    """快速探测 nitter 实例是否存活（用一个稳定账号测试）。"""
    test_url = f"{instance.rstrip('/')}/OpenAI/rss"
    try:
        resp = requests.get(
            test_url, headers=HEADERS, timeout=PROBE_TIMEOUT, verify=False
        )
        return resp.status_code == 200 and len(resp.content) > 500
    except Exception:
        return False


def _find_live_nitter_instances() -> list[str]:
    """在所有配置实例中找出当前可用的，返回可用列表。"""
    live = []
    for inst in NITTER_INSTANCES:
        if _probe_nitter_instance(inst):
            live.append(inst)
            print(f"    ✓ nitter 可用: {inst}")
        else:
            print(f"    ✗ nitter 不可用: {inst}")
    return live


def _nitter_rss_url(instance: str, handle: str) -> str:
    return f"{instance.rstrip('/')}/{handle}/rss"


def _fetch_twitter_handle(kol: dict, live_instances: list[str],
                          cutoff: datetime) -> list[dict]:
    """只尝试存活的 nitter 实例，返回该账号的推文。"""
    handle = kol["handle"]
    name = kol["name"]
    for instance in live_instances:
        url = _nitter_rss_url(instance, handle)
        articles = _parse_feed(
            url, f"{name} (@{handle})", "X", "en", cutoff,
            max_items=TWITTER_MAX_PER_HANDLE,
        )
        if articles:
            return articles
        time.sleep(0.2)
    return []


def fetch_twitter(cutoff: datetime) -> list[dict]:
    print(f"  → X/Twitter ({len(TWITTER_HANDLES)} KOLs via nitter)")
    print("    探测 nitter 实例…")
    live = _find_live_nitter_instances()
    if not live:
        print("    [WARN] 所有 nitter 实例均不可用，跳过 X/Twitter 抓取")
        return []

    all_articles = []
    for kol in TWITTER_HANDLES:
        arts = _fetch_twitter_handle(kol, live, cutoff)
        all_articles.extend(arts)
        if arts:
            time.sleep(0.3)
    print(f"    X/Twitter 抓到 {len(all_articles)} 条")
    return all_articles


# ─── 即刻 via RSSHub ──────────────────────────────────────────────────────────

def _jike_rss_url(rsshub: str, user_id: str) -> str:
    return f"{rsshub.rstrip('/')}/jike/user/{user_id}"


def _fetch_jike_user(user: dict, cutoff: datetime) -> list[dict]:
    name = user["name"]
    uid = user["id"]
    for rsshub in RSSHUB_INSTANCES:
        url = _jike_rss_url(rsshub, uid)
        articles = _parse_feed(url, f"{name} · 即刻", "即刻", "zh", cutoff)
        if articles:
            return articles
        time.sleep(0.5)
    print(f"    [SKIP] 即刻/{name}: all RSSHub instances failed")
    return []


def fetch_jike(cutoff: datetime) -> list[dict]:
    if not JIKE_USERS:
        print("  → 即刻: 暂无配置 (在 config.py 的 JIKE_USERS 中填入 UUID)")
        return []
    all_articles = []
    print(f"  → 即刻 ({len(JIKE_USERS)} KOLs via RSSHub)")
    for user in JIKE_USERS:
        arts = _fetch_jike_user(user, cutoff)
        all_articles.extend(arts)
    return all_articles


# ─── Substack / 博客 RSS ──────────────────────────────────────────────────────

def fetch_blogs(cutoff: datetime) -> list[dict]:
    # 博客用更长的时间窗口（周更节奏）
    blog_cutoff = datetime.now(tz=timezone.utc) - timedelta(hours=BLOG_TIME_WINDOW_HOURS)
    all_articles = []
    print(f"  → Substack/Blog ({len(BLOG_SOURCES)} sources, 过去{BLOG_TIME_WINDOW_HOURS}h)")
    for src in BLOG_SOURCES:
        arts = _parse_feed(
            src["url"], src["name"], "Blog", src.get("lang", "en"), blog_cutoff
        )
        if arts:
            print(f"    {src['name']}: {len(arts)} 条")
        all_articles.extend(arts)
        time.sleep(0.2)
    return all_articles


# ─── 主入口 ───────────────────────────────────────────────────────────────────

def fetch_all() -> list[dict]:
    cutoff = datetime.now(tz=timezone.utc) - timedelta(hours=TIME_WINDOW_HOURS)
    all_articles: list[dict] = []
    seen: set[str] = set()

    print(f"开始抓取 AI 情报（过去 {TIME_WINDOW_HOURS}h）…")

    for arts in [
        fetch_twitter(cutoff),
        fetch_jike(cutoff),
        fetch_blogs(cutoff),
    ]:
        for art in arts:
            key = art["url"] or art["title"]
            if key and key not in seen:
                seen.add(key)
                all_articles.append(art)

    print(f"抓取完成：共 {len(all_articles)} 条原始内容。")
    return all_articles
