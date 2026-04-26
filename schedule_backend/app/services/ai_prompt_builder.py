from __future__ import annotations

from typing import Any

from app.utils.json_utils import dumps_json


def _format_schema(schema: dict[str, Any]) -> str:
    return dumps_json(schema)


def build_test_connection_prompts(schema: dict[str, Any]) -> tuple[str, str]:
    system_prompt = (
        "You are an AI connectivity check for a local scheduling application. "
        "Return JSON only. Do not include markdown, code fences, or extra commentary."
    )
    user_prompt = (
        "Return a minimal JSON object that matches this schema:\n"
        f"{_format_schema(schema)}\n\n"
        "The message should confirm that the model is reachable and can follow JSON-only instructions."
    )
    return system_prompt, user_prompt


def build_parse_prompts(
    *,
    text: str,
    date_context: str | None,
    schema: dict[str, Any],
) -> tuple[str, str]:
    system_prompt = (
        "You extract structured schedule actions from natural language for a personal desktop planner. "
        "Return JSON only. Never wrap the JSON in markdown. "
        "Allowed action_type values are only add_task and add_event. "
        "Dates must use YYYY-MM-DD. Times must use 24-hour HH:MM or null. "
        "If the user gives a relative date, resolve it using date_context. "
        "If a duration is mentioned, fill planned_duration_minutes when relevant. "
        "Set is_study=true for study-related tasks, otherwise false. "
        "time_preference must be one of none, morning, afternoon, evening, night, or null if unknown."
    )
    user_prompt = (
        "Convert the following user input into structured schedule actions.\n\n"
        f"date_context: {date_context or 'null'}\n"
        f"user_input: {text}\n\n"
        "Target JSON schema:\n"
        f"{_format_schema(schema)}\n\n"
        "Rules:\n"
        "- Prefer add_event for appointments, meetings, interviews, doctor visits, travel, or one-off events.\n"
        "- Prefer add_task for tasks, study blocks, to-dos, review sessions, reading, or homework.\n"
        "- Keep the title concise and user-facing.\n"
        "- If the time is unknown, keep start_time/end_time null.\n"
        "- If the category is unknown, use other.\n"
        "- Return only the JSON object."
    )
    return system_prompt, user_prompt


def build_parse_repair_prompts(
    *,
    invalid_response: str,
    validation_error: str,
    schema: dict[str, Any],
) -> tuple[str, str]:
    system_prompt = (
        "You repair invalid model output into valid JSON for a scheduling application. "
        "Return JSON only. Do not explain what you changed."
    )
    user_prompt = (
        "Repair the following model output so that it becomes valid JSON matching this schema.\n\n"
        f"Schema:\n{_format_schema(schema)}\n\n"
        f"Validation error:\n{validation_error}\n\n"
        f"Invalid output:\n{invalid_response}\n"
    )
    return system_prompt, user_prompt


def build_plan_prompts(
    *,
    schema: dict[str, Any],
    planning_context: dict[str, Any],
) -> tuple[str, str]:
    system_prompt = (
        "You create concrete day plans for a personal schedule application. "
        "Return JSON only. Never output markdown. "
        "Each plan option must be realistic, conflict-free, and easy to apply. "
        "Allowed item_type values are only event and task_schedule. "
        "Use only the provided task IDs for task_schedule items. "
        "All dates must stay on the requested planning date. "
        "All times must use 24-hour HH:MM."
    )
    user_prompt = (
        "Create plan options for the following day context.\n\n"
        f"{dumps_json(planning_context)}\n\n"
        "Target JSON schema:\n"
        f"{_format_schema(schema)}\n\n"
        "Rules:\n"
        "- Respect busy time windows from existing tasks, events, and courses.\n"
        "- Prefer scheduling higher-priority and study-related work into available focus windows.\n"
        "- Keep short buffers between major items when possible.\n"
        "- Do not invent new task IDs.\n"
        "- Return only the JSON object."
    )
    return system_prompt, user_prompt


def build_plan_repair_prompts(
    *,
    invalid_response: str,
    validation_error: str,
    schema: dict[str, Any],
) -> tuple[str, str]:
    system_prompt = (
        "You repair invalid planning output into valid JSON for a local scheduling application. "
        "Return JSON only. Do not add explanations."
    )
    user_prompt = (
        "Repair the following planning output so that it becomes valid JSON matching this schema.\n\n"
        f"Schema:\n{_format_schema(schema)}\n\n"
        f"Validation error:\n{validation_error}\n\n"
        f"Invalid output:\n{invalid_response}\n"
    )
    return system_prompt, user_prompt
