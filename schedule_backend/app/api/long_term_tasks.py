from __future__ import annotations

from app.api.deps import DBSessionDep
from app.core.response import ApiResponse, success_response
from app.schemas.common import DeleteData
from app.schemas.long_term_task import (
    LongTermSubtaskCreate,
    LongTermSubtaskCreateDailyTaskData,
    LongTermSubtaskCreateDailyTaskRequest,
    LongTermSubtaskListData,
    LongTermSubtaskPatch,
    LongTermSubtaskRead,
    LongTermSubtaskUpdate,
    LongTermTaskCreate,
    LongTermTaskListData,
    LongTermTaskPatch,
    LongTermTaskQuery,
    LongTermTaskRead,
    LongTermTaskStatusUpdate,
    LongTermTaskUpdate,
)
from app.services.long_term_task_service import LongTermTaskService
from fastapi import APIRouter, Depends

router = APIRouter(tags=["long-term-tasks"])


@router.get("/long-term-tasks", response_model=ApiResponse[LongTermTaskListData])
def list_long_term_tasks(
    db: DBSessionDep,
    query: LongTermTaskQuery = Depends(),
) -> ApiResponse[LongTermTaskListData]:
    data = LongTermTaskService(db).list_tasks(query)
    return success_response(data)


@router.post("/long-term-tasks", response_model=ApiResponse[LongTermTaskRead])
def create_long_term_task(payload: LongTermTaskCreate, db: DBSessionDep) -> ApiResponse[LongTermTaskRead]:
    item = LongTermTaskService(db).create_task(payload)
    return success_response(item)


@router.get("/long-term-tasks/{task_id}", response_model=ApiResponse[LongTermTaskRead])
def get_long_term_task(task_id: int, db: DBSessionDep) -> ApiResponse[LongTermTaskRead]:
    item = LongTermTaskService(db).get_task(task_id)
    return success_response(item)


@router.put("/long-term-tasks/{task_id}", response_model=ApiResponse[LongTermTaskRead])
def update_long_term_task(
    task_id: int,
    payload: LongTermTaskUpdate,
    db: DBSessionDep,
) -> ApiResponse[LongTermTaskRead]:
    item = LongTermTaskService(db).update_task(task_id, payload)
    return success_response(item)


@router.patch("/long-term-tasks/{task_id}", response_model=ApiResponse[LongTermTaskRead])
def patch_long_term_task(
    task_id: int,
    payload: LongTermTaskPatch,
    db: DBSessionDep,
) -> ApiResponse[LongTermTaskRead]:
    item = LongTermTaskService(db).patch_task(task_id, payload)
    return success_response(item)


@router.delete("/long-term-tasks/{task_id}", response_model=ApiResponse[DeleteData])
def delete_long_term_task(task_id: int, db: DBSessionDep) -> ApiResponse[DeleteData]:
    LongTermTaskService(db).delete_task(task_id)
    return success_response(DeleteData(id=task_id))


@router.post("/long-term-tasks/{task_id}/status", response_model=ApiResponse[LongTermTaskRead])
def update_long_term_task_status(
    task_id: int,
    payload: LongTermTaskStatusUpdate,
    db: DBSessionDep,
) -> ApiResponse[LongTermTaskRead]:
    item = LongTermTaskService(db).update_task_status(task_id, payload.status)
    return success_response(item)


@router.get("/long-term-tasks/{task_id}/subtasks", response_model=ApiResponse[LongTermSubtaskListData])
def list_long_term_subtasks(task_id: int, db: DBSessionDep) -> ApiResponse[LongTermSubtaskListData]:
    data = LongTermTaskService(db).list_subtasks(task_id)
    return success_response(data)


@router.post("/long-term-tasks/{task_id}/subtasks", response_model=ApiResponse[LongTermSubtaskRead])
def create_long_term_subtask(
    task_id: int,
    payload: LongTermSubtaskCreate,
    db: DBSessionDep,
) -> ApiResponse[LongTermSubtaskRead]:
    item = LongTermTaskService(db).create_subtask(task_id, payload)
    return success_response(item)


@router.put("/long-term-subtasks/{subtask_id}", response_model=ApiResponse[LongTermSubtaskRead])
def update_long_term_subtask(
    subtask_id: int,
    payload: LongTermSubtaskUpdate,
    db: DBSessionDep,
) -> ApiResponse[LongTermSubtaskRead]:
    item = LongTermTaskService(db).update_subtask(subtask_id, payload)
    return success_response(item)


@router.patch("/long-term-subtasks/{subtask_id}", response_model=ApiResponse[LongTermSubtaskRead])
def patch_long_term_subtask(
    subtask_id: int,
    payload: LongTermSubtaskPatch,
    db: DBSessionDep,
) -> ApiResponse[LongTermSubtaskRead]:
    item = LongTermTaskService(db).patch_subtask(subtask_id, payload)
    return success_response(item)


@router.delete("/long-term-subtasks/{subtask_id}", response_model=ApiResponse[DeleteData])
def delete_long_term_subtask(subtask_id: int, db: DBSessionDep) -> ApiResponse[DeleteData]:
    LongTermTaskService(db).delete_subtask(subtask_id)
    return success_response(DeleteData(id=subtask_id))


@router.post("/long-term-subtasks/{subtask_id}/complete", response_model=ApiResponse[LongTermSubtaskRead])
def complete_long_term_subtask(subtask_id: int, db: DBSessionDep) -> ApiResponse[LongTermSubtaskRead]:
    item = LongTermTaskService(db).complete_subtask(subtask_id)
    return success_response(item)


@router.post("/long-term-subtasks/{subtask_id}/uncomplete", response_model=ApiResponse[LongTermSubtaskRead])
def uncomplete_long_term_subtask(subtask_id: int, db: DBSessionDep) -> ApiResponse[LongTermSubtaskRead]:
    item = LongTermTaskService(db).uncomplete_subtask(subtask_id)
    return success_response(item)


@router.post("/long-term-subtasks/{subtask_id}/create-daily-task", response_model=ApiResponse[LongTermSubtaskCreateDailyTaskData])
def create_daily_task_from_long_term_subtask(
    subtask_id: int,
    db: DBSessionDep,
    payload: LongTermSubtaskCreateDailyTaskRequest | None = None,
) -> ApiResponse[LongTermSubtaskCreateDailyTaskData]:
    data = LongTermTaskService(db).create_daily_task_from_subtask(subtask_id, payload)
    return success_response(data)
