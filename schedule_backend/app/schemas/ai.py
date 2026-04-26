from __future__ import annotations

from typing import Literal

from pydantic import Field, field_validator, model_validator

from app.schemas.common import AILogTypeEnum, BaseSchema, TimePreferenceEnum
from app.utils.validators import ensure_date_string, ensure_time_string, ensure_week_list


class AIConfigRead(BaseSchema):
    enabled: bool
    provider: str
    model_name: str
    plan_model_name: str
    base_url: str
    has_api_key: bool
    timeout: int
    temperature: float


class AIConfigUpdate(BaseSchema):
    enabled: bool
    provider: str = Field(min_length=1, max_length=50)
    base_url: str = Field(default="", max_length=500)
    api_key: str | None = Field(default=None, max_length=500)
    model_name: str = Field(min_length=1, max_length=100)
    plan_model_name: str = Field(min_length=1, max_length=100)
    timeout: int = Field(default=60, ge=1, le=600)
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)


class AITestConnectionData(BaseSchema):
    ok: bool
    message: str


class AIParseRequest(BaseSchema):
    text: str = Field(min_length=1, max_length=5000)
    date_context: str | None = None

    @field_validator("date_context")
    @classmethod
    def validate_date_context(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return ensure_date_string(value)


class AIAction(BaseSchema):
    action_type: Literal["add_task", "add_event", "add_course", "schedule_task"]
    title: str | None = Field(default=None, max_length=200)
    date: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    category: str | None = Field(default=None, max_length=50)
    is_study: bool | None = None
    planned_duration_minutes: int | None = Field(default=None, ge=0)
    time_preference: TimePreferenceEnum | None = None
    task_id: int | None = None
    weekday: int | None = Field(default=None, ge=1, le=7)
    week_list: list[int] | None = None
    location: str | None = Field(default=None, max_length=200)
    teacher: str | None = Field(default=None, max_length=100)
    term_name: str | None = Field(default=None, max_length=100)
    term_start_date: str | None = None
    term_end_date: str | None = None

    @field_validator(
        "title",
        "date",
        "start_time",
        "end_time",
        "category",
        "location",
        "teacher",
        "term_name",
        "term_start_date",
        "term_end_date",
        mode="before",
    )
    @classmethod
    def blank_to_none(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if isinstance(value, str):
            cleaned = value.strip()
            return cleaned or None
        return value

    @field_validator("date", "term_start_date", "term_end_date")
    @classmethod
    def validate_date(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return ensure_date_string(value)

    @field_validator("start_time", "end_time")
    @classmethod
    def validate_time(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return ensure_time_string(value)

    @field_validator("week_list")
    @classmethod
    def validate_week_list(cls, value: list[int] | None) -> list[int] | None:
        if value is None:
            return value
        return ensure_week_list(value)

    @model_validator(mode="after")
    def validate_action(self) -> "AIAction":
        if self.action_type in {"add_task", "add_event"}:
            if not self.title:
                raise ValueError("title is required for add_task and add_event")
        if self.action_type == "schedule_task" and self.task_id is None:
            raise ValueError("task_id is required for schedule_task")
        return self


class AIParseData(BaseSchema):
    actions: list[AIAction]
    raw_log_id: int


class AIParseApplyRequest(BaseSchema):
    log_id: int
    actions: list[AIAction] = Field(min_length=1)


class AIParseApplyData(BaseSchema):
    created_task_ids: list[int]
    created_event_ids: list[int]
    created_course_ids: list[int]


class AIPlanRequest(BaseSchema):
    date: str
    user_input: str = Field(min_length=1, max_length=5000)
    include_habits: bool = True
    option_count: int = Field(default=3, ge=1, le=3)

    @field_validator("date")
    @classmethod
    def validate_date(cls, value: str) -> str:
        return ensure_date_string(value)


class AIPlanItem(BaseSchema):
    item_type: Literal["event", "task_schedule"]
    task_id: int | None = None
    title: str
    date: str
    start_time: str
    end_time: str
    category: str | None = None

    @field_validator("date")
    @classmethod
    def validate_date(cls, value: str) -> str:
        return ensure_date_string(value)

    @field_validator("start_time", "end_time")
    @classmethod
    def validate_time(cls, value: str) -> str:
        return ensure_time_string(value)

    @model_validator(mode="after")
    def validate_item(self) -> "AIPlanItem":
        if self.item_type == "task_schedule" and self.task_id is None:
            raise ValueError("task_id is required for task_schedule items")
        return self


class AIPlanOption(BaseSchema):
    name: str
    items: list[AIPlanItem]
    reason: str


class AIPlanData(BaseSchema):
    plan_options: list[AIPlanOption]
    raw_log_id: int


class AIPlanApplyRequest(BaseSchema):
    log_id: int
    selected_option_index: int = Field(ge=0)


class AIPlanApplyData(BaseSchema):
    created_event_ids: list[int]
    scheduled_task_ids: list[int]


class AILogQuery(BaseSchema):
    log_type: AILogTypeEnum | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=200)


class AILogRead(BaseSchema):
    id: int
    log_type: AILogTypeEnum
    provider: str | None = None
    model_name: str | None = None
    user_input: str
    context_json: str | None = None
    ai_output_json: str | None = None
    parsed_success: bool
    applied_success: bool
    error_message: str | None = None
    created_at: str


class AILogListData(BaseSchema):
    items: list[AILogRead]
    total: int
    page: int
    page_size: int
