import logging

import httpx

from app.core.config import settings

logger = logging.getLogger("studio")

RESEND_API_URL = "https://api.resend.com/emails"


async def send_email(to: str, subject: str, html: str) -> None:
    """Best-effort transactional email via Resend's REST API — never raises.
    Email is a nice-to-have on top of core flows (registration, generation,
    credits), not a dependency: a missing/invalid RESEND_API_KEY should never
    block registration or job processing, so failures are logged and
    swallowed rather than propagated."""
    if not settings.resend_api_key:
        logger.info(f"[Email] RESEND_API_KEY not set, skipping email to {to!r}: {subject!r}")
        return

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                RESEND_API_URL,
                json={"from": settings.email_from_address, "to": [to], "subject": subject, "html": html},
                headers={"Authorization": f"Bearer {settings.resend_api_key}"},
                timeout=15,
            )
        if response.status_code >= 400:
            logger.warning(f"[Email] Resend HTTP {response.status_code}: {response.text[:500]}")
        else:
            logger.info(f"[Email] sent to {to!r}: {subject!r}")
    except httpx.RequestError as exc:
        logger.warning(f"[Email] request failed: {type(exc).__name__}: {exc!r}")


def verification_email_html(verify_url: str) -> str:
    return (
        f"<p>Welcome to {settings.app_name}. Confirm your email address:</p>"
        f'<p><a href="{verify_url}">{verify_url}</a></p>'
        "<p>This link expires in 24 hours.</p>"
    )


def password_reset_email_html(reset_url: str) -> str:
    return (
        "<p>A password reset was requested for your account.</p>"
        f'<p><a href="{reset_url}">{reset_url}</a></p>'
        "<p>If you didn't request this, you can ignore this email. This link expires in 1 hour.</p>"
    )


def generation_completed_email_html(job_type: str) -> str:
    return f"<p>Your {job_type} generation is ready — open {settings.app_name} to view it.</p>"


def low_credit_warning_email_html(credits_balance: int) -> str:
    return (
        f"<p>You're down to {credits_balance} credits on {settings.app_name}.</p>"
        "<p>Contact an admin to top up your balance.</p>"
    )


def welcome_email_html() -> str:
    return (
        f"<p>Welcome to {settings.app_name}! Your account is ready.</p>"
        "<p>You've been credited with your free plan's starting balance — jump in and generate something.</p>"
    )


def subscription_activated_email_html(plan: str) -> str:
    return f"<p>Your {settings.app_name} subscription is now active on the <strong>{plan}</strong> plan.</p>"
