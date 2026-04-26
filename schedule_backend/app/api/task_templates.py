from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import DBSessionDep
from app.core.response import ApiResponse, success_response
from app.schemas.common import DeleteData
from app.schemas.task_template import (
    TaskTemplateCreate,
    TaskTemplateListData,
    TaskTemplatePatch,
    TaskTemplateQuery,
    TaskTemplateRead,
    TaskTemplateRefreshData,
    TaskTemplateRefreshRequest,
    TaskTemplateToggleRequest,
    TaskTemplateUpdate,
)
from app.services.task_template_service import TaskTemplateService

router = APIRouter(prefix="/task-templates", tags=["task-templates"])


@router.post("/refresh-today", response_model=ApiResponse[TaskTemplateRefreshData])
def refresh_today(payload: TaskTemplateRefreshRequest, db: DBSessionDep) -> ApiResponse[TaskTemplateRefreshData]:
    data = TaskTemplateService(db).refresh_today(payload.date)
    return success_response(data)


@router.get("", response_model=ApiResponse[TaskTemplateListData])
def list_templates(db: DBSessionDep, query: TaskTemplateQuery = Depends()) -> ApiResponse[TaskTemplateListData]:
    items = TaskTemplateService(db).list_templates(query)
    return success_response(TaskTemplateListData(items=items))


@router.post("", response_model=ApiResponse[TaskTemplateRead])
def create_template(payload: TaskTemplateCreate, db: DBSessionDep) -> ApiResponse[TaskTemplateRead]:
    item = TaskTemplateService(db).create_template(payload)
    return success_response(item)


@router.get("/{template_id}", response_model=ApiResponse[TaskTemplateRead])
def get_template(template_id: int, db: DBSessionDep) -> ApiResponse[TaskTemplateRead]:
    item = TaskTemplateService(db).get_template(template_id)
    return success_response(item)


@router.put("/{template_id}", response_model=ApiResponse[TaskTemplateRead])
def update_template(template_id: int, payload: TaskTemplateUpdate, db: DBSessionDep) -> ApiResponse[TaskTemplateRead]:
    item = TaskTemplateService(db).update_template(template_id, payload)
    return success_response(item)


@router.patch("/{template_id}", response_model=ApiResponse[TaskTemplateRead])
def patch_template(template_id: int, payload: TaskTemplatePatch, db: DBSessionDep) -> ApiResponse[TaskTemplateRead]:
    item = TaskTemplateService(db).patch_template(template_id, payload)
    return success_response(item)


@router.delete("/{template_id}", response_model=ApiResponse[DeleteData])
def delete_template(template_id: int, db: DBSessionDep) -> ApiResponse[DeleteData]:
    TaskTemplateService(db).delete_template(template_id)
    return success_response(DeleteData(id=template_id))


@router.post("/{template_id}/toggle", response_model=ApiResponse[TaskTemplateRead])
def toggle_template(template_id: int, payload: TaskTemplateToggleRequest, db: DBSessionDep) -> ApiResponse[TaskTemplateRead]:
    item = TaskTemplateService(db).toggle_template(template_id, payload)
    return success_response(item)
