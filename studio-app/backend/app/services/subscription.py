from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.models.subscription import Subscription, SubscriptionPlan, SubscriptionStatus
from app.models.user import User
from app.services.email import send_email, subscription_activated_email_html
from app.services.notifications import create_notification

# Credits granted on plan activation, mirrors CREDIT_COSTS in credits.py —
# arbitrary starting values, tunable. Applied as a top-up (added to the
# current balance) rather than a hard reset, so activating/reactivating a
# plan never destroys credits a user already paid for or earned.
PLAN_CREDITS: dict[SubscriptionPlan, int] = {
    SubscriptionPlan.free: 30,
    SubscriptionPlan.pro: 500,
    SubscriptionPlan.enterprise: 2000,
}


async def activate_plan(
    db: AsyncSession, user: User, plan: SubscriptionPlan, source: str
) -> Subscription:
    """Single source of truth for changing a user's plan — per
    development-task.md 3.3, controllers must never mutate Subscription
    directly. Handles: activate plan, assign credits, notification, audit
    log. Does NOT commit and does NOT send email — callers commit, then
    call send_activation_email() after, matching the commit-then-notify
    convention already used in generation.py's _create_and_enqueue_job
    (so a rolled-back transaction never sends a misleading email).

    `source` is "admin" or "self_service" — both funnel through here so a
    real payment webhook can later call this exact function unchanged."""
    result = await db.execute(select(Subscription).where(Subscription.user_id == user.id))
    subscription = result.scalar_one_or_none()
    if subscription is None:
        subscription = Subscription(user_id=user.id, plan=plan, status=SubscriptionStatus.active)
        db.add(subscription)
    else:
        subscription.plan = plan
        subscription.status = SubscriptionStatus.active

    credits_granted = PLAN_CREDITS[plan]
    user.credits_balance += credits_granted

    await create_notification(
        db, user.id, "subscription_changed", f"Your plan is now {plan.value} (+{credits_granted} credits)."
    )
    db.add(AuditLog(user_id=user.id, action=f"subscription_activated:{plan.value}:{source}"))

    return subscription


async def send_activation_email(user: User, plan: SubscriptionPlan) -> None:
    await send_email(
        user.email, "Your subscription is active", subscription_activated_email_html(plan.value)
    )
