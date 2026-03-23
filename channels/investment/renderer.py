"""投资情报 HTML 渲染器（深色主题 + key_players + data_point）。"""

from datetime import datetime
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


def render(articles: list[dict], output_path: str) -> None:
    rows = ""
    for art in articles:
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
        source      = art.get("source", "")
        url         = art.get("url", "#")

        extra = ""
        if background:
            extra += f'<div class="tag bg-blue">📖 {background}</div>'
        if key_players:
            extra += f'<div class="tag bg-yellow">👥 {key_players}</div>'
        if data_point:
            extra += f'<div class="tag bg-green">📊 {data_point}</div>'
        if reason:
            extra += f'<div class="tag bg-purple">💡 {reason}</div>'

        rows += f"""
<div class="card">
  <div class="score" style="background:{color}1a;color:{color};">{sc}</div>
  <div class="body">
    <div class="title"><a href="{url}">{title_zh}</a></div>
    {'<div class="title-en">' + title_en + '</div>' if title_en else ''}
    <div class="tags">
      <span class="badge" style="color:{color};background:{color}1a;">{label}</span>
      <span class="badge source">{source}</span>
    </div>
    <div class="summary">{summary}</div>
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
</style>
</head>
<body>
<div class="header">
  <h1>每日 <span>投资</span> 情报</h1>
  <div class="meta">{now_str}</div>
  <div class="stats">
    <span class="stat" style="background:rgba(248,81,73,0.15);color:#f85149;">🔥 必读 {must_count}</span>
    <span class="stat" style="background:rgba(227,179,65,0.15);color:#e3b341;">⚡ 重要 {imp_count}</span>
    <span class="stat" style="background:rgba(255,255,255,0.05);color:#8b949e;">共 {len(articles)} 条</span>
  </div>
</div>
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
