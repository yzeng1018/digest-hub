#!/usr/bin/env python3
"""每日投资情报 — 主入口"""

import argparse
import os
import sys
from datetime import datetime
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
    HISTORY_RETENTION_DAYS, HISTORY_SIMILARITY_THRESHOLD, COMPANY_COOLDOWN_DAYS,
)
from portfolio import load_portfolio_watchlist, portfolio_context
from history import filter_seen_articles, load_history, save_sent_articles

from common.dedup     import deduplicate
from common.scorer    import score_articles, get_usage, get_metrics
from common.reporter  import report_to_gateway, report_model_score


_INSIGHT_PLATFORMS = {"Blog", "Memo", "Podcast"}


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
            + "\n当前重点持仓观察名单："
            + portfolio_context(watchlist)
        )
        articles = score_articles(articles, scoring_prompt, batch_size=10)
        usage_info    = get_usage()
        model_metrics = get_metrics(articles)
        report_to_gateway(usage_info, project="digest-hub/investment")
        report_model_score(usage_info, model_metrics, project="digest-hub/investment")

    articles.sort(key=lambda a: -a["score"])
    articles = _apply_source_caps(articles, SOURCE_CAPS)
    articles = _apply_insight_quota(articles, MAX_ARTICLES, INSIGHT_MIN_RATIO)

    if not args.no_score:
        articles = enrich_articles(articles, watchlist=watchlist)
    else:
        for art in articles:
            art["background_zh"]  = ""
            art["key_players_zh"] = ""
            art["data_point_zh"]  = ""

    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)
    date_str    = datetime.now().strftime("%Y-%m-%d")
    output_path = args.output or str(output_dir / f"{date_str}.html")
    render(articles, output_path, usage_info=usage_info, model_metrics=model_metrics)

    if not args.no_email:
        send_digest(articles, usage_info=usage_info, model_metrics=model_metrics)
        save_sent_articles(articles, sent_history, HISTORY_RETENTION_DAYS)

    must_reads = sum(1 for a in articles if a["score"] >= 8)
    print(f"\n完成。共 {len(articles)} 条 · 必读 {must_reads} 条")
    print(f"   HTML: file://{os.path.abspath(output_path)}")


if __name__ == "__main__":
    main()
