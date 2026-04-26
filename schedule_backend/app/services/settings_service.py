from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.response import AppException
from app.models.app_setting import AppSetting
from app.schemas.common import SettingValueTypeEnum
from app.schemas.settings import BatchSettingsUpdateRequest, SettingRead, SettingValueUpdate
from app.utils.json_utils import dumps_json, loads_json


def serialize_setting_value(value: Any, value_type: str) -> str:
    if value_type == SettingValueTypeEnum.bool.value:
        return "true" if bool(value) else "false"
    if value_type == SettingValueTypeEnum.json.value:
        return dumps_json(value)
    if value is None:
        return ""
    return str(value)


def deserialize_setting_value(value: str | None, value_type: str) -> Any:
    if value_type == SettingValueTypeEnum.int.value:
        return int(value) if value not in (None, "") else 0
    if value_type == SettingValueTypeEnum.float.value:
        return float(value) if value not in (None, "") else 0.0
    if value_type == SettingValueTypeEnum.bool.value:
        return str(value).lower() in {"1", "true", "yes", "on"}
    if value_type == SettingValueTypeEnum.json.value:
        return loads_json(value, default=None)
    return value


def build_setting_read(setting: AppSetting) -> SettingRead:
    return SettingRead(
        key=setting.setting_key,
        value=deserialize_setting_value(setting.setting_value, setting.value_type),
        value_type=setting.value_type,
        description=setting.description,
        created_at=setting.created_at,
        updated_at=setting.updated_at,
    )


class SettingsService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_settings(self) -> list[SettingRead]:
        settings = self.db.scalars(select(AppSetting).order_by(AppSetting.setting_key.asc())).all()
        return [build_setting_read(setting) for setting in settings]

    def get_setting_model(self, key: str) -> AppSetting:
        setting = self.db.scalar(select(AppSetting).where(AppSetting.setting_key == key))
        if setting is None:
            raise AppException(f"setting '{key}' not found", code=4041, status_code=404)
        return setting

    def get_setting(self, key: str) -> SettingRead:
        return build_setting_read(self.get_setting_model(key))

    def get_setting_value(self, key: str, default: Any = None) -> Any:
        setting = self.db.scalar(select(AppSetting).where(AppSetting.setting_key == key))
        if setting is None:
            return default
        return deserialize_setting_value(setting.setting_value, setting.value_type)

    def get_settings_map(self, keys: list[str] | None = None) -> dict[str, Any]:
        query = select(AppSetting)
        if keys:
            query = query.where(AppSetting.setting_key.in_(keys))
        settings = self.db.scalars(query).all()
        return {setting.setting_key: deserialize_setting_value(setting.setting_value, setting.value_type) for setting in settings}

    def upsert_setting(self, key: str, payload: SettingValueUpdate) -> SettingRead:
        setting = self.db.scalar(select(AppSetting).where(AppSetting.setting_key == key))
        if setting is None:
            setting = AppSetting(setting_key=key)
            self.db.add(setting)
        setting.setting_value = serialize_setting_value(payload.value, payload.value_type.value)
        setting.value_type = payload.value_type.value
        setting.description = payload.description
        self.db.commit()
        self.db.refresh(setting)
        return build_setting_read(setting)

    def bulk_upsert(self, payload: BatchSettingsUpdateRequest) -> tuple[list[SettingRead], list[str]]:
        updated_keys: list[str] = []
        for item in payload.items:
            self.upsert_setting(
                item.key,
                SettingValueUpdate(value=item.value, value_type=item.value_type, description=item.description),
            )
            updated_keys.append(item.key)
        settings = [self.get_setting(key) for key in updated_keys]
        return settings, updated_keys
