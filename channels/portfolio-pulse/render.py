"""HTML 渲染：重点持仓展开，其余一行带过。"""

from html import escape

from config import MARKET_LABEL, MARKET_NOTE, MARKET_ORDER

# 中国市场红涨绿跌
RED, GREEN, GRAY = "#d93025", "#1e8e3e", "#5f6368"


def _color(v: float) -> str:
    return RED if v > 0 else (GREEN if v < 0 else GRAY)


def _sign(v: float, digits: int = 2, suffix: str = "%") -> str:
    return f"{'+' if v > 0 else ''}{v:.{digits}f}{suffix}"


def _money(v: float) -> str:
    if abs(v) >= 1e8:
        return f"{v / 1e8:.2f} 亿"
    if abs(v) >= 1e4:
        return f"{v / 1e4:.1f} 万"
    return f"{v:,.0f}"


def _news_rows(news: list[dict], tag: str = "", tag_bg: str = "#f1f3f4",
               tag_fg: str = "#5f6368") -> str:
    if not news:
        return ""
    rows = ""
    for n in news:
        label = (f'<span style="display:inline-block;padding:0 5px;border-radius:3px;'
                 f'background:{tag_bg};color:{tag_fg};font-size:11px;'
                 f'margin-right:5px;">{tag}</span>') if tag else ""
        rows += (
            f'<div style="margin-top:5px;font-size:13px;line-height:1.5;">{label}'
            f'<a href="{escape(n["link"])}" style="color:#1a73e8;text-decoration:none;">'
            f'{escape(n["title"])}</a>'
            f'<span style="color:#9aa0a6;font-size:12px;"> · {escape(n["source"])} · {n["published"]}</span></div>'
        )
    return f'<div style="margin-top:8px;">{rows}</div>'


def _filings_row(filings: list[dict]) -> str:
    if not filings:
        return ""
    chips = ""
    for f in filings:
        earn = f.get("isEarnings")
        bg, fg = ("#fef7e0", "#8a6100") if earn else ("#f1f3f4", "#5f6368")
        chips += (
            f'<a href="{escape(f["url"])}" style="display:inline-block;margin-right:6px;'
            f'padding:2px 8px;border-radius:4px;background:{bg};color:{fg};'
            f'font-size:12px;font-weight:{"600" if earn else "500"};text-decoration:none;">'
            f'{escape(f["form"])} · {f["date"]}</a>'
        )
    return (f'<div style="margin-top:7px;"><span style="font-size:12px;color:#9aa0a6;">'
            f'官方报送 </span>{chips}</div>')


def _verdict_row(info: dict) -> str:
    """LLM 研判：一句话结论 + 财报要点 + 后续关注点。"""
    data = info.get("llm") or {}
    verdict = (data.get("verdict") or "").strip()
    if not verdict:
        return ""
    parts = [f'<div style="font-size:13px;color:#202124;line-height:1.6;">{escape(verdict)}</div>']
    earnings = (data.get("earnings") or "").strip()
    if earnings:
        parts.append(
            f'<div style="font-size:12px;color:#8a6100;line-height:1.6;margin-top:4px;">'
            f'<span style="color:#9aa0a6;">财报 </span>{escape(earnings)}</div>')
    watch = (data.get("watch") or "").strip()
    if watch:
        parts.append(
            f'<div style="font-size:12px;color:#5f6368;line-height:1.6;margin-top:4px;">'
            f'<span style="color:#9aa0a6;">关注 </span>{escape(watch)}</div>')
    driver = (data.get("driver") or "").strip()
    label = ""
    if driver and driver != "信息不足":
        label = (f'<span style="display:inline-block;padding:1px 7px;border-radius:3px;'
                 f'font-size:11px;background:#e8f0fe;color:#1967d2;margin-left:5px;">'
                 f'{escape(driver)}</span>')
    return (
        f'<div style="margin-top:9px;padding:9px 11px;border-radius:7px;'
        f'background:#f8f9fb;border-left:3px solid #c5d4f1;">'
        f'<div style="font-size:11px;color:#9aa0a6;letter-spacing:1px;">AI 研判{label}</div>'
        + "".join(parts) + "</div>")


def _badge(r: str) -> str:
    if r == "财报":
        bg, fg = "#fef7e0", "#8a6100"
    elif r == "异动":
        bg, fg = "#fce8e6", "#c5221f"
    else:
        bg, fg = "#f1f3f4", "#5f6368"
    return (f'<span style="display:inline-block;padding:1px 7px;border-radius:3px;'
            f'font-size:11px;background:{bg};color:{fg};margin-left:5px;">{escape(r)}</span>')


def _card(h: dict, q: dict, info: dict, reasons: list[str]) -> str:
    pct = q.get("chgPct") or 0.0
    c = _color(pct)
    badge = "".join(_badge(r) for r in reasons)
    return f"""
    <tr><td style="padding:14px 18px;border-bottom:1px solid #eceff1;">
      <table width="100%" cellpadding="0" cellspacing="0"><tr>
        <td width="72" valign="top">
          <div style="font-size:21px;font-weight:700;color:{c};line-height:1.1;">{_sign(pct)}</div>
          <div style="font-size:12px;color:{c};margin-top:2px;">{q.get('price')}</div>
        </td>
        <td valign="top">
          <div style="font-size:15px;font-weight:600;color:#202124;">
            {escape(h['name'])} <span style="font-weight:400;color:#80868b;font-size:13px;">{escape(h['ticker'])}</span>
            {badge}
          </div>
          <div style="font-size:12px;color:#80868b;margin-top:3px;">
            {escape(h['sector'])} · 持仓 {h['quantity']:,.0f} 股 · 市值 {_money(info['valueCny'])} · 成本 {h['avgCost']:.2f}
            <span style="color:{_color(info['pnlCny'])};">（{_sign(info['pnlCny'] / max(info['costCny'], 1) * 100)}）</span>
          </div>
          {_verdict_row(info)}
          {_news_rows(info.get('earnings') or [], tag="财报", tag_bg="#fef7e0", tag_fg="#8a6100")}
          {_filings_row(info.get('filings') or [])}
          {_news_rows(_plain_news(info))}
        </td>
      </tr></table>
    </td></tr>"""


def _plain_news(info: dict) -> list[dict]:
    """普通新闻：已在财报区出现过的不再重复。"""
    seen = {n.get("title") for n in (info.get("earnings") or [])}
    return [n for n in (info.get("news") or []) if n.get("title") not in seen]


def _quiet_rows(items: list[tuple[dict, dict, dict]]) -> str:
    rows = ""
    for h, q, info in items:
        pct = q.get("chgPct") or 0.0
        rows += f"""
      <tr>
        <td style="padding:7px 12px;border-bottom:1px solid #f1f3f4;font-size:13px;color:#202124;">{escape(h['name'])}</td>
        <td style="padding:7px 12px;border-bottom:1px solid #f1f3f4;font-size:12px;color:#80868b;">{escape(h['ticker'])}</td>
        <td style="padding:7px 12px;border-bottom:1px solid #f1f3f4;font-size:13px;text-align:right;color:#202124;">{q.get('price')}</td>
        <td style="padding:7px 12px;border-bottom:1px solid #f1f3f4;font-size:13px;text-align:right;color:{_color(pct)};font-weight:500;">{_sign(pct)}</td>
        <td style="padding:7px 12px;border-bottom:1px solid #f1f3f4;font-size:12px;text-align:right;color:#80868b;">{_money(info['valueCny'])}</td>
      </tr>"""
    return rows


def render(payload: dict) -> str:
    date_str = payload["date"]
    total = payload["totalValueCny"]
    day_pnl = payload["dayPnlCny"]
    total_pnl = payload["totalPnlCny"]
    alerts = payload["alerts"]
    quiet = payload["quiet"]

    head_color = _color(day_pnl)
    alert_html = ""
    for market in MARKET_ORDER:
        group = [a for a in alerts if a[0]["market"] == market]
        if not group:
            continue
        cards = "".join(_card(h, q, info, reasons) for h, q, info, reasons in group)
        alert_html += f"""
      <tr><td style="padding:12px 18px 6px;background:#fafbfc;font-size:12px;
          color:#5f6368;letter-spacing:1px;border-bottom:1px solid #eceff1;">
        {MARKET_LABEL[market]} · {MARKET_NOTE[market]}
      </td></tr>
      {cards}"""

    if not alert_html:
        alert_html = """
      <tr><td style="padding:26px 18px;text-align:center;color:#80868b;font-size:14px;">
        今日无个股触发异动或重点事件，全部持仓见下方汇总表。
      </td></tr>"""

    overview = (payload.get("overview") or "").strip()
    overview_html = ""
    if overview:
        overview_html = f"""
      <tr><td style="padding:14px 18px;background:#f8f9fb;border-bottom:1px solid #eceff1;">
        <div style="font-size:11px;color:#9aa0a6;letter-spacing:1px;">AI 总览</div>
        <div style="font-size:13px;color:#202124;line-height:1.65;margin-top:5px;">{escape(overview)}</div>
      </td></tr>"""

    quiet_html = ""
    if quiet:
        quiet_html = f"""
      <tr><td style="padding:14px 18px 8px;font-size:13px;font-weight:600;color:#202124;">
        其余 {len(quiet)} 只 · 无异动
      </td></tr>
      <tr><td style="padding:0 8px 8px;">
        <table width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #f1f3f4;border-radius:8px;">
          <tr style="background:#fafbfc;">
            <th align="left"  style="padding:6px 12px;font-size:11px;color:#9aa0a6;font-weight:500;">名称</th>
            <th align="left"  style="padding:6px 12px;font-size:11px;color:#9aa0a6;font-weight:500;">代码</th>
            <th align="right" style="padding:6px 12px;font-size:11px;color:#9aa0a6;font-weight:500;">现价</th>
            <th align="right" style="padding:6px 12px;font-size:11px;color:#9aa0a6;font-weight:500;">涨跌</th>
            <th align="right" style="padding:6px 12px;font-size:11px;color:#9aa0a6;font-weight:500;">市值</th>
          </tr>
          {_quiet_rows(quiet)}
        </table>
      </td></tr>"""

    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f4f5f7;font-family:-apple-system,'PingFang SC','Microsoft YaHei',sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f5f7;padding:18px 0;">
<tr><td align="center">
<table width="660" cellpadding="0" cellspacing="0" style="max-width:660px;width:100%;">
  <tr><td style="background:#1f2937;border-radius:12px 12px 0 0;padding:24px;">
    <div style="font-size:20px;font-weight:700;color:#fff;">我的持仓分析</div>
    <div style="font-size:13px;color:rgba(255,255,255,0.65);margin-top:4px;">{date_str} · 共 {payload['count']} 只</div>
    <div style="margin-top:16px;">
      <span style="display:inline-block;padding:2px 10px;border-radius:20px;background:rgba(255,255,255,0.12);color:#fff;font-size:12px;">总市值 {_money(total)}</span>
      <span style="display:inline-block;padding:2px 10px;border-radius:20px;margin-left:8px;font-size:12px;font-weight:600;
        background:{'rgba(217,48,37,0.18)' if day_pnl > 0 else 'rgba(30,142,62,0.18)'};color:{'#ff8a80' if day_pnl > 0 else '#81c995'};">
        当日 {_sign(day_pnl / max(total, 1) * 100)}（{'+' if day_pnl > 0 else ''}{_money(day_pnl)}）
      </span>
      <span style="display:inline-block;padding:2px 10px;border-radius:20px;margin-left:8px;background:rgba(255,255,255,0.12);color:rgba(255,255,255,0.9);font-size:12px;">
        累计 {'+' if total_pnl > 0 else ''}{_money(total_pnl)}
      </span>
    </div>
  </td></tr>
  <tr><td style="background:#fff;border-radius:0 0 12px 12px;border:1px solid #e3e5e8;border-top:none;">
    <table width="100%" cellpadding="0" cellspacing="0">
      {overview_html}
      {alert_html}
      {quiet_html}
      <tr><td style="padding:12px;text-align:center;background:#fafbfc;border-radius:0 0 12px 12px;">
        <div style="font-size:11px;color:#b0b4b9;">
          仅推送异动与重点事件 · 行情源新浪财经 · 财报与新闻源 Google News · 报送 SEC EDGAR
        </div>
      </td></tr>
    </table>
  </td></tr>
</table>
</td></tr></table>
</body></html>"""
