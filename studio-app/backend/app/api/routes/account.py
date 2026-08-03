from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.subscription import Subscription
from app.models.user import User
from app.schemas.account import AccountOut, SubscriptionOut, UpgradeRequest
from app.services.subscription import activate_plan, send_activation_email

router = APIRouter(prefix="/studio/me")


@router.get("/account", response_model=AccountOut)
async def get_account(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> AccountOut:
    result = await db.execute(select(Subscription).where(Subscription.user_id == current_user.id))
    subscription = result.scalar_one_or_none()

    return AccountOut(
        id=current_user.id,
        email=current_user.email,
        role=current_user.role,
        credits_balance=current_user.credits_balance,
        created_at=current_user.created_at,
        subscription=SubscriptionOut.model_validate(subscription) if subscription else None,
    )


@router.post("/subscription/upgrade", response_model=AccountOut)
async def upgrade_subscription(
    payload: UpgradeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AccountOut:
    """Self-service plan change — no real payment provider. Simulates a
    successful payment event and funnels through the same centralized
    Subscription Service the admin path uses, per development-task.md 3.3
    ("a real payment webhook should be able to call the exact same service
    without changing business logic")."""
    subscription = await activate_plan(db, current_user, payload.plan, source="self_service")
    await db.commit()
    await db.refresh(current_user)
    await send_activation_email(current_user, payload.plan)

    return AccountOut(
        id=current_user.id,
        email=current_user.email,
        role=current_user.role,
        credits_balance=current_user.credits_balance,
        created_at=current_user.created_at,
        subscription=SubscriptionOut.model_validate(subscription),
    )
