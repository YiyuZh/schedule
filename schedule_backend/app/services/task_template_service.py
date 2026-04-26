from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.response import AppException
from app.models.daily_task import DailyTask
from app.models.task_template import TaskTemplate
from app.schemas.task_template import (
    TaskTemplateCreate,
    TaskTemplatePatch,
    TaskTemplateQuery,
    TaskTemplateRead,
    TaskTemplateRefreshData,
    TaskTemplateToggleRequest,
    TaskTemplateUpdate,
)
from app.services.daily_task_service import _safe_enqueue_daily_task_change, get_next_sort_order
from app.utils.datetime_utils import today_str
from app.utils.uuid_utils import template_daily_task_sync_id


def _safe_enqueue_template_change(db: Session, template: TaskTemplate) -> None:
    from app.services.sync_service import SyncService

    SyncService(db).safe_enqueue_change("task_template", template.id, "upsert", model=template)


def _safe_enqueue_template_delete(db: Session, template_id: int, sync_id: str | None, sync_version: int | None) -> None:
    from app.services.sync_service import SyncService

    SyncService(db).safe_enqueue_delete(
        "task_template",
        entity_id=template_id,
        sync_id=sync_id,
        sync_version=sync_version,
    )


class TaskTemplateService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_templates(self, query: TaskTemplateQuery) -> list[TaskTemplateRead]:
        statement = select(TaskTemplate)
        if query.enabled is not None:
            statement = statement.where(TaskTemplate.is_enabled == query.enabled)
        if query.category is not None:
            statement = statement.where(TaskTemplate.category == query.category)
        if query.is_study is not None:
            statement = statement.where(TaskTemplate.is_study == query.is_study)
        statement = statement.order_by(TaskTemplate.created_at.asc())
        templates = self.db.scalars(statement).all()
        return [TaskTemplateRead.model_validate(template) for template in templates]

    def get_template_model(self, template_id: int) -> TaskTemplate:
        template = self.db.get(TaskTemplate, template_id)
        if template is None:
            raise AppException("task template not found", code=4045, status_code=404)
        return template

    def get_template(self, template_id: int) -> TaskTemplateRead:
        return TaskTemplateRead.model_validate(self.get_template_model(template_id))

    def _apply_payload(self, template: TaskTemplate, payload: TaskTemplateCreate | TaskTemplateUpdate | TaskTemplatePatch, partial: bool) -> None:
        data = payload.model_dump(exclude_unset=partial)
        for key, value in data.items():
            if key == "time_preference" and value is not None:
                value = value.value
            setattr(template, key, value)

    def create_template(self, payload: TaskTemplateCreate) -> TaskTemplateRead:
        template = TaskTemplate()
        self._apply_payload(template, payload, partial=False)
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        _safe_enqueue_template_change(self.db, template)
        return TaskTemplateRead.model_validate(template)

    def update_template(self, template_id: int, payload: TaskTemplateUpdate) -> TaskTemplateRead:
        template = self.get_template_model(template_id)
        self._apply_payload(template, payload, partial=False)
        self.db.commit()
        self.db.refresh(template)
        _safe_enqueue_template_change(self.db, template)
        return TaskTemplateRead.model_validate(template)

    def patch_template(self, template_id: int, payload: TaskTemplatePatch) -> TaskTemplateRead:
        template = self.get_template_model(template_id)
        self._apply_payload(template, payload, partial=True)
        self.db.commit()
        self.db.refresh(template)
        _safe_enqueue_template_change(self.db, template)
        return TaskTemplateRead.model_validate(template)

    def delete_template(self, template_id: int) -> None:
        template = self.get_template_model(template_id)
        sync_id = template.sync_id
        sync_version = template.sync_version
        self.db.delete(template)
        self.db.commit()
        _safe_enqueue_template_delete(self.db, template_id, sync_id, sync_version)

    def toggle_template(self, template_id: int, payload: TaskTemplateToggleRequest) -> TaskTemplateRead:
        template = self.get_template_model(template_id)
        template.is_enabled = payload.is_enabled
        self.db.commit()
        self.db.refresh(template)
        _safe_enqueue_template_change(self.db, template)
        return TaskTemplateRead.model_validate(template)

    def refresh_today(self, target_date: str | None = None) -> TaskTemplateRefreshData:
        task_date = target_date or today_str()
        templates = self.db.scalars(
            select(TaskTemplate).where(TaskTemplate.is_enabled.is_(True)).order_by(TaskTemplate.created_at.asc())
        ).all()

        created_task_ids: list[int] = []
        skipped_count = 0

        for template in templates:
            existing = self.db.scalar(
                select(DailyTask).where(
                    DailyTask.template_id == template.id,
                    DailyTask.task_date == task_date,
                )
            )
            if existing is not None:
                skipped_count += 1
                continue

            task = DailyTask(
                sync_id=template_daily_task_sync_id(template.sync_id, task_date),
                template_id=template.id,
                title=template.title,
                category=template.category,
                is_study=template.is_study,
                task_date=task_date,
                start_time=template.default_start_time,
                end_time=template.default_end_time,
                planned_duration_minutes=template.default_duration_minutes,
                actual_duration_minutes=0,
                priority=template.priority,
                status="pending",
                source="template",
                sort_order=get_next_sort_order(self.db, task_date),
                notes=template.notes,
            )
            self.db.add(task)
            self.db.flush()
            created_task_ids.append(task.id)

        self.db.commit()
        for task_id in created_task_ids:
            task = self.db.get(DailyTask, task_id)
            if task is not None:
                _safe_enqueue_daily_task_change(self.db, task)
        return TaskTemplateRefreshData(
            date=task_date,
            created_count=len(created_task_ids),
            skipped_count=skipped_count,
            task_ids=created_task_ids,
        )
