from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.subscription import Subscription
from app.models.user import User
from app.schemas.account import AccountOut, SubscriptionOut

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
