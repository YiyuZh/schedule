from __future__ import annotations

from pydantic import Field, field_validator, model_validator

from app.schemas.common import BaseSchema, TaskSourceEnum, TaskStatusEnum
from app.utils.validators import ensure_date_string, ensure_optional_time_range, ensure_priority, ensure_time_string


class DailyTaskQuery(BaseSchema):
    date: str
    status: TaskStatusEnum | None = None
    category: str | None = None
    is_study: bool | None = None
    source: TaskSourceEnum | None = None

    @field_validator("date")
    @classmethod
    def validate_date(cls, value: str) -> str:
        return ensure_date_string(value)


class DailyTaskBase(BaseSchema):
    template_id: int | None = None
    title: str = Field(min_length=1, max_length=200)
    category: str = Field(default="other", min_length=1, max_length=50)
    is_study: bool = False
    task_date: str
    start_time: str | None = None
    end_time: str | None = None
    planned_duration_minutes: int = Field(default=0, ge=0)
    priority: int = Field(default=3)
    status: TaskStatusEnum = TaskStatusEnum.pending
    source: TaskSourceEnum = TaskSourceEnum.manual
    sort_order: int = Field(default=0, ge=0)
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("task_date")
    @classmethod
    def validate_task_date(cls, value: str) -> str:
        return ensure_date_string(value)

    @field_validator("start_time", "end_time")
    @classmethod
    def validate_optional_time(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return ensure_time_string(value)

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, value: int) -> int:
        return ensure_priority(value)

    @model_validator(mode="after")
    def validate_time_range(self) -> "DailyTaskBase":
        ensure_optional_time_range(self.start_time, self.end_time)
        return self


class DailyTaskCreate(DailyTaskBase):
    pass


class DailyTaskUpdate(DailyTaskBase):
    pass


class DailyTaskPatch(BaseSchema):
    template_id: int | None = None
    title: str | None = Field(default=None, min_length=1, max_length=200)
    category: str | None = Field(default=None, min_length=1, max_length=50)
    is_study: bool | None = None
    task_date: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    planned_duration_minutes: int | None = Field(default=None, ge=0)
    priority: int | None = None
    status: TaskStatusEnum | None = None
    source: TaskSourceEnum | None = None
    sort_order: int | None = Field(default=None, ge=0)
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("task_date")
    @classmethod
    def validate_task_date(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return ensure_date_string(value)

    @field_validator("start_time", "end_time")
    @classmethod
    def validate_optional_time(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return ensure_time_string(value)

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, value: int | None) -> int | None:
        if value is None:
            return value
        return ensure_priority(value)

    @model_validator(mode="after")
    def validate_time_range(self) -> "DailyTaskPatch":
        ensure_optional_time_range(self.start_time, self.end_time)
        return self


class DailyTaskStatusUpdate(BaseSchema):
    status: TaskStatusEnum


class DailyTaskCompleteRequest(BaseSchema):
    actual_duration_minutes: int | None = Field(default=None, ge=0)
    sync_study_session: bool = False


class DailyTaskReorderItem(BaseSchema):
    id: int
    sort_order: int = Field(ge=0)


class DailyTaskReorderRequest(BaseSchema):
    date: str
    items: list[DailyTaskReorderItem] = Field(min_length=1)

    @field_validator("date")
    @classmethod
    def validate_date(cls, value: str) -> str:
        return ensure_date_string(value)


class DailyTaskInheritRequest(BaseSchema):
    from_date: str
    to_date: str

    @field_validator("from_date", "to_date")
    @classmethod
    def validate_date(cls, value: str) -> str:
        return ensure_date_string(value)


class DailyTaskRead(DailyTaskBase):
    id: int
    actual_duration_minutes: int
    completed_at: str | None = None
    created_at: str
    updated_at: str


class DailyTaskListData(BaseSchema):
    items: list[DailyTaskRead]


class DailyTaskSummaryData(BaseSchema):
    date: str
    total_count: int
    completed_count: int
    skipped_count: int
    pending_count: int
    running_count: int
    completion_rate: float
    study_task_count: int


class DailyTaskReorderData(BaseSchema):
    date: str
    updated_count: int


class DailyTaskInheritData(BaseSchema):
    from_date: str
    to_date: str
    created_count: int
    skipped_count: int
    task_ids: list[int]
