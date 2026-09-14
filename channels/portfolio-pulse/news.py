"""新闻与财报抓取。

财报走新闻媒体，不再只盯 SEC：Google News 按「公司名 + 财报/业绩」回溯三周，
中英文各按各的说法搜，SEC 报送只作为美股侧的官方佐证。三市都没有可靠的免费
财报 API（披露易与巨潮要爬复杂接口），所以媒体反而是最省事也最可读的一层。
"""

import re
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

import requests

import config

SEC_UA = "digest-hub portfolio-pulse (contact: yzeng1018@gmail.com)"
HEADERS = {"User-Agent": SEC_UA, "Accept-Encoding": "gzip, deflate"}

COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik:010d}.json"
GOOGLE_NEWS = "https://news.google.com/rss/search?q={q}&hl={hl}&gl={gl}&ceid={ceid}"

# 只关心这几类文件：年报、季报、重大事件、中概股常用报送表
REPORT_FORMS = {"10-K", "10-Q", "8-K", "20-F", "6-K"}

_ticker_cik_cache: dict[str, int] | None = None


def _load_ticker_map() -> dict[str, int]:
    global _ticker_cik_cache
    if _ticker_cik_cache is not None:
        return _ticker_cik_cache
    try:
        resp = requests.get(COMPANY_TICKERS_URL, headers=HEADERS, timeout=25)
        rows = resp.json()
        _ticker_cik_cache = {
            str(r["ticker"]).upper(): int(r["cik_str"]) for r in rows.values()
        }
    except Exception as exc:
        print(f"[WARN] SEC 代码表拉取失败: {exc}", flush=True)
        _ticker_cik_cache = {}
    return _ticker_cik_cache


def _sec_get(url: str, timeout: int = 25):
    resp = requests.get(url, headers=HEADERS, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def fetch_filings(ticker: str, days: int = 14) -> list[dict]:
    """返回近 days 天内的 SEC 报送记录。"""
    cik = _load_ticker_map().get(ticker.upper())
    if not cik:
        return []
    try:
        data = _sec_get(SUBMISSIONS_URL.format(cik=cik))
    except Exception as exc:
        print(f"[WARN] SEC {ticker} 查询失败: {exc}", flush=True)
        return []

    rec = data.get("filings", {}).get("recent", {})
    forms = rec.get("form", [])
    dates = rec.get("filingDate", [])
    accessions = rec.get("accessionNumber", [])
    docs = rec.get("primaryDocument", [])
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).date()

    out = []
    for form, date, acc, doc in zip(forms, dates, accessions, docs):
        if form not in REPORT_FORMS:
            continue
        try:
            filed = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            continue
        if filed < cutoff:
            continue
        acc_nodash = acc.replace("-", "")
        out.append({
            "form": form,
            "date": date,
            "url": f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc_nodash}/{doc}",
        })
        if len(out) >= 4:
            break
    return out


def _news_url(query: str, market: str) -> str:
    if market == "A":
        return GOOGLE_NEWS.format(q=requests.utils.quote(query),
                                  hl="zh-CN", gl="CN", ceid="CN:zh-Hans")
    if market == "HK":
        return GOOGLE_NEWS.format(q=requests.utils.quote(query),
                                  hl="zh-Hant", gl="HK", ceid="HK:zh-Hant")
    return GOOGLE_NEWS.format(q=requests.utils.quote(query),
                              hl="en-US", gl="US", ceid="US:en")


def _google_news(query: str, market: str, hours: int | None = None,
                 days: int | None = None, limit: int = 5) -> list[dict]:
    """拉 Google News RSS，按小时内或天数内过滤。"""
    suffix = f" when:{days}d" if days else ""
    url = _news_url(query + suffix, market)
    try:
        resp = requests.get(url, headers={"User-Agent": SEC_UA}, timeout=25)
        root = ET.fromstring(resp.content)
    except Exception as exc:
        print(f"[WARN] 新闻抓取失败 {query}: {exc}", flush=True)
        return []

    cutoff = None
    if hours:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    elif days:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    out = []
    for item in root.iter("item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub = (item.findtext("pubDate") or "").strip()
        when = None
        try:
            when = datetime.strptime(pub, "%a, %d %b %Y %H:%M:%S %Z").replace(
                tzinfo=timezone.utc)
        except ValueError:
            # 少数条目换过格式，放行但标不出时间
            pass
        if cutoff and when and when < cutoff:
            continue
        source = ""
        src_el = item.find("source")
        if src_el is not None:
            source = (src_el.text or "").strip()
        # 标题里的 " - 来源" 后缀去掉
        title = re.sub(r"\s+-\s+[^-]+$", "", title) if source else title
        out.append({"title": title, "link": link, "source": source,
                    "published": when.strftime("%m-%d %H:%M") if when else ""})
        if len(out) >= limit:
            break
    return out


def fetch_news(name: str, ticker: str, market: str,
               hours: int = 48, limit: int = 5) -> list[dict]:
    """抓最近 hours 小时内与该持仓相关的新闻。"""
    query = name if market in ("A", "HK") else f"{ticker} {name}"
    return _google_news(query, market, hours=hours, limit=limit)


def fetch_earnings_news(name: str, ticker: str, market: str,
                        days: int = 21, limit: int = 6) -> list[dict]:
    """专门搜财报/业绩报道。窗口按天算——财报是季度事件，48 小时抓不到。"""
    if market == "US":
        query = f"{ticker} {name} earnings results"
    else:
        query = f"{name} 财报 业绩"
    rows = _google_news(query, market, days=days, limit=limit)
    for r in rows:
        r["kind"] = "earnings"
    return rows


def _is_earnings(title: str) -> bool:
    low = (title or "").lower()
    return any(k.lower() in low for k in config.EARNINGS_KEYWORDS)


def build_news(holdings: list[dict], hours: int = 48) -> dict[str, dict]:
    """{ticker: {'news': [...], 'earnings': [...], 'filings': [...]}}

    earnings 是财报相关报道（专搜 + 普通新闻里命中关键词的），
    filings 只有美股有，带 isEarnings 标出哪些是真正的财报文件。
    """
    result: dict[str, dict] = {}
    for h in holdings:
        t = h["ticker"]
        news = fetch_news(h["name"], t, h["market"], hours=hours)
        earnings = fetch_earnings_news(
            h["name"], t, h["market"], days=config.EARNINGS_NEWS_DAYS)

        seen = {n["title"] for n in earnings}
        for n in news:
            if _is_earnings(n["title"]) and n["title"] not in seen:
                row = dict(n, kind="earnings")
                earnings.append(row)
                seen.add(n["title"])

        filings = []
        if h["market"] == "US":
            for f in fetch_filings(t, days=config.FILING_DAYS):
                f["isEarnings"] = f["form"] in config.EARNINGS_FORMS
                filings.append(f)

        result[t] = {"news": news, "earnings": earnings, "filings": filings}
        time.sleep(0.2)
    return result
