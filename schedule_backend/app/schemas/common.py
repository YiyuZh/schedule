from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.utils.validators import ensure_date_string


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid", populate_by_name=True)


class SettingValueTypeEnum(str, Enum):
    string = "string"
    int = "int"
    bool = "bool"
    json = "json"
    float = "float"


class TimePreferenceEnum(str, Enum):
    none = "none"
    morning = "morning"
    afternoon = "afternoon"
    evening = "evening"
    night = "night"


class TaskStatusEnum(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    skipped = "skipped"


class LongTermTaskStatusEnum(str, Enum):
    active = "active"
    paused = "paused"
    completed = "completed"
    archived = "archived"


class LongTermSubtaskStatusEnum(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    skipped = "skipped"


class TaskSourceEnum(str, Enum):
    manual = "manual"
    template = "template"
    ai = "ai"
    import_ = "import"


class EventStatusEnum(str, Enum):
    scheduled = "scheduled"
    completed = "completed"
    cancelled = "cancelled"


class EventSourceEnum(str, Enum):
    manual = "manual"
    ai = "ai"
    import_ = "import"


class StudySessionSourceEnum(str, Enum):
    timer = "timer"
    manual = "manual"
    import_ = "import"


class TimerStatusEnum(str, Enum):
    running = "running"
    paused = "paused"


class AILogTypeEnum(str, Enum):
    parse = "parse"
    plan = "plan"


class ImportTypeEnum(str, Enum):
    course = "course"
    csv = "csv"
    json = "json"


class ImportStatusEnum(str, Enum):
    success = "success"
    failed = "failed"
    partial = "partial"


class DeleteData(BaseSchema):
    id: int
    deleted: bool = True


class HealthData(BaseSchema):
    status: str = "ok"


class SystemInfoData(BaseSchema):
    app_name: str
    app_version: str
    database_status: str
    database_path: str
    ai_enabled: bool
    current_time: str
    python_version: str


class DateRangeQuery(BaseSchema):
    start_date: str | None = Field(default=None)
    end_date: str | None = Field(default=None)

    @field_validator("start_date", "end_date")
    @classmethod
    def validate_date(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return ensure_date_string(value)
