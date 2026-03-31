"""
News sources configuration.
Add/remove sources here without touching any other file.
"""

SOURCES = [
    # ── US Tech ─────────────────────────────────────────────────────────────
    {
        "name": "TechCrunch",
        "url": "https://techcrunch.com/feed/",
        "lang": "en",
        "category": "tech",
        "priority": 2,
    },
    {
        "name": "The Verge",
        "url": "https://www.theverge.com/rss/index.xml",
        "lang": "en",
        "category": "tech",
        "priority": 2,
    },
    {
        "name": "Wired",
        "url": "https://www.wired.com/feed/rss",
        "lang": "en",
        "category": "tech",
        "priority": 2,
    },
    {
        "name": "MIT Technology Review",
        "url": "https://www.technologyreview.com/feed/",
        "lang": "en",
        "category": "tech",
        "priority": 3,
    },
    {
        "name": "VentureBeat",
        "url": "https://venturebeat.com/feed/",
        "lang": "en",
        "category": "tech",
        "priority": 2,
    },
    {
        "name": "Ars Technica",
        "url": "https://feeds.arstechnica.com/arstechnica/index",
        "lang": "en",
        "category": "tech",
        "priority": 1,
    },
    # ── US Finance / Business ────────────────────────────────────────────────
    {
        "name": "Reuters Technology",
        "url": "https://feeds.reuters.com/reuters/technologyNews",
        "lang": "en",
        "category": "finance",
        "priority": 3,
    },
    {
        "name": "CNBC Tech",
        "url": "https://www.cnbc.com/id/19854910/device/rss/rss.html",
        "lang": "en",
        "category": "finance",
        "priority": 2,
    },
    {
        "name": "Bloomberg Technology",
        "url": "https://feeds.bloomberg.com/technology/news.rss",
        "lang": "en",
        "category": "finance",
        "priority": 3,
    },
    # ── China Tech ───────────────────────────────────────────────────────────
    {
        "name": "36氪",
        "url": "https://36kr.com/feed",
        "lang": "zh",
        "category": "tech",
        "priority": 3,
    },
    {
        "name": "虎嗅",
        "url": "https://www.huxiu.com/rss/0.xml",
        "lang": "zh",
        "category": "tech",
        "priority": 2,
    },
    {
        "name": "钛媒体",
        "url": "https://www.tmtpost.com/feed",
        "lang": "zh",
        "category": "tech",
        "priority": 2,
    },
    # ── Reddit (工程师社区视角) ────────────────────────────────────────────────
    {
        "name": "Reddit r/MachineLearning",
        "url": "https://www.reddit.com/r/MachineLearning/.rss",
        "lang": "en",
        "category": "tech",
        "priority": 3,
    },
    {
        "name": "Reddit r/artificial",
        "url": "https://www.reddit.com/r/artificial/.rss",
        "lang": "en",
        "category": "tech",
        "priority": 2,
    },
    {
        "name": "Reddit r/investing",
        "url": "https://www.reddit.com/r/investing/.rss",
        "lang": "en",
        "category": "finance",
        "priority": 2,
    },
    # ── Hacker News is fetched via API, not RSS (see fetcher.py) ────────────
]

# How many top HN stories to fetch
HN_TOP_COUNT = 10

# Max HN articles allowed in the final digest (after scoring)
HN_MAX_IN_DIGEST = 5

# How many hours back to include articles (older ones are discarded)
TIME_WINDOW_HOURS = 24

# After dedup + scoring, cap the final digest at this many articles
MAX_ARTICLES = 30

# Second-pass enrichment: only enrich articles scoring >= this
ENRICH_MIN_SCORE = 8
# Max articles to enrich (DuckDuckGo rate limit friendly)
ENRICH_MAX_COUNT = 10

# Score thresholds
SCORE_MUST_READ = 8    # 8-10 → 必读
SCORE_IMPORTANT = 6    # 6-7  → 重要
                       # <6   → 一般

# Similarity threshold for deduplication (0–1). Higher = stricter.
DEDUP_THRESHOLD = 0.45

# ── Qwen 评分视角 ──────────────────────────────────────────────────────────────
SCORING_SYSTEM_PROMPT = """你是一位顶级的科技创业者和风险投资人，同时也是一位对全球科技财经动态有深刻洞察的战略分析师。
你的任务是评估新闻文章对一位关注科技、AI、创业、投资机会的中国创业者的价值。

评分标准（1-10分）：
- 9-10分：极其重要。重大战略转折点、颠覆性技术突破、重要融资/IPO信号、监管重大变化、可能影响赛道格局的事件。
- 7-8分：值得深度关注。重要产品发布、知名公司重要动态、有价值的市场洞察、新兴趋势信号。
- 5-6分：一般参考。行业常规动态，有一定参考价值但不紧迫。
- 1-4分：噪音。重复报道、营销软文、无实质内容。

对于英文文章，提供：
- title_zh：准确自然的中文标题翻译
- summary_zh：简洁的中文摘要（2-3句话，突出核心信息）

对于中文文章：title_zh 和 summary_zh 直接复制原文。
"""
