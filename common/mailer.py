"""
通用 SMTP 发送模块。
只负责发送，不构建 HTML——HTML 由各 channel 的 mailer.py 生成。

默认走 163 邮箱投递到自己 Gmail，避免 Gmail 里堆满「自己发给自己」的邮件。

环境变量：
  SMTP_PASSWORD    必填（163 授权码，非登录密码）
  SMTP_USER        发件账号（默认 samuel295@163.com）
  SMTP_HOST        发件服务器（默认 smtp.163.com）
  SMTP_PORT        端口（默认 465 SSL；587 走 STARTTLS）
  SMTP_FROM_NAME   发件人显示名（默认 Daily Digest）
  DIGEST_RECIPIENT 收件人（默认 yzeng1018@gmail.com）

向后兼容：GMAIL_APP_PASSWORD 仍可作为 SMTP_PASSWORD 的旧别名。
"""

import os
import smtplib
import ssl

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.163.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "465"))
SMTP_USER = os.environ.get("SMTP_USER", "samuel295@163.com")
SENDER_NAME = os.environ.get("SMTP_FROM_NAME", "Daily Digest")
RECIPIENT = os.environ.get("DIGEST_RECIPIENT", "").strip() or "yzeng1018@gmail.com"


def _password() -> str:
    """优先读新变量名，回落旧的 GMAIL_APP_PASSWORD。"""
    return (
        os.environ.get("SMTP_PASSWORD")
        or os.environ.get("GMAIL_APP_PASSWORD")
        or ""
    ).replace(" ", "")


def send_html(subject: str, html_body: str) -> None:
    """通过 SMTP 发送 HTML 邮件。"""
    password = _password()
    if not password:
        print("[WARN] SMTP_PASSWORD not set – skipping email.")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{SENDER_NAME} <{SMTP_USER}>"
    msg["To"] = RECIPIENT
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    print(f"发送邮件 → {RECIPIENT}…  (via {SMTP_HOST}:{SMTP_PORT} as {SMTP_USER})")
    try:
        if SMTP_PORT == 587:
            ctx = ssl.create_default_context()
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=60) as server:
                server.starttls(context=ctx)
                server.login(SMTP_USER, password)
                server.send_message(msg)
        else:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=ctx, timeout=60) as server:
                server.login(SMTP_USER, password)
                server.send_message(msg)
        print(f"✉️  邮件已发送 → {RECIPIENT}")
    except Exception as exc:
        print(f"[ERROR] 邮件发送失败: {exc}")
