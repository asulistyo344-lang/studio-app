import asyncio
import hashlib
import hmac
import json
import logging
import time

import httpx
from fastapi import HTTPException

from app.core.config import settings

logger = logging.getLogger("studio")

POLL_INTERVAL_SECONDS = 5
MAX_WAIT_SECONDS = 600

MULTI_VIEW_TYPES = ["back", "left", "right"]

# Tencent's Hunyuan 3D generation lives under the "hunyuan" service on the
# international endpoint, not the "ai3d" service (ai3d.tencentcloudapi.com) —
# the latter returns ResourceUnavailable.InterfaceNotExist for intl accounts.
HOST = "hunyuan.intl.tencentcloudapi.com"
SERVICE = "hunyuan"
VERSION = "2023-09-01"


def _strip_data_uri(data_uri: str) -> str:
    if "," in data_uri and data_uri.strip().startswith("data:"):
        return data_uri.split(",", 1)[1]
    return data_uri


def _sha256hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _hmac_sha256(key: bytes, msg: str) -> bytes:
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


def _sign_request(action: str, payload: str) -> dict[str, str]:
    """Builds TC3-HMAC-SHA256 signed headers for a Tencent Cloud API POST request."""
    timestamp = int(time.time())
    date = time.strftime("%Y-%m-%d", time.gmtime(timestamp))
    content_type = "application/json; charset=utf-8"

    canonical_headers = f"content-type:{content_type}\nhost:{HOST}\nx-tc-action:{action.lower()}\n"
    signed_headers = "content-type;host;x-tc-action"
    hashed_payload = _sha256hex(payload.encode("utf-8"))
    canonical_request = (
        f"POST\n/\n\n{canonical_headers}\n{signed_headers}\n{hashed_payload}"
    )

    credential_scope = f"{date}/{SERVICE}/tc3_request"
    hashed_canonical_request = _sha256hex(canonical_request.encode("utf-8"))
    string_to_sign = (
        f"TC3-HMAC-SHA256\n{timestamp}\n{credential_scope}\n{hashed_canonical_request}"
    )

    secret_date = _hmac_sha256(("TC3" + settings.tencent_secret_key).encode("utf-8"), date)
    secret_service = _hmac_sha256(secret_date, SERVICE)
    secret_signing = _hmac_sha256(secret_service, "tc3_request")
    signature = hmac.new(secret_signing, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

    authorization = (
        f"TC3-HMAC-SHA256 Credential={settings.tencent_secret_id}/{credential_scope}, "
        f"SignedHeaders={signed_headers}, Signature={signature}"
    )

    return {
        "Authorization": authorization,
        "Content-Type": content_type,
        "Host": HOST,
        "X-TC-Action": action,
        "X-TC-Timestamp": str(timestamp),
        "X-TC-Version": VERSION,
        "X-TC-Region": settings.tencent_ai3d_region,
    }


def _require_credentials() -> None:
    if not settings.tencent_secret_id or not settings.tencent_secret_key:
        raise HTTPException(
            status_code=503,
            detail="Tencent 3D generation is not configured. Set TENCENT_SECRET_ID and TENCENT_SECRET_KEY.",
        )


async def _call(client: httpx.AsyncClient, action: str, params: dict) -> dict:
    payload = json.dumps(params)
    headers = _sign_request(action, payload)

    try:
        response = await client.post(f"https://{HOST}/", content=payload, headers=headers, timeout=60)
    except httpx.RequestError as exc:
        logger.error(f"[Tencent] {action} request failed: {type(exc).__name__}: {exc!r}")
        raise HTTPException(
            status_code=503,
            detail="Tencent 3D generation service unavailable. Please retry shortly.",
        ) from exc

    if response.status_code != 200:
        logger.error(f"[Tencent] {action} HTTP {response.status_code}: {response.text[:500]}")
        raise HTTPException(
            status_code=503,
            detail=f"Tencent 3D generation request failed (HTTP {response.status_code}). Please retry.",
        )

    data = response.json().get("Response", {})
    error = data.get("Error")
    if error:
        code = error.get("Code", "UnknownError")
        message = error.get("Message", "")
        logger.error(f"[Tencent] {action} failed: {code}: {message}")
        raise HTTPException(
            status_code=503,
            detail=f"Tencent 3D generation request failed ({code}). Please retry.",
        )

    return data


def _pick_result_file(result_files: list[dict], preferred_type: str = "GLB") -> dict | None:
    """ResultFile3Ds can contain multiple format variants (e.g. Pro job returns
    both an OBJ bundle and a GLB) — prefer the GLB entry when present so the
    frontend can preview it directly, otherwise fall back to whatever's there."""
    for file in result_files:
        if file.get("Type") == preferred_type:
            return file
    return result_files[0] if result_files else None


async def _convert_3d_format(client: httpx.AsyncClient, file_url: str, target_format: str) -> str:
    data = await _call(client, "Convert3DFormat", {"File3D": file_url, "Format": target_format})
    result_url = data.get("ResultFile3D")
    if not result_url:
        logger.error(f"[Tencent] Convert3DFormat returned no ResultFile3D: {data}")
        raise HTTPException(
            status_code=503,
            detail="Tencent 3D format conversion failed. Please retry.",
        )
    return result_url


def _build_rapid_submit_params(images_b64: list[str], user_prompt: str | None) -> dict:
    # SubmitHunyuanTo3DRapidJob only accepts a single ImageBase64/ImageUrl OR a
    # Prompt, never both together, and has no MultiViewImages parameter (that's
    # Pro-job only) — extra uploaded images beyond the first are ignored here.
    if images_b64:
        return {"ImageBase64": _strip_data_uri(images_b64[0]), "ResultFormat": "GLB"}
    return {"Prompt": (user_prompt or "")[:200], "ResultFormat": "GLB"}


def _build_pro_submit_params(images_b64: list[str], user_prompt: str | None) -> dict:
    # SubmitHunyuanTo3DProJob has no ResultFormat param — its response includes
    # both an OBJ bundle and a native GLB variant (verified empirically), so no
    # format conversion is needed here, unlike the AutoRigging path below.
    if images_b64:
        params: dict = {"ImageBase64": _strip_data_uri(images_b64[0]), "EnablePBR": True}
        if len(images_b64) > 1:
            params["MultiViewImages"] = [
                {"ViewType": view_type, "ViewImageBase64": _strip_data_uri(image)}
                for view_type, image in zip(MULTI_VIEW_TYPES, images_b64[1:])
            ]
        return params
    return {"Prompt": (user_prompt or "")[:1024], "EnablePBR": True}


async def _poll_job(client: httpx.AsyncClient, query_action: str, job_id: str) -> dict:
    elapsed = 0
    while elapsed < MAX_WAIT_SECONDS:
        data = await _call(client, query_action, {"JobId": job_id})
        status = data.get("Status")
        logger.info(f"[Tencent] {query_action} job_id={job_id} status={status!r}")

        if status == "DONE":
            return data
        if status == "FAIL":
            error_code = data.get("ErrorCode") or "unknown"
            logger.error(f"[Tencent] job {job_id} failed: {error_code}: {data.get('ErrorMessage')}")
            raise HTTPException(
                status_code=503,
                detail=f"Tencent 3D generation failed ({error_code}). Please retry.",
            )

        await asyncio.sleep(POLL_INTERVAL_SECONDS)
        elapsed += POLL_INTERVAL_SECONDS

    logger.error(f"[Tencent] job {job_id} timed out after {MAX_WAIT_SECONDS}s")
    raise HTTPException(
        status_code=503,
        detail="Tencent 3D generation timed out. Please retry.",
    )


async def _submit_and_poll(
    client: httpx.AsyncClient, submit_action: str, query_action: str, params: dict
) -> tuple[str, dict]:
    submitted = await _call(client, submit_action, params)
    job_id = submitted.get("JobId")
    if not job_id:
        logger.error(f"[Tencent] {submit_action} response had no JobId: {submitted}")
        raise HTTPException(
            status_code=503,
            detail="Tencent 3D generation task submission failed. Please retry.",
        )
    logger.info(f"[Tencent] {submit_action} submitted job_id={job_id!r}")

    result = await _poll_job(client, query_action, job_id)
    return job_id, result


def _result_from_files(job_id: str, result_files: list[dict], preferred_type: str = "GLB") -> dict:
    model_file = _pick_result_file(result_files, preferred_type)
    if model_file is None:
        logger.error(f"[Tencent] job {job_id} succeeded with no ResultFile3Ds")
        raise HTTPException(
            status_code=503,
            detail="Tencent 3D generation returned no model file. Please retry.",
        )

    return {
        "task_id": job_id,
        "status": "succeeded",
        "model_url": model_file.get("Url"),
        "preview_url": model_file.get("PreviewImageUrl"),
        "model_type": model_file.get("Type"),
    }


async def generate_3d_tencent(images_b64: list[str], user_prompt: str | None = None) -> dict:
    _require_credentials()
    async with httpx.AsyncClient() as client:
        job_id, result = await _submit_and_poll(
            client,
            "SubmitHunyuanTo3DRapidJob",
            "QueryHunyuanTo3DRapidJob",
            _build_rapid_submit_params(images_b64, user_prompt),
        )
    return _result_from_files(job_id, result.get("ResultFile3Ds") or [])


async def generate_3d_tencent_pro(images_b64: list[str], user_prompt: str | None = None) -> dict:
    _require_credentials()
    async with httpx.AsyncClient() as client:
        job_id, result = await _submit_and_poll(
            client,
            "SubmitHunyuanTo3DProJob",
            "QueryHunyuanTo3DProJob",
            _build_pro_submit_params(images_b64, user_prompt),
        )
    return _result_from_files(job_id, result.get("ResultFile3Ds") or [])


async def animate_3d_tencent(model_url: str, motion_type: int) -> dict:
    _require_credentials()
    async with httpx.AsyncClient() as client:
        # SubmitAutoRiggingJob only accepts a bare FBX or OBJ file (not a GLB,
        # and not the zipped OBJ bundle Pro jobs return) — convert first.
        fbx_url = await _convert_3d_format(client, model_url, "FBX")

        job_id, result = await _submit_and_poll(
            client,
            "SubmitAutoRiggingJob",
            "DescribeAutoRiggingJob",
            {"File3D": {"Url": fbx_url, "Type": "FBX"}, "MotionType": motion_type},
        )
    return _result_from_files(job_id, result.get("ResultFile3Ds") or [])
