from __future__ import annotations

import platform

from fastapi import APIRouter

from app.api.deps import DBSessionDep
from app.core.config import settings
from app.core.database import check_database_connection
from app.core.response import ApiResponse, success_response
from app.schemas.common import HealthData, SystemInfoData
from app.services.settings_service import SettingsService
from app.utils.datetime_utils import now_datetime_str

router = APIRouter(tags=["system"])


@router.get("/health", response_model=ApiResponse[HealthData])
def health_check() -> ApiResponse[HealthData]:
    return success_response(HealthData())


@router.get("/system/info", response_model=ApiResponse[SystemInfoData])
def get_system_info(db: DBSessionDep) -> ApiResponse[SystemInfoData]:
    database_status = "ok"
    try:
        check_database_connection()
    except Exception:
        database_status = "error"

    ai_enabled = bool(SettingsService(db).get_setting_value("ai_enabled", False))
    data = SystemInfoData(
        app_name=settings.app_name,
        app_version=settings.app_version,
        database_status=database_status,
        database_path=str(settings.database_path),
        ai_enabled=ai_enabled,
        current_time=now_datetime_str(),
        python_version=platform.python_version(),
    )
    return success_response(data)
