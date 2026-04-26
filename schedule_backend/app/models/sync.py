from __future__ import annotations

from sqlalchemy import Boolean, CheckConstraint, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin
from app.utils.datetime_utils import now_datetime_str
from app.utils.uuid_utils import new_uuid


class SyncState(TimestampMixin, Base):
    __tablename__ = "sync_state"
    __table_args__ = (
        Index("idx_sync_state_device_id", "device_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    server_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    user_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    device_id: Mapped[str] = mapped_column(String(64), nullable=False, default=new_uuid)
    device_name: Mapped[str] = mapped_column(String(100), nullable=False, default="Windows Desktop")
    access_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    refresh_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    latest_change_id: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_push_at: Mapped[str | None] = mapped_column(String(19), nullable=True)
    last_pull_at: Mapped[str | None] = mapped_column(String(19), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)


class SyncQueue(TimestampMixin, Base):
    __tablename__ = "sync_queue"
    __table_args__ = (
        CheckConstraint("operation IN ('create','update','upsert','delete')", name="ck_sync_queue_operation"),
        Index("idx_sync_queue_entity", "entity_type", "entity_id"),
        Index("idx_sync_queue_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False)
    operation: Mapped[str] = mapped_column(String(20), nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    base_version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)


class SyncConflict(TimestampMixin, Base):
    __tablename__ = "sync_conflicts"
    __table_args__ = (
        CheckConstraint("status IN ('open','resolved','ignored')", name="ck_sync_conflicts_status"),
        Index("idx_sync_conflicts_entity", "entity_type", "entity_id"),
        Index("idx_sync_conflicts_status", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False)
    local_payload_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    remote_payload_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    base_version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    remote_version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="open")
    resolution: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[str | None] = mapped_column(String(19), nullable=True)

    def mark_resolved(self, resolution: str) -> None:
        self.status = "resolved"
        self.resolution = resolution
        self.resolved_at = now_datetime_str()
