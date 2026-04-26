from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.utils.datetime_utils import now_datetime_str


class Base(DeclarativeBase):
    pass


class CreatedAtMixin:
    created_at: Mapped[str] = mapped_column(String(19), nullable=False, default=now_datetime_str)


class TimestampMixin(CreatedAtMixin):
    updated_at: Mapped[str] = mapped_column(
        String(19),
        nullable=False,
        default=now_datetime_str,
        onupdate=now_datetime_str,
    )
