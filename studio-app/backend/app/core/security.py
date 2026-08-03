import hashlib
import hmac
import time
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.core.config import settings

ACCESS_TOKEN_COOKIE_NAME = "studio_session"

# How long a signed file URL stays valid. Signed fresh on every job-status
# response (not baked into the stored file_path), so this only bounds how
# long a single API response's links are usable, not the file's lifetime.
FILE_URL_EXPIRY_SECONDS = 24 * 60 * 60


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> int | None:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        return None


def _file_signature(relative_path: str, expires_at: int) -> str:
    message = f"{relative_path}:{expires_at}".encode("utf-8")
    return hmac.new(settings.jwt_secret_key.encode("utf-8"), message, hashlib.sha256).hexdigest()


def sign_file_path(relative_path: str) -> tuple[int, str]:
    """Returns (expires_at, signature) for a storage-relative path. Used to
    build bearer-style URLs (like S3 presigned links) for /studio/files/ —
    those need to work with <model-viewer>'s internal fetch() and plain
    <img>/<a> tags, none of which reliably send our session cookie
    cross-origin, so this route can't rely on cookie auth."""
    expires_at = int(time.time()) + FILE_URL_EXPIRY_SECONDS
    return expires_at, _file_signature(relative_path, expires_at)


def verify_file_signature(relative_path: str, expires_at: int, signature: str) -> bool:
    if int(time.time()) > expires_at:
        return False
    expected = _file_signature(relative_path, expires_at)
    return hmac.compare_digest(expected, signature)


def create_action_token(user_id: int, action: str, expires_minutes: int) -> str:
    """Short-lived, single-purpose JWT for email verification / password
    reset links — separate from the session token (different claim, much
    shorter expiry, and checked against `action` so a verify-email link
    can't be reused to reset a password)."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "act": action,
        "iat": now,
        "exp": now + timedelta(minutes=expires_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_action_token(token: str, expected_action: str) -> int | None:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        if payload.get("act") != expected_action:
            return None
        return int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        return None
