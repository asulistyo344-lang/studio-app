from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.models.job import JobType
from app.models.user import User

# Arbitrary starting costs, tunable — image jobs generate 3 variants per
# call, 3D/animate are individually more expensive provider calls.
CREDIT_COSTS: dict[JobType, int] = {
    JobType.image: 10,
    JobType.threed: 20,
    JobType.animate: 15,
}

LOW_CREDIT_THRESHOLD = 20


async def check_and_consume_credits(db: AsyncSession, user: User, job_type: JobType) -> bool:
    """Checks balance and deducts credits *before* a job is created — a job
    is never created for a request that can't afford it. No refund on job
    failure (matches today-task.md's flow: check balance -> consume ->
    create job), consistent with most credit-based generation products
    billing for the attempt, not just successful output.

    Returns True if this consumption just crossed the low-credit threshold
    (caller decides whether to notify/email — kept out of this function so
    credit logic stays independent of notification side effects)."""
    cost = CREDIT_COSTS[job_type]
    if user.credits_balance < cost:
        raise HTTPException(
            status_code=402,
            detail=f"Not enough credits for this action (need {cost}, have {user.credits_balance}). "
            "Contact an admin to top up your balance.",
        )

    was_above_threshold = user.credits_balance >= LOW_CREDIT_THRESHOLD
    user.credits_balance -= cost
    db.add(AuditLog(user_id=user.id, action=f"credits_consumed:{job_type.value}:{cost}"))

    return was_above_threshold and user.credits_balance < LOW_CREDIT_THRESHOLD
