from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import DBSessionDep
from app.core.response import ApiResponse, success_response
from app.schemas.sync import (
    SyncConfigRead,
    SyncConfigUpdate,
    SyncConflictListData,
    SyncConflictRead,
    SyncConflictResolveRequest,
    SyncLoginRequest,
    SyncRegisterRequest,
    SyncRunResult,
    SyncStatusRead,
)
from app.services.sync_service import SyncService

router = APIRouter(prefix="/sync", tags=["sync"])


@router.get("/status", response_model=ApiResponse[SyncStatusRead])
def get_sync_status(db: DBSessionDep) -> ApiResponse[SyncStatusRead]:
    return success_response(SyncService(db).get_status())


@router.post("/config", response_model=ApiResponse[SyncConfigRead])
def save_sync_config(payload: SyncConfigUpdate, db: DBSessionDep) -> ApiResponse[SyncConfigRead]:
    status = SyncService(db).save_config(payload)
    return success_response(SyncConfigRead(status=status))


@router.post("/login", response_model=ApiResponse[SyncConfigRead])
def login_sync(payload: SyncLoginRequest, db: DBSessionDep) -> ApiResponse[SyncConfigRead]:
    status = SyncService(db).login(payload)
    return success_response(SyncConfigRead(status=status))


@router.post("/register", response_model=ApiResponse[SyncConfigRead])
def register_sync(payload: SyncRegisterRequest, db: DBSessionDep) -> ApiResponse[SyncConfigRead]:
    status = SyncService(db).register_account(payload)
    return success_response(SyncConfigRead(status=status))


@router.post("/logout", response_model=ApiResponse[SyncConfigRead])
def logout_sync(db: DBSessionDep) -> ApiResponse[SyncConfigRead]:
    status = SyncService(db).logout()
    return success_response(SyncConfigRead(status=status))


@router.post("/run", response_model=ApiResponse[SyncRunResult])
def run_sync(db: DBSessionDep) -> ApiResponse[SyncRunResult]:
    return success_response(SyncService(db).run())


@router.post("/push", response_model=ApiResponse[SyncRunResult])
def push_sync(db: DBSessionDep) -> ApiResponse[SyncRunResult]:
    return success_response(SyncService(db).push())


@router.post("/pull", response_model=ApiResponse[SyncRunResult])
def pull_sync(db: DBSessionDep) -> ApiResponse[SyncRunResult]:
    return success_response(SyncService(db).pull())


@router.get("/conflicts", response_model=ApiResponse[SyncConflictListData])
def list_sync_conflicts(db: DBSessionDep) -> ApiResponse[SyncConflictListData]:
    return success_response(SyncService(db).list_conflicts())


@router.post("/conflicts/{conflict_id}/resolve", response_model=ApiResponse[SyncConflictRead])
def resolve_sync_conflict(
    conflict_id: int,
    payload: SyncConflictResolveRequest,
    db: DBSessionDep,
) -> ApiResponse[SyncConflictRead]:
    return success_response(SyncService(db).resolve_conflict(conflict_id, payload))
