"""
投资情报源配置 — 专注 VC 融资、IPO、创业并购动态。
"""

# ── Nitter 实例（按优先级排列，自动 fallback）────────────────────────────────
NITTER_INSTANCES = [
    "https://nitter.net",
    "https://nitter.privacydev.net",
    "https://nitter.poast.org",
    "https://nitter.woodland.cafe",
    "https://nitter.1d4.us",
    "https://nitter.fdn.fr",
]

# ── 顶级投资人 Twitter 账号 ───────────────────────────────────────────────────
TWITTER_HANDLES = [
    {"name": "Michael Burry",    "handle": "michaeljburry"},   # Big Short 原型，宏观对冲
    {"name": "Brad Gerstner",    "handle": "altcap"},          # Altimeter Capital CEO
    {"name": "Chamath",          "handle": "chamath"},         # Social Capital, SPAC 王
    {"name": "ARK Invest",       "handle": "ARKInvest"},       # Cathie Wood 旗舰基金
]

TWITTER_MAX_PER_HANDLE = 5   # 每个账号最多抓取条数

# ── RSS 信源 ──────────────────────────────────────────────────────────────────
SOURCES = [
    # ── US Venture / Startup News ────────────────────────────────────────────
    {
        "name": "Crunchbase News",
        "url": "https://news.crunchbase.com/feed/",
        "lang": "en",
        "priority": 3,
    },
    {
        "name": "TechCrunch Startups",
        "url": "https://techcrunch.com/category/startups/feed/",
        "lang": "en",
        "priority": 3,
    },
    {
        "name": "TechCrunch Venture",
        "url": "https://techcrunch.com/category/venture/feed/",
        "lang": "en",
        "priority": 3,
    },
    {
        "name": "CNBC Deals",
        "url": "https://www.cnbc.com/id/15839135/device/rss/rss.html",
        "lang": "en",
        "priority": 2,
    },
    {
        "name": "Reuters Business",
        "url": "https://feeds.reuters.com/reuters/businessNews",
        "lang": "en",
        "priority": 2,
    },
    {
        "name": "Strictly VC",
        "url": "https://strictlyvc.substack.com/feed",
        "lang": "en",
        "priority": 2,
    },
    # ── VC Firm Blogs ─────────────────────────────────────────────────────────
    {
        "name": "a16z",
        "url": "https://a16z.com/feed/",
        "lang": "en",
        "priority": 3,
    },
    {
        "name": "Sequoia",
        "url": "https://www.sequoiacap.com/ideas/feed/",
        "lang": "en",
        "priority": 3,
    },
    {
        "name": "First Round Review",
        "url": "https://review.firstround.com/feed",
        "lang": "en",
        "priority": 2,
    },
    {
        "name": "Y Combinator Blog",
        "url": "https://www.ycombinator.com/blog/rss/",
        "lang": "en",
        "priority": 2,
    },
    # ── China Investment ──────────────────────────────────────────────────────
    {
        "name": "36氪",
        "url": "https://36kr.com/feed",
        "lang": "zh",
        "priority": 3,
    },
    {
        "name": "投资界",
        "url": "http://rss.pedaily.cn/pedaily.xml",
        "lang": "zh",
        "priority": 3,
    },
    {
        "name": "创业邦",
        "url": "https://www.cyzone.cn/rss.html",
        "lang": "zh",
        "priority": 2,
    },
    {
        "name": "虎嗅",
        "url": "https://www.huxiu.com/rss/0.xml",
        "lang": "zh",
        "priority": 2,
    },
    # ── Legendary Investor Memos / Newsletters ────────────────────────────────
    {
        "name": "Howard Marks (Oaktree)",
        "url": "https://www.oaktreecapital.com/insights/memos/rss",
        "lang": "en",
        "priority": 3,
    },
    {
        "name": "Fundsmith (Terry Smith)",
        "url": "https://www.fundsmith.co.uk/rss",
        "lang": "en",
        "priority": 3,
    },
    {
        "name": "Altimeter Capital",
        "url": "https://altimeter.com/feed",
        "lang": "en",
        "priority": 3,
    },
    # ── Investment Podcasts ───────────────────────────────────────────────────
    {
        "name": "Invest Like the Best",
        "url": "https://feeds.megaphone.fm/investlikethebest",
        "lang": "en",
        "priority": 3,
    },
    {
        "name": "All-In Podcast",
        "url": "https://feeds.megaphone.fm/all-in-with-chamath-jason-sacks-friedberg",
        "lang": "en",
        "priority": 3,
    },
    {
        "name": "We Study Billionaires",
        "url": "https://feeds.megaphone.fm/WSB",
        "lang": "en",
        "priority": 2,
    },
    {
        "name": "Capital Allocators",
        "url": "https://feeds.megaphone.fm/capital-allocators",
        "lang": "en",
        "priority": 2,
    },
]

# Hacker News：抓取评分最高的 top stories（投资相关关键词过滤）
HN_TOP_COUNT = 15

# ── 时间窗口 ──────────────────────────────────────────────────────────────────
TIME_WINDOW_HOURS = 24

# ── 上限与评分参数 ────────────────────────────────────────────────────────────
MAX_ARTICLES = 25
ENRICH_MIN_SCORE = 8
ENRICH_MAX_COUNT = 10

SCORE_MUST_READ = 8
SCORE_IMPORTANT = 6

DEDUP_THRESHOLD = 0.45

# ── Qwen 评分视角（投资人视角，聚焦融资/并购/IPO）────────────────────────────
SCORING_SYSTEM_PROMPT = """你是一位专注早期投资的风险投资人，关注全球 VC 融资动态、创业公司并购、IPO 信号和投资机会。
你的任务是评估每条内容对「VC、天使投资人、创业者寻找融资机会」的价值。

评分标准（1-10分）：
- 9-10分：极其重要。新的融资轮次（Series A/B/C/D及以上）、知名公司 IPO/SPAC、重大并购、顶级 VC 的公开投资论断、赛道格局重塑事件、监管变化影响投资逻辑。
- 7-8分：值得深度关注。种子轮/天使轮融资（有名 VC 参与）、VC 机构观点/年度报告、新兴赛道分析、创始人成功退出故事、重要市场数据发布。
- 5-6分：一般参考。行业常规动态、公司新产品发布（无融资信号）、一般性趋势观察。
- 1-4分：噪音。无实质内容的公关稿、与投资无关的技术细节、重复旧闻。

对于英文文章，提供：
- title_zh：准确的中文标题翻译（如涉及融资，格式为「[公司名]完成[金额][轮次]融资」）
- summary_zh：2-3句中文摘要，优先提取融资金额、估值、投资方

对于中文文章：title_zh 和 summary_zh 直接复制原文。
"""

# ── Enrichment Prompt ─────────────────────────────────────────────────────────
ENRICH_SYSTEM_PROMPT = """你是一位专注早期投资的风险投资人。
给定一篇投资/融资相关文章的正文（或搜索摘要），请提取以下4个字段：

1. reason_zh：一句话点评，说明这对 VC/创业者的战略意义（30字以内，要有洞见）
2. background_zh：1-2句背景介绍，帮助读者理解该公司或赛道背景
3. key_players_zh：涉及的关键投资方/被投公司/创始人，逗号分隔（如无则留空）
4. data_point_zh：最有价值的一个数字（融资金额/估值/增速/市场规模，如无则留空）

严格以 JSON 格式返回，不要任何其他文字：
{"reason_zh": "...", "background_zh": "...", "key_players_zh": "...", "data_point_zh": "..."}
"""
