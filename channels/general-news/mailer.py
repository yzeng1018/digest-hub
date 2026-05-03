"""科技财经速读 邮件模块：构建 HTML 后调用 common.mailer 发送。"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from datetime import datetime
from common.mailer import send_html


def _score_color(score: int) -> str:
    if score >= 8:
        return "#ff6b6b"
    if score >= 6:
        return "#ffa94d"
    return "#74c0fc"


def _score_label(score: int) -> str:
    if score >= 8:
        return "必读"
    if score >= 6:
        return "重要"
    return "一般"


def _perf_color(score: float) -> str:
    if score >= 8:  return "#69db7c"
    if score >= 6:  return "#ffa94d"
    return "#ff6b6b"


def _usage_bar(usage_info: dict, model_metrics: dict | None = None) -> str:
    if not usage_info or not usage_info.get("model"):
        return ""
    model  = usage_info.get("model", "unknown")
    prompt = usage_info.get("prompt_tokens", 0)
    comp   = usage_info.get("completion_tokens", 0)
    total  = usage_info.get("total_tokens", 0)
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
        f'🤖 {model} &nbsp;·&nbsp; '
        f'{token_str}'
        f'{perf_html}'
        f'</div>'
    )


def _build_email_html(articles: list[dict], date_str: str, usage_info: dict | None = None, model_metrics: dict | None = None) -> str:
    rows = ""
    for art in articles:
        sc           = art.get("score", 5)
        color        = _score_color(sc)
        label        = _score_label(sc)
        title_zh     = art.get("title_zh") or art.get("title", "")
        title_en     = art.get("title", "") if (art.get("lang") == "en" and art.get("title_zh") and art["title_zh"] != art.get("title", "")) else ""
        summary_zh   = art.get("summary_zh", "")
        summary_en   = art.get("summary", "")
        summary      = summary_zh or summary_en
        reason       = art.get("reason_zh", "")
        background   = art.get("background_zh", "")
        key_players  = art.get("key_players_zh", "")
        data_point   = art.get("data_point_zh", "")
        source       = art.get("source", "")
        url          = art.get("url", "#")

        title_en_row = (
            f'<div style="font-size:12px;color:#868e96;margin-top:3px;">{title_en}</div>'
            if title_en else ""
        )
        background_row = (
            f'<div style="margin-top:8px;padding:6px 10px;background:#e8f4fd;'
            f'border-radius:4px;font-size:12px;color:#1c7ed6;">📖 {background}</div>'
            if background else ""
        )
        key_players_row = (
            f'<div style="margin-top:6px;padding:6px 10px;background:#fff3cd;'
            f'border-radius:4px;font-size:12px;color:#856404;">👥 {key_players}</div>'
            if key_players else ""
        )
        data_point_row = (
            f'<div style="margin-top:6px;padding:6px 10px;background:#d4edda;'
            f'border-radius:4px;font-size:12px;color:#155724;">📊 {data_point}</div>'
            if data_point else ""
        )
        reason_row = (
            f'<div style="margin-top:6px;padding:6px 10px;background:#e2e3e5;'
            f'border-radius:4px;font-size:12px;color:#383d41;">💡 {reason}</div>'
            if reason else ""
        )

        rows += f"""
<tr>
  <td style="padding:16px 20px;border-bottom:1px solid #dee2e6;">
    <table width="100%" cellpadding="0" cellspacing="0">
      <tr>
        <td width="48" valign="top" style="padding-right:12px;">
          <div style="width:42px;height:42px;border-radius:8px;
                      background:{color}22;text-align:center;line-height:42px;
                      font-size:18px;font-weight:800;color:{color};">{sc}</div>
        </td>
        <td valign="top">
          <div style="font-size:15px;font-weight:600;color:#212529;line-height:1.4;">
            <a href="{url}" style="color:#212529;text-decoration:none;">{title_zh}</a>
          </div>
          {title_en_row}
          <div style="margin-top:6px;">
            <span style="display:inline-block;padding:1px 7px;border-radius:3px;
                         font-size:11px;font-weight:700;color:{color};background:{color}22;">{label}</span>
            <span style="display:inline-block;padding:1px 7px;border-radius:3px;
                         font-size:11px;color:#6c757d;background:#f8f9fa;
                         border:1px solid #dee2e6;margin-left:4px;">{source}</span>
          </div>
          <div style="margin-top:8px;font-size:13px;color:#495057;line-height:1.65;">
            {summary}
          </div>
          {"" if not (art.get("lang") == "en" and summary_zh and summary_en) else f'<div style="margin-top:5px;font-size:12px;color:#868e96;font-style:italic;line-height:1.5;">{summary_en}</div>'}
          {background_row}
          {key_players_row}
          {data_point_row}
          {reason_row}
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
    <td style="background:linear-gradient(135deg,#4c6ef5,#364fc7);
               border-radius:12px 12px 0 0;padding:28px 24px;text-align:center;">
      <div style="font-size:22px;font-weight:800;color:#ffffff;letter-spacing:0.5px;">
        每日科技财经速读
      </div>
      <div style="margin-top:6px;font-size:13px;color:rgba(255,255,255,0.8);">{date_str}</div>
      {_usage_bar(usage_info or {}, model_metrics)}
      <div style="margin-top:12px;">
        <span style="display:inline-block;padding:3px 12px;border-radius:20px;
                     background:rgba(255,107,107,0.25);color:#ff6b6b;font-size:12px;font-weight:600;">
          🔥 必读 {must_count}
        </span>
        <span style="display:inline-block;padding:3px 12px;border-radius:20px;
                     background:rgba(255,169,77,0.25);color:#ffa94d;font-size:12px;font-weight:600;margin-left:8px;">
          ⚡ 重要 {imp_count}
        </span>
        <span style="display:inline-block;padding:3px 12px;border-radius:20px;
                     background:rgba(255,255,255,0.15);color:rgba(255,255,255,0.9);font-size:12px;margin-left:8px;">
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
              AI 自动生成 · 来源：TechCrunch / Wired / Bloomberg / 36氪 / 虎嗅
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
    subject  = f"每日科技财经速读 · {datetime.now().strftime('%Y-%m-%d')}"
    html     = _build_email_html(articles, date_str, usage_info=usage_info, model_metrics=model_metrics)
    send_html(subject, html)
