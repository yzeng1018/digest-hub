"""持仓日报配置。

阈值按「只推异动与重点」的原则设定：安静的日子里邮件应该很短。
"""

import os

# 涨跌幅绝对值超过该值即视为异动
MOVE_PCT = 2.0

# 相对成本价的涨跌幅超过该值也提示（持仓回本或大幅浮盈浮亏时有用）
PNL_PCT_ALERT = 15.0

# SEC 报送回溯天数
FILING_DAYS = 14

# 只有这几类才算真正的财报文件；6-K / 8-K 多为杂项公告，不单独触发重点
EARNINGS_FORMS = {"10-K", "10-Q", "20-F"}

# 财报报道回溯天数。财报是季度事件，窗口得按天算；但拉太长会变成「过去三周
# 有人提过一次业绩」也算数，实测 21 天会让 24 只里 19 只都亮起来，失去意义
EARNINGS_NEWS_DAYS = 10

# 搜到之后还要够新才算数。一份财报的相关报道能持续一周以上，不设这道闸的话
# 同一份中报会连着推好几天，这正是「硬推送」；三天足够覆盖到，漏跑一天也不丢
EARNINGS_FRESH_DAYS = 3

# 新闻回溯小时数
NEWS_HOURS = 48

# 判定「这条新闻真的在说财报」的两道关：先要有事件词，再要有数字或比较。
# 只有事件词的多半是券商研报、行业综述、估值闲谈
EARNINGS_EVENT_WORDS = [
    "财报", "业绩", "季报", "年报", "半年报", "中报", "一季报", "三季报", "业绩会",
    "一季度", "二季度", "三季度", "四季度", "上半年", "下半年", "中期业绩",
    "earnings", "quarterly", "quarter", "q1", "q2", "q3", "q4",
    "annual results", "interim results", "results",
]
# 不用裸 % 和 rose/fell 这类涨跌词：一条「Q2 交付量涨 25%」会因此被当成财报
EARNINGS_FACT_WORDS = [
    "同比", "环比", "增长", "下降", "超预期", "低于预期", "预增", "预减",
    "预亏", "扭亏", "营收", "净利", "净利润", "亏损", "毛利", "指引",
    "beat", "miss", "estimate", "guidance", "revenue", "profit",
    "net income", "margin", "eps", "vs.",
]

# LLM 研判：无 key 或超时就静默跳过，不挡邮件
LLM_PROVIDER = os.environ.get("PORTFOLIO_LLM_PROVIDER", "deepseek")
LLM_MAX_ITEMS = 10

# 折算人民币用；实际汇率波动不大，固定值足够
FX = {"USD": 7.20, "HKD": 0.92, "CNY": 1.0, "": 1.0}

MARKET_ORDER = ["US", "HK", "A"]
MARKET_LABEL = {"US": "美股", "HK": "港股", "A": "A股"}
MARKET_NOTE = {
    "US": "昨夜收盘",
    "HK": "上一交易日收盘",
    "A": "上一交易日收盘",
}
