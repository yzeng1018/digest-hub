"""新浪 / 腾讯行情抓取。

新浪 hq.sinajs.cn 支持一次请求批量取多只股票，覆盖 A 股、港股、美股，
是本项目在 GitHub Actions（境外直连）上唯一验证过的稳定源。
腾讯 qt.gtimg.cn 作为备份；东财 push2 直连会超时，不用。
"""

import os
import re
import time

import requests

SINA_URL = "https://hq.sinajs.cn/list="
TENCENT_URL = "https://qt.gtimg.cn/q="

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    ),
    "Referer": "https://finance.sina.com.cn",
}

# 三个市场在新浪返回的字段顺序不同，逐个处理
MARKET_LABEL = {"US": "美股", "HK": "港股", "A": "A股"}


def sina_code(ticker: str, market: str) -> str:
    if market == "A":
        return ("sh" if ticker.startswith(("6", "9")) else "sz") + ticker
    if market == "HK":
        return "hk" + ticker.replace(".HK", "").zfill(5)
    return "gb_" + ticker.lower()


def _f(vals: list, idx: int):
    try:
        return float(vals[idx])
    except (IndexError, ValueError, TypeError):
        return None


def _parse_sina_line(line: str) -> dict | None:
    m = re.match(r'var hq_str_(\w+)="(.*)";', line.strip())
    if not m:
        return None
    code, raw = m.group(1), m.group(2)
    if not raw:
        return None
    v = raw.split(",")
    q = {"code": code}

    if code.startswith("hk"):
        # 英文名,中文名,今开,昨收,最高,最低,现价,涨跌额,涨跌幅,买,卖,成交额,成交量
        # 注意：港股这两个字段与 A 股顺序相反，[11] 是成交额、[12] 才是成交量
        q.update(name=v[1] or v[0], prev=_f(v, 3), price=_f(v, 6),
                 chg=_f(v, 7), chgPct=_f(v, 8), open=_f(v, 2),
                 high=_f(v, 4), low=_f(v, 5), volume=_f(v, 12),
                 amount=_f(v, 11), market="HK")
        if len(v) >= 19:
            q["quoteTime"] = f"{v[17]} {v[18]}"
    elif code.startswith("gb_"):
        # 名称,现价,涨跌幅%,时间,涨跌额,开盘,最高,最低,52周高,52周低,成交量
        price = _f(v, 1)
        chg = _f(v, 4)
        q.update(name=v[0], price=price, chgPct=_f(v, 2), chg=chg,
                 prev=(price - chg) if (price is not None and chg is not None) else None,
                 open=_f(v, 5), high=_f(v, 6), low=_f(v, 7),
                 week52High=_f(v, 8), week52Low=_f(v, 9),
                 volume=_f(v, 10), quoteTime=v[3] if len(v) > 3 else "",
                 market="US")
    else:
        # 名称,今开,昨收,现价,最高,最低,买一,卖一,成交量,成交额
        price, prev = _f(v, 3), _f(v, 2)
        q.update(name=v[0], open=_f(v, 1), prev=prev, price=price,
                 high=_f(v, 4), low=_f(v, 5), volume=_f(v, 8),
                 amount=_f(v, 9), market="A")
        if price is not None and prev:
            q["chg"] = round(price - prev, 4)
            q["chgPct"] = round((price - prev) / prev * 100, 3)
    return q


def _parse_tencent_line(line: str) -> dict | None:
    m = re.match(r'v_(\w+)="(.*)";', line.strip())
    if not m:
        return None
    code, raw = m.group(1), m.group(2)
    v = raw.split("~")
    if len(v) < 6:
        return None
    market = "US" if code.startswith("us") else ("HK" if code.startswith("hk") else "A")
    q = {"code": code, "name": v[1], "market": market}
    if market == "US":
        # 代码,名称,符号,现价,昨收,今开,成交量
        q.update(price=_f(v, 3), prev=_f(v, 4), open=_f(v, 5), volume=_f(v, 6))
    else:
        # 代码,名称,符号,现价,昨收,今开,成交量
        q.update(price=_f(v, 3), prev=_f(v, 4), open=_f(v, 5), volume=_f(v, 6))
    if q.get("price") is not None and q.get("prev"):
        q["chg"] = round(q["price"] - q["prev"], 4)
        q["chgPct"] = round((q["price"] - q["prev"]) / q["prev"] * 100, 3)
    return q


def _get(url: str, timeout: int = 20) -> str:
    resp = requests.get(url, headers=HEADERS, timeout=timeout)
    resp.encoding = "gbk" if "sinajs" in url else "gbk"
    return resp.text


def fetch_quotes(holdings: list[dict], timeout: int = 20) -> dict[str, dict]:
    """返回 {ticker: quote}，新浪失败时回退腾讯。"""
    code_map = {sina_code(h["ticker"], h["market"]): h for h in holdings}
    out: dict[str, dict] = {}

    try:
        text = _get(SINA_URL + ",".join(code_map), timeout)
        for line in text.strip().split("\n"):
            q = _parse_sina_line(line)
            if q and q.get("price"):
                h = code_map.get(q["code"])
                if h:
                    q["ticker"] = h["ticker"]
                    out[h["ticker"]] = q
    except Exception as exc:
        print(f"[WARN] 新浪行情失败: {exc}", flush=True)

    missing = [h for h in holdings if h["ticker"] not in out]
    if missing:
        print(f"  新浪缺 {len(missing)} 只，回退腾讯", flush=True)
        for h in missing:
            t = h["ticker"]
            code = ("us" + t if h["market"] == "US"
                    else "hk" + t.replace(".HK", "").zfill(5) if h["market"] == "HK"
                    else ("sh" if t.startswith(("6", "9")) else "sz") + t)
            try:
                text = _get(TENCENT_URL + code, timeout)
                q = _parse_tencent_line(text)
                if q and q.get("price"):
                    q["ticker"] = t
                    out[t] = q
            except Exception as exc:
                print(f"[WARN] 腾讯 {t} 失败: {exc}", flush=True)
            time.sleep(0.15)
    return out
