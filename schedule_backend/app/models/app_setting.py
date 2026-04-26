from __future__ import annotations

from sqlalchemy import Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class AppSetting(TimestampMixin, Base):
    __tablename__ = "app_settings"
    __table_args__ = (
        Index("idx_app_settings_setting_key", "setting_key"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    setting_key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    setting_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    value_type: Mapped[str] = mapped_column(String(20), nullable=False, default="string")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
