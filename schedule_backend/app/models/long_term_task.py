from __future__ import annotations

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.utils.uuid_utils import new_uuid


class LongTermTask(TimestampMixin, Base):
    __tablename__ = "long_term_tasks"
    __table_args__ = (
        CheckConstraint("priority BETWEEN 1 AND 5", name="ck_long_term_tasks_priority"),
        CheckConstraint("progress_percent BETWEEN 0 AND 100", name="ck_long_term_tasks_progress_percent"),
        CheckConstraint("status IN ('active','paused','completed','archived')", name="ck_long_term_tasks_status"),
        Index("idx_long_term_tasks_status", "status"),
        Index("idx_long_term_tasks_due_date", "due_date"),
        Index("idx_long_term_tasks_sort", "sort_order"),
        Index("idx_long_term_tasks_sync_id", "sync_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False, default="项目")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_date: Mapped[str | None] = mapped_column(String(10), nullable=True)
    due_date: Mapped[str | None] = mapped_column(String(10), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    progress_percent: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed_at: Mapped[str | None] = mapped_column(String(19), nullable=True)
    sync_id: Mapped[str] = mapped_column(String(36), nullable=False, default=new_uuid)
    sync_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    sync_dirty: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sync_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_synced_at: Mapped[str | None] = mapped_column(String(19), nullable=True)
    updated_by_device_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    subtasks = relationship(
        "LongTermSubtask",
        back_populates="long_task",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="LongTermSubtask.sort_order",
    )


class LongTermSubtask(TimestampMixin, Base):
    __tablename__ = "long_term_subtasks"
    __table_args__ = (
        CheckConstraint("planned_duration_minutes >= 0", name="ck_long_term_subtasks_planned_duration_minutes"),
        CheckConstraint("priority BETWEEN 1 AND 5", name="ck_long_term_subtasks_priority"),
        CheckConstraint("status IN ('pending','in_progress','completed','skipped')", name="ck_long_term_subtasks_status"),
        Index("idx_long_term_subtasks_long_task_id", "long_task_id"),
        Index("idx_long_term_subtasks_status", "status"),
        Index("idx_long_term_subtasks_due_date", "due_date"),
        Index("idx_long_term_subtasks_sort", "long_task_id", "sort_order"),
        Index("idx_long_term_subtasks_sync_id", "sync_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    long_task_id: Mapped[int] = mapped_column(ForeignKey("long_term_tasks.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False, default="项目")
    is_study: Mapped[bool] = mapped_column(nullable=False, default=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    due_date: Mapped[str | None] = mapped_column(String(10), nullable=True)
    planned_duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    linked_daily_task_id: Mapped[int | None] = mapped_column(ForeignKey("daily_tasks.id", ondelete="SET NULL"), nullable=True)
    completed_at: Mapped[str | None] = mapped_column(String(19), nullable=True)
    sync_id: Mapped[str] = mapped_column(String(36), nullable=False, default=new_uuid)
    sync_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    sync_dirty: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sync_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_synced_at: Mapped[str | None] = mapped_column(String(19), nullable=True)
    updated_by_device_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    long_task = relationship("LongTermTask", back_populates="subtasks")
    linked_daily_task = relationship("DailyTask")
