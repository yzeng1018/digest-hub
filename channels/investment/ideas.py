"""Select news-led content ideas while enforcing a cross-day topic cooldown."""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo


_INSIGHT_PLATFORMS = {"Blog", "Memo", "Podcast"}
_BUSINESS_TIMEZONE = ZoneInfo("Asia/Shanghai")
_TOPIC_FAMILIES = {
    "存储芯片": (
        "内存", "存储", "dram", "nand", "hbm", "ddr", "美光", "micron",
        "海力士", "hynix", "南亚科", "华邦电",
    ),
    "AI芯片": ("gpu", "ai芯片", "英伟达", "nvidia", "asic", "推理芯片"),
    "晶圆代工": ("晶圆代工", "台积电", "tsmc", "中芯国际", "foundry"),
    "AI模型": ("大模型", "基础模型", "openai", "anthropic", "智谱", "minimax"),
    "数据中心能源": ("数据中心电力", "并网", "液冷", "核电", "800v"),
}


def _now_utc(now: datetime | None = None) -> datetime:
    now = now or datetime.now(timezone.utc)
    return now if now.tzinfo else now.replace(tzinfo=timezone.utc)


def _parse_datetime(value: str) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _business_date(now: datetime) -> str:
    return now.astimezone(_BUSINESS_TIMEZONE).date().isoformat()


def _compact(text: str) -> str:
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", (text or "").casefold())


def _topic_family(text: str) -> str:
    compact = _compact(text)
    for family, aliases in _TOPIC_FAMILIES.items():
        if any(_compact(alias) in compact for alias in aliases):
            return family
    return ""


def _topic_grams(text: str) -> set[str]:
    compact = _compact(text)
    if len(compact) < 2:
        return {compact} if compact else set()
    return {compact[i:i + 2] for i in range(len(compact) - 1)}


def _topic_similarity(left: str, right: str) -> float:
    a, b = _topic_grams(left), _topic_grams(right)
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _same_topic(left: str, right: str) -> bool:
    left_family, right_family = _topic_family(left), _topic_family(right)
    if left_family and left_family == right_family:
        return True
    a, b = _compact(left), _compact(right)
    if min(len(a), len(b)) >= 4 and (a in b or b in a):
        return True
    return _topic_similarity(left, right) >= 0.5


def load_idea_history(path: str | Path) -> list[dict]:
    history_path = Path(path)
    if not history_path.exists():
        return []
    records = []
    for line in history_path.read_text(encoding="utf-8").splitlines():
        try:
            record = json.loads(line)
        except (TypeError, json.JSONDecodeError):
            continue
        if isinstance(record, dict):
            records.append(record)
    return records


def _is_fresh(article: dict, now: datetime, max_age_hours: int) -> bool:
    published = _parse_datetime(article.get("published_at", ""))
    if published:
        age = now - published.astimezone(timezone.utc)
        return timedelta(0) <= age <= timedelta(hours=max_age_hours)
    return article.get("platform") not in _INSIGHT_PLATFORMS


def select_content_ideas(
    articles: list[dict],
    history_path: str | Path,
    *,
    count: int = 3,
    cooldown_days: int = 14,
    max_age_hours: int = 72,
    now: datetime | None = None,
) -> list[dict]:
    """Mark and return fresh, non-repeated content ideas."""
    now = _now_utc(now)
    today = _business_date(now)
    cutoff = now - timedelta(days=cooldown_days)
    history = load_idea_history(history_path)
    recent = [
        item for item in history
        if (_parse_datetime(item.get("selected_at", "")) or datetime.min.replace(tzinfo=timezone.utc)) >= cutoff
    ]
    today_urls = {item.get("url") for item in recent if item.get("date") == today}

    for article in articles:
        article["_is_content_idea"] = False

    candidates = [
        article for article in articles
        if article.get("investment_angle_zh")
        and article.get("idea_topic_zh")
        and article.get("news_hook_zh")
        and _is_fresh(article, now, max_age_hours)
    ]
    platform_bonus = {"Primary": 2, "Research": 2, "Portfolio": 1, "Watchlist": 1, "Sector": 1}
    candidates.sort(
        key=lambda article: (
            article.get("url") in today_urls,
            article.get("score", 0) + platform_bonus.get(article.get("platform", ""), 0),
            article.get("priority", 0),
        ),
        reverse=True,
    )

    selected: list[dict] = []
    for article in candidates:
        topic = article["idea_topic_zh"]
        same_day = article.get("url") in today_urls
        if not same_day and any(
            _same_topic(topic, item.get("topic", ""))
            for item in recent
            if item.get("date") != today
        ):
            continue
        if any(_same_topic(topic, chosen["idea_topic_zh"]) for chosen in selected):
            continue
        article["_is_content_idea"] = True
        selected.append(article)
        if len(selected) >= count:
            break

    print(
        f"财经内容灵感：{len(candidates)} 条新鲜候选 → {len(selected)} 条"
        f"（主题冷却 {cooldown_days} 天）"
    )
    return selected


def record_content_ideas(ideas: list[dict], history_path: str | Path, now: datetime | None = None) -> None:
    if not ideas:
        return
    now = _now_utc(now)
    history_path = Path(history_path)
    history_path.parent.mkdir(parents=True, exist_ok=True)
    existing = load_idea_history(history_path)
    existing_keys = {(item.get("date"), item.get("url")) for item in existing}
    with history_path.open("a", encoding="utf-8") as handle:
        for article in ideas:
            key = (_business_date(now), article.get("url", ""))
            if key in existing_keys:
                continue
            record = {
                "date": key[0],
                "selected_at": now.isoformat(),
                "topic": article.get("idea_topic_zh", ""),
                "topic_family": _topic_family(article.get("idea_topic_zh", "")),
                "news_hook": article.get("news_hook_zh", ""),
                "title": article.get("title_zh") or article.get("title", ""),
                "source": article.get("source", ""),
                "url": key[1],
            }
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
            existing_keys.add(key)
