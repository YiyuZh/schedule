from __future__ import annotations

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, CreatedAtMixin
from app.utils.uuid_utils import new_uuid


class StudySession(CreatedAtMixin, Base):
    __tablename__ = "study_sessions"
    __table_args__ = (
        CheckConstraint("duration_minutes >= 0", name="ck_study_sessions_duration_minutes"),
        CheckConstraint("source IN ('timer','manual','import')", name="ck_study_sessions_source"),
        Index("idx_study_sessions_session_date", "session_date"),
        Index("idx_study_sessions_task_id", "task_id"),
        Index("idx_study_sessions_sync_id", "sync_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    task_id: Mapped[int | None] = mapped_column(ForeignKey("daily_tasks.id", ondelete="SET NULL"), nullable=True)
    task_title_snapshot: Mapped[str] = mapped_column(String(200), nullable=False)
    category_snapshot: Mapped[str] = mapped_column(String(50), nullable=False, default="study")
    session_date: Mapped[str] = mapped_column(String(10), nullable=False)
    start_at: Mapped[str] = mapped_column(String(19), nullable=False)
    end_at: Mapped[str] = mapped_column(String(19), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    source: Mapped[str] = mapped_column(String(20), nullable=False, default="timer")
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    sync_id: Mapped[str] = mapped_column(String(36), nullable=False, default=new_uuid)
    sync_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    sync_dirty: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sync_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_synced_at: Mapped[str | None] = mapped_column(String(19), nullable=True)
    updated_by_device_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    task = relationship("DailyTask", back_populates="study_sessions")
