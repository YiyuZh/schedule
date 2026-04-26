from __future__ import annotations

from pydantic import Field

from app.schemas.common import BaseSchema, TimerStatusEnum


class TimerStartRequest(BaseSchema):
    task_id: int


class TimerStopRequest(BaseSchema):
    note: str | None = Field(default=None, max_length=2000)


class TimerSwitchRequest(BaseSchema):
    new_task_id: int
    save_current_session: bool = True
    note: str | None = Field(default=None, max_length=2000)


class TimerCurrentData(BaseSchema):
    has_active_timer: bool
    task_id: int | None = None
    task_title: str | None = None
    started_at: str | None = None
    paused_at: str | None = None
    accumulated_seconds: int = 0
    status: TimerStatusEnum | None = None
    created_at: str | None = None
    updated_at: str | None = None


class TimerOperationData(BaseSchema):
    timer: TimerCurrentData
    generated_session_id: int | None = None
    message: str | None = None
