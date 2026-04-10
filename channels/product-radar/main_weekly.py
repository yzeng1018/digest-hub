#!/usr/bin/env python3
"""
产品设计雷达 · 周报
每周六早上发送，回顾过去7天最值得精读的产品设计内容。
严选模式：只保留真正值得深读的文章，配上更丰富的分析。
"""

import argparse
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from dotenv import load_dotenv
load_dotenv()

from fetcher  import fetch_rss
from enricher import _enrich_one
from config   import SOURCES, DEDUP_THRESHOLD, SCORING_SYSTEM_PROMPT

from common.dedup  import deduplicate
from common.scorer import score_articles
from common.mailer import send_html

import re
import html as html_lib
from datetime import timezone


# 周报专属配置
WEEKLY_TIME_WINDOW_HOURS = 168   # 7天
WEEKLY_MAX_ARTICLES      = 8     # 严选：最多8篇，宁缺毋滥
WEEKLY_MIN_SCORE         = 7     # 7分以下不进周报
WEEKLY_ENRICH_ALL        = True  # 所有入选文章都做深度分析


WEEKLY_SCORING_PROMPT = SCORING_SYSTEM_PROMPT + """

【周报严选模式】
本次评分用于周报筛选，标准更严格：
- 7分以下的文章不会出现在周报中
- 只有真正有产品设计洞见、值得花15分钟精读的内容才能上周报
- 宁可只有3篇真正好的，也不要凑够10篇平庸的
"""


def _fetch_weekly() -> list[dict]:
    """抓取过去7天的所有文章。"""
    from datetime import datetime, timezone, timedelta
    cutoff = datetime.now(tz=timezone.utc) - timedelta(hours=WEEKLY_TIME_WINDOW_HOURS)
    all_articles: list[dict] = []
    seen_urls: set[str] = set()

    print(f"[周报] 抓取过去7天内容，来源: {len(SOURCES)} 个 …")
    for source in SOURCES:
        print(f"  → {source['name']}")
        for art in fetch_rss(source, cutoff):
            key = art["url"] or art["title"]
            if key and key not in seen_urls:
                seen_urls.add(key)
                all_articles.append(art)

    print(f"抓取到 {len(all_articles)} 篇原始文章（7天）。")
    return all_articles


def _build_weekly_html(articles: list[dict], week_str: str) -> str:
    """构建周报 HTML，风格更像杂志精选，适合精读。"""
    rows = ""
    for i, art in enumerate(articles, 1):
        sc       = art.get("score", 5)
        title_zh = art.get("title_zh") or art.get("title", "")
        title_en = art.get("title", "") if art.get("lang") == "en" else ""
        summary  = art.get("summary_zh") or art.get("summary", "")
        source   = art.get("source", "")
        url      = art.get("url", "#")
        cat      = art.get("category", "product")

        insight    = art.get("product_insight_zh", "")
        pattern    = art.get("design_pattern_zh", "")
        crypto_rel = art.get("crypto_relevance_zh", "")
        data_pt    = art.get("data_point_zh", "")

        cat_color = {"crypto": "#f06595", "product": "#74c0fc", "ux": "#69db7c"}.get(cat, "#adb5bd")
        cat_label = {"crypto": "加密产品", "product": "产品设计", "ux": "UX研究"}.get(cat, cat)

        title_en_row = (
            f'<div style="font-size:12px;color:#868e96;margin-top:3px;font-style:italic;">{title_en}</div>'
            if title_en else ""
        )
        insight_row = (
            f'<div style="margin-top:10px;padding:10px 14px;background:#e6fcf5;'
            f'border-left:4px solid #20c997;border-radius:0 6px 6px 0;'
            f'font-size:13px;color:#0b7a63;line-height:1.6;">💡 <strong>产品洞察：</strong>{insight}</div>'
            if insight else ""
        )
        pattern_row = (
            f'<div style="margin-top:6px;padding:7px 12px;background:#f3f0ff;'
            f'border-radius:6px;font-size:12px;color:#6741d9;">'
            f'🧩 <strong>设计模式：</strong>{pattern}</div>'
            if pattern else ""
        )
        crypto_row = (
            f'<div style="margin-top:6px;padding:7px 12px;background:#fff9db;'
            f'border-radius:6px;font-size:12px;color:#7c5e00;">'
            f'₿ <strong>加密借鉴：</strong>{crypto_rel}</div>'
            if crypto_rel and crypto_rel != "暂无直接关联" else ""
        )
        data_row = (
            f'<div style="margin-top:6px;padding:7px 12px;background:#e8f4fd;'
            f'border-radius:6px;font-size:12px;color:#1c7ed6;">📊 {data_pt}</div>'
            if data_pt else ""
        )

        rows += f"""
<tr>
  <td style="padding:24px 28px;border-bottom:1px solid #dee2e6;">
    <div style="margin-bottom:10px;">
      <span style="display:inline-block;width:28px;height:28px;border-radius:50%;
                   background:#0ca678;text-align:center;line-height:28px;
                   font-size:13px;font-weight:800;color:#fff;margin-right:8px;">{i}</span>
      <span style="display:inline-block;padding:2px 8px;border-radius:3px;
                   font-size:11px;font-weight:700;color:{cat_color};background:{cat_color}22;">{cat_label}</span>
      <span style="display:inline-block;padding:2px 8px;border-radius:3px;
                   font-size:11px;color:#6c757d;background:#f8f9fa;
                   border:1px solid #dee2e6;margin-left:4px;">{source}</span>
      <span style="display:inline-block;padding:2px 8px;border-radius:3px;
                   font-size:11px;font-weight:700;color:#20c997;background:#e6fcf5;
                   margin-left:4px;">评分 {sc}</span>
    </div>
    <div style="font-size:17px;font-weight:700;color:#212529;line-height:1.4;margin-bottom:4px;">
      <a href="{url}" style="color:#212529;text-decoration:none;">{title_zh}</a>
    </div>
    {title_en_row}
    <div style="margin-top:10px;font-size:13px;color:#495057;line-height:1.7;">
      {summary}
    </div>
    {insight_row}
    {pattern_row}
    {crypto_row}
    {data_row}
  </td>
</tr>"""

    body = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f1f3f5;
             font-family:-apple-system,'PingFang SC','Microsoft YaHei',sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f1f3f5;padding:32px 0;">
<tr><td align="center">
<table width="660" cellpadding="0" cellspacing="0" style="max-width:660px;width:100%;">
  <tr>
    <td style="background:linear-gradient(135deg,#087f5b,#0ca678,#20c997);
               border-radius:16px 16px 0 0;padding:36px 32px;text-align:center;">
      <div style="font-size:11px;letter-spacing:3px;color:rgba(255,255,255,0.7);
                  text-transform:uppercase;margin-bottom:8px;">Weekly · Product Radar</div>
      <div style="font-size:26px;font-weight:800;color:#ffffff;">
        产品设计精选周报
      </div>
      <div style="margin-top:8px;font-size:14px;color:rgba(255,255,255,0.85);">{week_str}</div>
      <div style="margin-top:16px;padding:10px 20px;background:rgba(255,255,255,0.15);
                  border-radius:10px;display:inline-block;font-size:13px;color:#fff;">
        本周严选 <strong>{len(articles)}</strong> 篇 · 每篇均值得精读
      </div>
    </td>
  </tr>
  <tr>
    <td style="background:#fff8f0;padding:14px 28px;border-left:1px solid #dee2e6;
               border-right:1px solid #dee2e6;">
      <div style="font-size:12px;color:#868e96;line-height:1.6;">
        📌 <strong>周报说明</strong>：这是从过去7天100+篇产品设计文章中严选出来的精华，
        建议配合咖啡慢慢读。每篇都附有产品洞察和对加密产品的借鉴分析。
      </div>
    </td>
  </tr>
  <tr>
    <td style="background:#ffffff;border-radius:0 0 16px 16px;
               border:1px solid #dee2e6;border-top:none;">
      <table width="100%" cellpadding="0" cellspacing="0">
        {rows}
        <tr>
          <td style="padding:16px 28px;text-align:center;background:#f8f9fa;
                     border-radius:0 0 16px 16px;">
            <div style="font-size:11px;color:#adb5bd;">
              产品设计雷达 · 每周六精选 · AI 辅助分析
            </div>
          </td>
        </tr>
      </table>
    </td>
  </tr>
</table>
</td></tr>
</table>
</body>
</html>"""
    return body


def main():
    parser = argparse.ArgumentParser(description="Product Radar weekly digest")
    parser.add_argument("--no-score", action="store_true")
    parser.add_argument("--no-email", action="store_true")
    parser.add_argument("--output",   default="")
    args = parser.parse_args()

    articles = _fetch_weekly()
    if not articles:
        print("No articles fetched.")
        sys.exit(1)

    articles = deduplicate(articles, DEDUP_THRESHOLD)

    if args.no_score:
        for art in articles:
            art["score"]      = 5
            art["reason_zh"]  = ""
            art["title_zh"]   = art["title"]
            art["summary_zh"] = art["summary"]
    else:
        print(f"[周报] 评分 {len(articles)} 篇文章（严选模式）…")
        articles = score_articles(articles, WEEKLY_SCORING_PROMPT, batch_size=25)

    # 严选：只保留高分文章
    articles = [a for a in articles if a.get("score", 0) >= WEEKLY_MIN_SCORE]
    articles.sort(key=lambda a: -a["score"])
    articles = articles[:WEEKLY_MAX_ARTICLES]

    print(f"[周报] 严选后剩余 {len(articles)} 篇，全部做深度 enrich …")

    if not args.no_score and articles:
        for i, art in enumerate(articles, 1):
            print(f"  [{i}/{len(articles)}] {art['title'][:55]}…")
            _enrich_one(art)

    # 确保字段存在
    for art in articles:
        art.setdefault("product_insight_zh", "")
        art.setdefault("design_pattern_zh", "")
        art.setdefault("crypto_relevance_zh", "")
        art.setdefault("data_point_zh", "")

    # 生成周报 HTML
    today = datetime.now()
    week_start = today - timedelta(days=6)
    week_str = f"{week_start.strftime('%m月%d日')} – {today.strftime('%m月%d日')} 精选"

    output_dir  = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)
    date_str    = today.strftime("%Y-%m-%d")
    output_path = args.output or str(output_dir / f"weekly-{date_str}.html")

    html = _build_weekly_html(articles, week_str)
    Path(output_path).write_text(html, encoding="utf-8")
    print(f"HTML saved → {output_path}")

    if not args.no_email:
        subject = f"产品设计周报 · {week_str} · 严选{len(articles)}篇"
        send_html(subject, html)

    print(f"\n✅ 周报完成. 严选 {len(articles)} 篇精读文章")
    print(f"   HTML: file://{os.path.abspath(output_path)}")


if __name__ == "__main__":
    main()
