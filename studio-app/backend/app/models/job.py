import enum
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class JobType(str, enum.Enum):
    image = "image"
    threed = "3d"
    animate = "animate"


class JobStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class AIJob(Base):
    """One generation request. `job_type`/`provider` extend the base spec in
    today-task.md since Studio has multiple generation kinds and providers —
    the worker needs to know which service function to dispatch to."""

    __tablename__ = "ai_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    project_id: Mapped[int | None] = mapped_column(
        ForeignKey("projects.id", ondelete="SET NULL"), nullable=True
    )
    job_type: Mapped[JobType] = mapped_column(
        Enum(JobType, name="job_type", values_callable=lambda e: [m.value for m in e]),
        nullable=False,
    )
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, name="job_status", values_callable=lambda e: [m.value for m in e]),
        default=JobStatus.pending,
        nullable=False,
    )
    prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Full request payload (niche/style/images/provider/motion_type/etc) —
    # kept in Postgres rather than passed through the Redis job queue, since
    # input images are base64 and can be multi-MB; the queue only ever
    # carries a job_id, keeping Redis payloads small on a memory-constrained VPS.
    input_data: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    results: Mapped[list["GeneratedImage"]] = relationship(
        "GeneratedImage", back_populates="job", cascade="all, delete-orphan"
    )
