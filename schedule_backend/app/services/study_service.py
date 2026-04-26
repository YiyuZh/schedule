from __future__ import annotations

import csv
import io
from collections.abc import Sequence

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.response import AppException
from app.models.daily_task import DailyTask
from app.models.study_session import StudySession
from app.schemas.study_session import (
    StudySessionCreate,
    StudySessionExportData,
    StudySessionExportQuery,
    StudySessionListData,
    StudySessionQuery,
    StudySessionRead,
    StudySessionUpdate,
)
from app.services.daily_task_service import sync_task_actual_duration
from app.utils.json_utils import dumps_json


def _safe_enqueue_study_session_change(db: Session, session: StudySession) -> None:
    from app.services.sync_service import SyncService

    SyncService(db).safe_enqueue_change("study_session", session.id, "upsert", model=session)


def _safe_enqueue_study_session_delete(db: Session, session_id: int, sync_id: str | None, sync_version: int | None) -> None:
    from app.services.sync_service import SyncService

    SyncService(db).safe_enqueue_delete(
        "study_session",
        entity_id=session_id,
        sync_id=sync_id,
        sync_version=sync_version,
    )


class StudyService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _apply_filters(self, statement, query: StudySessionQuery | StudySessionExportQuery):
        if query.start_date is not None:
            statement = statement.where(StudySession.session_date >= query.start_date)
        if query.end_date is not None:
            statement = statement.where(StudySession.session_date <= query.end_date)
        if hasattr(query, "category") and query.category is not None:
            statement = statement.where(StudySession.category_snapshot == query.category)
        if hasattr(query, "task_id") and query.task_id is not None:
            statement = statement.where(StudySession.task_id == query.task_id)
        return statement

    def _get_task_snapshot(self, task_id: int | None) -> tuple[str | None, str | None]:
        if task_id is None:
            return None, None
        task = self.db.get(DailyTask, task_id)
        if task is None:
            raise AppException("task not found", code=4046, status_code=404)
        return task.title, task.category

    def _validate_payload(self, payload: StudySessionCreate | StudySessionUpdate) -> None:
        if payload.session_date != payload.start_at[:10]:
            raise AppException("session_date must match the start_at date", code=4008, status_code=400)

    def _apply_payload(self, session: StudySession, payload: StudySessionCreate | StudySessionUpdate) -> tuple[int | None, int | None]:
        self._validate_payload(payload)
        previous_task_id = session.task_id
        snapshot_title, snapshot_category = self._get_task_snapshot(payload.task_id)
        session.task_id = payload.task_id
        session.task_title_snapshot = payload.task_title_snapshot or snapshot_title or "Study Session"
        session.category_snapshot = payload.category_snapshot or snapshot_category or "study"
        session.session_date = payload.session_date
        session.start_at = payload.start_at
        session.end_at = payload.end_at
        session.duration_minutes = payload.duration_minutes or 0
        session.source = payload.source.value
        session.note = payload.note
        return previous_task_id, session.task_id

    def list_sessions(self, query: StudySessionQuery) -> StudySessionListData:
        base_statement = self._apply_filters(select(StudySession), query)
        total = len(self.db.scalars(base_statement).all())
        statement = (
            base_statement.order_by(desc(StudySession.start_at))
            .offset((query.page - 1) * query.page_size)
            .limit(query.page_size)
        )
        sessions = self.db.scalars(statement).all()
        return StudySessionListData(
            items=[StudySessionRead.model_validate(session) for session in sessions],
            total=total,
            page=query.page,
            page_size=query.page_size,
        )

    def _get_session_model(self, session_id: int) -> StudySession:
        session = self.db.get(StudySession, session_id)
        if session is None:
            raise AppException("study session not found", code=4047, status_code=404)
        return session

    def get_session(self, session_id: int) -> StudySessionRead:
        return StudySessionRead.model_validate(self._get_session_model(session_id))

    def create_session(self, payload: StudySessionCreate) -> StudySessionRead:
        session = StudySession()
        _, task_id = self._apply_payload(session, payload)
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        _safe_enqueue_study_session_change(self.db, session)
        sync_task_actual_duration(self.db, task_id)
        return StudySessionRead.model_validate(session)

    def update_session(self, session_id: int, payload: StudySessionUpdate) -> StudySessionRead:
        session = self._get_session_model(session_id)
        previous_task_id, task_id = self._apply_payload(session, payload)
        self.db.commit()
        self.db.refresh(session)
        sync_task_actual_duration(self.db, previous_task_id)
        if task_id != previous_task_id:
            sync_task_actual_duration(self.db, task_id)
        else:
            sync_task_actual_duration(self.db, task_id)
        self.db.refresh(session)
        _safe_enqueue_study_session_change(self.db, session)
        return StudySessionRead.model_validate(session)

    def delete_session(self, session_id: int) -> None:
        session = self._get_session_model(session_id)
        task_id = session.task_id
        sync_id = session.sync_id
        sync_version = session.sync_version
        self.db.delete(session)
        self.db.commit()
        _safe_enqueue_study_session_delete(self.db, session_id, sync_id, sync_version)
        sync_task_actual_duration(self.db, task_id)

    def export_sessions(self, query: StudySessionExportQuery) -> StudySessionExportData:
        statement = self._apply_filters(select(StudySession).order_by(desc(StudySession.start_at)), query)
        sessions = self.db.scalars(statement).all()
        reads = [StudySessionRead.model_validate(session) for session in sessions]
        if query.format == "csv":
            output = io.StringIO()
            writer = csv.DictWriter(
                output,
                fieldnames=[
                    "id",
                    "task_id",
                    "task_title_snapshot",
                    "category_snapshot",
                    "session_date",
                    "start_at",
                    "end_at",
                    "duration_minutes",
                    "source",
                    "note",
                    "created_at",
                ],
            )
            writer.writeheader()
            for item in reads:
                writer.writerow(item.model_dump())
            content = output.getvalue()
            file_name = "study_sessions.csv"
        else:
            content = dumps_json([item.model_dump() for item in reads])
            file_name = "study_sessions.json"

        return StudySessionExportData(
            format=query.format,
            file_name=file_name,
            item_count=len(reads),
            content=content,
        )
