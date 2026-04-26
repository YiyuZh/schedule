from __future__ import annotations

from pydantic import Field, field_validator, model_validator

from app.schemas.common import BaseSchema
from app.utils.validators import ensure_date_string, ensure_optional_time_range, ensure_time_string, ensure_week_list


class CourseQuery(BaseSchema):
    term_name: str | None = None
    weekday: int | None = Field(default=None, ge=1, le=7)
    batch_id: int | None = None


class CourseBase(BaseSchema):
    course_name: str = Field(min_length=1, max_length=200)
    weekday: int = Field(ge=1, le=7)
    start_time: str
    end_time: str
    location: str | None = Field(default=None, max_length=200)
    teacher: str | None = Field(default=None, max_length=100)
    term_name: str | None = Field(default=None, max_length=100)
    term_start_date: str
    term_end_date: str
    week_list: list[int] = Field(min_length=1)
    color: str | None = Field(default=None, max_length=20)
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("start_time", "end_time")
    @classmethod
    def validate_time(cls, value: str) -> str:
        return ensure_time_string(value)

    @field_validator("term_start_date", "term_end_date")
    @classmethod
    def validate_date(cls, value: str) -> str:
        return ensure_date_string(value)

    @field_validator("week_list")
    @classmethod
    def validate_week_list(cls, value: list[int]) -> list[int]:
        return ensure_week_list(value)

    @model_validator(mode="after")
    def validate_ranges(self) -> "CourseBase":
        ensure_optional_time_range(self.start_time, self.end_time)
        if self.term_start_date > self.term_end_date:
            raise ValueError("term_end_date must be later than or equal to term_start_date")
        return self


class CourseCreate(CourseBase):
    batch_id: int | None = None


class CourseUpdate(CourseBase):
    batch_id: int | None = None


class CourseRead(CourseBase):
    id: int
    batch_id: int | None = None
    week_list_json: str
    created_at: str
    updated_at: str


class CourseListData(BaseSchema):
    items: list[CourseRead]


class CourseDayViewQuery(BaseSchema):
    date: str

    @field_validator("date")
    @classmethod
    def validate_date(cls, value: str) -> str:
        return ensure_date_string(value)


class CourseWeekViewQuery(BaseSchema):
    start_date: str
    end_date: str

    @field_validator("start_date", "end_date")
    @classmethod
    def validate_date(cls, value: str) -> str:
        return ensure_date_string(value)


class CourseOccurrence(BaseSchema):
    course_id: int
    course_name: str
    date: str
    weekday: int
    start_time: str
    end_time: str
    location: str | None = None
    teacher: str | None = None
    term_name: str | None = None
    week_index: int
    batch_id: int | None = None
    color: str | None = None
    notes: str | None = None


class CourseDayViewData(BaseSchema):
    date: str
    items: list[CourseOccurrence]


class CourseWeekViewData(BaseSchema):
    start_date: str
    end_date: str
    items: list[CourseOccurrence]
