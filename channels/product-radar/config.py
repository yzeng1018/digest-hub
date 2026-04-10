"""
Product Radar — 产品设计雷达
信息源配置：专注于产品设计创新、UX 趋势、竞品动态
"""

SOURCES = [
    # ── 产品设计 / UX ──────────────────────────────────────────────────────────
    {
        "name": "UX Collective",
        "url": "https://uxdesign.cc/feed",
        "lang": "en",
        "category": "ux",
        "priority": 3,
    },
    {
        "name": "Nielsen Norman Group",
        "url": "https://www.nngroup.com/feed/rss/",
        "lang": "en",
        "category": "ux",
        "priority": 3,
    },
    {
        "name": "Smashing Magazine",
        "url": "https://www.smashingmagazine.com/feed/",
        "lang": "en",
        "category": "ux",
        "priority": 2,
    },
    {
        "name": "A List Apart",
        "url": "https://alistapart.com/main/feed/",
        "lang": "en",
        "category": "ux",
        "priority": 2,
    },
    # ── 顶级产品公司 Blog ──────────────────────────────────────────────────────
    {
        "name": "Figma Blog",
        "url": "https://www.figma.com/blog/feed/",
        "lang": "en",
        "category": "product",
        "priority": 3,
    },
    {
        "name": "Intercom Product",
        "url": "https://www.intercom.com/blog/feed/",
        "lang": "en",
        "category": "product",
        "priority": 3,
    },
    {
        "name": "Stripe Blog",
        "url": "https://stripe.com/blog/feed.rss",
        "lang": "en",
        "category": "product",
        "priority": 2,
    },
    {
        "name": "Notion Blog",
        "url": "https://www.notion.so/blog/rss.xml",
        "lang": "en",
        "category": "product",
        "priority": 2,
    },
    # ── Product Hunt ───────────────────────────────────────────────────────────
    {
        "name": "Product Hunt",
        "url": "https://www.producthunt.com/feed",
        "lang": "en",
        "category": "product",
        "priority": 2,
    },
    # ── 加密 / 金融产品 Blog ───────────────────────────────────────────────────
    {
        "name": "Coinbase Blog",
        "url": "https://blog.coinbase.com/feed",
        "lang": "en",
        "category": "crypto",
        "priority": 3,
    },
    {
        "name": "Binance Blog",
        "url": "https://www.binance.com/en/blog/rss",
        "lang": "en",
        "category": "crypto",
        "priority": 3,
    },
    {
        "name": "OKX Blog",
        "url": "https://www.okx.com/learn/rss",
        "lang": "en",
        "category": "crypto",
        "priority": 3,
    },
    # ── Reddit 产品社区 ────────────────────────────────────────────────────────
    {
        "name": "r/UXDesign",
        "url": "https://www.reddit.com/r/UXDesign/.rss",
        "lang": "en",
        "category": "ux",
        "priority": 2,
    },
    {
        "name": "r/ProductManagement",
        "url": "https://www.reddit.com/r/ProductManagement/.rss",
        "lang": "en",
        "category": "product",
        "priority": 2,
    },
    # ── 中文产品媒体 ───────────────────────────────────────────────────────────
    {
        "name": "少数派",
        "url": "https://sspai.com/feed",
        "lang": "zh",
        "category": "product",
        "priority": 3,
    },
    {
        "name": "36氪产品",
        "url": "https://36kr.com/feed",
        "lang": "zh",
        "category": "product",
        "priority": 2,
    },
]

# 抓取过去多少小时内的文章
TIME_WINDOW_HOURS = 36

# 最终邮件最多展示条数
MAX_ARTICLES = 20

# 第二次精细化分析阈值（分数 >= 此值才 enrich）
ENRICH_MIN_SCORE = 7
ENRICH_MAX_COUNT = 8

# 评分阈值
SCORE_MUST_READ = 8
SCORE_IMPORTANT = 6

# 去重相似度阈值
DEDUP_THRESHOLD = 0.45

# ── Qwen 评分视角（产品 PM 专属） ────────────────────────────────────────────
SCORING_SYSTEM_PROMPT = """你是一位在头部加密交易所（币安级别）负责产品的资深 PM，同时有快手/滴滴等超级 App 的产品经验。
你的任务是评估一篇文章对「提升产品设计能力、洞察竞品动态、发现可借鉴的设计模式」的价值。

评分标准（1-10分）：
- 9-10分：极其重要。产品设计范式转变、竞品重大产品更新（OKX/Coinbase/Bybit/Robinhood等）、新的 UX 交互模式首次出现、可能影响整个行业设计方向的事件。
- 7-8分：值得深度关注。重要产品功能上线（含竞品）、有实验数据支撑的设计原则、渐进式 UI / 个性化 / AI 驱动的界面变化。
- 5-6分：一般参考。产品设计方法论讨论、工具更新、行业惯例分析。
- 1-4分：噪音。营销内容、无实质设计洞见的公司新闻、重复报道。

对于英文文章，提供：
- title_zh：准确自然的中文标题翻译
- summary_zh：详细的中文摘要（4-6句话）。结构：① 这篇文章讲了什么 ② 核心观点或数据 ③ 为什么对产品人有价值。不要省略关键数字和结论。

对于中文文章：title_zh 直接复制，summary_zh 提炼核心要点（4-6句，不要只复制原文摘要）。

特别关注关键词：personalization / progressive UI / onboarding redesign /
adaptive interface / social trading / CEX+DEX / tokenized assets /
渐进式UI / 千人千面 / 智能推荐 / 新手引导 / 界面重设计
"""
