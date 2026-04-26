from __future__ import annotations

from pydantic import Field, field_validator, model_validator

from app.schemas.common import BaseSchema, TimePreferenceEnum
from app.utils.validators import ensure_optional_time_range, ensure_priority, ensure_time_string


class TaskTemplateQuery(BaseSchema):
    enabled: bool | None = None
    category: str | None = None
    is_study: bool | None = None


class TaskTemplateBase(BaseSchema):
    title: str = Field(min_length=1, max_length=200)
    category: str = Field(default="other", min_length=1, max_length=50)
    is_study: bool = False
    default_duration_minutes: int = Field(default=30, ge=0)
    default_start_time: str | None = Field(default=None)
    default_end_time: str | None = Field(default=None)
    time_preference: TimePreferenceEnum = TimePreferenceEnum.none
    priority: int = Field(default=3)
    is_enabled: bool = True
    inherit_unfinished: bool = False
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("default_start_time", "default_end_time")
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
    def validate_time_range(self) -> "TaskTemplateBase":
        ensure_optional_time_range(self.default_start_time, self.default_end_time)
        return self


class TaskTemplateCreate(TaskTemplateBase):
    pass


class TaskTemplateUpdate(TaskTemplateBase):
    pass


class TaskTemplatePatch(BaseSchema):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    category: str | None = Field(default=None, min_length=1, max_length=50)
    is_study: bool | None = None
    default_duration_minutes: int | None = Field(default=None, ge=0)
    default_start_time: str | None = None
    default_end_time: str | None = None
    time_preference: TimePreferenceEnum | None = None
    priority: int | None = None
    is_enabled: bool | None = None
    inherit_unfinished: bool | None = None
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("default_start_time", "default_end_time")
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
    def validate_time_range(self) -> "TaskTemplatePatch":
        ensure_optional_time_range(self.default_start_time, self.default_end_time)
        return self


class TaskTemplateToggleRequest(BaseSchema):
    is_enabled: bool


class TaskTemplateRefreshRequest(BaseSchema):
    date: str | None = None


class TaskTemplateRead(TaskTemplateBase):
    id: int
    created_at: str
    updated_at: str


class TaskTemplateListData(BaseSchema):
    items: list[TaskTemplateRead]


class TaskTemplateRefreshData(BaseSchema):
    date: str
    created_count: int
    skipped_count: int
    task_ids: list[int]
