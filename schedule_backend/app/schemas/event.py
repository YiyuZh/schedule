from __future__ import annotations

from pydantic import Field, field_validator, model_validator

from app.schemas.common import BaseSchema, EventSourceEnum, EventStatusEnum
from app.utils.validators import ensure_date_string, ensure_optional_time_range, ensure_priority, ensure_time_string


class EventQuery(BaseSchema):
    date: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    category: str | None = None
    status: EventStatusEnum | None = None

    @field_validator("date", "start_date", "end_date")
    @classmethod
    def validate_date(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return ensure_date_string(value)


class EventBase(BaseSchema):
    title: str = Field(min_length=1, max_length=200)
    category: str = Field(default="other", min_length=1, max_length=50)
    event_date: str
    start_time: str | None = None
    end_time: str | None = None
    location: str | None = Field(default=None, max_length=200)
    priority: int = Field(default=3)
    status: EventStatusEnum = EventStatusEnum.scheduled
    source: EventSourceEnum = EventSourceEnum.manual
    linked_task_id: int | None = None
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("event_date")
    @classmethod
    def validate_event_date(cls, value: str) -> str:
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
    def validate_time_range(self) -> "EventBase":
        ensure_optional_time_range(self.start_time, self.end_time)
        return self


class EventCreate(EventBase):
    pass


class EventUpdate(EventBase):
    pass


class EventPatch(BaseSchema):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    category: str | None = Field(default=None, min_length=1, max_length=50)
    event_date: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    location: str | None = Field(default=None, max_length=200)
    priority: int | None = None
    status: EventStatusEnum | None = None
    source: EventSourceEnum | None = None
    linked_task_id: int | None = None
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("event_date")
    @classmethod
    def validate_event_date(cls, value: str | None) -> str | None:
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
    def validate_time_range(self) -> "EventPatch":
        ensure_optional_time_range(self.start_time, self.end_time)
        return self


class EventStatusUpdate(BaseSchema):
    status: EventStatusEnum


class EventConflictCheckRequest(BaseSchema):
    event_date: str
    start_time: str
    end_time: str
    exclude_event_id: int | None = None

    @field_validator("event_date")
    @classmethod
    def validate_event_date(cls, value: str) -> str:
        return ensure_date_string(value)

    @field_validator("start_time", "end_time")
    @classmethod
    def validate_time(cls, value: str) -> str:
        return ensure_time_string(value)

    @model_validator(mode="after")
    def validate_time_range(self) -> "EventConflictCheckRequest":
        ensure_optional_time_range(self.start_time, self.end_time)
        return self


class EventTimelineQuery(BaseSchema):
    date: str

    @field_validator("date")
    @classmethod
    def validate_date(cls, value: str) -> str:
        return ensure_date_string(value)


class ConflictItem(BaseSchema):
    item_type: str
    id: int | None = None
    title: str
    date: str
    start_time: str | None = None
    end_time: str | None = None
    source: str
    detail: str | None = None


class EventConflictCheckData(BaseSchema):
    has_conflict: bool
    conflict_items: list[ConflictItem]


class TimelineItem(BaseSchema):
    item_type: str
    id: int | None = None
    title: str
    date: str
    start_time: str
    end_time: str
    source: str
    category: str | None = None
    detail: str | None = None


class TimelineData(BaseSchema):
    date: str
    items: list[TimelineItem]


class EventRead(EventBase):
    id: int
    created_at: str
    updated_at: str


class EventListData(BaseSchema):
    items: list[EventRead]
