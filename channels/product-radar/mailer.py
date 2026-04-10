"""产品雷达 邮件模块：构建 HTML 后调用 common.mailer 发送。"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from datetime import datetime
from common.mailer import send_html


def _score_color(score: int) -> str:
    if score >= 8: return "#20c997"
    if score >= 6: return "#74c0fc"
    return "#adb5bd"


def _score_label(score: int) -> str:
    if score >= 8: return "必学"
    if score >= 6: return "值得看"
    return "参考"


def _category_emoji(category: str) -> str:
    return {"crypto": "🔐", "product": "📦", "ux": "🎨"}.get(category, "📌")


def _build_email_html(articles: list[dict], date_str: str) -> str:
    rows = ""
    for art in articles:
        sc       = art.get("score", 5)
        color    = _score_color(sc)
        label    = _score_label(sc)
        cat_emoji = _category_emoji(art.get("category", ""))
        title_zh = art.get("title_zh") or art.get("title", "")
        title_en = art.get("title", "") if art.get("lang") == "en" else ""
        summary  = art.get("summary_zh") or art.get("summary", "")
        source   = art.get("source", "")
        url      = art.get("url", "#")

        # 产品专属字段
        insight      = art.get("product_insight_zh", "")
        pattern      = art.get("design_pattern_zh", "")
        crypto_rel   = art.get("crypto_relevance_zh", "")
        data_pt      = art.get("data_point_zh", "")

        og_image       = art.get("og_image", "")
        full_summary   = art.get("full_summary_zh", "")
        display_summary = full_summary or summary

        title_en_row = (
            f'<div style="font-size:11px;color:#868e96;margin-top:2px;font-style:italic;">{title_en}</div>'
            if title_en else ""
        )
        image_row = (
            f'<div style="margin:10px 0 4px 0;">'
            f'<img src="{og_image}" alt="" style="width:100%;max-height:200px;'
            f'object-fit:cover;border-radius:6px;display:block;" /></div>'
            if og_image else ""
        )
        insight_row = (
            f'<div style="margin-top:8px;padding:7px 12px;background:#e6fcf5;'
            f'border-left:3px solid #20c997;border-radius:0 5px 5px 0;'
            f'font-size:12px;color:#0b7a63;line-height:1.6;">💡 <strong>产品洞察：</strong>{insight}</div>'
            if insight else ""
        )
        pattern_row = (
            f'<div style="margin-top:5px;padding:5px 10px;background:#f3f0ff;'
            f'border-radius:4px;font-size:11px;color:#6741d9;">🧩 设计模式：{pattern}</div>'
            if pattern else ""
        )
        crypto_row = (
            f'<div style="margin-top:5px;padding:5px 10px;background:#fff3bf;'
            f'border-radius:4px;font-size:11px;color:#7c5e00;">₿ 加密借鉴：{crypto_rel}</div>'
            if crypto_rel and crypto_rel != "暂无直接关联" else ""
        )
        data_row = (
            f'<div style="margin-top:5px;padding:5px 10px;background:#e8f4fd;'
            f'border-radius:4px;font-size:11px;color:#1c7ed6;">📊 {data_pt}</div>'
            if data_pt else ""
        )

        rows += f"""
<tr>
  <td style="padding:18px 20px;border-bottom:1px solid #dee2e6;">
    <table width="100%" cellpadding="0" cellspacing="0">
      <tr>
        <td width="44" valign="top" style="padding-right:12px;">
          <div style="width:38px;height:38px;border-radius:8px;
                      background:{color}22;text-align:center;line-height:38px;
                      font-size:16px;font-weight:800;color:{color};">{sc}</div>
        </td>
        <td valign="top">
          <div style="font-size:14px;font-weight:600;color:#212529;line-height:1.4;">
            {cat_emoji} <a href="{url}" style="color:#212529;text-decoration:none;">{title_zh}</a>
          </div>
          {title_en_row}
          <div style="margin-top:5px;">
            <span style="display:inline-block;padding:1px 7px;border-radius:3px;
                         font-size:11px;font-weight:700;color:{color};background:{color}22;">{label}</span>
            <span style="display:inline-block;padding:1px 7px;border-radius:3px;
                         font-size:11px;color:#6c757d;background:#f8f9fa;
                         border:1px solid #dee2e6;margin-left:4px;">{source}</span>
          </div>
          {image_row}
          <div style="margin-top:8px;font-size:13px;color:#495057;line-height:1.75;">
            {display_summary}
          </div>
          {insight_row}
          {pattern_row}
          {crypto_row}
          {data_row}
        </td>
      </tr>
    </table>
  </td>
</tr>"""

    must_count = sum(1 for a in articles if a.get("score", 0) >= 8)
    imp_count  = sum(1 for a in articles if 6 <= a.get("score", 0) < 8)

    body = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f8f9fa;
             font-family:-apple-system,'PingFang SC','Microsoft YaHei',sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f8f9fa;padding:24px 0;">
<tr><td align="center">
<table width="640" cellpadding="0" cellspacing="0" style="max-width:640px;width:100%;">
  <tr>
    <td style="background:linear-gradient(135deg,#0ca678,#099268);
               border-radius:12px 12px 0 0;padding:28px 24px;text-align:center;">
      <div style="font-size:11px;letter-spacing:2px;color:rgba(255,255,255,0.7);
                  text-transform:uppercase;margin-bottom:6px;">Product Radar</div>
      <div style="font-size:22px;font-weight:800;color:#ffffff;letter-spacing:0.5px;">
        产品设计雷达 · 每日速递
      </div>
      <div style="margin-top:6px;font-size:13px;color:rgba(255,255,255,0.8);">{date_str}</div>
      <div style="margin-top:12px;">
        <span style="display:inline-block;padding:3px 12px;border-radius:20px;
                     background:rgba(255,255,255,0.2);color:#ffffff;font-size:12px;font-weight:600;">
          ⚡ 必学 {must_count}
        </span>
        <span style="display:inline-block;padding:3px 12px;border-radius:20px;
                     background:rgba(255,255,255,0.15);color:rgba(255,255,255,0.9);
                     font-size:12px;margin-left:8px;">
          👀 值得看 {imp_count}
        </span>
        <span style="display:inline-block;padding:3px 12px;border-radius:20px;
                     background:rgba(255,255,255,0.1);color:rgba(255,255,255,0.7);
                     font-size:12px;margin-left:8px;">
          共 {len(articles)} 条
        </span>
      </div>
    </td>
  </tr>
  <tr>
    <td style="background:#ffffff;border-radius:0 0 12px 12px;
               border:1px solid #dee2e6;border-top:none;">
      <table width="100%" cellpadding="0" cellspacing="0">
        {rows}
        <tr>
          <td style="padding:14px 20px;text-align:center;background:#f8f9fa;
                     border-radius:0 0 12px 12px;">
            <div style="font-size:11px;color:#adb5bd;">
              AI 自动生成 · 来源：UX Collective / NNG / Figma / Coinbase / OKX Blog / 少数派 等
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


def send_digest(articles: list[dict]) -> None:
    date_str = datetime.now().strftime("%Y年%m月%d日")
    subject  = f"产品设计雷达 · {datetime.now().strftime('%m/%d')} · {sum(1 for a in articles if a.get('score',0) >= 8)}条必学"
    html     = _build_email_html(articles, date_str)
    send_html(subject, html)
