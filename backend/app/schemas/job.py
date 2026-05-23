from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.db.models import JobStatus, JobType


class JobOut(BaseModel):
    id: int
    type: JobType
    status: JobStatus
    progress: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    result_summary: Optional[dict] = None

    model_config = {"from_attributes": True}


class JobCreated(BaseModel):
    job_id: int
