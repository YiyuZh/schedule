from __future__ import annotations

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.utils.uuid_utils import new_uuid


class Event(TimestampMixin, Base):
    __tablename__ = "events"
    __table_args__ = (
        CheckConstraint("priority BETWEEN 1 AND 5", name="ck_events_priority"),
        CheckConstraint("status IN ('scheduled','completed','cancelled')", name="ck_events_status"),
        CheckConstraint("source IN ('manual','ai','import')", name="ck_events_source"),
        Index("idx_events_event_date", "event_date"),
        Index("idx_events_date_time", "event_date", "start_time", "end_time"),
        Index("idx_events_sync_id", "sync_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False, default="other")
    event_date: Mapped[str] = mapped_column(String(10), nullable=False)
    start_time: Mapped[str | None] = mapped_column(String(5), nullable=True)
    end_time: Mapped[str | None] = mapped_column(String(5), nullable=True)
    location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="scheduled")
    source: Mapped[str] = mapped_column(String(20), nullable=False, default="manual")
    linked_task_id: Mapped[int | None] = mapped_column(ForeignKey("daily_tasks.id", ondelete="SET NULL"), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    sync_id: Mapped[str] = mapped_column(String(36), nullable=False, default=new_uuid)
    sync_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    sync_dirty: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sync_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_synced_at: Mapped[str | None] = mapped_column(String(19), nullable=True)
    updated_by_device_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    linked_task = relationship("DailyTask")
