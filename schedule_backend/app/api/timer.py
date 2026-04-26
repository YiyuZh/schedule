from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import DBSessionDep
from app.core.response import ApiResponse, success_response
from app.schemas.timer import TimerCurrentData, TimerOperationData, TimerStartRequest, TimerStopRequest, TimerSwitchRequest
from app.services.timer_service import TimerService

router = APIRouter(prefix="/timer", tags=["timer"])


@router.get("/current", response_model=ApiResponse[TimerCurrentData])
def get_current_timer(db: DBSessionDep) -> ApiResponse[TimerCurrentData]:
    data = TimerService(db).get_current_timer()
    return success_response(data)


@router.post("/start", response_model=ApiResponse[TimerOperationData])
def start_timer(payload: TimerStartRequest, db: DBSessionDep) -> ApiResponse[TimerOperationData]:
    data = TimerService(db).start_timer(payload)
    return success_response(data)


@router.post("/pause", response_model=ApiResponse[TimerOperationData])
def pause_timer(db: DBSessionDep) -> ApiResponse[TimerOperationData]:
    data = TimerService(db).pause_timer()
    return success_response(data)


@router.post("/resume", response_model=ApiResponse[TimerOperationData])
def resume_timer(db: DBSessionDep) -> ApiResponse[TimerOperationData]:
    data = TimerService(db).resume_timer()
    return success_response(data)


@router.post("/stop", response_model=ApiResponse[TimerOperationData])
def stop_timer(payload: TimerStopRequest, db: DBSessionDep) -> ApiResponse[TimerOperationData]:
    data = TimerService(db).stop_timer(payload)
    return success_response(data)


@router.post("/discard", response_model=ApiResponse[TimerOperationData])
def discard_timer(db: DBSessionDep) -> ApiResponse[TimerOperationData]:
    data = TimerService(db).discard_timer()
    return success_response(data)


@router.post("/switch", response_model=ApiResponse[TimerOperationData])
def switch_timer(payload: TimerSwitchRequest, db: DBSessionDep) -> ApiResponse[TimerOperationData]:
    data = TimerService(db).switch_timer(payload)
    return success_response(data)
