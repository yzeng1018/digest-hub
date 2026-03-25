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
from config   import MAX_ARTICLES, DEDUP_THRESHOLD, SCORING_SYSTEM_PROMPT, INSIGHT_MIN_RATIO, SOURCE_CAPS

from common.dedup     import deduplicate
from common.scorer    import score_articles, get_usage
from common.reporter  import report_to_gateway


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
    articles: list[dict], max_n: int, min_ratio: float
) -> list[dict]:
    """
    从已按分数排序的文章中取最终 max_n 条，
    同时保证 Blog/Memo/Podcast 至少占 min_ratio。
    策略：先满足配额槽，剩余槽按分数填充。
    """
    min_insight = max(1, int(max_n * min_ratio))

    insight = [a for a in articles if a.get("platform") in _INSIGHT_PLATFORMS]
    news    = [a for a in articles if a.get("platform") not in _INSIGHT_PLATFORMS]

    # 取配额数量的 insight（已按分数排序）
    picked_insight = insight[:min_insight]
    # 剩余槽位用新闻填满
    remaining = max_n - len(picked_insight)
    picked_news = news[:remaining]

    # 合并后重新按分数排序，让邮件里高分内容排前面
    result = picked_insight + picked_news
    result.sort(key=lambda a: -a["score"])
    return result


def main():
    parser = argparse.ArgumentParser(description="Daily investment digest")
    parser.add_argument("--no-score", action="store_true")
    parser.add_argument("--no-email", action="store_true")
    parser.add_argument("--output",   default="")
    args = parser.parse_args()

    articles = fetch_all()
    if not articles:
        print("No articles fetched. Check your network / sources.")
        sys.exit(1)

    articles = deduplicate(articles, DEDUP_THRESHOLD)

    if args.no_score:
        print("Skipping scoring (--no-score).")
        for art in articles:
            art["score"]          = 5
            art["reason_zh"]      = ""
            art["key_players_zh"] = ""
            art["data_point_zh"]  = ""
            art["title_zh"]       = art["title"]
            art["summary_zh"]     = art["summary"]
        usage_info = {}
    else:
        print(f"Scoring {len(articles)} articles with Qwen…")
        articles = score_articles(articles, SCORING_SYSTEM_PROMPT, batch_size=20)
        usage_info = get_usage()
        report_to_gateway(usage_info, project="digest-hub/investment")

    articles.sort(key=lambda a: -a["score"])
    articles = _apply_source_caps(articles, SOURCE_CAPS)
    articles = _apply_insight_quota(articles, MAX_ARTICLES, INSIGHT_MIN_RATIO)

    if not args.no_score:
        articles = enrich_articles(articles)
    else:
        for art in articles:
            art["background_zh"]  = ""
            art["key_players_zh"] = ""
            art["data_point_zh"]  = ""

    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)
    date_str    = datetime.now().strftime("%Y-%m-%d")
    output_path = args.output or str(output_dir / f"{date_str}.html")
    render(articles, output_path)

    if not args.no_email:
        send_digest(articles, usage_info=usage_info)

    must_reads = sum(1 for a in articles if a["score"] >= 8)
    print(f"\n完成。共 {len(articles)} 条 · 必读 {must_reads} 条")
    print(f"   HTML: file://{os.path.abspath(output_path)}")


if __name__ == "__main__":
    main()
