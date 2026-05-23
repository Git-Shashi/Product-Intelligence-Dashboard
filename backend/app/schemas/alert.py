from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.db.models import AlertStatus, Severity


class AlertOut(BaseModel):
    id: int
    product_id: Optional[int] = None
    type: str
    severity: Severity
    message: str
    status: AlertStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class AlertAcknowledge(BaseModel):
    status: AlertStatus = AlertStatus.ACKNOWLEDGED
