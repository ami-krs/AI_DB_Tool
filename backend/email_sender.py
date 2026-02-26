"""
Send password-reset emails via SMTP.
Configure with env: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, EMAIL_FROM, FRONTEND_URL.
If SMTP is not configured, the reset link is logged (for development) and no exception is raised.
"""

from __future__ import annotations

import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

logger = logging.getLogger(__name__)


def _smtp_config() -> Optional[dict]:
    host = os.getenv("SMTP_HOST", "").strip()
    if not host:
        return None
    return {
        "host": host,
        "port": int(os.getenv("SMTP_PORT", "587")),
        "user": os.getenv("SMTP_USER", "").strip(),
        "password": os.getenv("SMTP_PASSWORD", "").strip(),
        "from_addr": os.getenv("EMAIL_FROM", os.getenv("SMTP_USER", "")).strip(),
        "frontend_url": os.getenv("FRONTEND_URL", "http://localhost:3000").strip().rstrip("/"),
    }


def send_reset_email(to_email: str, reset_token: str) -> bool:
    """
    Send an email containing the password-reset link.
    Link is: {FRONTEND_URL}/reset-password?token={reset_token}
    Returns True if email was sent, False if SMTP not configured (and logs the link).
    Raises only on actual send failure.
    """
    cfg = _smtp_config()
    base_url = (cfg and cfg.get("frontend_url")) or os.getenv("FRONTEND_URL", "http://localhost:3000").strip().rstrip("/")
    reset_link = f"{base_url}/reset-password?token={reset_token}"
    if not cfg:
        logger.warning("SMTP not configured. Password reset link (dev): %s", reset_link)
        return False
    subject = "Reset your password – AI Database Copilot"
    body_text = f"""You requested a password reset for AI Database Copilot.

Click the link below to set a new password (link expires in 1 hour):

{reset_link}

If you did not request this, you can ignore this email.
"""
    body_html = f"""<p>You requested a password reset for AI Database Copilot.</p>
<p><a href="{reset_link}">Click here to set a new password</a> (link expires in 1 hour).</p>
<p>If you did not request this, you can ignore this email.</p>"""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = cfg["from_addr"]
    msg["To"] = to_email
    msg.attach(MIMEText(body_text, "plain"))
    msg.attach(MIMEText(body_html, "html"))
    with smtplib.SMTP(cfg["host"], cfg["port"]) as server:
        server.starttls()
        if cfg["user"] and cfg["password"]:
            server.login(cfg["user"], cfg["password"])
        server.sendmail(cfg["from_addr"], to_email, msg.as_string())
    return True
