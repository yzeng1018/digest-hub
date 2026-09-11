#!/usr/bin/env python3
"""财经内容灵感 — 独立日报。

读取投资情报跑完后落盘的 data/ideas/<date>.json 渲染成一封独立邮件，
避免为同一批数据重复执行抓取与付费评分。本身不调用 LLM，也不需要网络。

用法：
    python channels/investment/main_ideas.py
    python channels/investment/main_ideas.py --date 2026-09-11

发信由 WorkBuddy automation 读取产出的 HTML 后走 Agent Mail，这里不碰 SMTP。
"""

import argparse
import json
import os
import sys
from datetime import datetime
from html import escape
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT       = Path(__file__).resolve().parents[2]
IDEAS_DIR  = ROOT / "data" / "ideas"
OUTPUT_DIR = Path(__file__).parent / "output"


def _load_ideas(date_str: str) -> dict | None:
    target = IDEAS_DIR / f"{date_str}.json"
    if not target.exists():
        return None
    try:
        return json.loads(target.read_text(encoding="utf-8"))
    except ValueError as exc:
        print(f"数据解析失败: {target} ({exc})")
        return None


def _card(idea: dict, index: int) -> str:
    signal = idea.get("signal") or ""
    signal_row = (
        '<div style="color:#2b8a3e;font-size:12px;margin-top:7px;">'
        f'验证信号：{escape(signal)}</div>'
    ) if signal else ""
    title = idea.get("title") or ""
    source = idea.get("source") or ""
    return (
        '<tr><td style="padding:16px 20px;border-bottom:1px solid #f1f3f5;">'
        f'<div style="font-size:11px;color:#adb5bd;letter-spacing:1.5px;">IDEA {index:02d}</div>'
        f'<div style="font-size:17px;font-weight:800;color:#9c5b00;margin-top:4px;">{escape(idea.get("topic", ""))}</div>'
        '<div style="font-size:13px;color:#495057;line-height:1.7;margin-top:9px;">'
        f'<b>新闻钩子：</b>{escape(idea.get("hook", ""))}</div>'
        '<div style="font-size:13px;color:#212529;line-height:1.75;margin-top:7px;">'
        f'{escape(idea.get("angle", ""))}</div>'
        f'{signal_row}'
        f'<a href="{escape(idea.get("url", "#"), quote=True)}" style="display:inline-block;'
        'margin-top:9px;font-size:11px;color:#1c7ed6;text-decoration:none;">'
        f'来源：{escape(source)} · {escape(title)}</a>'
        '</td></tr>'
    )


def _ensure_dir(path: Path) -> None:
    """mkdir(exist_ok=True) can still raise EEXIST under the sandbox shim."""
    try:
        path.mkdir(parents=True, exist_ok=True)
    except OSError:
        if not path.is_dir():
            raise


def render(payload: dict, output_path: str) -> None:
    ideas    = payload.get("ideas", [])
    date_str = payload.get("date", "")
    cards    = "".join(_card(idea, index) for index, idea in enumerate(ideas, start=1))
    if not ideas:
        cards = (
            '<tr><td style="padding:26px 20px;color:#868e96;font-size:13px;line-height:1.7;">'
            '今日没有通过冷却筛选的新灵感。<br>14 天内已覆盖的主题不会重复出现，'
            '冷清是常态而不是故障。</td></tr>'
        )
    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>财经内容灵感 {date_str}</title></head>
<body style="margin:0;padding:0;background:#f8f9fa;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f8f9fa;padding:20px 0;">
<tr><td align="center">
<table width="640" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:10px;overflow:hidden;font-family:-apple-system,BlinkMacSystemFont,'PingFang SC','Helvetica Neue',sans-serif;">
  <tr><td style="padding:22px 20px;background:#fff9e8;border-bottom:2px solid #f3dfb3;">
    <div style="font-size:20px;font-weight:800;color:#9c5b00;">💡 今日财经内容灵感</div>
    <div style="font-size:12px;color:#8c7a55;margin-top:5px;">{date_str} · 由近 72 小时新闻钩子驱动，主题冷却 14 天</div>
  </td></tr>
  {cards}
  <tr><td style="padding:14px 20px;background:#f8f9fa;font-size:11px;color:#adb5bd;line-height:1.6;">
    每个选题都是待验证的研究假设，不是买卖建议。DRAM / NAND / HBM / 存储共享同一冷却桶，避免同一条主线换皮重出。
  </td></tr>
</table>
</td></tr></table>
</body></html>"""
    Path(output_path).write_text(html, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Standalone content ideas digest")
    parser.add_argument("--date", default="")
    args = parser.parse_args()

    timezone = ZoneInfo("Asia/Shanghai")
    date_str = args.date or datetime.now(timezone).strftime("%Y-%m-%d")
    payload  = _load_ideas(date_str)
    if not payload:
        print(f"No ideas payload for {date_str}.")
        print("先跑投资情报（python channels/investment/main.py --no-email）生成 data/ideas。")
        sys.exit(1)

    _ensure_dir(OUTPUT_DIR)
    output_path = str(OUTPUT_DIR / f"ideas-{date_str}.html")
    render(payload, output_path)

    count = len(payload.get("ideas", []))
    print(f"\n完成。共 {count} 条内容灵感")
    print(f"   HTML: file://{os.path.abspath(output_path)}")


if __name__ == "__main__":
    main()
