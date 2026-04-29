"""生成本地 HTML 存档文件（供调试用）。"""

from datetime import datetime
from pathlib import Path
from mailer import _build_email_html


def render(articles: list[dict], output_path: str, usage_info: dict | None = None, model_metrics: dict | None = None) -> None:
    date_str = datetime.now().strftime("%Y年%m月%d日")
    html = _build_email_html(articles, date_str, usage_info, model_metrics)
    Path(output_path).write_text(html, encoding="utf-8")
    print(f"HTML saved → {output_path}")
