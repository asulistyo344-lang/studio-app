from datetime import datetime
from typing import Generic, Optional, TypeVar

from pydantic import BaseModel

from app.models.job import JobStatus, JobType
from app.models.subscription import SubscriptionPlan, SubscriptionStatus
from app.models.user import UserRole, UserStatus

T = TypeVar("T")


class Paginated(BaseModel, Generic[T]):
    items: list[T]
    total: int


class AdminUserOut(BaseModel):
    id: int
    email: str
    role: UserRole
    status: UserStatus
    credits_balance: int
    created_at: datetime
    plan: Optional[SubscriptionPlan] = None
    subscription_status: Optional[SubscriptionStatus] = None
    job_count: int = 0


class AdminUserUpdate(BaseModel):
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None
    credits_balance: Optional[int] = None
    plan: Optional[SubscriptionPlan] = None


class AdminJobOut(BaseModel):
    id: int
    user_id: int
    user_email: str
    job_type: JobType
    provider: str
    status: JobStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class AdminStatsOut(BaseModel):
    total_users: int
    active_users_7d: int
    new_registrations_7d: int
    users_by_plan: dict[str, int]
    total_jobs: int
    jobs_by_status: dict[str, int]
    jobs_by_type: dict[str, int]
    queue_depth: int
    failure_rate: float
    avg_generation_seconds: Optional[float] = None
    total_credits_consumed: int


class AdminAuditLogOut(BaseModel):
    id: int
    user_id: Optional[int] = None
    user_email: Optional[str] = None
    action: str
    timestamp: datetime
