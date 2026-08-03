import base64
import binascii
import io
import logging

from arq.connections import ArqRedis
from fastapi import APIRouter, Depends, HTTPException
from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_arq_pool_dep, get_current_user, get_db
from app.core.config import settings
from app.models.audit_log import AuditLog
from app.models.job import AIJob, JobType
from app.models.user import User
from app.schemas.generation import (
    AnimateRequest,
    Generate3DRequest,
    GenerateImagesRequest,
    HealthResponse,
    StylesResponse,
)
from app.schemas.job import JobOut
from app.services.credits import check_and_consume_credits
from app.services.email import low_credit_warning_email_html, send_email
from app.services.notifications import create_notification
from app.services.prompts import NICHE_STYLES

logger = logging.getLogger("studio")

router = APIRouter(prefix="/studio")

MIN_IMAGE_DIMENSION = 14


def _decode_data_uri(data_uri: str) -> bytes:
    if "," in data_uri and data_uri.strip().startswith("data:"):
        data_uri = data_uri.split(",", 1)[1]
    return base64.b64decode(data_uri, validate=False)


def _validate_image(data_uri: str, index: int) -> None:
    try:
        raw = _decode_data_uri(data_uri)
        with Image.open(io.BytesIO(raw)) as img:
            width, height = img.size
    except (binascii.Error, ValueError, OSError):
        raise HTTPException(
            status_code=400,
            detail=f"Image {index + 1} is invalid or too small (minimum 14x14 pixels)",
        )

    if width < MIN_IMAGE_DIMENSION or height < MIN_IMAGE_DIMENSION:
        raise HTTPException(
            status_code=400,
            detail=f"Image {index + 1} is invalid or too small (minimum 14x14 pixels)",
        )


async def _create_and_enqueue_job(
    db: AsyncSession,
    arq_pool: ArqRedis,
    worker_function: str,
    *,
    current_user: User,
    job_type: JobType,
    provider: str,
    prompt: str | None,
    input_data: dict,
) -> JobOut:
    # Check + consume happen in the same transaction as job creation, so a
    # request can never create a job it couldn't afford.
    crossed_low_threshold = await check_and_consume_credits(db, current_user, job_type)

    job = AIJob(
        user_id=current_user.id,
        job_type=job_type,
        provider=provider,
        prompt=prompt,
        input_data=input_data,
    )
    db.add(job)
    await db.flush()
    db.add(AuditLog(user_id=current_user.id, action=f"job_created:{job_type.value}:{job.id}"))

    if crossed_low_threshold:
        await create_notification(
            db,
            current_user.id,
            "low_credit_warning",
            f"You're down to {current_user.credits_balance} credits.",
        )

    await db.commit()
    await db.refresh(job)

    if crossed_low_threshold:
        await send_email(
            current_user.email,
            "Low credit balance",
            low_credit_warning_email_html(current_user.credits_balance),
        )

    await arq_pool.enqueue_job(worker_function, job.id)
    logger.info(f"[Jobs] enqueued job_id={job.id} type={job_type.value} provider={provider}")

    return JobOut(
        id=job.id,
        job_type=job.job_type,
        provider=job.provider,
        status=job.status,
        error_message=job.error_message,
        created_at=job.created_at,
        completed_at=job.completed_at,
        results=[],
    )


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", app=settings.app_name, port=settings.port)


@router.get("/styles", response_model=StylesResponse)
async def styles() -> StylesResponse:
    return StylesResponse(**NICHE_STYLES)


@router.post("/generate-images", response_model=JobOut, status_code=202)
async def generate_images(
    payload: GenerateImagesRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    arq_pool: ArqRedis = Depends(get_arq_pool_dep),
) -> JobOut:
    if payload.niche not in NICHE_STYLES:
        raise HTTPException(
            status_code=400,
            detail="Niche must be one of: interior, exterior, product_model",
        )

    if payload.style not in NICHE_STYLES[payload.niche]:
        raise HTTPException(
            status_code=400,
            detail=f"Style '{payload.style}' not valid for niche '{payload.niche}'",
        )

    if not payload.images:
        raise HTTPException(status_code=400, detail="At least one image is required")

    for i, image in enumerate(payload.images):
        _validate_image(image, i)

    return await _create_and_enqueue_job(
        db,
        arq_pool,
        "run_generate_images",
        current_user=current_user,
        job_type=JobType.image,
        provider="byteplus_seedream",
        prompt=payload.user_prompt,
        input_data={
            "niche": payload.niche,
            "style": payload.style,
            "images": payload.images,
            "user_prompt": payload.user_prompt,
            "n_variants": payload.n_variants or 3,
        },
    )


@router.post("/generate-3d", response_model=JobOut, status_code=202)
async def generate_3d_endpoint(
    payload: Generate3DRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    arq_pool: ArqRedis = Depends(get_arq_pool_dep),
) -> JobOut:
    if not payload.images:
        raise HTTPException(status_code=400, detail="At least one image is required")

    for i, image in enumerate(payload.images):
        _validate_image(image, i)

    return await _create_and_enqueue_job(
        db,
        arq_pool,
        "run_generate_3d",
        current_user=current_user,
        job_type=JobType.threed,
        provider=payload.provider,
        prompt=payload.user_prompt,
        input_data={"images": payload.images, "user_prompt": payload.user_prompt},
    )


@router.post("/animate-3d", response_model=JobOut, status_code=202)
async def animate_3d_endpoint(
    payload: AnimateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    arq_pool: ArqRedis = Depends(get_arq_pool_dep),
) -> JobOut:
    return await _create_and_enqueue_job(
        db,
        arq_pool,
        "run_animate_3d",
        current_user=current_user,
        job_type=JobType.animate,
        provider="tencent_autorig",
        prompt=None,
        input_data={"model_url": payload.model_url, "motion_type": payload.motion_type},
    )
