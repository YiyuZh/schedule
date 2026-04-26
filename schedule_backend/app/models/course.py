from __future__ import annotations

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.utils.json_utils import loads_json
from app.utils.uuid_utils import new_uuid


class Course(TimestampMixin, Base):
    __tablename__ = "courses"
    __table_args__ = (
        CheckConstraint("weekday BETWEEN 1 AND 7", name="ck_courses_weekday"),
        Index("idx_courses_weekday", "weekday"),
        Index("idx_courses_term_name", "term_name"),
        Index("idx_courses_batch_id", "batch_id"),
        Index("idx_courses_sync_id", "sync_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    batch_id: Mapped[int | None] = mapped_column(ForeignKey("import_batches.id", ondelete="SET NULL"), nullable=True)
    course_name: Mapped[str] = mapped_column(String(200), nullable=False)
    weekday: Mapped[int] = mapped_column(Integer, nullable=False)
    start_time: Mapped[str] = mapped_column(String(5), nullable=False)
    end_time: Mapped[str] = mapped_column(String(5), nullable=False)
    location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    teacher: Mapped[str | None] = mapped_column(String(100), nullable=True)
    term_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    term_start_date: Mapped[str] = mapped_column(String(10), nullable=False)
    term_end_date: Mapped[str] = mapped_column(String(10), nullable=False)
    week_list_json: Mapped[str] = mapped_column(Text, nullable=False)
    color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    sync_id: Mapped[str] = mapped_column(String(36), nullable=False, default=new_uuid)
    sync_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    sync_dirty: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sync_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_synced_at: Mapped[str | None] = mapped_column(String(19), nullable=True)
    updated_by_device_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    batch = relationship("ImportBatch", back_populates="courses")

    @property
    def week_list(self) -> list[int]:
        return loads_json(self.week_list_json, default=[])
