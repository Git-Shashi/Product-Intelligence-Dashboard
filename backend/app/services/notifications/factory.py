from app.db.models import Alert
from app.services.notifications.email_notifier import EmailNotifier
from app.services.notifications.inapp_notifier import InAppNotifier

_inapp = InAppNotifier()
_email = EmailNotifier()


async def notify(alert: Alert) -> None:
    """Send via all configured notifiers. Failures are logged, never raised."""
    await _inapp.send(alert)
    await _email.send(alert)
