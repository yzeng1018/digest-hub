"""
生成独立的 HTML digest 文件。
"""

import html as html_lib
from datetime import datetime

from config import SCORE_MUST_READ, SCORE_IMPORTANT

CSS = """
:root {
  --bg: #0d1117;
  --surface: #161b22;
  --surface2: #1e2432;
  --border: #272e3d;
  --text: #e6edf3;
  --text-muted: #7d8590;
  --accent: #58a6ff;
  --must-read: #f85149;
  --important: #e3b341;
  --normal: #3fb950;
  --tag-bg: #1e2432;
  --zh-tag: #1b3a2d;
  --en-tag: #1b2a3d;
  --x-tag: #1a1a2e;
  --jike-tag: #2a1f35;
  --blog-tag: #1a2e2e;
  --podcast-tag: #2a1a1a;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  background: var(--bg);
  color: var(--text);
  font-family: -apple-system, "PingFang SC", "Microsoft YaHei", "Segoe UI", sans-serif;
  line-height: 1.6;
  padding: 0 0 80px;
}
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }

.header {
  background: linear-gradient(135deg, #161b22 0%, #0d1117 100%);
  border-bottom: 1px solid var(--border);
  padding: 32px 40px 24px;
  position: sticky;
  top: 0;
  z-index: 100;
  backdrop-filter: blur(12px);
}
.header-inner { max-width: 900px; margin: 0 auto; }
.header h1 { font-size: 22px; font-weight: 700; letter-spacing: 0.5px; }
.header h1 .accent { color: var(--accent); }
.header-meta {
  display: flex;
  gap: 12px;
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

.card-list { max-width: 900px; margin: 0 auto; padding: 0 40px; }
.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  margin-bottom: 12px;
  padding: 18px 22px;
  transition: border-color 0.15s, transform 0.1s;
}
.card:hover { border-color: var(--accent); transform: translateY(-1px); }
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
.must-read .score-badge { background: rgba(248,81,73,0.15); color: var(--must-read); }
.important .score-badge { background: rgba(227,179,65,0.15); color: var(--important); }
.normal .score-badge    { background: rgba(63,185,80,0.15);  color: var(--normal); }

.card-title-block { flex: 1; }
.card-title-zh { font-size: 16px; font-weight: 600; line-height: 1.4; margin-bottom: 3px; }
.card-title-en { font-size: 12px; color: var(--text-muted); line-height: 1.4; }

.card-tags { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 10px; }
.tag {
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  padding: 2px 7px;
}
.tag-source  { background: var(--tag-bg); color: var(--text-muted); border: 1px solid var(--border); }
.tag-zh      { background: var(--zh-tag); color: #56d364; }
.tag-en      { background: var(--en-tag); color: #79c0ff; }
.tag-x       { background: var(--x-tag);       color: #e0e0e0; }
.tag-jike    { background: var(--jike-tag);   color: #c084fc; }
.tag-blog    { background: var(--blog-tag);   color: #34d399; }
.tag-podcast { background: var(--podcast-tag); color: #fb923c; }

.card-summary { font-size: 14px; color: var(--text-muted); margin-bottom: 10px; line-height: 1.65; }

.card-background {
  font-size: 12px; color: #79c0ff;
  background: rgba(121,192,255,0.07);
  border-radius: 6px; padding: 6px 10px;
  margin-bottom: 8px; line-height: 1.6;
}
.card-reason {
  display: flex; align-items: center; gap: 6px;
  font-size: 12px; color: #56d364;
  background: rgba(86,211,100,0.07);
  border-radius: 6px; padding: 6px 10px;
  margin-bottom: 10px;
}
.card-reason::before { content: "💡"; font-size: 13px; }

.card-footer {
  display: flex; align-items: center; gap: 12px;
  font-size: 12px; color: var(--text-muted);
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
  background: var(--accent); border-color: var(--accent); color: #fff;
}

.hidden { display: none !important; }
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
    const vis = s.querySelectorAll('.card:not(.hidden)').length;
    const title = s.querySelector('.section-title');
    const list  = s.querySelector('.card-list');
    if (title) title.style.display = vis ? '' : 'none';
    if (list)  list.style.display  = vis ? '' : 'none';
  });
}
"""

PLATFORM_TAG = {
    "X":       ("tag-x",       "𝕏 Twitter"),
    "即刻":    ("tag-jike",    "即刻"),
    "Blog":    ("tag-blog",    "Blog"),
    "Podcast": ("tag-podcast", "🎙 Podcast"),
}


def _card_class(score: int) -> str:
    if score >= SCORE_MUST_READ:
        return "must-read"
    if score >= SCORE_IMPORTANT:
        return "important"
    return "normal"


def _e(text: str) -> str:
    return html_lib.escape(str(text or ""))


def _format_time(iso: str) -> str:
    if not iso:
        return ""
    try:
        return datetime.fromisoformat(iso).strftime("%m-%d %H:%M UTC")
    except Exception:
        return ""


def _render_card(art: dict) -> str:
    cls       = _card_class(art["score"])
    score     = art["score"]
    title_zh  = _e(art.get("title_zh") or art["title"])
    title_en  = _e(art["title"]) if art["lang"] == "en" else ""
    summary   = _e(art.get("summary_zh") or art.get("summary", ""))
    reason    = _e(art.get("reason_zh", ""))
    background = _e(art.get("background_zh", ""))
    source    = _e(art["source"])
    url       = _e(art.get("url", "#"))
    pub       = _format_time(art.get("published", ""))

    platform = art.get("platform", "Blog")
    ptag_cls, ptag_label = PLATFORM_TAG.get(platform, ("tag-blog", platform))
    lang_cls = "tag-zh" if art["lang"] == "zh" else "tag-en"
    lang_label = "中文" if art["lang"] == "zh" else "EN"

    title_en_html   = f'<div class="card-title-en">{title_en}</div>' if title_en else ""
    reason_html     = f'<div class="card-reason">{reason}</div>'     if reason    else ""
    background_html = f'<div class="card-background">📖 {background}</div>' if background else ""
    pub_html        = f'<span>{pub}</span>'                           if pub       else ""

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
    <span class="tag {ptag_cls}">{ptag_label}</span>
    <span class="tag {lang_cls}">{lang_label}</span>
  </div>
  <div class="card-summary">{summary}</div>
  {background_html}
  {reason_html}
  <div class="card-footer">
    {pub_html}
    <a class="read-link" href="{url}" target="_blank" rel="noopener">查看原文 →</a>
  </div>
</div>"""


def render(articles: list[dict], output_path: str) -> None:
    date_str   = datetime.now().strftime("%Y年%m月%d日")
    short_date = datetime.now().strftime("%Y-%m-%d")

    must_reads = [a for a in articles if a["score"] >= SCORE_MUST_READ]
    important  = [a for a in articles if SCORE_IMPORTANT <= a["score"] < SCORE_MUST_READ]
    normal     = [a for a in articles if a["score"] < SCORE_IMPORTANT]

    def section(title: str, items: list[dict]) -> str:
        if not items:
            return ""
        cards = "\n".join(_render_card(a) for a in items)
        return f"""
<div class="section">
  <div class="section-title">{_e(title)}</div>
  <div class="card-list">{cards}</div>
</div>"""

    body = (
        section(f"🔥 必读  ·  {len(must_reads)} 条", must_reads)
        + section(f"⚡ 重要  ·  {len(important)} 条", important)
        + section(f"📌 一般  ·  {len(normal)} 条",    normal)
    )

    total    = len(articles)
    gen_time = datetime.now().strftime("%H:%M")

    html_out = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>每日 AI 情报 · {short_date}</title>
  <style>{CSS}</style>
</head>
<body>

<div class="header">
  <div class="header-inner">
    <h1>每日 <span class="accent">AI</span> 情报</h1>
    <div class="header-meta">
      <span>{date_str}</span>
      <span class="stat-badge">共 {total} 条</span>
      <span class="stat-badge">🔥 必读 {len(must_reads)}</span>
      <span class="stat-badge">⚡ 重要 {len(important)}</span>
      <span class="stat-badge">生成于 {gen_time}</span>
    </div>
  </div>
</div>

<div class="filter-bar">
  <button class="filter-btn active" data-filter="all"      onclick="filterCards('all')">全部</button>
  <button class="filter-btn"        data-filter="must-read" onclick="filterCards('must-read')">🔥 必读</button>
  <button class="filter-btn"        data-filter="important" onclick="filterCards('important')">⚡ 重要</button>
  <button class="filter-btn"        data-filter="normal"    onclick="filterCards('normal')">📌 一般</button>
</div>

{body}

<script>{JS}</script>
</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_out)
    print(f"HTML 已保存 → {output_path}")
