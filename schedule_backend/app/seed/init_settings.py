from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.app_setting import AppSetting
from app.utils.datetime_utils import now_datetime_str
from app.utils.json_utils import dumps_json

DEFAULT_SETTINGS: list[dict[str, Any]] = [
    {
        "key": "default_task_duration",
        "value": 30,
        "value_type": "int",
        "description": "Default planned duration in minutes for new tasks",
    },
    {
        "key": "auto_inherit_unfinished",
        "value": False,
        "value_type": "bool",
        "description": "Whether unfinished tasks should be inherited automatically",
    },
    {
        "key": "complete_task_auto_stop_timer",
        "value": False,
        "value_type": "bool",
        "description": "Stop timer automatically when task is completed",
    },
    {
        "key": "ai_enabled",
        "value": False,
        "value_type": "bool",
        "description": "Enable AI features",
    },
    {
        "key": "ai_provider",
        "value": "deepseek",
        "value_type": "string",
        "description": "AI provider label, such as deepseek, openai_compatible, openrouter, local",
    },
    {
        "key": "ai_base_url",
        "value": "https://api.deepseek.com/v1",
        "value_type": "string",
        "description": "OpenAI-compatible base URL, for example https://api.deepseek.com/v1",
    },
    {
        "key": "ai_api_key",
        "value": "",
        "value_type": "string",
        "description": "AI provider API key",
    },
    {
        "key": "ai_model_name",
        "value": "deepseek-chat",
        "value_type": "string",
        "description": "AI chat / parse model name",
    },
    {
        "key": "ai_plan_model_name",
        "value": "deepseek-reasoner",
        "value_type": "string",
        "description": "AI planning / reasoning model name",
    },
    {
        "key": "ai_timeout",
        "value": 60,
        "value_type": "int",
        "description": "AI request timeout in seconds",
    },
    {
        "key": "ai_temperature",
        "value": 0.2,
        "value_type": "float",
        "description": "AI generation temperature",
    },
]

DEEPSEEK_DEFAULTS = {
    "ai_provider": "deepseek",
    "ai_base_url": "https://api.deepseek.com/v1",
    "ai_model_name": "deepseek-chat",
    "ai_plan_model_name": "deepseek-reasoner",
}


def _serialize_value(value: Any, value_type: str) -> str:
    if value_type == "bool":
        return "true" if bool(value) else "false"
    if value_type == "json":
        return dumps_json(value)
    return str(value) if value is not None else ""


def _migrate_legacy_ai_defaults(db: Session) -> None:
    settings = {
        setting.setting_key: setting
        for setting in db.scalars(
            select(AppSetting).where(
                AppSetting.setting_key.in_(
                    [
                        "ai_provider",
                        "ai_base_url",
                        "ai_api_key",
                        "ai_model_name",
                        "ai_plan_model_name",
                    ]
                )
            )
        ).all()
    }

    provider_value = (settings.get("ai_provider") and settings["ai_provider"].setting_value or "").strip()
    base_url_value = (settings.get("ai_base_url") and settings["ai_base_url"].setting_value or "").strip()
    api_key_value = (settings.get("ai_api_key") and settings["ai_api_key"].setting_value or "").strip()
    model_value = (settings.get("ai_model_name") and settings["ai_model_name"].setting_value or "").strip()
    plan_model_value = (settings.get("ai_plan_model_name") and settings["ai_plan_model_name"].setting_value or "").strip()

    looks_legacy = provider_value in {"", "mock", "openai_compatible"} and not base_url_value and not api_key_value and model_value in {
        "",
        "mock-schedule-model",
    }
    needs_plan_model = not plan_model_value

    if not looks_legacy and not needs_plan_model:
        return

    now = now_datetime_str()
    for key, default_value in DEEPSEEK_DEFAULTS.items():
        if key == "ai_plan_model_name" and not (looks_legacy or needs_plan_model):
            continue
        if key != "ai_plan_model_name" and not looks_legacy:
            continue

        setting = settings.get(key)
        if setting is None:
            continue
        setting.setting_value = str(default_value)
        setting.updated_at = now

    db.commit()


def seed_default_settings(db: Session) -> None:
    existing_keys = set(db.scalars(select(AppSetting.setting_key)).all())
    created = False
    now = now_datetime_str()
    for item in DEFAULT_SETTINGS:
        if item["key"] in existing_keys:
            continue
        db.add(
            AppSetting(
                setting_key=item["key"],
                setting_value=_serialize_value(item["value"], item["value_type"]),
                value_type=item["value_type"],
                description=item["description"],
                created_at=now,
                updated_at=now,
            )
        )
        created = True
    if created:
        db.commit()
    _migrate_legacy_ai_defaults(db)
