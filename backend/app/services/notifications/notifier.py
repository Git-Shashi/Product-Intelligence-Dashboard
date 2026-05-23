from typing import Protocol, runtime_checkable

from app.db.models import Alert


@runtime_checkable
class Notifier(Protocol):
    async def send(self, alert: Alert) -> None:
        ...
