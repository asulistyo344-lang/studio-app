from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.job import JobStatus, JobType


class ResultOut(BaseModel):
    label: Optional[str] = None
    url: str
    preview_url: Optional[str] = None
    file_type: Optional[str] = None


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_type: JobType
    provider: str
    status: JobStatus
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    results: list[ResultOut] = []
