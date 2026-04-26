from __future__ import annotations

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class TimerState(TimestampMixin, Base):
    __tablename__ = "timer_state"
    __table_args__ = (
        CheckConstraint("accumulated_seconds >= 0", name="ck_timer_state_accumulated_seconds"),
        CheckConstraint("status IN ('running','paused')", name="ck_timer_state_status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("daily_tasks.id", ondelete="CASCADE"), nullable=False)
    started_at: Mapped[str] = mapped_column(String(19), nullable=False)
    paused_at: Mapped[str | None] = mapped_column(String(19), nullable=True)
    accumulated_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="running")

    task = relationship("DailyTask", back_populates="timer_state")
