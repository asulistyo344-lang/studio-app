import asyncio
import logging

import httpx
from fastapi import HTTPException

from app.core.config import settings

logger = logging.getLogger("studio")

POLL_INTERVAL_SECONDS = 15
MAX_WAIT_SECONDS = 1200


HYPER3D_DEFAULT_FLAGS = "--ff glb --resolution 1536pro --request_type 3"


async def _submit_task(client: httpx.AsyncClient, images_b64: list[str]) -> str:
    payload = {
        "model": settings.byteplus_3d_model,
        "content": [
            {"type": "text", "text": HYPER3D_DEFAULT_FLAGS},
            *[{"type": "image_url", "image_url": {"url": image}} for image in images_b64],
        ],
    }

    try:
        response = await client.post(
            f"{settings.byteplus_base_url}/contents/generations/tasks",
            json=payload,
            headers={"Authorization": f"Bearer {settings.byteplus_api_key}"},
            timeout=60,
        )
    except httpx.RequestError as exc:
        logger.error(f"[BytePlus] Hyper3D submit request failed: {type(exc).__name__}: {exc!r}")
        raise HTTPException(
            status_code=503,
            detail="Hyper3D service unavailable. Please retry shortly.",
        ) from exc

    if response.status_code not in (200, 201, 202):
        logger.error(f"[BytePlus] HTTP {response.status_code}: {response.text[:500]}")
        raise HTTPException(
            status_code=503,
            detail="3D generation task submission failed. Please retry.",
        )

    logger.info(f"[BytePlus] Hyper3D submit response: {response.text[:500]}")

    try:
        data = response.json()
        return data["id"]
    except (KeyError, ValueError) as exc:
        logger.error(f"[BytePlus] unexpected task submit response shape: {response.text[:500]}")
        raise HTTPException(
            status_code=503,
            detail="3D generation task submission failed. Please retry.",
        ) from exc


async def _poll_task(client: httpx.AsyncClient, task_id: str) -> dict:
    elapsed = 0
    while elapsed < MAX_WAIT_SECONDS:
        try:
            response = await client.get(
                f"{settings.byteplus_base_url}/contents/generations/tasks/{task_id}",
                headers={"Authorization": f"Bearer {settings.byteplus_api_key}"},
                timeout=30,
            )
        except httpx.RequestError as exc:
            logger.error(f"[BytePlus] Hyper3D poll request failed: {type(exc).__name__}: {exc!r}")
            raise HTTPException(
                status_code=503,
                detail="Hyper3D service unavailable. Please retry shortly.",
            ) from exc

        if response.status_code != 200:
            logger.error(f"[BytePlus] HTTP {response.status_code}: {response.text[:500]}")
            raise HTTPException(
                status_code=503,
                detail="3D generation status check failed. Please retry.",
            )

        data = response.json()
        status = data.get("status")
        logger.info(f"[BytePlus] Hyper3D poll status={status!r}: {response.text[:500]}")

        if status == "succeeded":
            return data
        if status == "failed":
            logger.error(f"[BytePlus] Hyper3D task {task_id} failed: {data}")
            raise HTTPException(
                status_code=503,
                detail="3D generation failed. Please retry.",
            )

        await asyncio.sleep(POLL_INTERVAL_SECONDS)
        elapsed += POLL_INTERVAL_SECONDS

    logger.error(f"[BytePlus] Hyper3D task {task_id} timed out after {MAX_WAIT_SECONDS}s")
    raise HTTPException(
        status_code=503,
        detail="3D generation timed out. Please retry.",
    )


async def generate_3d(images_b64: list[str], user_prompt: str | None = None) -> dict:
    async with httpx.AsyncClient() as client:
        task_id = await _submit_task(client, images_b64)
        result = await _poll_task(client, task_id)

    return {
        "task_id": task_id,
        "status": result.get("status", "succeeded"),
        "model_url": result.get("content", {}).get("file_url"),
        "preview_url": None,
        "model_type": "GLB",
    }
