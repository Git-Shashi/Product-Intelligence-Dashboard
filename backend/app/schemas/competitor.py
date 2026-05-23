from pydantic import BaseModel


class CompetitorRefreshOut(BaseModel):
    job_id: int


class CompetitorUploadOut(BaseModel):
    inserted: int
    skipped: int
