from __future__ import annotations

import json
from typing import Any

from app.models.course import Course
from app.models.daily_task import DailyTask
from app.models.event import Event
from app.models.long_term_task import LongTermSubtask, LongTermTask
from app.models.study_session import StudySession
from app.models.task_template import TaskTemplate


SYNC_ENTITY_MODELS = {
    "task_template": TaskTemplate,
    "daily_task": DailyTask,
    "event": Event,
    "course": Course,
    "study_session": StudySession,
    "long_term_task": LongTermTask,
    "long_term_subtask": LongTermSubtask,
}


ENTITY_FIELDS: dict[str, tuple[str, ...]] = {
    "task_template": (
        "id",
        "title",
        "category",
        "is_study",
        "default_duration_minutes",
        "default_start_time",
        "default_end_time",
        "time_preference",
        "priority",
        "is_enabled",
        "inherit_unfinished",
        "notes",
        "created_at",
        "updated_at",
    ),
    "daily_task": (
        "id",
        "template_id",
        "title",
        "category",
        "is_study",
        "task_date",
        "start_time",
        "end_time",
        "planned_duration_minutes",
        "actual_duration_minutes",
        "priority",
        "status",
        "source",
        "sort_order",
        "notes",
        "completed_at",
        "created_at",
        "updated_at",
    ),
    "event": (
        "id",
        "title",
        "category",
        "event_date",
        "start_time",
        "end_time",
        "location",
        "priority",
        "status",
        "source",
        "linked_task_id",
        "notes",
        "created_at",
        "updated_at",
    ),
    "course": (
        "id",
        "batch_id",
        "course_name",
        "weekday",
        "start_time",
        "end_time",
        "location",
        "teacher",
        "term_name",
        "term_start_date",
        "term_end_date",
        "week_list_json",
        "color",
        "notes",
        "created_at",
        "updated_at",
    ),
    "study_session": (
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
    ),
    "long_term_task": (
        "id",
        "title",
        "category",
        "description",
        "start_date",
        "due_date",
        "status",
        "priority",
        "progress_percent",
        "sort_order",
        "completed_at",
        "created_at",
        "updated_at",
    ),
    "long_term_subtask": (
        "id",
        "long_task_id",
        "title",
        "category",
        "is_study",
        "description",
        "due_date",
        "planned_duration_minutes",
        "status",
        "priority",
        "sort_order",
        "linked_daily_task_id",
        "completed_at",
        "created_at",
        "updated_at",
    ),
}

RELATION_FIELDS: dict[str, dict[str, tuple[str, str]]] = {
    "daily_task": {
        "template_id": ("task_template", "template_sync_id"),
    },
    "event": {
        "linked_task_id": ("daily_task", "linked_task_sync_id"),
    },
    "study_session": {
        "task_id": ("daily_task", "task_sync_id"),
    },
    "long_term_subtask": {
        "long_task_id": ("long_term_task", "long_task_sync_id"),
        "linked_daily_task_id": ("daily_task", "linked_daily_task_sync_id"),
    },
}


def to_json(data: dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


def parse_json(text: str | None) -> Any:
    if not text:
        return None
    return json.loads(text)


def model_to_payload(entity_type: str, model: object) -> dict[str, Any]:
    fields = ENTITY_FIELDS.get(entity_type)
    if fields is None:
        raise ValueError(f"unsupported sync entity type: {entity_type}")

    relation_sync_ids: dict[str, str | None] = {}
    for local_field, (target_entity_type, relation_key) in RELATION_FIELDS.get(entity_type, {}).items():
        local_id = getattr(model, local_field, None)
        relation_sync_ids[relation_key] = None
        if local_id is not None:
            target_model = SYNC_ENTITY_MODELS[target_entity_type]
            related = getattr(model, local_field.replace("_id", ""), None)
            relation_sync_ids[relation_key] = getattr(related, "sync_id", None) if related is not None else None

    return {
        "entity_type": entity_type,
        "local_id": getattr(model, "id"),
        "sync_id": getattr(model, "sync_id", None),
        "sync_version": getattr(model, "sync_version", 1),
        "sync_deleted": getattr(model, "sync_deleted", False),
        "updated_by_device_id": getattr(model, "updated_by_device_id", None),
        "relation_sync_ids": relation_sync_ids,
        "data": {field: getattr(model, field) for field in fields},
    }


def normalize_sync_payload(entity_type: str, entity_id: str, payload: dict[str, Any] | None) -> dict[str, Any]:
    """Return a stable sync envelope for old desktop payloads and flat mobile payloads."""
    raw = payload or {}
    nested = raw.get("data")
    if isinstance(nested, dict):
        data = dict(nested)
    else:
        metadata = {
            "entity_type",
            "local_id",
            "sync_id",
            "sync_version",
            "sync_deleted",
            "updated_by_device_id",
            "relation_sync_ids",
            "last_synced_at",
        }
        data = {key: value for key, value in raw.items() if key not in metadata}

    sync_id = str(raw.get("sync_id") or data.get("sync_id") or entity_id)
    relation_sync_ids = raw.get("relation_sync_ids")
    if not isinstance(relation_sync_ids, dict):
        relation_sync_ids = {}

    return {
        "entity_type": str(raw.get("entity_type") or entity_type),
        "sync_id": sync_id,
        "sync_version": int(raw.get("sync_version") or data.get("sync_version") or 1),
        "sync_deleted": bool(raw.get("sync_deleted") or data.get("sync_deleted") or False),
        "updated_by_device_id": raw.get("updated_by_device_id") or data.get("updated_by_device_id"),
        "relation_sync_ids": relation_sync_ids,
        "data": data,
    }


def delete_payload(entity_type: str, *, entity_id: int | str, sync_id: str | None, sync_version: int = 1) -> dict[str, Any]:
    return {
        "entity_type": entity_type,
        "local_id": entity_id,
        "sync_id": sync_id,
        "sync_version": sync_version,
        "sync_deleted": True,
        "data": {"id": entity_id},
    }
