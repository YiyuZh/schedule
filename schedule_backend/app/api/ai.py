from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import DBSessionDep
from app.core.response import ApiResponse, success_response
from app.schemas.ai import (
    AIConfigRead,
    AIConfigUpdate,
    AILogListData,
    AILogQuery,
    AILogRead,
    AIParseApplyData,
    AIParseApplyRequest,
    AIParseData,
    AIParseRequest,
    AIPlanApplyData,
    AIPlanApplyRequest,
    AIPlanData,
    AIPlanRequest,
    AITestConnectionData,
)
from app.schemas.common import DeleteData
from app.services.ai_service import AIService

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/config", response_model=ApiResponse[AIConfigRead])
def get_ai_config(db: DBSessionDep) -> ApiResponse[AIConfigRead]:
    data = AIService(db).get_config()
    return success_response(data)


@router.put("/config", response_model=ApiResponse[AIConfigRead])
def update_ai_config(payload: AIConfigUpdate, db: DBSessionDep) -> ApiResponse[AIConfigRead]:
    data = AIService(db).update_config(payload)
    return success_response(data)


@router.post("/test-connection", response_model=ApiResponse[AITestConnectionData])
def test_ai_connection(db: DBSessionDep) -> ApiResponse[AITestConnectionData]:
    data = AIService(db).test_connection()
    return success_response(data)


@router.post("/parse", response_model=ApiResponse[AIParseData])
def parse_with_ai(payload: AIParseRequest, db: DBSessionDep) -> ApiResponse[AIParseData]:
    data = AIService(db).parse(payload)
    return success_response(data)


@router.post("/parse/apply", response_model=ApiResponse[AIParseApplyData])
def apply_parse_result(payload: AIParseApplyRequest, db: DBSessionDep) -> ApiResponse[AIParseApplyData]:
    data = AIService(db).parse_apply(payload)
    return success_response(data)


@router.post("/plan", response_model=ApiResponse[AIPlanData])
def create_plan(payload: AIPlanRequest, db: DBSessionDep) -> ApiResponse[AIPlanData]:
    data = AIService(db).plan(payload)
    return success_response(data)


@router.post("/plan/apply", response_model=ApiResponse[AIPlanApplyData])
def apply_plan(payload: AIPlanApplyRequest, db: DBSessionDep) -> ApiResponse[AIPlanApplyData]:
    data = AIService(db).plan_apply(payload)
    return success_response(data)


@router.get("/logs", response_model=ApiResponse[AILogListData])
def list_ai_logs(db: DBSessionDep, query: AILogQuery = Depends()) -> ApiResponse[AILogListData]:
    data = AIService(db).list_logs(query)
    return success_response(data)


@router.get("/logs/{log_id}", response_model=ApiResponse[AILogRead])
def get_ai_log(log_id: int, db: DBSessionDep) -> ApiResponse[AILogRead]:
    data = AIService(db).get_log(log_id)
    return success_response(data)


@router.delete("/logs/{log_id}", response_model=ApiResponse[DeleteData])
def delete_ai_log(log_id: int, db: DBSessionDep) -> ApiResponse[DeleteData]:
    AIService(db).delete_log(log_id)
    return success_response(DeleteData(id=log_id))
