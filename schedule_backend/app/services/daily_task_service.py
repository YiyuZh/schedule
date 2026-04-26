from __future__ import annotations

from datetime import datetime, time, timedelta
from typing import Iterable

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.response import AppException
from app.models.daily_task import DailyTask
from app.models.study_session import StudySession
from app.models.task_template import TaskTemplate
from app.schemas.common import StudySessionSourceEnum, TaskStatusEnum
from app.schemas.daily_task import (
    DailyTaskCompleteRequest,
    DailyTaskCreate,
    DailyTaskInheritData,
    DailyTaskInheritRequest,
    DailyTaskPatch,
    DailyTaskQuery,
    DailyTaskRead,
    DailyTaskReorderRequest,
    DailyTaskSummaryData,
    DailyTaskUpdate,
)
from app.schemas.study_session import StudySessionCreate
from app.utils.datetime_utils import DATETIME_FORMAT, now_datetime_str, now_local, parse_date_str


def get_next_sort_order(db: Session, task_date: str) -> int:
    max_sort_order = db.scalar(select(func.max(DailyTask.sort_order)).where(DailyTask.task_date == task_date))
    return (max_sort_order or 0) + 1


def sync_task_actual_duration(db: Session, task_id: int | None) -> None:
    if task_id is None:
        return
    task = db.get(DailyTask, task_id)
    if task is None:
        return
    total_duration = db.scalar(
        select(func.coalesce(func.sum(StudySession.duration_minutes), 0)).where(StudySession.task_id == task_id)
    )
    task.actual_duration_minutes = int(total_duration or 0)
    db.commit()
    _safe_enqueue_daily_task_change(db, task)


def _safe_enqueue_daily_task_change(db: Session, task: DailyTask) -> None:
    from app.services.sync_service import SyncService

    SyncService(db).safe_enqueue_change("daily_task", task.id, "upsert", model=task)


def _safe_enqueue_daily_task_status_change(db: Session, task: DailyTask) -> None:
    from app.services.sync_service import SyncService

    SyncService(db).safe_enqueue_change(
        "daily_task",
        task.id,
        "upsert",
        model=task,
        sync_scope="daily_task_status",
        changed_fields=["status", "completed_at", "actual_duration_minutes"],
    )


def _safe_enqueue_daily_task_delete(db: Session, task_id: int, sync_id: str | None, sync_version: int | None) -> None:
    from app.services.sync_service import SyncService

    SyncService(db).safe_enqueue_delete(
        "daily_task",
        entity_id=task_id,
        sync_id=sync_id,
        sync_version=sync_version,
    )


def _safe_enqueue_study_session_delete(db: Session, session_id: int, sync_id: str | None, sync_version: int | None) -> None:
    from app.services.sync_service import SyncService

    SyncService(db).safe_enqueue_delete(
        "study_session",
        entity_id=session_id,
        sync_id=sync_id,
        sync_version=sync_version,
    )


class DailyTaskService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_tasks(self, query: DailyTaskQuery) -> list[DailyTaskRead]:
        statement = select(DailyTask).where(DailyTask.task_date == query.date)
        if query.status is not None:
            statement = statement.where(DailyTask.status == query.status.value)
        if query.category is not None:
            statement = statement.where(DailyTask.category == query.category)
        if query.is_study is not None:
            statement = statement.where(DailyTask.is_study == query.is_study)
        if query.source is not None:
            statement = statement.where(DailyTask.source == query.source.value)
        statement = statement.order_by(DailyTask.sort_order.asc(), DailyTask.created_at.asc())
        tasks = self.db.scalars(statement).all()
        return [DailyTaskRead.model_validate(task) for task in tasks]

    def get_task_model(self, task_id: int) -> DailyTask:
        task = self.db.get(DailyTask, task_id)
        if task is None:
            raise AppException("task not found", code=4042, status_code=404)
        return task

    def get_task(self, task_id: int) -> DailyTaskRead:
        return DailyTaskRead.model_validate(self.get_task_model(task_id))

    def _validate_template(self, template_id: int | None) -> None:
        if template_id is None:
            return
        template = self.db.get(TaskTemplate, template_id)
        if template is None:
            raise AppException("task template not found", code=4043, status_code=404)

    def _apply_payload(self, task: DailyTask, payload: DailyTaskCreate | DailyTaskUpdate | DailyTaskPatch, partial: bool) -> None:
        data = payload.model_dump(exclude_unset=partial)
        if "template_id" in data:
            self._validate_template(data["template_id"])
        for key, value in data.items():
            if key == "source" and value is not None:
                value = value.value
            if key == "status" and value is not None:
                value = value.value
            setattr(task, key, value)
        if task.sort_order == 0:
            task.sort_order = get_next_sort_order(self.db, task.task_date)
        if task.status == TaskStatusEnum.completed.value and not task.completed_at:
            task.completed_at = now_datetime_str()
        if task.status != TaskStatusEnum.completed.value:
            task.completed_at = None

    def create_task(self, payload: DailyTaskCreate) -> DailyTaskRead:
        self._validate_template(payload.template_id)
        task = DailyTask()
        self._apply_payload(task, payload, partial=False)
        if task.sort_order == 0:
            task.sort_order = get_next_sort_order(self.db, task.task_date)
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        _safe_enqueue_daily_task_change(self.db, task)
        return DailyTaskRead.model_validate(task)

    def update_task(self, task_id: int, payload: DailyTaskUpdate) -> DailyTaskRead:
        task = self.get_task_model(task_id)
        self._apply_payload(task, payload, partial=False)
        self.db.commit()
        self.db.refresh(task)
        _safe_enqueue_daily_task_change(self.db, task)
        return DailyTaskRead.model_validate(task)

    def patch_task(self, task_id: int, payload: DailyTaskPatch) -> DailyTaskRead:
        task = self.get_task_model(task_id)
        self._apply_payload(task, payload, partial=True)
        self.db.commit()
        self.db.refresh(task)
        _safe_enqueue_daily_task_change(self.db, task)
        return DailyTaskRead.model_validate(task)

    def delete_task(self, task_id: int) -> None:
        task = self.get_task_model(task_id)
        if task.timer_state is not None:
            raise AppException("cannot delete task while timer is active", code=4006, status_code=400)
        sync_id = getattr(task, "sync_id", None)
        sync_version = getattr(task, "sync_version", None)
        self.db.delete(task)
        self.db.commit()
        _safe_enqueue_daily_task_delete(self.db, task_id, sync_id, sync_version)

    def _build_manual_session_window(self, task_date: str, actual_duration_minutes: int) -> tuple[str, str]:
        task_day = parse_date_str(task_date)
        end_at = datetime.combine(task_day, now_local().time().replace(microsecond=0))
        day_start = datetime.combine(task_day, time.min)
        start_at = end_at - timedelta(minutes=actual_duration_minutes)
        if start_at < day_start:
            start_at = day_start
        return start_at.strftime(DATETIME_FORMAT), end_at.strftime(DATETIME_FORMAT)

    def _create_manual_study_session(self, task: DailyTask, actual_duration_minutes: int) -> None:
        from app.services.study_service import StudyService

        start_at, end_at = self._build_manual_session_window(task.task_date, actual_duration_minutes)
        StudyService(self.db).create_session(
            StudySessionCreate(
                task_id=task.id,
                task_title_snapshot=task.title,
                category_snapshot=task.category,
                session_date=task.task_date,
                start_at=start_at,
                end_at=end_at,
                duration_minutes=actual_duration_minutes,
                source=StudySessionSourceEnum.manual,
                note=None,
            )
        )

    def _delete_manual_study_sessions_for_task(self, task_id: int) -> None:
        sessions = self.db.scalars(
            select(StudySession).where(
                StudySession.task_id == task_id,
                StudySession.source == StudySessionSourceEnum.manual.value,
            )
        ).all()
        if not sessions:
            return

        deleted_items = [(session.id, session.sync_id, session.sync_version) for session in sessions]
        for session in sessions:
            self.db.delete(session)
        self.db.commit()

        for session_id, sync_id, sync_version in deleted_items:
            _safe_enqueue_study_session_delete(self.db, session_id, sync_id, sync_version)
        sync_task_actual_duration(self.db, task_id)

    def update_status(self, task_id: int, status: TaskStatusEnum) -> DailyTaskRead:
        task = self.get_task_model(task_id)
        task.status = status.value
        task.completed_at = now_datetime_str() if status == TaskStatusEnum.completed else None
        self.db.commit()
        self.db.refresh(task)
        _safe_enqueue_daily_task_status_change(self.db, task)
        return DailyTaskRead.model_validate(task)

    def complete_task(self, task_id: int, payload: DailyTaskCompleteRequest | None = None) -> DailyTaskRead:
        task = self.get_task_model(task_id)

        if payload is not None:
            if payload.sync_study_session and not task.is_study:
                raise AppException("sync_study_session is only available for study tasks", code=4015, status_code=400)
            if payload.sync_study_session and payload.actual_duration_minutes is None:
                raise AppException("actual_duration_minutes is required when syncing a study session", code=4016, status_code=400)
            if payload.sync_study_session and payload.actual_duration_minutes == 0:
                raise AppException("actual_duration_minutes must be greater than 0 when syncing a study session", code=4017, status_code=400)

            if payload.sync_study_session:
                self._delete_manual_study_sessions_for_task(task.id)
                task = self.get_task_model(task_id)
                self._create_manual_study_session(task, payload.actual_duration_minutes or 0)
                task = self.get_task_model(task_id)
            elif payload.actual_duration_minutes is not None:
                task.actual_duration_minutes = payload.actual_duration_minutes

        task.status = TaskStatusEnum.completed.value
        task.completed_at = now_datetime_str()
        self.db.commit()
        self.db.refresh(task)
        _safe_enqueue_daily_task_status_change(self.db, task)
        return DailyTaskRead.model_validate(task)

    def uncomplete_task(self, task_id: int) -> DailyTaskRead:
        task = self.get_task_model(task_id)
        if task.is_study:
            self._delete_manual_study_sessions_for_task(task.id)
        return self.update_status(task_id, TaskStatusEnum.pending)

    def reorder_tasks(self, payload: DailyTaskReorderRequest) -> int:
        task_ids = [item.id for item in payload.items]
        tasks = self.db.scalars(select(DailyTask).where(DailyTask.id.in_(task_ids))).all()
        if len(tasks) != len(task_ids):
            raise AppException("one or more tasks were not found", code=4044, status_code=404)
        task_map = {task.id: task for task in tasks}
        for item in payload.items:
            task = task_map[item.id]
            if task.task_date != payload.date:
                raise AppException("all tasks must belong to the specified date", code=4007, status_code=400)
            task.sort_order = item.sort_order
        self.db.commit()
        for task in tasks:
            _safe_enqueue_daily_task_change(self.db, task)
        return len(task_ids)

    def inherit_unfinished(self, payload: DailyTaskInheritRequest) -> DailyTaskInheritData:
        statement = (
            select(DailyTask)
            .where(DailyTask.task_date == payload.from_date)
            .where(DailyTask.status.in_([TaskStatusEnum.pending.value, TaskStatusEnum.running.value]))
            .order_by(DailyTask.sort_order.asc(), DailyTask.created_at.asc())
        )
        source_tasks = self.db.scalars(statement).all()

        created_task_ids: list[int] = []
        skipped_count = 0

        for source_task in source_tasks:
            if source_task.template_id is not None:
                existing = self.db.scalar(
                    select(DailyTask).where(
                        DailyTask.template_id == source_task.template_id,
                        DailyTask.task_date == payload.to_date,
                    )
                )
                if existing is not None:
                    skipped_count += 1
                    continue

            new_task = DailyTask(
                template_id=source_task.template_id,
                title=source_task.title,
                category=source_task.category,
                is_study=source_task.is_study,
                task_date=payload.to_date,
                start_time=source_task.start_time,
                end_time=source_task.end_time,
                planned_duration_minutes=source_task.planned_duration_minutes,
                actual_duration_minutes=0,
                priority=source_task.priority,
                status=TaskStatusEnum.pending.value,
                source=source_task.source,
                sort_order=get_next_sort_order(self.db, payload.to_date),
                notes=source_task.notes,
                completed_at=None,
            )
            self.db.add(new_task)
            self.db.flush()
            created_task_ids.append(new_task.id)

        self.db.commit()
        for task_id in created_task_ids:
            task = self.db.get(DailyTask, task_id)
            if task is not None:
                _safe_enqueue_daily_task_change(self.db, task)
        return DailyTaskInheritData(
            from_date=payload.from_date,
            to_date=payload.to_date,
            created_count=len(created_task_ids),
            skipped_count=skipped_count,
            task_ids=created_task_ids,
        )

    def get_summary(self, task_date: str) -> DailyTaskSummaryData:
        tasks = self.db.scalars(select(DailyTask).where(DailyTask.task_date == task_date)).all()
        total_count = len(tasks)
        completed_count = sum(task.status == TaskStatusEnum.completed.value for task in tasks)
        skipped_count = sum(task.status == TaskStatusEnum.skipped.value for task in tasks)
        pending_count = sum(task.status == TaskStatusEnum.pending.value for task in tasks)
        running_count = sum(task.status == TaskStatusEnum.running.value for task in tasks)
        study_task_count = sum(task.is_study for task in tasks)
        completion_rate = round((completed_count / total_count) * 100, 2) if total_count else 0.0
        return DailyTaskSummaryData(
            date=task_date,
            total_count=total_count,
            completed_count=completed_count,
            skipped_count=skipped_count,
            pending_count=pending_count,
            running_count=running_count,
            completion_rate=completion_rate,
            study_task_count=study_task_count,
        )


def tasks_to_reads(tasks: Iterable[DailyTask]) -> list[DailyTaskRead]:
    return [DailyTaskRead.model_validate(task) for task in tasks]
