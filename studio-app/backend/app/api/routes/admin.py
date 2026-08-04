import logging
from datetime import datetime, timedelta, timezone

from arq.connections import ArqRedis
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_arq_pool_dep, get_db, require_admin
from app.models.audit_log import AuditLog
from app.models.job import AIJob, JobStatus, JobType
from app.models.subscription import Subscription
from app.models.user import User
from app.schemas.admin import (
    AdminAuditLogOut,
    AdminJobOut,
    AdminStatsOut,
    AdminUserOut,
    AdminUserUpdate,
    Paginated,
)
from app.services.subscription import activate_plan, send_activation_email

logger = logging.getLogger("studio")

router = APIRouter(prefix="/studio/admin", dependencies=[Depends(require_admin)])

# Mirrors the worker_function each generation.py route enqueues under —
# duplicated here (not imported) since generation.py hardcodes these inline
# per-route rather than exposing a shared mapping.
WORKER_FUNCTION_BY_JOB_TYPE: dict[JobType, str] = {
    JobType.image: "run_generate_images",
    JobType.threed: "run_generate_3d",
    JobType.animate: "run_animate_3d",
}


@router.get("/users", response_model=Paginated[AdminUserOut])
async def list_users(
    db: AsyncSession = Depends(get_db), limit: int = 50, offset: int = 0, q: str | None = None
) -> Paginated[AdminUserOut]:
    base_query = select(User)
    count_query = select(func.count(User.id))
    if q:
        base_query = base_query.where(User.email.ilike(f"%{q}%"))
        count_query = count_query.where(User.email.ilike(f"%{q}%"))

    total = (await db.execute(count_query)).scalar_one()
    users = (
        (
            await db.execute(
                base_query.order_by(User.created_at.desc()).limit(min(limit, 200)).offset(offset)
            )
        )
        .scalars()
        .all()
    )
    subscriptions = {s.user_id: s for s in (await db.execute(select(Subscription))).scalars().all()}
    job_counts = dict(
        (await db.execute(select(AIJob.user_id, func.count(AIJob.id)).group_by(AIJob.user_id))).all()
    )

    return Paginated(
        total=total,
        items=[
            AdminUserOut(
                id=u.id,
                email=u.email,
                role=u.role,
                status=u.status,
                credits_balance=u.credits_balance,
                created_at=u.created_at,
                plan=subscriptions[u.id].plan if u.id in subscriptions else None,
                subscription_status=subscriptions[u.id].status if u.id in subscriptions else None,
                job_count=job_counts.get(u.id, 0),
            )
            for u in users
        ],
    )


@router.patch("/users/{user_id}", response_model=AdminUserOut)
async def update_user(
    user_id: int,
    payload: AdminUserUpdate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminUserOut:
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")

    changes = []
    if payload.role is not None:
        user.role = payload.role
        changes.append(f"role={payload.role.value}")
    if payload.status is not None:
        user.status = payload.status
        changes.append(f"status={payload.status.value}")
    if payload.credits_balance is not None:
        user.credits_balance = payload.credits_balance
        changes.append(f"credits={payload.credits_balance}")

    result = await db.execute(select(Subscription).where(Subscription.user_id == user.id))
    subscription = result.scalar_one_or_none()

    # Plan changes go through the centralized Subscription Service (not a
    # direct mutation here) — see services/subscription.py for why. Only
    # activate when the plan is actually changing: the frontend always
    # includes the user's *current* plan in every save payload (even a
    # credits-only edit), and activate_plan() grants a full credit top-up
    # unconditionally — routing every save through it regardless of whether
    # the plan changed silently added bonus credits on top of whatever an
    # admin explicitly typed into the credits field.
    plan_activated = False
    if payload.plan is not None and (subscription is None or subscription.plan != payload.plan):
        subscription = await activate_plan(db, user, payload.plan, source="admin")
        changes.append(f"plan={payload.plan.value}")
        plan_activated = True

    if changes:
        db.add(AuditLog(user_id=admin.id, action=f"admin_updated_user:{user.id}:{','.join(changes)}"))
        await db.commit()
        await db.refresh(user)

    if plan_activated:
        await send_activation_email(user, payload.plan)

    return AdminUserOut(
        id=user.id,
        email=user.email,
        role=user.role,
        status=user.status,
        credits_balance=user.credits_balance,
        created_at=user.created_at,
        plan=subscription.plan if subscription else None,
        subscription_status=subscription.status if subscription else None,
        job_count=0,
    )


@router.get("/jobs", response_model=Paginated[AdminJobOut])
async def list_all_jobs(
    db: AsyncSession = Depends(get_db), limit: int = 100, offset: int = 0
) -> Paginated[AdminJobOut]:
    total = (await db.execute(select(func.count(AIJob.id)))).scalar_one()
    result = await db.execute(
        select(AIJob, User.email)
        .join(User, User.id == AIJob.user_id)
        .order_by(AIJob.created_at.desc())
        .limit(min(limit, 500))
        .offset(offset)
    )
    return Paginated(
        total=total,
        items=[
            AdminJobOut(
                id=job.id,
                user_id=job.user_id,
                user_email=email,
                job_type=job.job_type,
                provider=job.provider,
                status=job.status,
                created_at=job.created_at,
                completed_at=job.completed_at,
                error_message=job.error_message,
            )
            for job, email in result.all()
        ],
    )


@router.get("/stats", response_model=AdminStatsOut)
async def get_stats(db: AsyncSession = Depends(get_db)) -> AdminStatsOut:
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)

    total_users = (await db.execute(select(func.count(User.id)))).scalar_one()
    active_users_7d = (
        await db.execute(select(func.count(User.id)).where(User.last_login_at >= seven_days_ago))
    ).scalar_one()
    new_registrations_7d = (
        await db.execute(select(func.count(User.id)).where(User.created_at >= seven_days_ago))
    ).scalar_one()
    users_by_plan = dict(
        (await db.execute(select(Subscription.plan, func.count(Subscription.id)).group_by(Subscription.plan))).all()
    )

    total_jobs = (await db.execute(select(func.count(AIJob.id)))).scalar_one()
    jobs_by_status = dict(
        (await db.execute(select(AIJob.status, func.count(AIJob.id)).group_by(AIJob.status))).all()
    )
    jobs_by_type = dict(
        (await db.execute(select(AIJob.job_type, func.count(AIJob.id)).group_by(AIJob.job_type))).all()
    )

    jobs_by_status_str = {(k.value if hasattr(k, "value") else str(k)): v for k, v in jobs_by_status.items()}
    completed_count = jobs_by_status_str.get("completed", 0)
    failed_count = jobs_by_status_str.get("failed", 0)
    settled = completed_count + failed_count
    failure_rate = round(failed_count / settled, 4) if settled else 0.0

    queue_depth = jobs_by_status_str.get("pending", 0) + jobs_by_status_str.get("processing", 0)

    avg_seconds = (
        await db.execute(
            select(func.avg(func.extract("epoch", AIJob.completed_at - AIJob.created_at))).where(
                AIJob.status == JobStatus.completed
            )
        )
    ).scalar_one()

    audit_actions = (
        (await db.execute(select(AuditLog.action).where(AuditLog.action.like("credits_consumed:%"))))
        .scalars()
        .all()
    )
    total_credits_consumed = sum(int(action.rsplit(":", 1)[1]) for action in audit_actions)

    return AdminStatsOut(
        total_users=total_users,
        active_users_7d=active_users_7d,
        new_registrations_7d=new_registrations_7d,
        users_by_plan={(k.value if hasattr(k, "value") else str(k)): v for k, v in users_by_plan.items()},
        total_jobs=total_jobs,
        jobs_by_status=jobs_by_status_str,
        jobs_by_type={(k.value if hasattr(k, "value") else str(k)): v for k, v in jobs_by_type.items()},
        queue_depth=queue_depth,
        failure_rate=failure_rate,
        avg_generation_seconds=round(float(avg_seconds), 2) if avg_seconds is not None else None,
        total_credits_consumed=total_credits_consumed,
    )


@router.get("/audit-logs", response_model=Paginated[AdminAuditLogOut])
async def list_audit_logs(
    db: AsyncSession = Depends(get_db), limit: int = 100, offset: int = 0
) -> Paginated[AdminAuditLogOut]:
    total = (await db.execute(select(func.count(AuditLog.id)))).scalar_one()
    result = await db.execute(
        select(AuditLog, User.email)
        .outerjoin(User, User.id == AuditLog.user_id)
        .order_by(AuditLog.timestamp.desc())
        .limit(min(limit, 500))
        .offset(offset)
    )
    return Paginated(
        total=total,
        items=[
            AdminAuditLogOut(
                id=log.id, user_id=log.user_id, user_email=email, action=log.action, timestamp=log.timestamp
            )
            for log, email in result.all()
        ],
    )


@router.post("/jobs/{job_id}/retry", response_model=AdminJobOut)
async def retry_job(
    job_id: int,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    arq_pool: ArqRedis = Depends(get_arq_pool_dep),
) -> AdminJobOut:
    job = await db.get(AIJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")
    if job.status != JobStatus.failed:
        raise HTTPException(status_code=400, detail="Only failed jobs can be retried.")

    worker_function = WORKER_FUNCTION_BY_JOB_TYPE[job.job_type]
    job.status = JobStatus.pending
    job.error_message = None
    job.completed_at = None
    db.add(AuditLog(user_id=admin.id, action=f"admin_retried_job:{job.job_type.value}:{job.id}"))
    await db.commit()
    await db.refresh(job)

    await arq_pool.enqueue_job(worker_function, job.id)
    logger.info(f"[Admin] retried job_id={job.id} type={job.job_type.value}")

    user_email = (await db.execute(select(User.email).where(User.id == job.user_id))).scalar_one()
    return AdminJobOut(
        id=job.id,
        user_id=job.user_id,
        user_email=user_email,
        job_type=job.job_type,
        provider=job.provider,
        status=job.status,
        created_at=job.created_at,
        completed_at=job.completed_at,
        error_message=job.error_message,
    )
