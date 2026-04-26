from __future__ import annotations

from pydantic import Field, field_validator, model_validator

from app.schemas.common import BaseSchema, LongTermSubtaskStatusEnum, LongTermTaskStatusEnum
from app.schemas.daily_task import DailyTaskRead
from app.utils.validators import ensure_date_string, ensure_priority


class LongTermTaskQuery(BaseSchema):
    status: LongTermTaskStatusEnum | None = None
    keyword: str | None = Field(default=None, max_length=100)


class LongTermTaskBase(BaseSchema):
    title: str = Field(min_length=1, max_length=200)
    category: str = Field(default="项目", min_length=1, max_length=50)
    description: str | None = Field(default=None, max_length=4000)
    start_date: str | None = None
    due_date: str | None = None
    status: LongTermTaskStatusEnum = LongTermTaskStatusEnum.active
    priority: int = Field(default=3)
    sort_order: int = Field(default=0, ge=0)

    @field_validator("start_date", "due_date")
    @classmethod
    def validate_date(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return ensure_date_string(value)

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, value: int) -> int:
        return ensure_priority(value)

    @model_validator(mode="after")
    def validate_date_range(self) -> "LongTermTaskBase":
        if self.start_date and self.due_date and self.start_date > self.due_date:
            raise ValueError("start_date must be earlier than or equal to due_date")
        return self


class LongTermTaskCreate(LongTermTaskBase):
    pass


class LongTermTaskUpdate(LongTermTaskBase):
    pass


class LongTermTaskPatch(BaseSchema):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    category: str | None = Field(default=None, min_length=1, max_length=50)
    description: str | None = Field(default=None, max_length=4000)
    start_date: str | None = None
    due_date: str | None = None
    status: LongTermTaskStatusEnum | None = None
    priority: int | None = None
    sort_order: int | None = Field(default=None, ge=0)

    @field_validator("start_date", "due_date")
    @classmethod
    def validate_date(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return ensure_date_string(value)

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, value: int | None) -> int | None:
        if value is None:
            return value
        return ensure_priority(value)

    @model_validator(mode="after")
    def validate_date_range(self) -> "LongTermTaskPatch":
        if self.start_date and self.due_date and self.start_date > self.due_date:
            raise ValueError("start_date must be earlier than or equal to due_date")
        return self


class LongTermTaskStatusUpdate(BaseSchema):
    status: LongTermTaskStatusEnum


class LongTermTaskRead(LongTermTaskBase):
    id: int
    progress_percent: int
    completed_at: str | None = None
    created_at: str
    updated_at: str
    subtask_count: int = 0
    completed_subtask_count: int = 0


class LongTermTaskListData(BaseSchema):
    items: list[LongTermTaskRead]


class LongTermSubtaskBase(BaseSchema):
    title: str = Field(min_length=1, max_length=200)
    category: str = Field(default="项目", min_length=1, max_length=50)
    is_study: bool = False
    description: str | None = Field(default=None, max_length=4000)
    due_date: str | None = None
    planned_duration_minutes: int = Field(default=30, ge=0)
    status: LongTermSubtaskStatusEnum = LongTermSubtaskStatusEnum.pending
    priority: int = Field(default=3)
    sort_order: int = Field(default=0, ge=0)

    @field_validator("due_date")
    @classmethod
    def validate_date(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return ensure_date_string(value)

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, value: int) -> int:
        return ensure_priority(value)


class LongTermSubtaskCreate(LongTermSubtaskBase):
    pass


class LongTermSubtaskUpdate(LongTermSubtaskBase):
    pass


class LongTermSubtaskPatch(BaseSchema):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    category: str | None = Field(default=None, min_length=1, max_length=50)
    is_study: bool | None = None
    description: str | None = Field(default=None, max_length=4000)
    due_date: str | None = None
    planned_duration_minutes: int | None = Field(default=None, ge=0)
    status: LongTermSubtaskStatusEnum | None = None
    priority: int | None = None
    sort_order: int | None = Field(default=None, ge=0)

    @field_validator("due_date")
    @classmethod
    def validate_date(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return ensure_date_string(value)

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, value: int | None) -> int | None:
        if value is None:
            return value
        return ensure_priority(value)


class LongTermSubtaskRead(LongTermSubtaskBase):
    id: int
    long_task_id: int
    linked_daily_task_id: int | None = None
    completed_at: str | None = None
    created_at: str
    updated_at: str


class LongTermSubtaskListData(BaseSchema):
    items: list[LongTermSubtaskRead]


class LongTermSubtaskCreateDailyTaskRequest(BaseSchema):
    task_date: str | None = None

    @field_validator("task_date")
    @classmethod
    def validate_date(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return ensure_date_string(value)


class LongTermSubtaskCreateDailyTaskData(BaseSchema):
    subtask: LongTermSubtaskRead
    daily_task: DailyTaskRead
