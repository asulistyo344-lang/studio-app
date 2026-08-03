import mimetypes

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.core.security import verify_file_signature
from app.services.storage import storage_service

router = APIRouter(prefix="/studio/files")

EXTRA_CONTENT_TYPES = {
    ".glb": "model/gltf-binary",
    ".fbx": "application/octet-stream",
    ".obj": "text/plain",
}


@router.get("/{user_id}/{job_id}/{filename}")
async def get_file(user_id: int, job_id: int, filename: str, exp: int, sig: str) -> FileResponse:
    # Signed-URL auth (S3-presigned-link pattern), not the session cookie —
    # this route is loaded by <model-viewer>'s internal fetch() and plain
    # <img>/<a> tags, none of which reliably carry cookies cross-origin.
    relative_path = f"{user_id}/{job_id}/{filename}"
    if not verify_file_signature(relative_path, exp, sig):
        raise HTTPException(status_code=403, detail="Link expired or invalid.")

    path = storage_service.local_path(relative_path)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="File not found.")

    ext = path.suffix.lower()
    content_type = EXTRA_CONTENT_TYPES.get(ext) or mimetypes.guess_type(filename)[0] or "application/octet-stream"
    return FileResponse(path, media_type=content_type, filename=filename)
