import asyncio
import logging

import httpx
from fastapi import HTTPException

from app.core.config import settings
from app.services.prompts import build_prompt

logger = logging.getLogger("studio")

VARIANT_LABELS = ["Variant 1", "Variant 2", "Variant 3"]


async def _generate_one(
    client: httpx.AsyncClient,
    niche: str,
    style: str,
    images: list[str],
    user_prompt: str | None,
    variant_index: int,
) -> str:
    prompt = build_prompt(niche, style, user_prompt, variant_index)

    payload = {
        "model": settings.byteplus_image_model,
        "prompt": prompt,
        "image": images,
        "size": "2K",
        "response_format": "url",
        "watermark": False,
        "stream": False,
    }

    try:
        response = await client.post(
            f"{settings.byteplus_base_url}/images/generations",
            json=payload,
            headers={"Authorization": f"Bearer {settings.byteplus_api_key}"},
            timeout=120,
        )
    except httpx.RequestError as exc:
        logger.error(f"[BytePlus] request failed for variant {variant_index + 1}: {exc}")
        raise HTTPException(
            status_code=503,
            detail="Seedream service unavailable. Please retry shortly.",
        ) from exc

    if response.status_code != 200:
        logger.error(f"[BytePlus] HTTP {response.status_code}: {response.text[:500]}")
        raise HTTPException(
            status_code=503,
            detail="Image generation failed. Please retry.",
        )

    try:
        data = response.json()
        return data["data"][0]["url"]
    except (KeyError, IndexError, ValueError) as exc:
        logger.error(f"[BytePlus] unexpected response shape: {response.text[:500]}")
        raise HTTPException(
            status_code=503,
            detail="Image generation failed. Please retry.",
        ) from exc


async def generate_variants(
    niche: str,
    style: str,
    images: list[str],
    user_prompt: str | None,
    n_variants: int = 3,
) -> list[dict]:
    async with httpx.AsyncClient() as client:
        results = await asyncio.gather(
            *[
                _generate_one(client, niche, style, images, user_prompt, i)
                for i in range(n_variants)
            ]
        )

    return [
        {"label": VARIANT_LABELS[i] if i < len(VARIANT_LABELS) else f"Variant {i + 1}", "url": url}
        for i, url in enumerate(results)
    ]
