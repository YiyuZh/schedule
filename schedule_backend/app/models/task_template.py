from __future__ import annotations

from sqlalchemy import Boolean, CheckConstraint, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.utils.uuid_utils import new_uuid


class TaskTemplate(TimestampMixin, Base):
    __tablename__ = "task_templates"
    __table_args__ = (
        CheckConstraint("default_duration_minutes >= 0", name="ck_task_templates_default_duration_minutes"),
        CheckConstraint("priority BETWEEN 1 AND 5", name="ck_task_templates_priority"),
        CheckConstraint(
            "time_preference IN ('none','morning','afternoon','evening','night')",
            name="ck_task_templates_time_preference",
        ),
        Index("idx_task_templates_category", "category"),
        Index("idx_task_templates_enabled", "is_enabled"),
        Index("idx_task_templates_sync_id", "sync_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False, default="other")
    is_study: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    default_duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    default_start_time: Mapped[str | None] = mapped_column(String(5), nullable=True)
    default_end_time: Mapped[str | None] = mapped_column(String(5), nullable=True)
    time_preference: Mapped[str] = mapped_column(String(20), nullable=False, default="none")
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    inherit_unfinished: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    sync_id: Mapped[str] = mapped_column(String(36), nullable=False, default=new_uuid)
    sync_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    sync_dirty: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sync_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_synced_at: Mapped[str | None] = mapped_column(String(19), nullable=True)
    updated_by_device_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    daily_tasks = relationship("DailyTask", back_populates="template")
