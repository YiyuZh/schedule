from __future__ import annotations

from sqlalchemy import CheckConstraint, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin


class AILog(CreatedAtMixin, Base):
    __tablename__ = "ai_logs"
    __table_args__ = (
        CheckConstraint("log_type IN ('parse','plan')", name="ck_ai_logs_log_type"),
        Index("idx_ai_logs_type", "log_type"),
        Index("idx_ai_logs_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    log_type: Mapped[str] = mapped_column(String(20), nullable=False)
    provider: Mapped[str | None] = mapped_column(String(50), nullable=True)
    model_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    user_input: Mapped[str] = mapped_column(Text, nullable=False)
    context_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_output_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    parsed_success: Mapped[bool] = mapped_column(nullable=False, default=False)
    applied_success: Mapped[bool] = mapped_column(nullable=False, default=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
