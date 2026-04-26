from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.response import AppException
from app.models.daily_task import DailyTask
from app.models.event import Event
from app.schemas.event import (
    ConflictItem,
    EventConflictCheckData,
    EventConflictCheckRequest,
    EventCreate,
    EventPatch,
    EventQuery,
    EventRead,
    EventStatusUpdate,
    EventTimelineQuery,
    EventUpdate,
    TimelineData,
    TimelineItem,
)
from app.services.course_service import CourseService
from app.utils.datetime_utils import overlaps


def _safe_enqueue_event_change(db: Session, event: Event) -> None:
    from app.services.sync_service import SyncService

    SyncService(db).safe_enqueue_change("event", event.id, "upsert", model=event)


def _safe_enqueue_event_delete(db: Session, event_id: int, sync_id: str | None, sync_version: int | None) -> None:
    from app.services.sync_service import SyncService

    SyncService(db).safe_enqueue_delete("event", entity_id=event_id, sync_id=sync_id, sync_version=sync_version)


class EventService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_events(self, query: EventQuery) -> list[EventRead]:
        statement = select(Event)
        if query.date is not None:
            statement = statement.where(Event.event_date == query.date)
        if query.start_date is not None:
            statement = statement.where(Event.event_date >= query.start_date)
        if query.end_date is not None:
            statement = statement.where(Event.event_date <= query.end_date)
        if query.category is not None:
            statement = statement.where(Event.category == query.category)
        if query.status is not None:
            statement = statement.where(Event.status == query.status.value)
        statement = statement.order_by(Event.event_date.asc(), Event.start_time.asc(), Event.created_at.asc())
        events = self.db.scalars(statement).all()
        return [EventRead.model_validate(event) for event in events]

    def get_event_model(self, event_id: int) -> Event:
        event = self.db.get(Event, event_id)
        if event is None:
            raise AppException("event not found", code=4050, status_code=404)
        return event

    def get_event(self, event_id: int) -> EventRead:
        return EventRead.model_validate(self.get_event_model(event_id))

    def _apply_payload(self, event: Event, payload: EventCreate | EventUpdate | EventPatch, partial: bool) -> None:
        data = payload.model_dump(exclude_unset=partial)
        for key, value in data.items():
            if key in {"status", "source"} and value is not None:
                value = value.value
            setattr(event, key, value)

    def create_event(self, payload: EventCreate) -> EventRead:
        event = Event()
        self._apply_payload(event, payload, partial=False)
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        _safe_enqueue_event_change(self.db, event)
        return EventRead.model_validate(event)

    def update_event(self, event_id: int, payload: EventUpdate) -> EventRead:
        event = self.get_event_model(event_id)
        self._apply_payload(event, payload, partial=False)
        self.db.commit()
        self.db.refresh(event)
        _safe_enqueue_event_change(self.db, event)
        return EventRead.model_validate(event)

    def patch_event(self, event_id: int, payload: EventPatch) -> EventRead:
        event = self.get_event_model(event_id)
        self._apply_payload(event, payload, partial=True)
        self.db.commit()
        self.db.refresh(event)
        _safe_enqueue_event_change(self.db, event)
        return EventRead.model_validate(event)

    def delete_event(self, event_id: int) -> None:
        event = self.get_event_model(event_id)
        sync_id = event.sync_id
        sync_version = event.sync_version
        self.db.delete(event)
        self.db.commit()
        _safe_enqueue_event_delete(self.db, event_id, sync_id, sync_version)

    def update_status(self, event_id: int, payload: EventStatusUpdate) -> EventRead:
        event = self.get_event_model(event_id)
        event.status = payload.status.value
        self.db.commit()
        self.db.refresh(event)
        _safe_enqueue_event_change(self.db, event)
        return EventRead.model_validate(event)

    def check_conflict(self, payload: EventConflictCheckRequest) -> EventConflictCheckData:
        conflict_items: list[ConflictItem] = []

        event_statement = (
            select(Event)
            .where(Event.event_date == payload.event_date)
            .where(Event.start_time.is_not(None))
            .where(Event.end_time.is_not(None))
        )
        if payload.exclude_event_id is not None:
            event_statement = event_statement.where(Event.id != payload.exclude_event_id)

        for event in self.db.scalars(event_statement).all():
            if overlaps(payload.start_time, payload.end_time, event.start_time, event.end_time):
                conflict_items.append(
                    ConflictItem(
                        item_type="event",
                        id=event.id,
                        title=event.title,
                        date=event.event_date,
                        start_time=event.start_time,
                        end_time=event.end_time,
                        source=event.source,
                        detail=event.location,
                    )
                )

        task_statement = (
            select(DailyTask)
            .where(DailyTask.task_date == payload.event_date)
            .where(DailyTask.start_time.is_not(None))
            .where(DailyTask.end_time.is_not(None))
        )
        for task in self.db.scalars(task_statement).all():
            if overlaps(payload.start_time, payload.end_time, task.start_time, task.end_time):
                conflict_items.append(
                    ConflictItem(
                        item_type="task",
                        id=task.id,
                        title=task.title,
                        date=task.task_date,
                        start_time=task.start_time,
                        end_time=task.end_time,
                        source=task.source,
                        detail=task.category,
                    )
                )

        course_items = CourseService(self.db).get_course_occurrences_for_date(payload.event_date)
        for course in course_items:
            if overlaps(payload.start_time, payload.end_time, course.start_time, course.end_time):
                conflict_items.append(
                    ConflictItem(
                        item_type="course",
                        id=course.course_id,
                        title=course.course_name,
                        date=course.date,
                        start_time=course.start_time,
                        end_time=course.end_time,
                        source="course",
                        detail=course.location,
                    )
                )

        return EventConflictCheckData(has_conflict=bool(conflict_items), conflict_items=conflict_items)

    def get_timeline(self, query: EventTimelineQuery) -> TimelineData:
        items: list[TimelineItem] = []

        events = self.db.scalars(
            select(Event)
            .where(Event.event_date == query.date)
            .where(Event.start_time.is_not(None))
            .where(Event.end_time.is_not(None))
            .order_by(Event.start_time.asc())
        ).all()
        for event in events:
            items.append(
                TimelineItem(
                    item_type="event",
                    id=event.id,
                    title=event.title,
                    date=event.event_date,
                    start_time=event.start_time,
                    end_time=event.end_time,
                    source=event.source,
                    category=event.category,
                    detail=event.location,
                )
            )

        tasks = self.db.scalars(
            select(DailyTask)
            .where(DailyTask.task_date == query.date)
            .where(DailyTask.start_time.is_not(None))
            .where(DailyTask.end_time.is_not(None))
            .order_by(DailyTask.start_time.asc())
        ).all()
        for task in tasks:
            items.append(
                TimelineItem(
                    item_type="task",
                    id=task.id,
                    title=task.title,
                    date=task.task_date,
                    start_time=task.start_time,
                    end_time=task.end_time,
                    source=task.source,
                    category=task.category,
                    detail=task.notes,
                )
            )

        for course in CourseService(self.db).get_course_occurrences_for_date(query.date):
            items.append(
                TimelineItem(
                    item_type="course",
                    id=course.course_id,
                    title=course.course_name,
                    date=course.date,
                    start_time=course.start_time,
                    end_time=course.end_time,
                    source="course",
                    category=course.term_name,
                    detail=course.location,
                )
            )

        items.sort(key=lambda item: (item.start_time, item.end_time, item.title))
        return TimelineData(date=query.date, items=items)
