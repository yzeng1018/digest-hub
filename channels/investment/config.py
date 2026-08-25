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
    {"name": "Bill Ackman",      "handle": "BillAckman"},      # Pershing Square，激进投资人
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
        "platform": "Blog",
        "priority": 3,
    },
    {
        "name": "Sequoia",
        "url": "https://www.sequoiacap.com/ideas/feed/",
        "lang": "en",
        "platform": "Blog",
        "priority": 3,
    },
    {
        "name": "First Round Review",
        "url": "https://review.firstround.com/feed",
        "lang": "en",
        "platform": "Blog",
        "priority": 3,
    },
    {
        "name": "Y Combinator Blog",
        "url": "https://www.ycombinator.com/blog/rss/",
        "lang": "en",
        "platform": "Blog",
        "priority": 2,
    },
    {
        "name": "USV (Union Square Ventures)",
        "url": "https://www.usv.com/writing/feed/",
        "lang": "en",
        "platform": "Blog",
        "priority": 3,
    },
    {
        "name": "Lux Capital",
        "url": "https://luxcapital.substack.com/feed",
        "lang": "en",
        "platform": "Blog",
        "priority": 2,
    },
    # ── Legendary Investor Personal Blogs / Memos ─────────────────────────────
    {
        "name": "Howard Marks (Oaktree)",
        "url": "https://www.oaktreecapital.com/insights/memos/rss",
        "lang": "en",
        "platform": "Memo",
        "priority": 3,
    },
    {
        "name": "Bill Gurley (Above the Crowd)",
        "url": "https://abovethecrowd.com/feed/",
        "lang": "en",
        "platform": "Memo",
        "priority": 3,
    },
    {
        "name": "Fred Wilson (AVC)",
        "url": "https://avc.com/feed/",
        "lang": "en",
        "platform": "Memo",
        "priority": 3,
    },
    {
        "name": "Morgan Housel (Collaborative Fund)",
        "url": "https://collabfund.com/feed",
        "lang": "en",
        "platform": "Memo",
        "priority": 3,
    },
    {
        "name": "Morgan Housel (Substack)",
        "url": "https://morganhousel.substack.com/feed",
        "lang": "en",
        "platform": "Memo",
        "priority": 3,
    },
    {
        "name": "Mark Suster (Upfront Ventures)",
        "url": "https://bothsidesofthetable.com/feed",
        "lang": "en",
        "platform": "Memo",
        "priority": 3,
    },
    {
        "name": "David Sacks",
        "url": "https://davidsacks.substack.com/feed",
        "lang": "en",
        "platform": "Memo",
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
    # ── Investment Podcasts ───────────────────────────────────────────────────
    {
        "name": "Invest Like the Best",
        "url": "https://feeds.megaphone.fm/investlikethebest",
        "lang": "en",
        "platform": "Podcast",
        "priority": 3,
    },
    {
        "name": "Acquired",
        "url": "https://feeds.simplecast.com/6khJWNb1",
        "lang": "en",
        "platform": "Podcast",
        "priority": 3,
    },
    {
        "name": "20VC (Harry Stebbings)",
        "url": "https://20vc.libsyn.com/rss",
        "lang": "en",
        "platform": "Podcast",
        "priority": 3,
    },
    {
        "name": "All-In Podcast",
        "url": "https://feeds.megaphone.fm/all-in-with-chamath-jason-sacks-friedberg",
        "lang": "en",
        "platform": "Podcast",
        "priority": 3,
    },
    {
        "name": "Founders Podcast",
        "url": "https://feeds.transistor.fm/founders-podcast",
        "lang": "en",
        "platform": "Podcast",
        "priority": 3,
    },
    {
        "name": "We Study Billionaires",
        "url": "https://feeds.megaphone.fm/WSB",
        "lang": "en",
        "platform": "Podcast",
        "priority": 2,
    },
    {
        "name": "Capital Allocators",
        "url": "https://feeds.megaphone.fm/capital-allocators",
        "lang": "en",
        "platform": "Podcast",
        "priority": 2,
    },
]

# Hacker News：抓取评分最高的 top stories（投资相关关键词过滤）
HN_TOP_COUNT = 15

# ── ARK ETF 每日持仓 CSV ──────────────────────────────────────────────────────
# ARK 每天更新当日持仓，通过 CSV 直接获取
ARK_FUND_CSVS = [
    {
        "name": "ARK Innovation (ARKK)",
        "ticker": "ARKK",
        "url": "https://ark-funds.com/wp-content/uploads/funds-etf-csv/ARK_INNOVATION_ETF_ARKK_HOLDINGS.csv",
    },
    {
        "name": "ARK Next Gen Internet (ARKW)",
        "ticker": "ARKW",
        "url": "https://ark-funds.com/wp-content/uploads/funds-etf-csv/ARK_NEXT_GENERATION_INTERNET_ETF_ARKW_HOLDINGS.csv",
    },
    {
        "name": "ARK Genomic Revolution (ARKG)",
        "ticker": "ARKG",
        "url": "https://ark-funds.com/wp-content/uploads/funds-etf-csv/ARK_GENOMIC_REVOLUTION_ETF_ARKG_HOLDINGS.csv",
    },
]

# ── SEC EDGAR 13F 申报监控 ─────────────────────────────────────────────────────
# 用 SEC Atom RSS 追踪顶级机构的季度持仓申报，使用更长的时间窗口
SEC_13F_SOURCES = [
    {"name": "Berkshire Hathaway (Buffett)",  "cik": "0001067983"},
    {"name": "Pershing Square (Ackman)",      "cik": "0001336528"},
    {"name": "Duquesne Capital (Druckenmiller)", "cik": "0001064290"},
    {"name": "Soros Fund Management",         "cik": "0001029160"},
    {"name": "Renaissance Technologies",      "cik": "0001037389"},
    {"name": "Altimeter Capital",             "cik": "0001418819"},
    {"name": "Appaloosa (Tepper)",            "cik": "0001141119"},
]
# 13F 为季度申报，使用7天窗口以捕获最新提交
SEC_13F_WINDOW_DAYS = 7

# ── 时间窗口 ──────────────────────────────────────────────────────────────────
TIME_WINDOW_HOURS = 24
# Blog/Memo/Podcast 更新频率低，使用更长的时间窗口
INSIGHT_WINDOW_DAYS = 14

# ── 上限与评分参数 ────────────────────────────────────────────────────────────
MAX_ARTICLES = 15
INSIGHT_MIN_RATIO = 0.20   # Blog/Memo/Podcast 最少占总数的 20%
INSIGHT_MIN_SCORE = 7      # 不为凑“深度内容”配额而塞入泛创业鸡汤
PORTFOLIO_MIN_COUNT = 6    # 有足够候选时，至少保留 6 条持仓直接相关新闻
PORTFOLIO_MIN_SCORE = 6    # 纯股价播报/产品软文不占持仓雷达配额
SOURCE_CAPS = {"36氪": 2}  # 每个来源的最大文章数（按分数保留最高的）
ENRICH_MIN_SCORE = 7
ENRICH_MAX_COUNT = 10

SCORE_MUST_READ = 8
SCORE_IMPORTANT = 6

DEDUP_THRESHOLD = 0.45

# 已发送内容滚动记忆：旧故事直接过滤，同一公司近期反复出现则降低排序权重。
HISTORY_RETENTION_DAYS = 30
HISTORY_SIMILARITY_THRESHOLD = 0.50
COMPANY_COOLDOWN_DAYS = 3

# 持仓的上游/同业信号。行业新闻不享受持仓配额，仍需通过全局评分竞争入选。
PORTFOLIO_SECTOR_QUERIES = [
    {"sector": "中国互联网平台", "query": "平台经济 OR 即时零售 OR 中国电商", "holdings": ["快手", "美团", "拼多多", "阿里巴巴", "滴滴出行"]},
    {"sector": "新能源汽车与电池", "query": "新能源汽车价格战 OR 动力电池", "holdings": ["小米集团", "蔚来汽车", "比亚迪", "宁德时代"]},
    {"sector": "中国半导体", "query": "晶圆代工 OR 中国半导体设备", "holdings": ["中芯国际"]},
    {"sector": "在线旅游", "query": "出境游 OR 在线旅游市场", "holdings": ["携程集团"]},
    {"sector": "AI应用与金融科技", "query": "AI教育 OR 设计软件 OR 金融科技", "holdings": ["多邻国", "Figma", "SoFi Technologies", "Block"]},
]

# ── Qwen 评分视角（投资人视角，聚焦融资/并购/IPO）────────────────────────────
SCORING_SYSTEM_PROMPT = """你是一位服务个人投资组合的全球公开市场研究员，覆盖中国A股、港股、中概股和美股。
你的任务是评估每条内容对「发现投资线索、验证持仓逻辑、识别组合风险」的价值，而不是按媒体热度评分。

组合相关规则：
- 标记为 Portfolio/持仓雷达的内容，若会改变收入、利润率、竞争格局、监管风险或估值锚，优先级应明显提高。
- 仅仅提到公司名、股价涨跌或重复旧闻，不应因是持仓而获得高分。
- 区分事实和推论；没有增量信息的评论、PR稿和标题党降分。

评分标准（1-10分）：
- 9-10分：可能显著改变持仓基本面或行业利润池。财报/指引重大变化、强监管、重大产品周期、价格战转折、资本配置或竞争格局重塑。
- 7-8分：可形成可验证投资假设。关键经营数据、产业链供需变化、可靠的深度分析、重要同业信号。
- 5-6分：值得知道但暂不改变判断。常规产品发布、一般融资并购、单一机构观点。
- 1-4分：噪音。无实质内容的公关稿、纯股价复述、重复旧闻、泛创业鸡汤。

对于英文文章，提供：
- title_zh：准确的中文标题翻译（如涉及融资，格式为「[公司名]完成[金额][轮次]融资」）
- summary_zh：2-3句中文摘要，优先提取融资金额、估值、投资方

对于中文文章：title_zh 和 summary_zh 直接复制原文。
"""

# ── Enrichment Prompt ─────────────────────────────────────────────────────────
ENRICH_SYSTEM_PROMPT = """你是一位专注早期投资的风险投资人。
给定一篇投资/融资相关文章的正文（或搜索摘要），请提取以下4个字段：

1. reason_zh：一句话说清新闻改变了什么（30字以内）
2. background_zh：1-2句背景介绍，帮助读者理解该公司或赛道背景
3. key_players_zh：涉及的关键投资方/被投公司/创始人，逗号分隔（如无则留空）
4. data_point_zh：最有价值的一个数字（收入/利润率/销量/估值/增速/市场规模，如无则留空）
5. portfolio_relevance_zh：若与给定持仓有关，说明影响哪只持仓及方向；无关则留空
6. investment_angle_zh：用“事实→传导链→潜在受益/受损者”写一条投资灵感，必须标明其中的推论（60字以内）
7. confirmation_signal_zh：未来应跟踪的一个可观测验证信号（30字以内）
8. risk_zh：这条投资推论最可能错在哪里（30字以内）

严格以 JSON 格式返回，不要任何其他文字：
{"reason_zh":"...","background_zh":"...","key_players_zh":"...","data_point_zh":"...","portfolio_relevance_zh":"...","investment_angle_zh":"...","confirmation_signal_zh":"...","risk_zh":"..."}
"""
