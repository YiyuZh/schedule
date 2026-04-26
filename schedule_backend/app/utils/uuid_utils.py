from __future__ import annotations

from uuid import NAMESPACE_URL, uuid4, uuid5


def new_uuid() -> str:
    return str(uuid4())


def template_daily_task_sync_id(template_sync_id: str, task_date: str) -> str:
    return str(uuid5(NAMESPACE_URL, f"schedule:daily-task:{template_sync_id}:{task_date}"))
