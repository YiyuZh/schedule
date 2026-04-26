from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import DBSessionDep
from app.core.response import ApiResponse, success_response
from app.schemas.common import DeleteData
from app.schemas.study_session import (
    StudySessionCreate,
    StudySessionExportData,
    StudySessionExportQuery,
    StudySessionListData,
    StudySessionQuery,
    StudySessionRead,
    StudySessionUpdate,
)
from app.services.study_service import StudyService

router = APIRouter(prefix="/study-sessions", tags=["study-sessions"])


@router.get("/export", response_model=ApiResponse[StudySessionExportData])
def export_study_sessions(db: DBSessionDep, query: StudySessionExportQuery = Depends()) -> ApiResponse[StudySessionExportData]:
    data = StudyService(db).export_sessions(query)
    return success_response(data)


@router.get("", response_model=ApiResponse[StudySessionListData])
def list_study_sessions(db: DBSessionDep, query: StudySessionQuery = Depends()) -> ApiResponse[StudySessionListData]:
    data = StudyService(db).list_sessions(query)
    return success_response(data)


@router.post("", response_model=ApiResponse[StudySessionRead])
def create_study_session(payload: StudySessionCreate, db: DBSessionDep) -> ApiResponse[StudySessionRead]:
    item = StudyService(db).create_session(payload)
    return success_response(item)


@router.get("/{session_id}", response_model=ApiResponse[StudySessionRead])
def get_study_session(session_id: int, db: DBSessionDep) -> ApiResponse[StudySessionRead]:
    item = StudyService(db).get_session(session_id)
    return success_response(item)


@router.put("/{session_id}", response_model=ApiResponse[StudySessionRead])
def update_study_session(session_id: int, payload: StudySessionUpdate, db: DBSessionDep) -> ApiResponse[StudySessionRead]:
    item = StudyService(db).update_session(session_id, payload)
    return success_response(item)


@router.delete("/{session_id}", response_model=ApiResponse[DeleteData])
def delete_study_session(session_id: int, db: DBSessionDep) -> ApiResponse[DeleteData]:
    StudyService(db).delete_session(session_id)
    return success_response(DeleteData(id=session_id))
