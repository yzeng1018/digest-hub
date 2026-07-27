"""Portfolio-aware investment digest HTML renderer."""

from datetime import datetime
from html import escape
from pathlib import Path

from config import SCORE_MUST_READ, SCORE_IMPORTANT


def _score_color(score: int) -> str:
    if score >= SCORE_MUST_READ:
        return "#f85149"
    if score >= SCORE_IMPORTANT:
        return "#e3b341"
    return "#3fb950"


def _score_label(score: int) -> str:
    if score >= SCORE_MUST_READ:
        return "必读"
    if score >= SCORE_IMPORTANT:
        return "重要"
    return "一般"


def _usage_bar(usage_info: dict, model_metrics: dict | None = None) -> str:
    if not usage_info or not usage_info.get("model"):
        return ""
    model  = usage_info.get("model", "unknown")
    prompt = usage_info.get("prompt_tokens", 0)
    comp   = usage_info.get("completion_tokens", 0)
    total  = usage_info.get("total_tokens", 0)

    perf_html = ""
    if model_metrics and model_metrics.get("perf_score") is not None:
        ps    = model_metrics["perf_score"]
        pr    = int(model_metrics.get("parse_rate", 0) * 100)
        tr    = int(model_metrics.get("translation_rate", 0) * 100)
        ss    = model_metrics.get("score_spread", 0)
        color = "#69db7c" if ps >= 8 else ("#ffa94d" if ps >= 6 else "#ff6b6b")
        perf_html = (
            f' &nbsp;·&nbsp; <span style="color:{color};font-weight:700;">流水线质量 {ps}/10</span>'
            f' (解析率 {pr}% · 翻译率 {tr}% · 区分度 {ss:.1f}σ)'
        )

    return (
        f'<div class="usage-bar">'
        f'🤖 {model} &nbsp;·&nbsp; ↑ {prompt:,} &nbsp;↓ {comp:,} &nbsp;共 {total:,} tokens'
        f'{perf_html}'
        f'</div>'
    )


def _section(art: dict) -> tuple[str, str]:
    if art.get("platform") == "Portfolio":
        return "portfolio", "🎯 持仓雷达"
    if art.get("platform") in {"Blog", "Memo", "Podcast"}:
        return "insight", "🧠 投资框架"
    return "market", "🌍 中外市场机会"


def _display_order(articles: list[dict]) -> list[dict]:
    return sorted(
        articles,
        key=lambda a: (
            {"portfolio": 0, "market": 1, "insight": 2}[_section(a)[0]],
            -a.get("score", 0),
        ),
    )


def _ideas_panel(articles: list[dict]) -> str:
    ideas = [a for a in articles if a.get("investment_angle_zh")][:3]
    if not ideas:
        return ""
    rows = ""
    for article in ideas:
        label = "、".join(article.get("portfolio_matches", []))
        label = label or article.get("portfolio_sector") or "市场线索"
        signal = article.get("confirmation_signal_zh", "")
        signal_html = f"<small>验证：{escape(signal)}</small>" if signal else ""
        rows += (
            f'<div class="idea"><b>{escape(label)}</b>'
            f'<div>{escape(article["investment_angle_zh"])}</div>'
            f"{signal_html}</div>"
        )
    return f'<div class="ideas"><h2>💡 今日投资线索</h2><p>以下是基于新闻的研究假设，不是买卖建议。</p>{rows}</div>'


def render(articles: list[dict], output_path: str, usage_info: dict | None = None, model_metrics: dict | None = None) -> None:
    rows = ""
    current_section = ""
    for art in _display_order(articles):
        section_key, section_title = _section(art)
        if section_key != current_section:
            rows += f'<div class="section-title">{section_title}</div>'
            current_section = section_key
        sc          = art.get("score", 5)
        color       = _score_color(sc)
        label       = _score_label(sc)
        title_zh    = art.get("title_zh") or art.get("title", "")
        title_en    = art.get("title", "") if art.get("lang") == "en" else ""
        summary     = art.get("summary_zh") or art.get("summary", "")
        reason      = art.get("reason_zh", "")
        background  = art.get("background_zh", "")
        key_players = art.get("key_players_zh", "")
        data_point  = art.get("data_point_zh", "")
        relevance   = art.get("portfolio_relevance_zh", "")
        angle       = art.get("investment_angle_zh", "")
        signal      = art.get("confirmation_signal_zh", "")
        risk        = art.get("risk_zh", "")
        source      = art.get("source", "")
        url         = art.get("url", "#")

        extra = ""
        if background:
            extra += f'<div class="tag bg-blue">📖 {escape(background)}</div>'
        if key_players:
            extra += f'<div class="tag bg-yellow">👥 {escape(key_players)}</div>'
        if data_point:
            extra += f'<div class="tag bg-green">📊 {escape(data_point)}</div>'
        if reason:
            extra += f'<div class="tag bg-purple">💡 {escape(reason)}</div>'
        if relevance:
            extra += f'<div class="tag bg-portfolio">🎯 {escape(relevance)}</div>'
        if angle:
            extra += f'<div class="tag bg-angle">🔎 {escape(angle)}</div>'
        if signal:
            extra += f'<div class="tag bg-signal">✅ 验证：{escape(signal)}</div>'
        if risk:
            extra += f'<div class="tag bg-risk">⚠️ 反证：{escape(risk)}</div>'

        rows += f"""
<div class="card">
  <div class="score" style="background:{color}1a;color:{color};">{sc}</div>
  <div class="body">
    <div class="title"><a href="{escape(url, quote=True)}">{escape(title_zh)}</a></div>
    {'<div class="title-en">' + escape(title_en) + '</div>' if title_en else ''}
    <div class="tags">
      <span class="badge" style="color:{color};background:{color}1a;">{label}</span>
      <span class="badge source">{escape(source)}</span>
    </div>
    <div class="summary">{escape(summary)}</div>
    {extra}
  </div>
</div>"""

    must_count = sum(1 for a in articles if a.get("score", 0) >= SCORE_MUST_READ)
    imp_count  = sum(1 for a in articles if SCORE_IMPORTANT <= a.get("score", 0) < SCORE_MUST_READ)
    now_str    = datetime.now().strftime("%Y-%m-%d %H:%M")

    html = f"""<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>投资情报 {now_str}</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#0d1117;color:#e6edf3;font-family:-apple-system,'PingFang SC','Microsoft YaHei',sans-serif;}}
.header{{background:linear-gradient(135deg,#1a1f2c,#0d1117);padding:28px 24px;text-align:center;border-bottom:1px solid #21262d;}}
.header h1{{font-size:22px;font-weight:800;color:#e6edf3;}}
.header h1 span{{color:#f0c040;}}
.header .meta{{margin-top:6px;font-size:13px;color:#8b949e;}}
.filters{{padding:16px 24px;display:flex;gap:8px;flex-wrap:wrap;border-bottom:1px solid #21262d;}}
.filter-btn{{padding:5px 14px;border-radius:20px;border:1px solid #30363d;background:#161b22;color:#8b949e;cursor:pointer;font-size:12px;}}
.filter-btn.active{{border-color:#f0c040;color:#f0c040;background:#f0c0401a;}}
.stats{{display:flex;gap:12px;margin-top:12px;justify-content:center;flex-wrap:wrap;}}
.stat{{padding:3px 12px;border-radius:20px;font-size:12px;font-weight:600;}}
.container{{max-width:780px;margin:0 auto;padding:16px 16px 40px;}}
.ideas{{max-width:780px;margin:16px auto 0;padding:16px;border:1px solid #3d3412;border-radius:10px;background:#19170e;}}
.ideas h2{{font-size:16px;color:#f0c040;}}.ideas>p{{font-size:11px;color:#8b949e;margin-top:4px;}}
.idea{{margin-top:12px;padding-top:12px;border-top:1px solid #302b16;font-size:13px;line-height:1.6;}}
.idea b{{color:#f0c040;}}.idea small{{display:block;color:#56d364;margin-top:3px;}}
.section-title{{font-size:15px;font-weight:800;color:#e6edf3;margin:18px 2px 10px;padding-bottom:8px;border-bottom:1px solid #30363d;}}
.card{{display:flex;gap:12px;padding:16px;border:1px solid #21262d;border-radius:8px;margin-bottom:12px;background:#161b22;}}
.score{{flex-shrink:0;width:42px;height:42px;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:18px;font-weight:800;}}
.body{{flex:1;min-width:0;}}
.title a{{color:#e6edf3;text-decoration:none;font-size:15px;font-weight:600;line-height:1.4;}}
.title a:hover{{color:#58a6ff;}}
.title-en{{font-size:12px;color:#8b949e;margin-top:3px;}}
.tags{{margin-top:6px;display:flex;gap:6px;flex-wrap:wrap;}}
.badge{{padding:1px 7px;border-radius:3px;font-size:11px;font-weight:700;}}
.badge.source{{color:#8b949e;background:#21262d;font-weight:400;}}
.summary{{margin-top:8px;font-size:13px;color:#8b949e;line-height:1.65;}}
.tag{{margin-top:8px;padding:6px 10px;border-radius:4px;font-size:12px;line-height:1.5;}}
.bg-blue{{background:#0d2137;color:#79c0ff;}}
.bg-yellow{{background:#1f1a00;color:#e3c000;}}
.bg-green{{background:#0d2010;color:#56d364;}}
.bg-purple{{background:#1a0d2e;color:#c084fc;}}
.bg-portfolio{{background:#2a1807;color:#ffb86b;}}
.bg-angle{{background:#121d32;color:#9ecbff;}}
.bg-signal{{background:#0d2010;color:#56d364;}}
.bg-risk{{background:#2b1113;color:#ff8c8c;}}
.usage-bar{{margin-top:10px;padding:5px 14px;background:rgba(255,255,255,0.08);border-radius:20px;
            font-size:11px;color:rgba(255,255,255,0.7);display:inline-block;}}
</style>
</head>
<body>
<div class="header">
  <h1>每日 <span>投资</span> 情报</h1>
  <div class="meta">{now_str}</div>
  {_usage_bar(usage_info or dict(), model_metrics)}
  <div class="stats">
    <span class="stat" style="background:rgba(248,81,73,0.15);color:#f85149;">🔥 必读 {must_count}</span>
    <span class="stat" style="background:rgba(227,179,65,0.15);color:#e3b341;">⚡ 重要 {imp_count}</span>
    <span class="stat" style="background:rgba(255,255,255,0.05);color:#8b949e;">共 {len(articles)} 条</span>
  </div>
</div>
{_ideas_panel(articles)}
<div class="filters">
  <button class="filter-btn active" onclick="filter('all')">全部</button>
  <button class="filter-btn" onclick="filter('must')">必读</button>
  <button class="filter-btn" onclick="filter('important')">重要</button>
  <button class="filter-btn" onclick="filter('normal')">一般</button>
</div>
<div class="container" id="feed">
{rows}
</div>
<script>
function filter(t){{
  document.querySelectorAll('.filter-btn').forEach(b=>b.classList.remove('active'));
  event.target.classList.add('active');
  document.querySelectorAll('.card').forEach(c=>{{
    const s=parseInt(c.querySelector('.score').textContent);
    const show=t==='all'||(t==='must'&&s>=8)||(t==='important'&&s>=6&&s<8)||(t==='normal'&&s<6);
    c.style.display=show?'flex':'none';
  }});
}}
</script>
</body>
</html>"""

    Path(output_path).write_text(html, encoding="utf-8")
    print(f"HTML 已生成: {output_path}")
