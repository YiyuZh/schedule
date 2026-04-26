from __future__ import annotations

from sqlalchemy import CheckConstraint, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, CreatedAtMixin


class ImportBatch(CreatedAtMixin, Base):
    __tablename__ = "import_batches"
    __table_args__ = (
        CheckConstraint("import_type IN ('course','csv','json')", name="ck_import_batches_import_type"),
        CheckConstraint("parsed_count >= 0", name="ck_import_batches_parsed_count"),
        CheckConstraint("status IN ('success','failed','partial')", name="ck_import_batches_status"),
        Index("idx_import_batches_type", "import_type"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    import_type: Mapped[str] = mapped_column(String(20), nullable=False)
    file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    raw_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    parsed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="success")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    courses = relationship("Course", back_populates="batch")
