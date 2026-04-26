from __future__ import annotations

from typing import Iterable

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.response import AppException
from app.models.daily_task import DailyTask
from app.models.long_term_task import LongTermSubtask, LongTermTask
from app.schemas.common import LongTermSubtaskStatusEnum, LongTermTaskStatusEnum, TaskSourceEnum, TaskStatusEnum
from app.schemas.daily_task import DailyTaskCreate, DailyTaskRead
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
    LongTermTaskUpdate,
)
from app.services.daily_task_service import DailyTaskService
from app.utils.datetime_utils import now_datetime_str, today_str


def _next_long_task_sort_order(db: Session) -> int:
    max_sort_order = db.scalar(select(func.max(LongTermTask.sort_order)))
    return (max_sort_order or 0) + 1


def _next_subtask_sort_order(db: Session, long_task_id: int) -> int:
    max_sort_order = db.scalar(
        select(func.max(LongTermSubtask.sort_order)).where(LongTermSubtask.long_task_id == long_task_id)
    )
    return (max_sort_order or 0) + 1


def _safe_enqueue_long_task_change(db: Session, task: LongTermTask) -> None:
    from app.services.sync_service import SyncService

    SyncService(db).safe_enqueue_change("long_term_task", task.id, "upsert", model=task)


def _safe_enqueue_long_task_delete(db: Session, task_id: int, sync_id: str | None, sync_version: int | None) -> None:
    from app.services.sync_service import SyncService

    SyncService(db).safe_enqueue_delete(
        "long_term_task",
        entity_id=task_id,
        sync_id=sync_id,
        sync_version=sync_version,
    )


def _safe_enqueue_subtask_change(db: Session, subtask: LongTermSubtask) -> None:
    from app.services.sync_service import SyncService

    SyncService(db).safe_enqueue_change("long_term_subtask", subtask.id, "upsert", model=subtask)


def _safe_enqueue_subtask_delete(db: Session, subtask_id: int, sync_id: str | None, sync_version: int | None) -> None:
    from app.services.sync_service import SyncService

    SyncService(db).safe_enqueue_delete(
        "long_term_subtask",
        entity_id=subtask_id,
        sync_id=sync_id,
        sync_version=sync_version,
    )


class LongTermTaskService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _get_task_model(self, task_id: int) -> LongTermTask:
        task = self.db.get(LongTermTask, task_id)
        if task is None:
            raise AppException("long term task not found", code=4080, status_code=404)
        return task

    def _get_subtask_model(self, subtask_id: int) -> LongTermSubtask:
        subtask = self.db.get(LongTermSubtask, subtask_id)
        if subtask is None:
            raise AppException("long term subtask not found", code=4081, status_code=404)
        return subtask

    def _sync_progress(self, task_id: int) -> None:
        self.db.flush()
        task = self._get_task_model(task_id)
        total_count = self.db.scalar(
            select(func.count(LongTermSubtask.id)).where(LongTermSubtask.long_task_id == task_id)
        )
        completed_count = self.db.scalar(
            select(func.count(LongTermSubtask.id)).where(
                LongTermSubtask.long_task_id == task_id,
                LongTermSubtask.status == LongTermSubtaskStatusEnum.completed.value,
            )
        )
        if not total_count:
            task.progress_percent = 0
            return
        task.progress_percent = round((int(completed_count or 0) / int(total_count)) * 100)

    def _apply_task_payload(
        self,
        task: LongTermTask,
        payload: LongTermTaskCreate | LongTermTaskUpdate | LongTermTaskPatch,
        *,
        partial: bool,
    ) -> None:
        data = payload.model_dump(exclude_unset=partial)
        for key, value in data.items():
            if key == "status" and value is not None:
                value = value.value
            setattr(task, key, value)
        if task.sort_order == 0:
            task.sort_order = _next_long_task_sort_order(self.db)
        task.completed_at = now_datetime_str() if task.status == LongTermTaskStatusEnum.completed.value else None

    def _apply_subtask_payload(
        self,
        subtask: LongTermSubtask,
        payload: LongTermSubtaskCreate | LongTermSubtaskUpdate | LongTermSubtaskPatch,
        *,
        partial: bool,
    ) -> None:
        data = payload.model_dump(exclude_unset=partial)
        for key, value in data.items():
            if key == "status" and value is not None:
                value = value.value
            setattr(subtask, key, value)
        if subtask.sort_order == 0:
            subtask.sort_order = _next_subtask_sort_order(self.db, subtask.long_task_id)
        subtask.completed_at = now_datetime_str() if subtask.status == LongTermSubtaskStatusEnum.completed.value else None

    def _task_to_read(self, task: LongTermTask) -> LongTermTaskRead:
        total_count = self.db.scalar(
            select(func.count(LongTermSubtask.id)).where(LongTermSubtask.long_task_id == task.id)
        )
        completed_count = self.db.scalar(
            select(func.count(LongTermSubtask.id)).where(
                LongTermSubtask.long_task_id == task.id,
                LongTermSubtask.status == LongTermSubtaskStatusEnum.completed.value,
            )
        )
        data = LongTermTaskRead.model_validate(task)
        data.subtask_count = int(total_count or 0)
        data.completed_subtask_count = int(completed_count or 0)
        return data

    def _subtask_to_read(self, subtask: LongTermSubtask) -> LongTermSubtaskRead:
        return LongTermSubtaskRead.model_validate(subtask)

    def list_tasks(self, query: LongTermTaskQuery) -> LongTermTaskListData:
        statement = select(LongTermTask)
        if query.status is not None:
            statement = statement.where(LongTermTask.status == query.status.value)
        if query.keyword:
            keyword = f"%{query.keyword.strip()}%"
            statement = statement.where(
                or_(
                    LongTermTask.title.like(keyword),
                    LongTermTask.category.like(keyword),
                    LongTermTask.description.like(keyword),
                )
            )
        statement = statement.order_by(LongTermTask.sort_order.asc(), LongTermTask.created_at.desc())
        tasks = self.db.scalars(statement).all()
        return LongTermTaskListData(items=[self._task_to_read(task) for task in tasks])

    def get_task(self, task_id: int) -> LongTermTaskRead:
        return self._task_to_read(self._get_task_model(task_id))

    def create_task(self, payload: LongTermTaskCreate) -> LongTermTaskRead:
        task = LongTermTask()
        self._apply_task_payload(task, payload, partial=False)
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        _safe_enqueue_long_task_change(self.db, task)
        return self._task_to_read(task)

    def update_task(self, task_id: int, payload: LongTermTaskUpdate) -> LongTermTaskRead:
        task = self._get_task_model(task_id)
        self._apply_task_payload(task, payload, partial=False)
        self.db.commit()
        self.db.refresh(task)
        _safe_enqueue_long_task_change(self.db, task)
        return self._task_to_read(task)

    def patch_task(self, task_id: int, payload: LongTermTaskPatch) -> LongTermTaskRead:
        task = self._get_task_model(task_id)
        self._apply_task_payload(task, payload, partial=True)
        self.db.commit()
        self.db.refresh(task)
        _safe_enqueue_long_task_change(self.db, task)
        return self._task_to_read(task)

    def update_task_status(self, task_id: int, status: LongTermTaskStatusEnum) -> LongTermTaskRead:
        task = self._get_task_model(task_id)
        task.status = status.value
        task.completed_at = now_datetime_str() if status.value == LongTermTaskStatusEnum.completed.value else None
        self.db.commit()
        self.db.refresh(task)
        _safe_enqueue_long_task_change(self.db, task)
        return self._task_to_read(task)

    def delete_task(self, task_id: int) -> None:
        task = self._get_task_model(task_id)
        sync_id = getattr(task, "sync_id", None)
        sync_version = getattr(task, "sync_version", None)
        subtask_sync_items = [
            (subtask.id, getattr(subtask, "sync_id", None), getattr(subtask, "sync_version", None))
            for subtask in task.subtasks
        ]
        self.db.delete(task)
        self.db.commit()
        for subtask_id, subtask_sync_id, subtask_sync_version in subtask_sync_items:
            _safe_enqueue_subtask_delete(self.db, subtask_id, subtask_sync_id, subtask_sync_version)
        _safe_enqueue_long_task_delete(self.db, task_id, sync_id, sync_version)

    def list_subtasks(self, task_id: int) -> LongTermSubtaskListData:
        self._get_task_model(task_id)
        statement = (
            select(LongTermSubtask)
            .where(LongTermSubtask.long_task_id == task_id)
            .order_by(LongTermSubtask.sort_order.asc(), LongTermSubtask.created_at.asc())
        )
        subtasks = self.db.scalars(statement).all()
        return LongTermSubtaskListData(items=[self._subtask_to_read(subtask) for subtask in subtasks])

    def create_subtask(self, task_id: int, payload: LongTermSubtaskCreate) -> LongTermSubtaskRead:
        self._get_task_model(task_id)
        subtask = LongTermSubtask(long_task_id=task_id)
        self._apply_subtask_payload(subtask, payload, partial=False)
        self.db.add(subtask)
        self.db.flush()
        self._sync_progress(task_id)
        self.db.commit()
        self.db.refresh(subtask)
        _safe_enqueue_subtask_change(self.db, subtask)
        task = self._get_task_model(task_id)
        _safe_enqueue_long_task_change(self.db, task)
        return self._subtask_to_read(subtask)

    def update_subtask(self, subtask_id: int, payload: LongTermSubtaskUpdate) -> LongTermSubtaskRead:
        subtask = self._get_subtask_model(subtask_id)
        self._apply_subtask_payload(subtask, payload, partial=False)
        self._sync_progress(subtask.long_task_id)
        self.db.commit()
        self.db.refresh(subtask)
        _safe_enqueue_subtask_change(self.db, subtask)
        task = self._get_task_model(subtask.long_task_id)
        _safe_enqueue_long_task_change(self.db, task)
        return self._subtask_to_read(subtask)

    def patch_subtask(self, subtask_id: int, payload: LongTermSubtaskPatch) -> LongTermSubtaskRead:
        subtask = self._get_subtask_model(subtask_id)
        self._apply_subtask_payload(subtask, payload, partial=True)
        self._sync_progress(subtask.long_task_id)
        self.db.commit()
        self.db.refresh(subtask)
        _safe_enqueue_subtask_change(self.db, subtask)
        task = self._get_task_model(subtask.long_task_id)
        _safe_enqueue_long_task_change(self.db, task)
        return self._subtask_to_read(subtask)

    def delete_subtask(self, subtask_id: int) -> None:
        subtask = self._get_subtask_model(subtask_id)
        task_id = subtask.long_task_id
        sync_id = getattr(subtask, "sync_id", None)
        sync_version = getattr(subtask, "sync_version", None)
        self.db.delete(subtask)
        self.db.flush()
        self._sync_progress(task_id)
        self.db.commit()
        _safe_enqueue_subtask_delete(self.db, subtask_id, sync_id, sync_version)
        task = self._get_task_model(task_id)
        _safe_enqueue_long_task_change(self.db, task)

    def complete_subtask(self, subtask_id: int) -> LongTermSubtaskRead:
        return self.patch_subtask(
            subtask_id,
            LongTermSubtaskPatch(status=LongTermSubtaskStatusEnum.completed),
        )

    def uncomplete_subtask(self, subtask_id: int) -> LongTermSubtaskRead:
        return self.patch_subtask(
            subtask_id,
            LongTermSubtaskPatch(status=LongTermSubtaskStatusEnum.pending),
        )

    def create_daily_task_from_subtask(
        self,
        subtask_id: int,
        payload: LongTermSubtaskCreateDailyTaskRequest | None = None,
    ) -> LongTermSubtaskCreateDailyTaskData:
        subtask = self._get_subtask_model(subtask_id)
        if subtask.linked_daily_task_id is not None:
            existing_task = self.db.get(DailyTask, subtask.linked_daily_task_id)
            if existing_task is not None:
                return LongTermSubtaskCreateDailyTaskData(
                    subtask=self._subtask_to_read(subtask),
                    daily_task=DailyTaskRead.model_validate(existing_task),
                )

        target_date = payload.task_date if payload and payload.task_date else today_str()
        daily_task = DailyTaskService(self.db).create_task(
            DailyTaskCreate(
                template_id=None,
                title=subtask.title,
                category=subtask.category,
                is_study=subtask.is_study,
                task_date=target_date,
                start_time=None,
                end_time=None,
                planned_duration_minutes=subtask.planned_duration_minutes,
                priority=subtask.priority,
                status=TaskStatusEnum.pending,
                source=TaskSourceEnum.manual,
                sort_order=0,
                notes=f"来自长期任务子任务：{subtask.title}",
            )
        )
        subtask.linked_daily_task_id = daily_task.id
        self.db.commit()
        self.db.refresh(subtask)
        _safe_enqueue_subtask_change(self.db, subtask)
        return LongTermSubtaskCreateDailyTaskData(
            subtask=self._subtask_to_read(subtask),
            daily_task=daily_task,
        )


def long_term_tasks_to_reads(service: LongTermTaskService, tasks: Iterable[LongTermTask]) -> list[LongTermTaskRead]:
    return [service._task_to_read(task) for task in tasks]
