import logging
from pathlib import Path

import httpx

from app.core.config import settings
from app.core.security import sign_file_path

logger = logging.getLogger("studio")


class StorageService:
    """Local-disk storage for generated results, behind an interface that
    can be swapped for S3/R2 later without touching callers. Files are laid
    out as {base_path}/{user_id}/{job_id}/{filename} — the worker downloads
    each provider result once and persists it here, since provider URLs
    (especially Tencent's) expire after ~24h."""

    def __init__(self, base_path: str, public_base_url: str):
        self.base_path = Path(base_path)
        self.public_base_url = public_base_url.rstrip("/")

    def _path_for(self, user_id: int, job_id: int, filename: str) -> Path:
        return self.base_path / str(user_id) / str(job_id) / filename

    async def save_from_url(
        self, client: httpx.AsyncClient, user_id: int, job_id: int, source_url: str, filename: str
    ) -> str:
        """Downloads source_url and writes it to local disk. Returns the
        relative 'user_id/job_id/filename' path (use get_url() to build the
        full servable URL from it)."""
        dest = self._path_for(user_id, job_id, filename)
        dest.parent.mkdir(parents=True, exist_ok=True)

        response = await client.get(source_url, timeout=120)
        response.raise_for_status()
        dest.write_bytes(response.content)

        logger.info(f"[Storage] saved {dest} ({len(response.content)} bytes)")
        return f"{user_id}/{job_id}/{filename}"

    def delete(self, relative_path: str) -> None:
        path = self.base_path / relative_path
        if path.exists():
            path.unlink()

    def local_path(self, relative_path: str) -> Path:
        return self.base_path / relative_path

    def signed_url(self, relative_path: str) -> str:
        """Builds a bearer-style signed URL (S3-presigned-link pattern) —
        signed fresh at call time, not stored, so links returned by the API
        are always valid for FILE_URL_EXPIRY_SECONDS from the moment they're
        requested regardless of how old the underlying file is."""
        expires_at, signature = sign_file_path(relative_path)
        return f"{self.public_base_url}/studio/files/{relative_path}?exp={expires_at}&sig={signature}"


storage_service = StorageService(settings.storage_path, settings.public_base_url)
