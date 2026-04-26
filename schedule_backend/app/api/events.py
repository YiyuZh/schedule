from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import DBSessionDep
from app.core.response import ApiResponse, success_response
from app.schemas.common import DeleteData
from app.schemas.event import (
    EventConflictCheckData,
    EventConflictCheckRequest,
    EventCreate,
    EventListData,
    EventPatch,
    EventQuery,
    EventRead,
    EventStatusUpdate,
    EventTimelineQuery,
    EventUpdate,
    TimelineData,
)
from app.services.event_service import EventService

router = APIRouter(prefix="/events", tags=["events"])


@router.post("/check-conflict", response_model=ApiResponse[EventConflictCheckData])
def check_conflict(payload: EventConflictCheckRequest, db: DBSessionDep) -> ApiResponse[EventConflictCheckData]:
    data = EventService(db).check_conflict(payload)
    return success_response(data)


@router.get("/timeline", response_model=ApiResponse[TimelineData])
def get_timeline(db: DBSessionDep, query: EventTimelineQuery = Depends()) -> ApiResponse[TimelineData]:
    data = EventService(db).get_timeline(query)
    return success_response(data)


@router.get("", response_model=ApiResponse[EventListData])
def list_events(db: DBSessionDep, query: EventQuery = Depends()) -> ApiResponse[EventListData]:
    items = EventService(db).list_events(query)
    return success_response(EventListData(items=items))


@router.post("", response_model=ApiResponse[EventRead])
def create_event(payload: EventCreate, db: DBSessionDep) -> ApiResponse[EventRead]:
    item = EventService(db).create_event(payload)
    return success_response(item)


@router.get("/{event_id}", response_model=ApiResponse[EventRead])
def get_event(event_id: int, db: DBSessionDep) -> ApiResponse[EventRead]:
    item = EventService(db).get_event(event_id)
    return success_response(item)


@router.put("/{event_id}", response_model=ApiResponse[EventRead])
def update_event(event_id: int, payload: EventUpdate, db: DBSessionDep) -> ApiResponse[EventRead]:
    item = EventService(db).update_event(event_id, payload)
    return success_response(item)


@router.patch("/{event_id}", response_model=ApiResponse[EventRead])
def patch_event(event_id: int, payload: EventPatch, db: DBSessionDep) -> ApiResponse[EventRead]:
    item = EventService(db).patch_event(event_id, payload)
    return success_response(item)


@router.delete("/{event_id}", response_model=ApiResponse[DeleteData])
def delete_event(event_id: int, db: DBSessionDep) -> ApiResponse[DeleteData]:
    EventService(db).delete_event(event_id)
    return success_response(DeleteData(id=event_id))


@router.post("/{event_id}/status", response_model=ApiResponse[EventRead])
def update_event_status(event_id: int, payload: EventStatusUpdate, db: DBSessionDep) -> ApiResponse[EventRead]:
    item = EventService(db).update_status(event_id, payload)
    return success_response(item)
