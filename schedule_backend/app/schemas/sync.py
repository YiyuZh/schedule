from __future__ import annotations

from enum import Enum

from pydantic import Field, field_validator

from app.schemas.common import BaseSchema


class SyncOperationEnum(str, Enum):
    create = "create"
    update = "update"
    upsert = "upsert"
    delete = "delete"


class SyncConflictStatusEnum(str, Enum):
    open = "open"
    resolved = "resolved"
    ignored = "ignored"


class SyncStatusRead(BaseSchema):
    enabled: bool
    configured: bool
    logged_in: bool
    server_url: str | None = None
    user_email: str | None = None
    device_id: str
    device_name: str
    pending_count: int
    conflict_count: int
    last_push_at: str | None = None
    last_pull_at: str | None = None
    last_error: str | None = None


class SyncConfigUpdate(BaseSchema):
    server_url: str | None = Field(default=None, max_length=500)
    device_name: str | None = Field(default=None, min_length=1, max_length=100)
    enabled: bool = False

    @field_validator("server_url")
    @classmethod
    def normalize_server_url(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip().rstrip("/")
        return value or None


class SyncLoginRequest(BaseSchema):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=1, max_length=500)
    server_url: str | None = Field(default=None, max_length=500)
    device_name: str | None = Field(default=None, min_length=1, max_length=100)

    @field_validator("server_url")
    @classmethod
    def normalize_server_url(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip().rstrip("/")
        return value or None


class SyncRegisterRequest(BaseSchema):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8, max_length=500)
    display_name: str | None = Field(default=None, max_length=100)
    server_url: str | None = Field(default=None, max_length=500)
    device_name: str | None = Field(default=None, min_length=1, max_length=100)

    @field_validator("server_url")
    @classmethod
    def normalize_server_url(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip().rstrip("/")
        return value or None


class SyncRunResult(BaseSchema):
    push_count: int = 0
    pull_count: int = 0
    conflict_count: int = 0
    error_count: int = 0
    message: str = "success"


class SyncConflictRead(BaseSchema):
    id: int
    entity_type: str
    entity_id: str
    status: SyncConflictStatusEnum
    local_payload_json: str | None = None
    remote_payload_json: str | None = None
    created_at: str
    updated_at: str


class SyncConflictListData(BaseSchema):
    items: list[SyncConflictRead]


class SyncConflictResolveRequest(BaseSchema):
    resolution: str = Field(min_length=1, max_length=50)


class SyncConfigRead(BaseSchema):
    status: SyncStatusRead
