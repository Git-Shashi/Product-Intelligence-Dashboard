import logging
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Job, JobStatus

logger = logging.getLogger(__name__)


async def mark_running(db: AsyncSession, job: Job) -> None:
    job.status = JobStatus.RUNNING
    job.started_at = datetime.now(timezone.utc)
    job.progress = 0
    await db.commit()


async def update_progress(db: AsyncSession, job: Job, progress: int) -> None:
    job.progress = min(progress, 99)
    await db.commit()


async def mark_completed(db: AsyncSession, job: Job, result_summary: dict | None = None) -> None:
    job.status = JobStatus.COMPLETED
    job.progress = 100
    job.completed_at = datetime.now(timezone.utc)
    job.result_summary = result_summary or {}
    await db.commit()


async def mark_partial(db: AsyncSession, job: Job, result_summary: dict) -> None:
    job.status = JobStatus.PARTIALLY_COMPLETED
    job.progress = 100
    job.completed_at = datetime.now(timezone.utc)
    job.result_summary = result_summary
    await db.commit()


async def mark_failed(db: AsyncSession, job: Job, error: str) -> None:
    job.status = JobStatus.FAILED
    job.completed_at = datetime.now(timezone.utc)
    job.error = error
    await db.commit()
