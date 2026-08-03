import logging
import re
from datetime import datetime, timezone

import httpx
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.models.audit_log import AuditLog
from app.models.generated_image import GeneratedImage
from app.models.job import AIJob, JobStatus
from app.models.user import User
from app.services.email import generation_completed_email_html, send_email
from app.services.gen_3d import generate_3d
from app.services.gen_3d_tencent import animate_3d_tencent, generate_3d_tencent, generate_3d_tencent_pro
from app.services.image_gen import generate_variants
from app.services.notifications import create_notification
from app.services.storage import storage_service
from app.workers.queue import JOB_TIMEOUT_SECONDS, get_redis_settings

logger = logging.getLogger("studio")


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "file"


async def _mark_failed(session: AsyncSession, job: AIJob, message: str) -> None:
    job.status = JobStatus.failed
    job.completed_at = datetime.now(timezone.utc)
    job.error_message = message[:2000]
    session.add(AuditLog(user_id=job.user_id, action=f"job_failed:{job.job_type.value}:{job.id}"))
    await create_notification(
        session, job.user_id, "generation_failed", f"Your {job.job_type.value} generation failed: {message[:200]}"
    )
    await session.commit()


async def _mark_completed(session: AsyncSession, job: AIJob) -> None:
    job.status = JobStatus.completed
    job.completed_at = datetime.now(timezone.utc)
    session.add(AuditLog(user_id=job.user_id, action=f"job_completed:{job.job_type.value}:{job.id}"))
    await create_notification(
        session, job.user_id, "generation_completed", f"Your {job.job_type.value} generation is ready."
    )
    await session.commit()

    user = await session.get(User, job.user_id)
    if user is not None:
        await send_email(
            user.email,
            "Your generation is ready",
            generation_completed_email_html(job.job_type.value),
        )


async def run_generate_images(ctx: dict, job_id: int) -> None:
    async with AsyncSessionLocal() as session:
        job = await session.get(AIJob, job_id)
        if job is None:
            logger.error(f"[Worker] generate_images: job {job_id} not found")
            return

        job.status = JobStatus.processing
        await session.commit()

        data = job.input_data or {}
        try:
            variants = await generate_variants(
                niche=data["niche"],
                style=data["style"],
                images=data["images"],
                user_prompt=data.get("user_prompt"),
                n_variants=data.get("n_variants", 3),
            )
            async with httpx.AsyncClient() as client:
                for variant in variants:
                    filename = f"{_slugify(variant['label'])}.jpg"
                    relative_path = await storage_service.save_from_url(
                        client, job.user_id, job.id, variant["url"], filename
                    )
                    session.add(
                        GeneratedImage(
                            user_id=job.user_id,
                            project_id=job.project_id,
                            job_id=job.id,
                            label=variant["label"],
                            file_path=relative_path,
                            file_type="image",
                        )
                    )
            await _mark_completed(session, job)
            logger.info(f"[Worker] job {job_id} (image) completed")
        except HTTPException as exc:
            await _mark_failed(session, job, str(exc.detail))
        except Exception:
            logger.exception(f"[Worker] job {job_id} (image) unexpected failure")
            await _mark_failed(session, job, "Unexpected error during image generation. Please retry.")


async def _persist_3d_result(session: AsyncSession, job: AIJob, result: dict) -> None:
    model_type = (result.get("model_type") or "glb").lower()

    async with httpx.AsyncClient() as client:
        model_relative = await storage_service.save_from_url(
            client, job.user_id, job.id, result["model_url"], f"model.{model_type}"
        )

        preview_relative = None
        if result.get("preview_url"):
            preview_relative = await storage_service.save_from_url(
                client, job.user_id, job.id, result["preview_url"], "preview.png"
            )

    session.add(
        GeneratedImage(
            user_id=job.user_id,
            project_id=job.project_id,
            job_id=job.id,
            file_path=model_relative,
            preview_url=preview_relative,
            file_type=result.get("model_type"),
        )
    )


async def run_generate_3d(ctx: dict, job_id: int) -> None:
    async with AsyncSessionLocal() as session:
        job = await session.get(AIJob, job_id)
        if job is None:
            logger.error(f"[Worker] generate_3d: job {job_id} not found")
            return

        job.status = JobStatus.processing
        await session.commit()

        data = job.input_data or {}
        images = data.get("images", [])
        user_prompt = data.get("user_prompt")
        try:
            if job.provider == "tencent_hunyuan3d":
                result = await generate_3d_tencent(images, user_prompt)
            elif job.provider == "tencent_hunyuan3d_pro":
                result = await generate_3d_tencent_pro(images, user_prompt)
            else:
                result = await generate_3d(images, user_prompt)

            await _persist_3d_result(session, job, result)
            await _mark_completed(session, job)
            logger.info(f"[Worker] job {job_id} (3d/{job.provider}) completed")
        except HTTPException as exc:
            await _mark_failed(session, job, str(exc.detail))
        except Exception:
            logger.exception(f"[Worker] job {job_id} (3d) unexpected failure")
            await _mark_failed(session, job, "Unexpected error during 3D generation. Please retry.")


async def run_animate_3d(ctx: dict, job_id: int) -> None:
    async with AsyncSessionLocal() as session:
        job = await session.get(AIJob, job_id)
        if job is None:
            logger.error(f"[Worker] animate_3d: job {job_id} not found")
            return

        job.status = JobStatus.processing
        await session.commit()

        data = job.input_data or {}
        try:
            # NOTE: data["model_url"] may be our own storage URL (from a
            # prior generate_3d job) rather than a raw provider URL —
            # animate_3d_tencent hands it back to Tencent's Convert3DFormat
            # action, so PUBLIC_BASE_URL must be genuinely reachable from
            # Tencent's servers in production, not just from the user's
            # browser (this can't be exercised in a sandbox with no public
            # endpoint — verify this specific path once actually deployed).
            result = await animate_3d_tencent(data["model_url"], data["motion_type"])
            await _persist_3d_result(session, job, result)
            await _mark_completed(session, job)
            logger.info(f"[Worker] job {job_id} (animate) completed")
        except HTTPException as exc:
            await _mark_failed(session, job, str(exc.detail))
        except Exception:
            logger.exception(f"[Worker] job {job_id} (animate) unexpected failure")
            await _mark_failed(session, job, "Unexpected error during animation. Please retry.")


class WorkerSettings:
    functions = [run_generate_images, run_generate_3d, run_animate_3d]
    redis_settings = get_redis_settings()
    job_timeout = JOB_TIMEOUT_SECONDS
    max_jobs = 3
