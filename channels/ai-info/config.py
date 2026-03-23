"""
AI情报源配置 — 只关注AI相关的KOL和思想领袖。
在这里添加/删除信源，无需改动其他文件。
"""

# ── Nitter 实例（按优先级排列，自动 fallback）────────────────────────────────
# nitter 是 Twitter 的开源前端，无需API密钥
# 实例可能随时失效，多备几个
NITTER_INSTANCES = [
    "https://nitter.net",               # 最稳定，优先
    "https://nitter.privacydev.net",
    "https://nitter.poast.org",
    "https://nitter.woodland.cafe",
    "https://nitter.1d4.us",
    "https://nitter.fdn.fr",
]

# ── X/Twitter KOLs（个人账号优先，兼顾头部机构官号）────────────────────────
TWITTER_HANDLES = [
    # ── 顶级研究员 / 创始人 ──────────────────────────────────────────────────
    {"name": "Andrej Karpathy",    "handle": "karpathy"},
    {"name": "Sam Altman",         "handle": "sama"},
    {"name": "Yann LeCun",         "handle": "ylecun"},
    {"name": "Dario Amodei",       "handle": "DarioAmodei"},
    {"name": "Greg Brockman",      "handle": "gdb"},
    {"name": "Ilya Sutskever",     "handle": "ilyasut"},
    {"name": "François Chollet",   "handle": "fchollet"},
    {"name": "Jim Fan (NVIDIA)",   "handle": "drjimfan"},
    {"name": "Demis Hassabis",     "handle": "demishassabis"},
    # ── 实践者 / 工程师 / 教育者 ────────────────────────────────────────────
    {"name": "Ethan Mollick",      "handle": "emollick"},
    {"name": "Simon Willison",     "handle": "simonw"},
    {"name": "swyx",               "handle": "swyx"},
    {"name": "Riley Goodside",     "handle": "goodside"},
    {"name": "Harrison Chase",     "handle": "hwchase17"},
    {"name": "Rohan Paul",         "handle": "rohanpaul_ai"},
    {"name": "Jack Clark",         "handle": "jackclarkSF"},
    {"name": "Alexandr Wang",      "handle": "alexandr_wang"},
    {"name": "Amanda Askell",      "handle": "AmandaAskell"},      # Anthropic 对齐研究
    {"name": "Peter Steinberger",  "handle": "steipete"},          # 独立开发者，AI 工具
    {"name": "Dan Shipper",        "handle": "danshipper"},        # Every.to 创始人
    {"name": "Matt Turck",         "handle": "mattturck"},         # AI 方向 VC
    # ── 创始人 / 产品负责人 ──────────────────────────────────────────────────
    {"name": "Kevin Weil",         "handle": "kevinweil"},         # OpenAI CPO
    {"name": "Alex Albert",        "handle": "alexalbert__"},      # Anthropic Claude 产品
    {"name": "Amjad Masad",        "handle": "amasad"},            # Replit CEO
    {"name": "Guillermo Rauch",    "handle": "rauchg"},            # Vercel CEO
    {"name": "Garry Tan",          "handle": "garrytan"},          # YC 总裁
    {"name": "Aaron Levie",        "handle": "levie"},             # Box CEO
    {"name": "Josh Woodward",      "handle": "joshwoodward"},      # Google Labs VP
    {"name": "Peter Yang",         "handle": "petergyang"},        # 产品写作
    {"name": "Zara Zhang",         "handle": "zarazhangrui"},      # AI builder
    {"name": "Cat Wu",             "handle": "_catwu"},
    {"name": "Thariq",             "handle": "trq212"},
    {"name": "Ryan Lu",            "handle": "ryolu_"},
    {"name": "Nikunj Kothari",     "handle": "nikunj"},
    {"name": "Aditya Agarwal",     "handle": "adityaag"},
    {"name": "Madhu Guru",         "handle": "realmadhuguru"},
    {"name": "The Nanu",           "handle": "thenanyu"},
    # ── 机构官号（头部一手动态）──────────────────────────────────────────────
    {"name": "OpenAI",             "handle": "OpenAI"},
    {"name": "Anthropic",          "handle": "AnthropicAI"},
    {"name": "Google DeepMind",    "handle": "GoogleDeepMind"},
    {"name": "Google Labs",        "handle": "GoogleLabs"},
    {"name": "Claude AI",          "handle": "claudeai"},
    {"name": "Hugging Face",       "handle": "huggingface"},
    {"name": "Perplexity AI",      "handle": "perplexity_ai"},
    # ── 中文 KOL（X 上活跃）────────────────────────────────────────────────
    {"name": "向阳乔木",           "handle": "vista8"},
    {"name": "歸藏",               "handle": "op7418"},
    {"name": "宝玉xp",             "handle": "dotey"},
    {"name": "阑夕",               "handle": "foxshuo"},
    {"name": "小互",               "handle": "imxiaohu"},
    {"name": "李继刚",             "handle": "lijigang_com"},
]

# ── 即刻 KOLs via RSSHub ─────────────────────────────────────────────────────
# UUID 获取方式：打开 web.okjike.com/u/{uuid} 即可在地址栏看到
# RSSHub 路由：/jike/user/{uuid}
JIKE_USERS = [
    {"name": "歸藏",    "id": "267038a3-eb0f-43f7-b551-d05bf342e4ba"},   # AI工具测评
    {"name": "宝玉xp",  "id": "e34889cf-adef-471f-bee7-2fdcb9683f0b"},   # AI技术翻译分享
    {"name": "阑夕",    "id": "FBAA4408-2343-45AD-9B4F-4ABD52FB84CA"},   # 科技评论
    {"name": "小互",    "id": "43123D1E-7E29-486A-8333-3880A422FEDD"},   # AI应用
    {"name": "李继刚",  "id": "752D3103-1107-43A0-BA49-20EC29D09E36"},   # Prompt工程
    # 向阳乔木主要在 X(@vista8)活跃，即刻未找到
]

# RSSHub 公共实例（按优先级 fallback）
RSSHUB_INSTANCES = [
    "https://rsshub.app",
    "https://rsshub.rssforever.com",
    "https://rss.shab.fun",
]

# ── Substack / 个人博客 RSS（稳定可靠）────────────────────────────────────────
BLOG_SOURCES = [
    {
        "name": "One Useful Thing · Ethan Mollick",
        "url": "https://www.oneusefulthing.org/feed",
        "lang": "en",
    },
    {
        "name": "Simon Willison's Weblog",
        "url": "https://simonwillison.net/atom/everything/",
        "lang": "en",
    },
    {
        "name": "Lilian Weng · OpenAI",
        "url": "https://lilianweng.github.io/index.xml",
        "lang": "en",
    },
    {
        "name": "Ahead of AI · Sebastian Raschka",
        "url": "https://magazine.sebastianraschka.com/feed",
        "lang": "en",
    },
    {
        "name": "Import AI · Jack Clark",
        "url": "https://importai.substack.com/feed",
        "lang": "en",
    },
    {
        "name": "The Batch · Andrew Ng",
        "url": "https://www.deeplearning.ai/the-batch/feed/",
        "lang": "en",
    },
    {
        "name": "Karpathy Blog",
        "url": "https://karpathy.github.io/feed.xml",
        "lang": "en",
    },
    {
        "name": "swyx.io",
        "url": "https://www.swyx.io/rss.xml",
        "lang": "en",
    },
    {
        "name": "Last Week in AI",
        "url": "https://lastweekin.ai/feed",
        "lang": "en",
    },
    {
        "name": "AI Snake Oil · Arvind Narayanan",
        "url": "https://www.aisnakeoil.com/feed",
        "lang": "en",
    },
    {
        "name": "Interconnects · Nathan Lambert",
        "url": "https://www.interconnects.ai/feed",
        "lang": "en",
    },
    {
        "name": "Chip Huyen · ML Systems",
        "url": "https://huyenchip.com/feed.xml",
        "lang": "en",
    },
    {
        "name": "Eugene Yan · Applied ML",
        "url": "https://eugeneyan.com/rss.xml",
        "lang": "en",
    },
    {
        "name": "Hugging Face Blog",
        "url": "https://huggingface.co/blog/feed.xml",
        "lang": "en",
    },
    {
        "name": "OpenAI Research Blog",
        "url": "https://openai.com/news/rss.xml",
        "lang": "en",
    },
    {
        "name": "Gradient Descent · Weights & Biases",
        "url": "https://wandb.ai/fully-connected/feed.xml",
        "lang": "en",
    },
    # ── 中文 AI 博客/Substack ──────────────────────────────────────────────────
    {
        "name": "少数派 · AI 频道",
        "url": "https://sspai.com/feed",
        "lang": "zh",
    },
    {
        "name": "ByteByteGo Newsletter",
        "url": "https://blog.bytebytego.com/feed",
        "lang": "en",
    },
]

# ── AI 播客（YouTube）────────────────────────────────────────────────────────
# type: "channel" 用 channel_id；"playlist" 用 playlist_id
PODCAST_SOURCES = [
    {
        "name": "Latent Space",
        "type": "channel",
        "id": "UCxBcwypKK-W3GHd_RZ9FZrQ",
    },
    {
        "name": "No Priors",
        "type": "channel",
        "id": "UCSI7h9hydQ40K5MJHnCrQvw",
    },
    {
        "name": "Unsupervised Learning",
        "type": "channel",
        "id": "UCUl-s_Vp-Kkk_XVyDylNwLA",
    },
    {
        "name": "Data Driven NYC",
        "type": "channel",
        "id": "UCQID78IY6EOojr5RUdD47MQ",
    },
    {
        "name": "Training Data",
        "type": "playlist",
        "id": "PLOhHNjZItNnMm5tdW61JpnyxeYH5NDDx8",
    },
]

# 播客抓取时间窗口（小时）— 周更节奏，用较长窗口
PODCAST_TIME_WINDOW_HOURS = 168   # 7天

# ── 参数 ─────────────────────────────────────────────────────────────────────
# 每个 Twitter 账号最多抓几条
TWITTER_MAX_PER_HANDLE = 5

# 社交媒体（X/即刻）只抓多少小时内的内容
TIME_WINDOW_HOURS = 24

# 博客/Substack 使用更长窗口（大V写长文是周更节奏）
BLOG_TIME_WINDOW_HOURS = 72

# 最终 digest 上限
MAX_ARTICLES = 30

# 二次 enrichment 分数门槛
ENRICH_MIN_SCORE = 8
ENRICH_MAX_COUNT = 8

# 分数分级
SCORE_MUST_READ = 9   # 9-10 → 必读
SCORE_IMPORTANT = 6   # 6-7  → 重要
                      # <6   → 一般

# 去重相似度阈值
DEDUP_THRESHOLD = 0.55

# ── Qwen 评分视角 ──────────────────────────────────────────────────────────────
SCORING_SYSTEM_PROMPT = """你是一位深度关注 AI 领域的创业者和产品人，同时也是活跃的 AI 工具用户。
你的任务是评估每条 AI 相关内容对「AI 从业者、创业者、AI 工具深度用户」的价值。

评分标准（1-10分）：
- 9-10分：极其重要。重大模型发布/突破、行业格局转折、重要研究成果、创始人级别的深度洞察、可能改变工作方式的新工具/新范式。
- 7-8分：值得关注。有价值的实用技巧、重要产品更新、有洞见的行业观察、值得传播的实验结果。
- 5-6分：一般参考。常规更新、轻度观点，有一定参考价值但不紧迫。
- 1-4分：噪音。日常闲聊、无实质观点的转发、参会打卡、纯营销推广。

对于英文内容，提供：
- title_zh：准确自然的中文标题翻译（Twitter 格式：「[职位+姓名]：[核心观点]」）
- summary_zh：2-3句中文摘要，有大胆预判或反常识观点的优先放在开头

对于中文内容：title_zh 和 summary_zh 直接复制原文。
"""
