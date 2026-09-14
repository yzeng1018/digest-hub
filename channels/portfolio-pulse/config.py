"""持仓日报配置。

阈值按「只推异动与重点」的原则设定：安静的日子里邮件应该很短。
"""

# 涨跌幅绝对值超过该值即视为异动
MOVE_PCT = 2.0

# 相对成本价的涨跌幅超过该值也提示（持仓回本或大幅浮盈浮亏时有用）
PNL_PCT_ALERT = 15.0

# SEC 报送回溯天数
FILING_DAYS = 14

# 新闻回溯小时数
NEWS_HOURS = 48

# 命中任一关键词的新闻视为「重点」，而非普通资讯
EARNINGS_KEYWORDS = [
    "财报", "业绩", "季报", "年报", "半年报", "营收", "净利", "亏损",
    "指引", "预告", "回购", "分红", "增持", "减持", "停牌", "退市",
    "earnings", "quarterly", "results", "guidance", "revenue",
    "profit", "loss", "buyback", "dividend", "downgrade", "upgrade",
]

# 折算人民币用；实际汇率波动不大，固定值足够
FX = {"USD": 7.20, "HKD": 0.92, "CNY": 1.0, "": 1.0}

MARKET_ORDER = ["US", "HK", "A"]
MARKET_LABEL = {"US": "美股", "HK": "港股", "A": "A股"}
MARKET_NOTE = {
    "US": "昨夜收盘",
    "HK": "上一交易日收盘",
    "A": "上一交易日收盘",
}
