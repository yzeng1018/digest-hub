"""新闻与财报抓取。

新闻走 Google News RSS（中文查公司名、英文查代码），覆盖 A 股/港股/美股。
美股财报用 SEC EDGAR：先用 company_tickers.json 把代码换成 CIK，
再查该公司的 submissions 拿最近 filings。港股与 A 股没有等价的免费接口，
财报动态同样交给新闻覆盖。
"""

import re
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

import requests

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


def fetch_news(name: str, ticker: str, market: str,
               hours: int = 48, limit: int = 5) -> list[dict]:
    """抓最近 hours 小时内与该持仓相关的新闻。"""
    query = name if market in ("A", "HK") else f"{ticker} {name}"
    try:
        resp = requests.get(_news_url(query, market),
                            headers={"User-Agent": SEC_UA}, timeout=20)
        root = ET.fromstring(resp.content)
    except Exception:
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    out = []
    for item in root.iter("item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub = (item.findtext("pubDate") or "").strip()
        try:
            when = datetime.strptime(pub, "%a, %d %b %Y %H:%M:%S %Z").replace(
                tzinfo=timezone.utc)
        except ValueError:
            continue
        if when < cutoff:
            continue
        source = ""
        src_el = item.find("source")
        if src_el is not None:
            source = (src_el.text or "").strip()
        # 标题里的 " - 来源" 后缀去掉
        title = re.sub(r"\s+-\s+[^-]+$", "", title) if source else title
        out.append({"title": title, "link": link, "source": source,
                    "published": when.strftime("%m-%d %H:%M")})
        if len(out) >= limit:
            break
    return out


def build_news(holdings: list[dict], hours: int = 48) -> dict[str, dict]:
    """{ticker: {'news': [...], 'filings': [...]}}"""
    result: dict[str, dict] = {}
    for h in holdings:
        t = h["ticker"]
        news = fetch_news(h["name"], t, h["market"], hours=hours)
        filings = fetch_filings(t) if h["market"] == "US" else []
        result[t] = {"news": news, "filings": filings}
        time.sleep(0.2)
    return result
