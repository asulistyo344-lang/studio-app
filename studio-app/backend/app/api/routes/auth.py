import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.security import (
    ACCESS_TOKEN_COOKIE_NAME,
    create_access_token,
    create_action_token,
    decode_action_token,
    hash_password,
    verify_password,
)
from app.core.config import settings
from app.models.audit_log import AuditLog
from app.models.project import Project
from app.models.subscription import Subscription
from app.models.user import User, UserStatus
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    RegisterRequest,
    ResetPasswordRequest,
    UserOut,
    VerifyEmailRequest,
)
from app.services.email import (
    password_reset_email_html,
    send_email,
    verification_email_html,
    welcome_email_html,
)
from app.services.notifications import create_notification

logger = logging.getLogger("studio")

router = APIRouter(prefix="/studio/auth")

COOKIE_MAX_AGE_SECONDS = settings.jwt_expire_minutes * 60

VERIFY_EMAIL_ACTION = "verify_email"
RESET_PASSWORD_ACTION = "reset_password"
VERIFY_EMAIL_EXPIRY_MINUTES = 24 * 60
RESET_PASSWORD_EXPIRY_MINUTES = 60


def _set_session_cookie(response: Response, user_id: int) -> None:
    token = create_access_token(user_id)
    response.set_cookie(
        key=ACCESS_TOKEN_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.environment == "production",
        # Lax works fine in dev (localhost:5173 -> localhost:8006 is same-site,
        # only the port differs) but breaks silently once frontend/backend are
        # on different registrable domains in production (e.g. Vercel's own
        # domain + a VPS domain) — cross-site fetch() calls never send a Lax
        # cookie. None requires Secure, which is already conditional above.
        samesite="none" if settings.environment == "production" else "lax",
        max_age=COOKIE_MAX_AGE_SECONDS,
        path="/",
    )


@router.post("/register", response_model=UserOut)
async def register(payload: RegisterRequest, response: Response, db: AsyncSession = Depends(get_db)) -> User:
    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="An account with this email already exists.")

    user = User(email=payload.email, password_hash=hash_password(payload.password))
    db.add(user)
    await db.flush()

    db.add(Subscription(user_id=user.id))
    db.add(Project(user_id=user.id, name="Default"))
    db.add(AuditLog(user_id=user.id, action="user_registered"))
    await create_notification(db, user.id, "welcome", f"Welcome to {settings.app_name}! Your account is ready.")
    await db.commit()
    await db.refresh(user)

    logger.info(f"[Auth] registered user_id={user.id} email={user.email!r}")

    verify_token = create_action_token(user.id, VERIFY_EMAIL_ACTION, VERIFY_EMAIL_EXPIRY_MINUTES)
    verify_url = f"{settings.frontend_base_url}/verify-email?token={verify_token}"
    await send_email(user.email, "Verify your email", verification_email_html(verify_url))
    await send_email(user.email, f"Welcome to {settings.app_name}", welcome_email_html())

    _set_session_cookie(response, user.id)
    return user


@router.post("/login", response_model=UserOut)
async def login(payload: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)) -> User:
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password.")
    if user.status == UserStatus.suspended:
        raise HTTPException(status_code=403, detail="This account has been suspended. Contact an admin for help.")

    user.last_login_at = datetime.now(timezone.utc)
    db.add(AuditLog(user_id=user.id, action="user_login"))
    await db.commit()

    logger.info(f"[Auth] logged in user_id={user.id}")
    _set_session_cookie(response, user.id)
    return user


@router.post("/logout")
async def logout(response: Response) -> dict:
    # Must match _set_session_cookie's secure/samesite exactly — browsers
    # refuse to let a non-Secure Set-Cookie clear an existing Secure cookie
    # (Chrome's "Leave Secure Cookies Alone"), so a bare delete_cookie() call
    # here silently no-ops in production and logout appears to do nothing.
    response.delete_cookie(
        key=ACCESS_TOKEN_COOKIE_NAME,
        path="/",
        secure=settings.environment == "production",
        samesite="none" if settings.environment == "production" else "lax",
    )
    return {"status": "ok"}


@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.post("/verify-email", response_model=UserOut)
async def verify_email(payload: VerifyEmailRequest, db: AsyncSession = Depends(get_db)) -> User:
    user_id = decode_action_token(payload.token, VERIFY_EMAIL_ACTION)
    if user_id is None:
        raise HTTPException(status_code=400, detail="This verification link is invalid or has expired.")

    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Account not found.")

    user.email_verified = True
    db.add(AuditLog(user_id=user.id, action="email_verified"))
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/forgot-password")
async def forgot_password(payload: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)) -> dict:
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()

    # Always return the same response regardless of whether the email
    # exists — don't let this endpoint confirm which emails are registered.
    if user is not None:
        reset_token = create_action_token(user.id, RESET_PASSWORD_ACTION, RESET_PASSWORD_EXPIRY_MINUTES)
        reset_url = f"{settings.frontend_base_url}/reset-password?token={reset_token}"
        await send_email(user.email, "Reset your password", password_reset_email_html(reset_url))
        logger.info(f"[Auth] password reset requested user_id={user.id}")

    return {"status": "ok"}


@router.post("/reset-password")
async def reset_password(payload: ResetPasswordRequest, db: AsyncSession = Depends(get_db)) -> dict:
    user_id = decode_action_token(payload.token, RESET_PASSWORD_ACTION)
    if user_id is None:
        raise HTTPException(status_code=400, detail="This reset link is invalid or has expired.")

    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Account not found.")

    user.password_hash = hash_password(payload.new_password)
    db.add(AuditLog(user_id=user.id, action="password_reset"))
    await db.commit()
    logger.info(f"[Auth] password reset completed user_id={user.id}")
    return {"status": "ok"}
