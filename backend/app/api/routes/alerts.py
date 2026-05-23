from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.db.models import Alert, AlertStatus, Severity
from app.schemas.alert import AlertAcknowledge, AlertOut

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertOut])
async def list_alerts(
    severity: str | None = None,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Alert).order_by(Alert.id.desc())
    result = await db.execute(stmt)
    alerts = result.scalars().all()

    if severity:
        sev = Severity(severity.upper())
        alerts = [a for a in alerts if a.severity == sev]
    if status:
        st = AlertStatus(status.upper())
        alerts = [a for a in alerts if a.status == st]
    return alerts


@router.get("/count")
async def alert_count(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(func.count()).where(Alert.status == AlertStatus.OPEN)
    )
    return {"open": result.scalar_one()}


@router.post("/acknowledge-all")
async def acknowledge_all(db: AsyncSession = Depends(get_db)):
    await db.execute(
        update(Alert).where(Alert.status == AlertStatus.OPEN).values(status=AlertStatus.ACKNOWLEDGED)
    )
    await db.commit()
    return {"ok": True}


@router.patch("/{alert_id}/acknowledge", response_model=AlertOut)
async def acknowledge_alert(alert_id: int, db: AsyncSession = Depends(get_db)):
    alert = await db.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.status = AlertStatus.ACKNOWLEDGED
    await db.commit()
    await db.refresh(alert)
    return alert
