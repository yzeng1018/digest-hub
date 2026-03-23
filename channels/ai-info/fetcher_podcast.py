"""
AI 播客抓取器：YouTube RSS 获取最新视频 + youtube-transcript-api 拉转录稿。

每个播客源每次最多取 1 集（最新一期），转录稿作为正文供 Qwen 生成摘要。
"""

import time
from datetime import datetime, timedelta, timezone

import feedparser
import requests

from config import PODCAST_SOURCES, PODCAST_TIME_WINDOW_HOURS

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
}
TIMEOUT = 12


def _youtube_rss_url(source: dict) -> str:
    if source["type"] == "playlist":
        return f"https://www.youtube.com/feeds/videos.xml?playlist_id={source['id']}"
    return f"https://www.youtube.com/feeds/videos.xml?channel_id={source['id']}"


def _parse_time(entry) -> datetime | None:
    for field in ("published_parsed", "updated_parsed"):
        t = getattr(entry, field, None)
        if t:
            try:
                return datetime(*t[:6], tzinfo=timezone.utc)
            except Exception:
                pass
    return None


def _get_transcript(video_id: str) -> str:
    """用 youtube-transcript-api 拉转录稿，失败返回空字符串。"""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        from youtube_transcript_api._errors import RequestBlocked, NoTranscriptFound
        api = YouTubeTranscriptApi()
        transcript = api.fetch(video_id)
        return " ".join(s.text for s in transcript)
    except Exception as exc:
        err = str(exc)
        if "RequestBlocked" in type(exc).__name__ or "RequestBlocked" in err:
            print(f"    [TRANSCRIPT] {video_id}: YouTube IP 限制，跳过转录稿（仍使用标题评分）")
        else:
            print(f"    [TRANSCRIPT WARN] {video_id}: {type(exc).__name__}")
        return ""


def _video_id_from_url(url: str) -> str:
    """从 youtube watch URL 提取 video_id。"""
    if "watch?v=" in url:
        return url.split("watch?v=")[-1].split("&")[0]
    if "youtu.be/" in url:
        return url.split("youtu.be/")[-1].split("?")[0]
    return ""


def fetch_podcasts() -> list[dict]:
    if not PODCAST_SOURCES:
        return []

    cutoff = datetime.now(tz=timezone.utc) - timedelta(hours=PODCAST_TIME_WINDOW_HOURS)
    all_articles = []
    print(f"  → Podcasts ({len(PODCAST_SOURCES)} 个，过去 {PODCAST_TIME_WINDOW_HOURS}h)")

    for src in PODCAST_SOURCES:
        rss_url = _youtube_rss_url(src)
        try:
            resp = requests.get(rss_url, headers=HEADERS, timeout=TIMEOUT)
            if resp.status_code != 200:
                print(f"    [SKIP] {src['name']}: HTTP {resp.status_code}")
                continue
            feed = feedparser.parse(resp.content)
        except Exception as exc:
            print(f"    [WARN] {src['name']}: {exc}")
            continue

        # 只取时间窗口内最新一集
        candidates = []
        for entry in feed.entries:
            pub = _parse_time(entry)
            if pub and pub >= cutoff:
                candidates.append((pub, entry))

        if not candidates:
            print(f"    {src['name']}: 时间窗口内无新集")
            continue

        # 取最新一集
        candidates.sort(key=lambda x: x[0], reverse=True)
        pub, entry = candidates[0]

        title = getattr(entry, "title", "").strip()
        url   = getattr(entry, "link", "")
        video_id = _video_id_from_url(url)

        print(f"    {src['name']}: 《{title[:60]}》 → 拉转录稿…")
        transcript = _get_transcript(video_id) if video_id else ""

        # 截取前 4000 字供评分/摘要使用（完整转录稿存入 transcript 字段）
        summary_text = transcript[:4000] if transcript else title

        all_articles.append({
            "id":           url or title,
            "title":        title,
            "title_zh":     "",
            "summary":      summary_text,
            "summary_zh":   "",
            "transcript":   transcript,          # 完整转录稿
            "url":          url,
            "source":       src["name"],
            "platform":     "Podcast",
            "lang":         "en",
            "published":    pub.isoformat(),
            "score":        0,
            "reason_zh":    "",
            "background_zh": "",
            "priority":     1,                   # 播客优先级高
        })

        time.sleep(1.0)   # 避免频繁请求

    print(f"    Podcasts 共抓到 {len(all_articles)} 集")
    return all_articles
