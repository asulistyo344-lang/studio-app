from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_db
from app.models.job import AIJob
from app.models.user import User
from app.schemas.job import JobOut, ResultOut
from app.services.storage import storage_service

router = APIRouter(prefix="/studio/jobs")


def _job_to_out(job: AIJob) -> JobOut:
    return JobOut(
        id=job.id,
        job_type=job.job_type,
        provider=job.provider,
        status=job.status,
        error_message=job.error_message,
        created_at=job.created_at,
        completed_at=job.completed_at,
        results=[
            ResultOut(
                label=r.label,
                url=storage_service.signed_url(r.file_path),
                preview_url=storage_service.signed_url(r.preview_url) if r.preview_url else None,
                file_type=r.file_type,
            )
            for r in job.results
        ],
    )


@router.get("", response_model=list[JobOut])
async def list_jobs(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
) -> list[JobOut]:
    result = await db.execute(
        select(AIJob)
        .options(selectinload(AIJob.results))
        .where(AIJob.user_id == current_user.id)
        .order_by(AIJob.created_at.desc())
        .limit(min(limit, 200))
    )
    return [_job_to_out(job) for job in result.scalars().all()]


@router.get("/{job_id}", response_model=JobOut)
async def get_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JobOut:
    result = await db.execute(
        select(AIJob).options(selectinload(AIJob.results)).where(AIJob.id == job_id)
    )
    job = result.scalar_one_or_none()

    # 404 (not 403) for jobs that exist but belong to someone else — avoids
    # confirming to a caller that a given job_id exists at all.
    if job is None or job.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Job not found.")

    return _job_to_out(job)
