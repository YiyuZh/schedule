from __future__ import annotations

from pydantic import Field, field_validator, model_validator

from app.schemas.common import BaseSchema, ImportStatusEnum, ImportTypeEnum
from app.utils.validators import ensure_date_string, ensure_optional_time_range, ensure_time_string, ensure_week_list


class ImportBatchQuery(BaseSchema):
    import_type: ImportTypeEnum | None = None


class CourseImportCourseItem(BaseSchema):
    course_name: str = Field(min_length=1, max_length=200)
    weekday: int = Field(ge=1, le=7)
    start_time: str
    end_time: str
    location: str | None = Field(default=None, max_length=200)
    teacher: str | None = Field(default=None, max_length=100)
    weeks: list[int] = Field(min_length=1)
    color: str | None = Field(default=None, max_length=20)
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("start_time", "end_time")
    @classmethod
    def validate_time(cls, value: str) -> str:
        return ensure_time_string(value)

    @field_validator("weeks")
    @classmethod
    def validate_weeks(cls, value: list[int]) -> list[int]:
        return ensure_week_list(value)

    @model_validator(mode="after")
    def validate_time_range(self) -> "CourseImportCourseItem":
        ensure_optional_time_range(self.start_time, self.end_time)
        return self


class CourseImportPayload(BaseSchema):
    file_name: str | None = Field(default=None, max_length=255)
    semester_name: str = Field(min_length=1, max_length=100)
    term_start_date: str
    term_end_date: str
    courses: list[CourseImportCourseItem] = Field(min_length=1)

    @field_validator("term_start_date", "term_end_date")
    @classmethod
    def validate_date(cls, value: str) -> str:
        return ensure_date_string(value)

    @model_validator(mode="after")
    def validate_term_range(self) -> "CourseImportPayload":
        if self.term_start_date > self.term_end_date:
            raise ValueError("term_end_date must be later than or equal to term_start_date")
        return self


class CourseImportPreviewItem(BaseSchema):
    course_name: str
    weekday: int
    start_time: str
    end_time: str
    location: str | None = None
    teacher: str | None = None
    term_name: str
    term_start_date: str
    term_end_date: str
    week_list: list[int]
    color: str | None = None
    notes: str | None = None


class CourseImportValidateData(BaseSchema):
    valid: bool
    parsed_count: int
    preview_items: list[CourseImportPreviewItem]
    errors: list[str]


class CourseImportResultData(BaseSchema):
    batch_id: int
    parsed_count: int
    preview_items: list[CourseImportPreviewItem]


class ImportBatchRead(BaseSchema):
    id: int
    import_type: ImportTypeEnum
    file_name: str | None = None
    raw_content: str | None = None
    parsed_count: int
    status: ImportStatusEnum
    error_message: str | None = None
    created_at: str


class ImportBatchListData(BaseSchema):
    items: list[ImportBatchRead]


class ImportBatchDeleteCoursesData(BaseSchema):
    batch_id: int
    deleted_count: int
