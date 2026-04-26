from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import DBSessionDep
from app.core.response import ApiResponse, success_response
from app.schemas.common import DeleteData
from app.schemas.daily_task import (
    DailyTaskCompleteRequest,
    DailyTaskCreate,
    DailyTaskInheritData,
    DailyTaskInheritRequest,
    DailyTaskListData,
    DailyTaskPatch,
    DailyTaskQuery,
    DailyTaskRead,
    DailyTaskReorderData,
    DailyTaskReorderRequest,
    DailyTaskStatusUpdate,
    DailyTaskSummaryData,
    DailyTaskUpdate,
)
from app.services.daily_task_service import DailyTaskService

router = APIRouter(prefix="/daily-tasks", tags=["daily-tasks"])


@router.get("/summary", response_model=ApiResponse[DailyTaskSummaryData])
def get_summary(date: str, db: DBSessionDep) -> ApiResponse[DailyTaskSummaryData]:
    data = DailyTaskService(db).get_summary(date)
    return success_response(data)


@router.post("/reorder", response_model=ApiResponse[DailyTaskReorderData])
def reorder_tasks(payload: DailyTaskReorderRequest, db: DBSessionDep) -> ApiResponse[DailyTaskReorderData]:
    updated_count = DailyTaskService(db).reorder_tasks(payload)
    return success_response(DailyTaskReorderData(date=payload.date, updated_count=updated_count))


@router.post("/inherit-unfinished", response_model=ApiResponse[DailyTaskInheritData])
def inherit_unfinished(payload: DailyTaskInheritRequest, db: DBSessionDep) -> ApiResponse[DailyTaskInheritData]:
    data = DailyTaskService(db).inherit_unfinished(payload)
    return success_response(data)


@router.get("", response_model=ApiResponse[DailyTaskListData])
def list_tasks(db: DBSessionDep, query: DailyTaskQuery = Depends()) -> ApiResponse[DailyTaskListData]:
    items = DailyTaskService(db).list_tasks(query)
    return success_response(DailyTaskListData(items=items))


@router.post("", response_model=ApiResponse[DailyTaskRead])
def create_task(payload: DailyTaskCreate, db: DBSessionDep) -> ApiResponse[DailyTaskRead]:
    item = DailyTaskService(db).create_task(payload)
    return success_response(item)


@router.get("/{task_id}", response_model=ApiResponse[DailyTaskRead])
def get_task(task_id: int, db: DBSessionDep) -> ApiResponse[DailyTaskRead]:
    item = DailyTaskService(db).get_task(task_id)
    return success_response(item)


@router.put("/{task_id}", response_model=ApiResponse[DailyTaskRead])
def update_task(task_id: int, payload: DailyTaskUpdate, db: DBSessionDep) -> ApiResponse[DailyTaskRead]:
    item = DailyTaskService(db).update_task(task_id, payload)
    return success_response(item)


@router.patch("/{task_id}", response_model=ApiResponse[DailyTaskRead])
def patch_task(task_id: int, payload: DailyTaskPatch, db: DBSessionDep) -> ApiResponse[DailyTaskRead]:
    item = DailyTaskService(db).patch_task(task_id, payload)
    return success_response(item)


@router.delete("/{task_id}", response_model=ApiResponse[DeleteData])
def delete_task(task_id: int, db: DBSessionDep) -> ApiResponse[DeleteData]:
    DailyTaskService(db).delete_task(task_id)
    return success_response(DeleteData(id=task_id))


@router.post("/{task_id}/status", response_model=ApiResponse[DailyTaskRead])
def update_task_status(task_id: int, payload: DailyTaskStatusUpdate, db: DBSessionDep) -> ApiResponse[DailyTaskRead]:
    item = DailyTaskService(db).update_status(task_id, payload.status)
    return success_response(item)


@router.post("/{task_id}/complete", response_model=ApiResponse[DailyTaskRead])
def complete_task(task_id: int, db: DBSessionDep, payload: DailyTaskCompleteRequest | None = None) -> ApiResponse[DailyTaskRead]:
    item = DailyTaskService(db).complete_task(task_id, payload)
    return success_response(item)


@router.post("/{task_id}/uncomplete", response_model=ApiResponse[DailyTaskRead])
def uncomplete_task(task_id: int, db: DBSessionDep) -> ApiResponse[DailyTaskRead]:
    item = DailyTaskService(db).uncomplete_task(task_id)
    return success_response(item)
