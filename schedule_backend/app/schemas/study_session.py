from __future__ import annotations

from pydantic import Field, field_validator, model_validator

from app.schemas.common import BaseSchema, DateRangeQuery, StudySessionSourceEnum
from app.utils.datetime_utils import minutes_between
from app.utils.validators import ensure_date_string, ensure_datetime_order, ensure_datetime_string


class StudySessionQuery(DateRangeQuery):
    category: str | None = None
    task_id: int | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=200)

    @field_validator("start_date", "end_date")
    @classmethod
    def validate_date(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return ensure_date_string(value)


class StudySessionBase(BaseSchema):
    task_id: int | None = None
    task_title_snapshot: str | None = Field(default=None, max_length=200)
    category_snapshot: str | None = Field(default=None, max_length=50)
    session_date: str
    start_at: str
    end_at: str
    duration_minutes: int | None = Field(default=None, ge=0)
    source: StudySessionSourceEnum = StudySessionSourceEnum.manual
    note: str | None = Field(default=None, max_length=2000)

    @field_validator("session_date")
    @classmethod
    def validate_session_date(cls, value: str) -> str:
        return ensure_date_string(value)

    @field_validator("start_at", "end_at")
    @classmethod
    def validate_datetime(cls, value: str) -> str:
        return ensure_datetime_string(value)

    @model_validator(mode="after")
    def validate_range(self) -> "StudySessionBase":
        ensure_datetime_order(self.start_at, self.end_at)
        if self.duration_minutes is None:
            self.duration_minutes = minutes_between(self.start_at, self.end_at)
        return self


class StudySessionCreate(StudySessionBase):
    pass


class StudySessionUpdate(StudySessionBase):
    pass


class StudySessionRead(StudySessionBase):
    id: int
    created_at: str


class StudySessionListData(BaseSchema):
    items: list[StudySessionRead]
    total: int
    page: int
    page_size: int


class StudyStatsOverviewData(BaseSchema):
    today_minutes: int
    week_minutes: int
    month_minutes: int
    total_minutes: int
    query_total_minutes: int


class StudyCategoryStatItem(BaseSchema):
    category: str
    duration_minutes: int


class StudyTaskStatItem(BaseSchema):
    task_id: int | None = None
    task_title: str
    duration_minutes: int


class StudyDayStatItem(BaseSchema):
    session_date: str
    duration_minutes: int


class StudyStatsByCategoryData(BaseSchema):
    items: list[StudyCategoryStatItem]


class StudyStatsByTaskData(BaseSchema):
    items: list[StudyTaskStatItem]


class StudyStatsByDayData(BaseSchema):
    items: list[StudyDayStatItem]


class StudySessionExportQuery(DateRangeQuery):
    format: str = Field(default="json", pattern="^(json|csv)$")

    @field_validator("start_date", "end_date")
    @classmethod
    def validate_date(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return ensure_date_string(value)


class StudySessionExportData(BaseSchema):
    format: str
    file_name: str
    item_count: int
    content: str
