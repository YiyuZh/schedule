from __future__ import annotations

from typing import Any

from pydantic import Field, field_validator

from app.schemas.common import BaseSchema, SettingValueTypeEnum


AllowedSettingValue = str | int | float | bool | dict[str, Any] | list[Any] | None


class SettingValueUpdate(BaseSchema):
    value: AllowedSettingValue
    value_type: SettingValueTypeEnum = SettingValueTypeEnum.string
    description: str | None = Field(default=None, max_length=500)

    @field_validator("value")
    @classmethod
    def validate_value(cls, value: AllowedSettingValue) -> AllowedSettingValue:
        if value is None:
            return value
        if isinstance(value, (str, int, float, bool, dict, list)):
            return value
        raise ValueError("unsupported setting value type")


class BatchSettingItemUpdate(SettingValueUpdate):
    key: str = Field(min_length=1, max_length=100)


class BatchSettingsUpdateRequest(BaseSchema):
    items: list[BatchSettingItemUpdate] = Field(min_length=1)


class SettingRead(BaseSchema):
    key: str
    value: AllowedSettingValue
    value_type: SettingValueTypeEnum
    description: str | None = None
    created_at: str
    updated_at: str


class SettingsListData(BaseSchema):
    settings: list[SettingRead]


class BatchSettingsUpdateData(BaseSchema):
    settings: list[SettingRead]
    updated_keys: list[str]
