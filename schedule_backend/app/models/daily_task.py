from __future__ import annotations

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.utils.uuid_utils import new_uuid


class DailyTask(TimestampMixin, Base):
    __tablename__ = "daily_tasks"
    __table_args__ = (
        UniqueConstraint("template_id", "task_date", name="uq_daily_tasks_template_date"),
        CheckConstraint("planned_duration_minutes >= 0", name="ck_daily_tasks_planned_duration_minutes"),
        CheckConstraint("actual_duration_minutes >= 0", name="ck_daily_tasks_actual_duration_minutes"),
        CheckConstraint("priority BETWEEN 1 AND 5", name="ck_daily_tasks_priority"),
        CheckConstraint("status IN ('pending','running','completed','skipped')", name="ck_daily_tasks_status"),
        CheckConstraint("source IN ('manual','template','ai','import')", name="ck_daily_tasks_source"),
        Index("idx_daily_tasks_task_date", "task_date"),
        Index("idx_daily_tasks_status", "status"),
        Index("idx_daily_tasks_template_id", "template_id"),
        Index("idx_daily_tasks_date_sort", "task_date", "sort_order"),
        Index("idx_daily_tasks_sync_id", "sync_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    template_id: Mapped[int | None] = mapped_column(ForeignKey("task_templates.id", ondelete="SET NULL"), nullable=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False, default="other")
    is_study: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    task_date: Mapped[str] = mapped_column(String(10), nullable=False)
    start_time: Mapped[str | None] = mapped_column(String(5), nullable=True)
    end_time: Mapped[str | None] = mapped_column(String(5), nullable=True)
    planned_duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    actual_duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    source: Mapped[str] = mapped_column(String(20), nullable=False, default="manual")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    completed_at: Mapped[str | None] = mapped_column(String(19), nullable=True)
    sync_id: Mapped[str] = mapped_column(String(36), nullable=False, default=new_uuid)
    sync_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    sync_dirty: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sync_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_synced_at: Mapped[str | None] = mapped_column(String(19), nullable=True)
    updated_by_device_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    template = relationship("TaskTemplate", back_populates="daily_tasks")
    study_sessions = relationship("StudySession", back_populates="task")
    timer_state = relationship("TimerState", back_populates="task", uselist=False)
