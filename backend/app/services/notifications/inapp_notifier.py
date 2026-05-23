"""
In-app notifier: the alert row is already written to the DB by the pipeline.
This notifier is a no-op for the default case — the alert IS the notification.
It exists so other notifiers (email, Slack) can be swapped in behind the same interface.
"""
import logging

from app.db.models import Alert

logger = logging.getLogger(__name__)


class InAppNotifier:
    async def send(self, alert: Alert) -> None:
        logger.info(
            "Alert [%s] %s: %s",
            alert.severity,
            alert.type,
            alert.message[:120],
        )
