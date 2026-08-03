from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class GeneratedImage(Base):
    """One output artifact of an AIJob. Named per today-task.md's spec, but
    also holds 3D-model outputs (file_path points at whatever was produced —
    an image, a .glb, etc.) — a job can have multiple rows (e.g. 3 image
    variants)."""

    __tablename__ = "generated_images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    project_id: Mapped[int | None] = mapped_column(
        ForeignKey("projects.id", ondelete="SET NULL"), nullable=True
    )
    job_id: Mapped[int] = mapped_column(ForeignKey("ai_jobs.id", ondelete="CASCADE"), nullable=False)
    prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    label: Mapped[str | None] = mapped_column(String(100), nullable=True)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    preview_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    file_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    job: Mapped["AIJob"] = relationship("AIJob", back_populates="results")
