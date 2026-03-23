"""
通用 Gmail SMTP 发送模块。
只负责发送，不构建 HTML——HTML 由各 channel 的 mailer.py 生成。

环境变量：
  GMAIL_APP_PASSWORD  必填（16位 App 密码）
  DIGEST_RECIPIENT    收件人（可选，默认同发件人）
"""

import os
import smtplib
import ssl

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

SENDER = "yzeng1018@gmail.com"


def send_html(subject: str, html_body: str) -> None:
    """通过 Gmail SMTP 发送 HTML 邮件。"""
    app_password = os.environ.get("GMAIL_APP_PASSWORD", "").replace(" ", "")
    if not app_password:
        print("[WARN] GMAIL_APP_PASSWORD not set – skipping email.")
        return

    recipient = os.environ.get("DIGEST_RECIPIENT", "").strip() or SENDER

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"Daily Digest <{SENDER}>"
    msg["To"] = recipient
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    print(f"发送邮件 → {recipient}…")
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ctx) as server:
            server.login(SENDER, app_password)
            server.send_message(msg)
        print(f"✉️  邮件已发送 → {recipient}")
    except Exception as exc:
        print(f"[ERROR] 邮件发送失败: {exc}")
