"""
SMTP email notifier (bonus). No-op + log if SMTP env vars are not configured.
"""
import logging
import smtplib
from email.mime.text import MIMEText

from app.core.config import settings
from app.db.models import Alert

logger = logging.getLogger(__name__)


class EmailNotifier:
    async def send(self, alert: Alert) -> None:
        if not settings.smtp_host or not settings.smtp_user:
            logger.debug("SMTP not configured — skipping email notification")
            return
        try:
            msg = MIMEText(
                f"Alert type: {alert.type}\n"
                f"Severity: {alert.severity}\n\n"
                f"{alert.message}"
            )
            msg["Subject"] = f"[{alert.severity}] Product Alert: {alert.type}"
            msg["From"] = settings.smtp_from or settings.smtp_user
            msg["To"] = settings.smtp_user

            with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
                server.starttls()
                server.login(settings.smtp_user, settings.smtp_password)
                server.send_message(msg)

            logger.info("Email alert sent for %s", alert.type)
        except Exception as e:
            logger.warning("Email notification failed: %s", e)
