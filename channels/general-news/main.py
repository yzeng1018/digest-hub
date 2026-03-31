#!/usr/bin/env python3
"""每日科技财经速读 — 主入口"""

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
from config   import MAX_ARTICLES, DEDUP_THRESHOLD, SCORING_SYSTEM_PROMPT, HN_MAX_IN_DIGEST

from common.dedup     import deduplicate
from common.scorer    import score_articles, get_usage
from common.reporter  import report_to_gateway


def main():
    parser = argparse.ArgumentParser(description="Daily tech/finance news digest")
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
            art["score"] = 5
            art["reason_zh"] = ""
            art["key_players_zh"] = ""
            art["data_point_zh"] = ""
            art["title_zh"] = art["title"]
            art["summary_zh"] = art["summary"]
        usage_info = {}
    else:
        print(f"Scoring {len(articles)} articles with Qwen…")
        articles = score_articles(articles, SCORING_SYSTEM_PROMPT, batch_size=25)
        usage_info = get_usage()
        report_to_gateway(usage_info, project="digest-hub/general-news")

    articles.sort(key=lambda a: -a["score"])

    # Cap HN articles to avoid them dominating the digest
    hn_seen = 0
    capped = []
    for art in articles:
        if art.get("source") == "Hacker News":
            if hn_seen >= HN_MAX_IN_DIGEST:
                continue
            hn_seen += 1
        capped.append(art)
    articles = capped[:MAX_ARTICLES]

    if not args.no_score:
        articles = enrich_articles(articles)
    else:
        for art in articles:
            art["background_zh"] = ""
            art["key_players_zh"] = ""
            art["data_point_zh"] = ""

    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)
    date_str    = datetime.now().strftime("%Y-%m-%d")
    output_path = args.output or str(output_dir / f"{date_str}.html")
    render(articles, output_path)

    if not args.no_email:
        send_digest(articles, usage_info=usage_info)

    must_reads = sum(1 for a in articles if a["score"] >= 8)
    print(f"\n✅ Done. {len(articles)} articles · {must_reads} must-reads")
    print(f"   HTML: file://{os.path.abspath(output_path)}")


if __name__ == "__main__":
    main()
