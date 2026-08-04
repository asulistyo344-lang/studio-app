from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.subscription import SubscriptionPlan, SubscriptionStatus
from app.models.user import UserRole


class SubscriptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    plan: SubscriptionPlan
    status: SubscriptionStatus
    start_date: datetime
    expiry_date: Optional[datetime] = None


class AccountOut(BaseModel):
    id: int
    email: str
    role: UserRole
    credits_balance: int
    created_at: datetime
    subscription: Optional[SubscriptionOut] = None
