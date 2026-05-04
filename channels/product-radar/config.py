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
    # ── Substack 产品/增长 Newsletter ─────────────────────────────────────────
    {
        "name": "Lenny's Newsletter",
        "url": "https://www.lennysnewsletter.com/feed",
        "lang": "en",
        "category": "product",
        "priority": 3,
    },
    {
        "name": "Reforge Blog",
        "url": "https://www.reforge.com/blog/rss.xml",
        "lang": "en",
        "category": "product",
        "priority": 3,
    },
    {
        "name": "First Round Review",
        "url": "https://review.firstround.com/feed.xml",
        "lang": "en",
        "category": "product",
        "priority": 3,
    },
    {
        "name": "Mind the Product",
        "url": "https://www.mindtheproduct.com/feed/",
        "lang": "en",
        "category": "product",
        "priority": 2,
    },
    {
        "name": "Stratechery",
        "url": "https://stratechery.com/feed/",
        "lang": "en",
        "category": "product",
        "priority": 3,
    },
    {
        "name": "Andrew Chen Blog",
        "url": "https://andrewchen.com/feed/",
        "lang": "en",
        "category": "product",
        "priority": 3,
    },
    {
        "name": "Elezea",
        "url": "https://elezea.com/feed/",
        "lang": "en",
        "category": "ux",
        "priority": 2,
    },
    # ── Podcast 文字稿/Show Notes ──────────────────────────────────────────────
    {
        "name": "Lenny's Podcast",
        "url": "https://feeds.transistor.fm/lenny-s-podcast-product-growth-career",
        "lang": "en",
        "category": "product",
        "priority": 3,
    },
    {
        "name": "Masters of Scale",
        "url": "https://mastersofscale.com/feed/podcast/",
        "lang": "en",
        "category": "product",
        "priority": 2,
    },
    {
        "name": "This is Product Management",
        "url": "https://feeds.buzzsprout.com/489175.rss",
        "lang": "en",
        "category": "product",
        "priority": 2,
    },
    # ── YouTube 频道（RSS） ────────────────────────────────────────────────────
    {
        "name": "Y Combinator",
        "url": "https://www.youtube.com/feeds/videos.xml?channel_id=UCcefcZRL2oaA_uBNeo5UOWg",
        "lang": "en",
        "category": "product",
        "priority": 2,
    },
    {
        "name": "a16z",
        "url": "https://www.youtube.com/feeds/videos.xml?channel_id=UC9cn0TuPq4dnbTY-CBsm3XA",
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
    {
        "name": "晚点LatePost",
        "url": "https://latepost.com/rss.xml",
        "lang": "zh",
        "category": "product",
        "priority": 3,
    },
]

# 抓取过去多少小时内的文章
TIME_WINDOW_HOURS = 48

# 最终邮件最多展示条数
MAX_ARTICLES = 15

# 第二次精细化分析阈值（分数 >= 此值才 enrich）
ENRICH_MIN_SCORE = 7
ENRICH_MAX_COUNT = 4

# 评分阈值
SCORE_MUST_READ = 8
SCORE_IMPORTANT = 6

# 去重相似度阈值
DEDUP_THRESHOLD = 0.45

# ── Qwen 评分视角（产品 PM 专属） ────────────────────────────────────────────
SCORING_SYSTEM_PROMPT = """你是一位在头部加密交易所（币安级别）负责产品的资深 PM，同时有快手/滴滴等超级 App 的产品经验。
你的任务是评估文章对「提升产品设计能力、洞察竞品动态、发现可借鉴设计模式」的价值。

评分标准（1-10分，要敢于给高分）：
- 9-10分：极其重要。AI 重构产品交互范式、竞品重大产品更新（OKX/Coinbase/Bybit/Robinhood/Figma 等）、新 UX 模式首次出现、有大量实验数据支撑的设计原则、可能改变行业设计方向的洞察。
- 7-8分：值得关注。重要产品功能上线、有数据支撑的设计案例、渐进式 UI / 个性化 / AI 驱动界面变化、顶级产品人深度分享。
- 5-6分：一般参考。方法论讨论、工具更新、行业惯例分析。
- 1-4分：噪音。监管新闻与产品设计无关、营销软文、重复报道、纯金融数据。

注意：
- 来自 UX Collective、NNG、Figma、Lenny's Newsletter、Stratechery、First Round Review 的深度文章，默认起评 7 分，除非内容空洞。
- 来自 36氪/晚点 的中文文章，如果主题是监管政策、金融数据、公司融资而非产品设计，打 1-3 分。

对于英文文章：
- title_zh：准确的中文标题翻译
- summary_zh：4-6句中文摘要，结构：① 核心主题 ② 关键观点或数据 ③ 对产品设计的启示

对于中文文章：title_zh 直接复制，summary_zh 提炼设计相关核心要点（4-6句）。
"""
