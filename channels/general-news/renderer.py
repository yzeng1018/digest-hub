"""
Generates a self-contained HTML digest file.
"""

import html as html_lib
from datetime import datetime

from config import SCORE_MUST_READ, SCORE_IMPORTANT

CSS = """
:root {
  --bg: #0f1117;
  --surface: #1a1d27;
  --surface2: #22253a;
  --border: #2e3150;
  --text: #e8eaf6;
  --text-muted: #8b8fa8;
  --accent: #6c7dff;
  --must-read: #ff6b6b;
  --important: #ffa94d;
  --normal: #74c0fc;
  --tag-bg: #2a2d42;
  --zh-tag: #2d3b2d;
  --en-tag: #2d3046;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  background: var(--bg);
  color: var(--text);
  font-family: -apple-system, "PingFang SC", "Microsoft YaHei", "Segoe UI", sans-serif;
  line-height: 1.6;
  padding: 0 0 60px;
}
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }

/* ── Header ── */
.header {
  background: linear-gradient(135deg, #1a1d27 0%, #0f1117 100%);
  border-bottom: 1px solid var(--border);
  padding: 32px 40px 24px;
  position: sticky;
  top: 0;
  z-index: 100;
  backdrop-filter: blur(10px);
}
.header-inner { max-width: 900px; margin: 0 auto; }
.header h1 { font-size: 22px; font-weight: 700; letter-spacing: 0.5px; }
.header h1 span { color: var(--accent); }
.header-meta {
  display: flex;
  gap: 16px;
  align-items: center;
  margin-top: 8px;
  font-size: 13px;
  color: var(--text-muted);
  flex-wrap: wrap;
}
.stat-badge {
  background: var(--tag-bg);
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 2px 10px;
  font-size: 12px;
}

/* ── Filter tabs ── */
.filter-bar {
  max-width: 900px;
  margin: 20px auto 0;
  padding: 0 40px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.filter-btn {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 20px;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 13px;
  padding: 6px 16px;
  transition: all 0.15s;
}
.filter-btn:hover { border-color: var(--accent); color: var(--text); }
.filter-btn.active {
  background: var(--accent);
  border-color: var(--accent);
  color: #fff;
  font-weight: 600;
}

/* ── Section headings ── */
.section-title {
  max-width: 900px;
  margin: 32px auto 12px;
  padding: 0 40px;
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1.5px;
  color: var(--text-muted);
}
.section-title::after {
  content: "";
  flex: 1;
  height: 1px;
  background: var(--border);
}

/* ── Article card ── */
.card-list { max-width: 900px; margin: 0 auto; padding: 0 40px; }
.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  margin-bottom: 14px;
  padding: 20px 24px;
  transition: border-color 0.15s, transform 0.1s;
}
.card:hover {
  border-color: var(--accent);
  transform: translateY(-1px);
}
.card.must-read { border-left: 3px solid var(--must-read); }
.card.important { border-left: 3px solid var(--important); }
.card.normal     { border-left: 3px solid var(--normal); }

.card-header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 10px;
}
.score-badge {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 15px;
  font-weight: 800;
}
.must-read .score-badge  { background: rgba(255,107,107,0.15); color: var(--must-read); }
.important .score-badge  { background: rgba(255,169,77,0.15); color: var(--important); }
.normal .score-badge     { background: rgba(116,192,252,0.15); color: var(--normal); }

.card-title-block { flex: 1; }
.card-title-zh {
  font-size: 16px;
  font-weight: 600;
  line-height: 1.4;
  margin-bottom: 3px;
}
.card-title-en {
  font-size: 12px;
  color: var(--text-muted);
  line-height: 1.4;
}

.card-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 10px;
}
.tag {
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  padding: 2px 7px;
}
.tag-source { background: var(--tag-bg); color: var(--text-muted); border: 1px solid var(--border); }
.tag-zh { background: var(--zh-tag); color: #81c784; }
.tag-en { background: var(--en-tag); color: #90caf9; }
.tag-tech    { background: #1e2d3d; color: #64b5f6; }
.tag-finance { background: #2d2515; color: #ffb74d; }

.card-summary {
  font-size: 14px;
  color: var(--text-muted);
  margin-bottom: 10px;
  line-height: 1.65;
}

.card-background {
  font-size: 12px;
  color: #90caf9;
  background: rgba(100,181,246,0.07);
  border-radius: 6px;
  padding: 6px 10px;
  margin-bottom: 8px;
  line-height: 1.6;
}

.card-reason {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #a5d6a7;
  background: rgba(129,199,132,0.07);
  border-radius: 6px;
  padding: 6px 10px;
  margin-bottom: 10px;
}
.card-reason::before { content: "💡"; font-size: 13px; }

.card-footer {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 12px;
  color: var(--text-muted);
}
.card-footer a.read-link {
  margin-left: auto;
  background: var(--tag-bg);
  border: 1px solid var(--border);
  border-radius: 6px;
  color: var(--text);
  font-weight: 600;
  padding: 4px 12px;
  transition: background 0.15s;
}
.card-footer a.read-link:hover {
  background: var(--accent);
  border-color: var(--accent);
  color: #fff;
  text-decoration: none;
}

/* ── Empty state ── */
.empty { color: var(--text-muted); font-size: 14px; padding: 20px 40px; }

/* ── Filter JS ── */
.hidden { display: none !important; }

/* ── Usage bar ── */
.usage-bar {
  background: rgba(255,255,255,0.06);
  border-radius: 20px;
  color: var(--text-muted);
  display: inline-block;
  font-size: 11px;
  margin-top: 8px;
  padding: 4px 12px;
}
"""

JS = """
function filterCards(level) {
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  document.querySelector('[data-filter="' + level + '"]').classList.add('active');
  document.querySelectorAll('.card').forEach(c => {
    if (level === 'all') {
      c.classList.remove('hidden');
    } else {
      c.classList.toggle('hidden', !c.classList.contains(level));
    }
  });
  document.querySelectorAll('.section').forEach(s => {
    const visible = s.querySelectorAll('.card:not(.hidden)').length;
    s.querySelector('.section-title') && (s.querySelector('.section-title').style.display = visible ? '' : 'none');
    s.querySelector('.card-list')     && (s.querySelector('.card-list').style.display     = visible ? '' : 'none');
  });
}
"""


def _card_class(score: int) -> str:
    if score >= SCORE_MUST_READ:
        return "must-read"
    if score >= SCORE_IMPORTANT:
        return "important"
    return "normal"


def _e(text: str) -> str:
    """HTML-escape a string."""
    return html_lib.escape(str(text or ""))


def _format_time(iso: str) -> str:
    if not iso:
        return ""
    try:
        dt = datetime.fromisoformat(iso)
        return dt.strftime("%m-%d %H:%M UTC")
    except Exception:
        return ""


def _render_card(art: dict) -> str:
    cls = _card_class(art["score"])
    score = art["score"]
    title_zh = _e(art.get("title_zh") or art["title"])
    title_en = _e(art["title"]) if art["lang"] == "en" else ""
    summary = _e(art.get("summary_zh") or art.get("summary", ""))
    reason = _e(art.get("reason_zh", ""))
    background = _e(art.get("background_zh", ""))
    source = _e(art["source"])
    lang_tag = "中文" if art["lang"] == "zh" else "EN"
    lang_cls = "tag-zh" if art["lang"] == "zh" else "tag-en"
    cat_cls = "tag-finance" if art["category"] == "finance" else "tag-tech"
    cat_label = "财经" if art["category"] == "finance" else "科技"
    pub = _format_time(art.get("published", ""))
    url = _e(art.get("url", "#"))

    title_en_html = (
        f'<div class="card-title-en">{title_en}</div>' if title_en else ""
    )
    reason_html = (
        f'<div class="card-reason">{reason}</div>' if reason else ""
    )
    background_html = (
        f'<div class="card-background">📖 {background}</div>' if background else ""
    )
    key_players = _e(art.get("key_players_zh", ""))
    data_point = _e(art.get("data_point_zh", ""))
    key_players_html = (
        f'<div class="card-background">👥 {key_players}</div>' if key_players else ""
    )
    data_point_html = (
        f'<div class="card-background">📊 {data_point}</div>' if data_point else ""
    )
    pub_html = f'<span>{pub}</span>' if pub else ""

    return f"""
<div class="card {cls}" data-score="{score}">
  <div class="card-header">
    <div class="score-badge">{score}</div>
    <div class="card-title-block">
      <div class="card-title-zh">{title_zh}</div>
      {title_en_html}
    </div>
  </div>
  <div class="card-tags">
    <span class="tag tag-source">{source}</span>
    <span class="tag {lang_cls}">{lang_tag}</span>
    <span class="tag {cat_cls}">{cat_label}</span>
  </div>
  <div class="card-summary">{summary}</div>
  {background_html}
  {key_players_html}
  {data_point_html}
  {reason_html}
  <div class="card-footer">
    {pub_html}
    <a class="read-link" href="{url}" target="_blank" rel="noopener">阅读原文 →</a>
  </div>
</div>"""


def _usage_bar_html(usage_info: dict, model_metrics: dict | None = None) -> str:
    if not usage_info or not usage_info.get("total_tokens"):
        return ""
    model  = usage_info.get("model", "unknown")
    prompt = usage_info.get("prompt_tokens", 0)
    comp   = usage_info.get("completion_tokens", 0)
    total  = usage_info.get("total_tokens", 0)

    perf = ""
    if model_metrics and model_metrics.get("perf_score") is not None:
        ps    = model_metrics["perf_score"]
        pr    = int(model_metrics.get("parse_rate", 0) * 100)
        tr    = int(model_metrics.get("translation_rate", 0) * 100)
        ss    = model_metrics.get("score_spread", 0)
        color = "#69db7c" if ps >= 8 else ("#ffa94d" if ps >= 6 else "#ff6b6b")
        perf = (
            f' &nbsp;·&nbsp; <span style="color:{color};font-weight:700;">评分 {ps}/10</span>'
            f' (解析率 {pr}% · 翻译率 {tr}% · 区分度 {ss:.1f}σ)'
        )

    return (
        f'<span class="usage-bar">'
        f'🤖 {_e(model)} &nbsp;·&nbsp; ↑ {prompt:,} &nbsp;↓ {comp:,} &nbsp;共 {total:,} tokens'
        f'{perf}'
        f'</span>'
    )


def render(articles: list[dict], output_path: str, usage_info: dict | None = None, model_metrics: dict | None = None) -> None:
    """Write a self-contained HTML digest to *output_path*."""
    date_str = datetime.now().strftime("%Y年%m月%d日")
    short_date = datetime.now().strftime("%Y-%m-%d")

    must_reads = [a for a in articles if a["score"] >= SCORE_MUST_READ]
    important  = [a for a in articles if SCORE_IMPORTANT <= a["score"] < SCORE_MUST_READ]
    normal     = [a for a in articles if a["score"] < SCORE_IMPORTANT]

    def section(title: str, items: list[dict], section_class: str) -> str:
        if not items:
            return ""
        cards = "\n".join(_render_card(a) for a in items)
        return f"""
<div class="section">
  <div class="section-title">{_e(title)}</div>
  <div class="card-list">{cards}</div>
</div>"""

    body_sections = (
        section(f"🔥 必读  ·  {len(must_reads)} 篇", must_reads, "must-read")
        + section(f"⚡ 重要  ·  {len(important)} 篇", important, "important")
        + section(f"📌 一般  ·  {len(normal)} 篇", normal, "normal")
    )

    total = len(articles)
    gen_time = datetime.now().strftime("%H:%M")

    html_out = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>每日科技财经速读 · {short_date}</title>
  <style>{CSS}</style>
</head>
<body>

<div class="header">
  <div class="header-inner">
    <h1>每日<span>科技财经</span>速读</h1>
    <div class="header-meta">
      <span>{date_str}</span>
      <span class="stat-badge">共 {total} 篇</span>
      <span class="stat-badge">🔥 必读 {len(must_reads)}</span>
      <span class="stat-badge">⚡ 重要 {len(important)}</span>
      <span class="stat-badge">生成于 {gen_time}</span>
      {_usage_bar_html(usage_info or {}, model_metrics)}
    </div>
  </div>
</div>

<div class="filter-bar">
  <button class="filter-btn active" data-filter="all"    onclick="filterCards('all')">全部</button>
  <button class="filter-btn"        data-filter="must-read" onclick="filterCards('must-read')">🔥 必读</button>
  <button class="filter-btn"        data-filter="important" onclick="filterCards('important')">⚡ 重要</button>
  <button class="filter-btn"        data-filter="normal"    onclick="filterCards('normal')">📌 一般</button>
</div>

{body_sections}

<script>{JS}</script>
</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_out)

    print(f"Digest saved → {output_path}")
