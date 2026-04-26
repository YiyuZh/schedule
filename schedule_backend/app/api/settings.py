from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import DBSessionDep
from app.core.response import ApiResponse, success_response
from app.schemas.settings import (
    BatchSettingsUpdateData,
    BatchSettingsUpdateRequest,
    SettingRead,
    SettingsListData,
    SettingValueUpdate,
)
from app.services.settings_service import SettingsService

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=ApiResponse[SettingsListData])
def list_settings(db: DBSessionDep) -> ApiResponse[SettingsListData]:
    items = SettingsService(db).list_settings()
    return success_response(SettingsListData(settings=items))


@router.get("/{key}", response_model=ApiResponse[SettingRead])
def get_setting(key: str, db: DBSessionDep) -> ApiResponse[SettingRead]:
    item = SettingsService(db).get_setting(key)
    return success_response(item)


@router.put("/{key}", response_model=ApiResponse[SettingRead])
def upsert_setting(key: str, payload: SettingValueUpdate, db: DBSessionDep) -> ApiResponse[SettingRead]:
    item = SettingsService(db).upsert_setting(key, payload)
    return success_response(item)


@router.put("", response_model=ApiResponse[BatchSettingsUpdateData])
def bulk_upsert_settings(payload: BatchSettingsUpdateRequest, db: DBSessionDep) -> ApiResponse[BatchSettingsUpdateData]:
    settings_list, updated_keys = SettingsService(db).bulk_upsert(payload)
    return success_response(BatchSettingsUpdateData(settings=settings_list, updated_keys=updated_keys))
