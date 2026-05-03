"""产品雷达 邮件模块：构建 HTML 后调用 common.mailer 发送。"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from datetime import datetime
from common.mailer import send_html


def _score_color(score: int) -> str:
    if score >= 8: return "#ff6b6b"
    if score >= 6: return "#ffa94d"
    return "#74c0fc"


def _score_label(score: int) -> str:
    if score >= 8: return "必读"
    if score >= 6: return "重要"
    return "一般"


def _perf_color(score: float) -> str:
    if score >= 8:  return "#69db7c"
    if score >= 6:  return "#ffa94d"
    return "#ff6b6b"


def _usage_bar(usage_info: dict, model_metrics: dict | None = None) -> str:
    if not usage_info or not usage_info.get("model"):
        return ""
    model     = usage_info.get("model", "unknown")
    prompt    = usage_info.get("prompt_tokens", 0)
    comp      = usage_info.get("completion_tokens", 0)
    total     = usage_info.get("total_tokens", 0)
    token_str = f"↑ {prompt:,} &nbsp;↓ {comp:,} &nbsp;共 {total:,} tokens" if total else "token 数据不可用"

    perf_html = ""
    if model_metrics and model_metrics.get("perf_score") is not None:
        ps    = model_metrics["perf_score"]
        pr    = int(model_metrics.get("parse_rate", 0) * 100)
        tr    = int(model_metrics.get("translation_rate", 0) * 100)
        ss    = model_metrics.get("score_spread", 0)
        color = _perf_color(ps)
        perf_html = (
            f'&nbsp;·&nbsp;'
            f'<span style="color:{color};font-weight:700;">评分 {ps}/10</span>'
            f'&nbsp;(解析率 {pr}% · 翻译率 {tr}% · 区分度 {ss:.1f}σ)'
        )

    return (
        f'<div style="margin-top:10px;padding:6px 14px;background:rgba(255,255,255,0.15);'
        f'border-radius:8px;font-size:11px;color:rgba(255,255,255,0.85);display:inline-block;">'
        f'🤖 {model} &nbsp;·&nbsp; {token_str}{perf_html}'
        f'</div>'
    )


def _build_email_html(articles: list[dict], date_str: str, usage_info: dict | None = None, model_metrics: dict | None = None) -> str:
    rows = ""
    for art in articles:
        sc       = art.get("score", 5)
        color    = _score_color(sc)
        label    = _score_label(sc)
        title_zh = art.get("title_zh") or art.get("title", "")
        title_en = art.get("title", "") if (art.get("lang") == "en" and art.get("title_zh") and art["title_zh"] != art.get("title", "")) else ""
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
            f'border-left:3px solid #099268;border-radius:0 5px 5px 0;'
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
        <td width="46" valign="top" style="padding-right:12px;">
          <div style="width:42px;height:42px;border-radius:8px;
                      background:{color}22;text-align:center;line-height:42px;
                      font-size:18px;font-weight:800;color:{color};">{sc}</div>
        </td>
        <td valign="top">
          <div style="font-size:15px;font-weight:600;color:#212529;line-height:1.4;">
            <a href="{url}" style="color:#212529;text-decoration:none;">{title_zh}</a>
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
      {_usage_bar(usage_info or {}, model_metrics)}
      <div style="margin-top:12px;">
        <span style="display:inline-block;padding:3px 12px;border-radius:20px;
                     background:rgba(255,107,107,0.25);color:#ff6b6b;font-size:12px;font-weight:600;">
          🔥 必读 {must_count}
        </span>
        <span style="display:inline-block;padding:3px 12px;border-radius:20px;
                     background:rgba(255,169,77,0.25);color:#ffa94d;
                     font-size:12px;font-weight:600;margin-left:8px;">
          ⚡ 重要 {imp_count}
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


def send_digest(articles: list[dict], usage_info: dict | None = None, model_metrics: dict | None = None) -> None:
    date_str = datetime.now().strftime("%Y年%m月%d日")
    subject  = f"产品设计雷达 · {datetime.now().strftime('%Y-%m-%d')} · {sum(1 for a in articles if a.get('score',0) >= 8)}条必读"
    html     = _build_email_html(articles, date_str, usage_info, model_metrics)
    send_html(subject, html)
