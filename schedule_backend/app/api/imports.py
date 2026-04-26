from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import DBSessionDep
from app.core.response import ApiResponse, success_response
from app.schemas.import_schema import (
    CourseImportPayload,
    CourseImportResultData,
    CourseImportValidateData,
    ImportBatchDeleteCoursesData,
    ImportBatchListData,
    ImportBatchRead,
)
from app.services.import_service import ImportService

router = APIRouter(tags=["imports"])


@router.get("/import-batches", response_model=ApiResponse[ImportBatchListData])
def list_import_batches(db: DBSessionDep) -> ApiResponse[ImportBatchListData]:
    items = ImportService(db).list_batches()
    return success_response(ImportBatchListData(items=items))


@router.get("/import-batches/{batch_id}", response_model=ApiResponse[ImportBatchRead])
def get_import_batch(batch_id: int, db: DBSessionDep) -> ApiResponse[ImportBatchRead]:
    item = ImportService(db).get_batch(batch_id)
    return success_response(item)


@router.post("/import/courses/validate", response_model=ApiResponse[CourseImportValidateData])
def validate_courses_json(payload: CourseImportPayload, db: DBSessionDep) -> ApiResponse[CourseImportValidateData]:
    data = ImportService(db).validate_courses_json(payload)
    return success_response(data)


@router.post("/import/courses/json", response_model=ApiResponse[CourseImportResultData])
def import_courses_json(payload: CourseImportPayload, db: DBSessionDep) -> ApiResponse[CourseImportResultData]:
    data = ImportService(db).import_courses_json(payload)
    return success_response(data)


@router.delete("/import-batches/{batch_id}/courses", response_model=ApiResponse[ImportBatchDeleteCoursesData])
def delete_batch_courses(batch_id: int, db: DBSessionDep) -> ApiResponse[ImportBatchDeleteCoursesData]:
    deleted_count = ImportService(db).delete_batch_courses(batch_id)
    return success_response(ImportBatchDeleteCoursesData(batch_id=batch_id, deleted_count=deleted_count))
