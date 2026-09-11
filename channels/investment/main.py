#!/usr/bin/env python3
"""每日投资情报 — 主入口"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from dotenv import load_dotenv
load_dotenv()

from fetcher  import fetch_all
from enricher import enrich_articles
from renderer import render
from mailer   import send_digest
from config   import (
    MAX_ARTICLES, DEDUP_THRESHOLD, SCORING_SYSTEM_PROMPT, INSIGHT_MIN_RATIO,
    INSIGHT_MIN_SCORE, PORTFOLIO_MIN_COUNT, PORTFOLIO_MIN_SCORE, SOURCE_CAPS,
    PRE_SCORE_MAX_ARTICLES, PRE_SCORE_SOURCE_CAPS, RANK_BATCH_SIZE,
    WATCHLIST_MIN_COUNT, WATCHLIST_MIN_SCORE,
    HISTORY_RETENTION_DAYS, HISTORY_SIMILARITY_THRESHOLD, COMPANY_COOLDOWN_DAYS,
    CONTENT_IDEA_COUNT, CONTENT_IDEA_COOLDOWN_DAYS, CONTENT_IDEA_MAX_AGE_HOURS,
    CONTENT_IDEA_HISTORY_PATH,
)
from portfolio import load_portfolio_watchlist, portfolio_context
from history import filter_seen_articles, load_history, save_sent_articles
from ideas import select_content_ideas, record_content_ideas

from common.dedup     import deduplicate
from common.scorer    import score_articles, get_usage, get_metrics
from common.reporter  import report_to_gateway, report_model_score


_INSIGHT_PLATFORMS = {"Blog", "Memo", "Podcast"}
_NOISE_RE = re.compile(
    r"(?:开盘|早盘|午盘|盘中|收盘).{0,12}(?:涨|跌)|涨超|跌超|值得买吗|"
    r"真相实测|行情播报|今日股价|创新高|创新低",
    re.I,
)
_SIGNAL_RE = re.compile(
    r"财报|业绩|盈利|亏损|营收|收入|毛利|指引|订单|销量|交付|处罚|监管|"
    r"回购|增持|减持|融资|配售|可转债|合作|发布|模型|降价|涨价|市场份额|"
    r"earnings|revenue|margin|guidance|orders|deliveries|regulat|funding|model",
    re.I,
)


def _apply_pre_score_filters(articles: list[dict]) -> list[dict]:
    """Remove obvious noise and cap prolific sources before paid scoring."""
    filtered = []
    for article in articles:
        text = f'{article.get("title", "")} {article.get("summary", "")}'
        if (
            article.get("platform") in {"Portfolio", "Watchlist"}
            and _NOISE_RE.search(text)
            and not _SIGNAL_RE.search(text)
        ):
            continue
        filtered.append(article)

    def rank(article: dict) -> tuple[int, int]:
        platform = article.get("platform")
        text = f'{article.get("title", "")} {article.get("summary", "")}'
        relevance = 4 if platform == "Portfolio" else 0
        relevance += 3 if platform == "Watchlist" else 0
        relevance += 3 if platform == "Sector" else 0
        relevance += 2 if platform in _INSIGHT_PLATFORMS else 0
        relevance += 2 if _SIGNAL_RE.search(text) else 0
        return relevance, int(article.get("priority", 0))

    filtered.sort(key=rank, reverse=True)
    selected = _apply_source_caps(filtered, PRE_SCORE_SOURCE_CAPS)
    selected = selected[:PRE_SCORE_MAX_ARTICLES]
    print(f"付费评分前过滤：{len(articles)} → {len(selected)} 条。")
    return selected


def _apply_source_caps(articles: list[dict], caps: dict[str, int]) -> list[dict]:
    """按来源限制文章数量，每个来源只保留分数最高的 N 篇。"""
    counts: dict[str, int] = {}
    result = []
    for a in articles:  # articles 已按分数降序排列
        source = a.get("source", "")
        cap = caps.get(source)
        if cap is not None:
            counts[source] = counts.get(source, 0) + 1
            if counts[source] > cap:
                continue
        result.append(a)
    return result


def _apply_insight_quota(
    articles: list[dict], max_n: int, min_ratio: float,
    portfolio_min: int = PORTFOLIO_MIN_COUNT,
    watchlist_min: int = WATCHLIST_MIN_COUNT,
) -> list[dict]:
    """
    从已按分数排序的文章中取最终 max_n 条，
    优先保证“有信息增量”的持仓新闻和深度内容配额；低分内容不为凑数入选。
    未用完的配额槽按全局分数回填。
    """
    articles = sorted(
        articles,
        key=lambda a: -(a.get("score", 0) - a.get("history_penalty", 0)),
    )
    min_insight = max(1, int(max_n * min_ratio))
    portfolio = [
        a for a in articles
        if a.get("platform") == "Portfolio" and a.get("score", 0) >= PORTFOLIO_MIN_SCORE
    ]
    watchlist = [
        a for a in articles
        if a.get("platform") == "Watchlist" and a.get("score", 0) >= WATCHLIST_MIN_SCORE
    ]
    insight = [
        a for a in articles
        if a.get("platform") in _INSIGHT_PLATFORMS and a.get("score", 0) >= INSIGHT_MIN_SCORE
    ]

    result: list[dict] = []
    seen: set[str] = set()

    def add(candidates: list[dict], count: int) -> None:
        if count <= 0:
            return
        added = 0
        for article in candidates:
            key = article.get("id") or article.get("url") or article.get("title", "")
            if key in seen:
                continue
            result.append(article)
            seen.add(key)
            added += 1
            if added >= count:
                break

    add(portfolio, min(portfolio_min, max_n))
    add(watchlist, min(watchlist_min, max_n - len(result)))
    add(insight, min(min_insight, max_n - len(result)))
    # Always backfill unused quota slots from the globally ranked list. The old
    # implementation could return only a handful of stories on a quiet news day.
    for article in articles:
        if len(result) >= max_n:
            break
        key = article.get("id") or article.get("url") or article.get("title", "")
        if key not in seen:
            result.append(article)
            seen.add(key)

    result.sort(key=lambda a: -a["score"])
    return result


def _dump_ideas(content_ideas: list[dict], date_str: str) -> Path:
    """Persist today's ideas so the standalone ideas digest can reuse them
    without re-running the expensive fetch + scoring pipeline."""
    target_dir = Path(__file__).resolve().parents[2] / "data" / "ideas"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{date_str}.json"
    payload = {
        "date": date_str,
        "generated_at": datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(),
        "ideas": [
            {
                "topic": idea.get("idea_topic_zh") or "市场线索",
                "hook": idea.get("news_hook_zh", ""),
                "angle": idea.get("investment_angle_zh", ""),
                "signal": idea.get("confirmation_signal_zh", ""),
                "title": idea.get("title_zh") or idea.get("title", ""),
                "source": idea.get("source", ""),
                "url": idea.get("url", "#"),
            }
            for idea in content_ideas
        ],
    }
    target.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"   内容灵感已落盘: data/ideas/{date_str}.json（{len(content_ideas)} 条）")
    return target


def main():
    parser = argparse.ArgumentParser(description="Daily investment digest")
    parser.add_argument("--no-score", action="store_true")
    parser.add_argument("--no-email", action="store_true")
    parser.add_argument("--output",   default="")
    args = parser.parse_args()

    watchlist = load_portfolio_watchlist()
    sent_history = load_history(HISTORY_RETENTION_DAYS)
    articles = fetch_all()
    if not articles:
        print("No articles fetched. Check your network / sources.")
        sys.exit(1)

    articles = deduplicate(articles, DEDUP_THRESHOLD)
    articles = filter_seen_articles(
        articles,
        sent_history,
        similarity_threshold=HISTORY_SIMILARITY_THRESHOLD,
        company_cooldown_days=COMPANY_COOLDOWN_DAYS,
    )
    articles = _apply_pre_score_filters(articles)

    if args.no_score:
        print("Skipping scoring (--no-score).")
        for art in articles:
            art["score"]          = 5
            art["reason_zh"]      = ""
            art["key_players_zh"] = ""
            art["data_point_zh"]  = ""
            art["title_zh"]       = art["title"]
            art["summary_zh"]     = art["summary"]
        usage_info    = {}
        model_metrics = {}
    else:
        print(f"Scoring {len(articles)} articles…")
        scoring_prompt = (
            SCORING_SYSTEM_PROMPT
            + "\n当前重点持仓与观察名单："
            + portfolio_context(watchlist)
            + "\n本轮仅做快速筛选：严格只返回 id、score、reason_zh，"
              "不翻译标题、不生成摘要。"
        )
        articles = score_articles(
            articles,
            scoring_prompt,
            batch_size=RANK_BATCH_SIZE,
            summary_fn=lambda art: (art.get("summary") or "")[:160],
            compact=True,
        )

    articles.sort(key=lambda a: -a["score"])
    articles = _apply_source_caps(articles, SOURCE_CAPS)
    articles = _apply_insight_quota(articles, MAX_ARTICLES, INSIGHT_MIN_RATIO)

    if not args.no_score:
        articles = enrich_articles(articles, watchlist=watchlist)
        usage_info = get_usage()
        model_metrics = get_metrics(articles)
        report_to_gateway(usage_info, project="digest-hub/investment")
        report_model_score(usage_info, model_metrics, project="digest-hub/investment")
    else:
        for art in articles:
            art["background_zh"]  = ""
            art["key_players_zh"] = ""
            art["data_point_zh"]  = ""

    idea_history_path = Path(__file__).resolve().parents[2] / CONTENT_IDEA_HISTORY_PATH
    content_ideas = select_content_ideas(
        articles,
        idea_history_path,
        count=CONTENT_IDEA_COUNT,
        cooldown_days=CONTENT_IDEA_COOLDOWN_DAYS,
        max_age_hours=CONTENT_IDEA_MAX_AGE_HOURS,
    )

    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)
    # CI runs on UTC, so pin the digest date to Beijing time. Otherwise a run
    # that fires before UTC midnight labels the email with yesterday's date.
    date_str    = datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d")
    output_path = args.output or str(output_dir / f"{date_str}.html")
    render(articles, output_path, usage_info=usage_info, model_metrics=model_metrics)
    record_content_ideas(content_ideas, idea_history_path)
    _dump_ideas(content_ideas, date_str)

    if not args.no_email:
        send_digest(articles, usage_info=usage_info, model_metrics=model_metrics)
        save_sent_articles(articles, sent_history, HISTORY_RETENTION_DAYS)

    must_reads = sum(1 for a in articles if a["score"] >= 8)
    print(f"\n完成。共 {len(articles)} 条 · 必读 {must_reads} 条")
    print(f"   HTML: file://{os.path.abspath(output_path)}")


if __name__ == "__main__":
    main()
