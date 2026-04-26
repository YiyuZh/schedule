from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.response import AppException
from app.models.course import Course
from app.models.import_batch import ImportBatch
from app.schemas.import_schema import (
    CourseImportPayload,
    CourseImportPreviewItem,
    CourseImportResultData,
    CourseImportValidateData,
    ImportBatchRead,
)
from app.utils.json_utils import dumps_json


class ImportService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_batches(self) -> list[ImportBatchRead]:
        batches = self.db.scalars(select(ImportBatch).order_by(ImportBatch.created_at.desc())).all()
        return [ImportBatchRead.model_validate(batch) for batch in batches]

    def get_batch_model(self, batch_id: int) -> ImportBatch:
        batch = self.db.get(ImportBatch, batch_id)
        if batch is None:
            raise AppException("import batch not found", code=4049, status_code=404)
        return batch

    def get_batch(self, batch_id: int) -> ImportBatchRead:
        return ImportBatchRead.model_validate(self.get_batch_model(batch_id))

    def _build_preview_items(self, payload: CourseImportPayload) -> list[CourseImportPreviewItem]:
        return [
            CourseImportPreviewItem(
                course_name=item.course_name,
                weekday=item.weekday,
                start_time=item.start_time,
                end_time=item.end_time,
                location=item.location,
                teacher=item.teacher,
                term_name=payload.semester_name,
                term_start_date=payload.term_start_date,
                term_end_date=payload.term_end_date,
                week_list=item.weeks,
                color=item.color,
                notes=item.notes,
            )
            for item in payload.courses
        ]

    def validate_courses_json(self, payload: CourseImportPayload) -> CourseImportValidateData:
        preview_items = self._build_preview_items(payload)
        return CourseImportValidateData(
            valid=True,
            parsed_count=len(preview_items),
            preview_items=preview_items,
            errors=[],
        )

    def import_courses_json(self, payload: CourseImportPayload) -> CourseImportResultData:
        preview_items = self._build_preview_items(payload)
        batch = ImportBatch(
            import_type="course",
            file_name=payload.file_name,
            raw_content=dumps_json(payload.model_dump()),
            parsed_count=len(preview_items),
            status="success",
            error_message=None,
        )
        self.db.add(batch)
        self.db.flush()

        for item in payload.courses:
            course = Course(
                batch_id=batch.id,
                course_name=item.course_name,
                weekday=item.weekday,
                start_time=item.start_time,
                end_time=item.end_time,
                location=item.location,
                teacher=item.teacher,
                term_name=payload.semester_name,
                term_start_date=payload.term_start_date,
                term_end_date=payload.term_end_date,
                week_list_json=dumps_json(item.weeks),
                color=item.color,
                notes=item.notes,
            )
            self.db.add(course)

        self.db.commit()
        return CourseImportResultData(batch_id=batch.id, parsed_count=len(preview_items), preview_items=preview_items)

    def delete_batch_courses(self, batch_id: int) -> int:
        self.get_batch_model(batch_id)
        courses = self.db.scalars(select(Course).where(Course.batch_id == batch_id)).all()
        deleted_count = len(courses)
        for course in courses:
            self.db.delete(course)
        self.db.commit()
        return deleted_count
