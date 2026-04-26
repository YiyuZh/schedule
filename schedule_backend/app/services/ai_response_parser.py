from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from jsonschema import Draft202012Validator
from pydantic import Field, model_validator

from app.core.response import AppException
from app.schemas.ai import AIAction, AIPlanItem, AIPlanOption
from app.schemas.common import BaseSchema, TimePreferenceEnum
from app.utils.datetime_utils import combine_date_time, overlaps


class AITestConnectionEnvelope(BaseSchema):
    ok: bool
    message: str = Field(min_length=1, max_length=500)


class AIParseEnvelope(BaseSchema):
    actions: list[AIAction] = Field(min_length=1, max_length=20)

    @model_validator(mode="after")
    def validate_actions(self) -> "AIParseEnvelope":
        for action in self.actions:
            if action.action_type not in {"add_task", "add_event"}:
                raise ValueError("Only add_task and add_event are allowed in parse results.")
        return self


class AIPlanEnvelope(BaseSchema):
    plan_options: list[AIPlanOption] = Field(min_length=1, max_length=5)

    @model_validator(mode="after")
    def validate_options(self) -> "AIPlanEnvelope":
        for option in self.plan_options:
            if not option.name.strip():
                raise ValueError("Plan option name cannot be empty.")
            if not option.reason.strip():
                raise ValueError("Plan option reason cannot be empty.")
            if not option.items:
                raise ValueError("Each plan option must contain at least one item.")
        return self


def _strip_code_fences(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines:
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    return cleaned


def _extract_balanced_json_object(text: str) -> str:
    start_index = None
    depth = 0
    for index, char in enumerate(text):
        if char == "{":
            if start_index is None:
                start_index = index
            depth += 1
        elif char == "}":
            if start_index is None:
                continue
            depth -= 1
            if depth == 0:
                return text[start_index : index + 1]
    raise AppException("AI response does not contain a valid JSON object.", code=4066, status_code=502)


def extract_json_payload(text: str) -> dict[str, Any]:
    cleaned = _strip_code_fences(text)
    candidates = [cleaned]
    if "{" in cleaned and "}" in cleaned:
        candidates.append(_extract_balanced_json_object(cleaned))

    last_error: Exception | None = None
    for candidate in candidates:
        try:
            payload = json.loads(candidate)
        except json.JSONDecodeError as exc:
            last_error = exc
            continue
        if isinstance(payload, dict):
            return payload
        raise AppException("AI response must be a JSON object.", code=4066, status_code=502)

    raise AppException(
        f"Failed to parse AI response as JSON: {last_error}",
        code=4066,
        status_code=502,
    )


@lru_cache(maxsize=8)
def _get_validator(model_class: type[BaseSchema]) -> Draft202012Validator:
    return Draft202012Validator(model_class.model_json_schema())


def _validate_with_schema(payload: dict[str, Any], model_class: type[BaseSchema]) -> None:
    validator = _get_validator(model_class)
    errors = sorted(validator.iter_errors(payload), key=lambda error: list(error.absolute_path))
    if not errors:
        return

    first_error = errors[0]
    location = ".".join(str(item) for item in first_error.absolute_path) or "<root>"
    raise AppException(
        f"AI JSON schema validation failed at {location}: {first_error.message}",
        code=4067,
        status_code=502,
    )


def get_test_connection_schema() -> dict[str, Any]:
    return AITestConnectionEnvelope.model_json_schema()


def get_parse_schema() -> dict[str, Any]:
    return AIParseEnvelope.model_json_schema()


def get_plan_schema() -> dict[str, Any]:
    return AIPlanEnvelope.model_json_schema()


def _infer_time_preference(start_time: str | None) -> TimePreferenceEnum | None:
    if not start_time:
        return None
    hour = int(start_time.split(":", maxsplit=1)[0])
    if 5 <= hour < 12:
        return TimePreferenceEnum.morning
    if 12 <= hour < 18:
        return TimePreferenceEnum.afternoon
    if 18 <= hour < 22:
        return TimePreferenceEnum.evening
    return TimePreferenceEnum.night


def _duration_from_range(date_value: str, start_time: str | None, end_time: str | None) -> int | None:
    if not start_time or not end_time:
        return None
    start_dt = combine_date_time(date_value, start_time)
    end_dt = combine_date_time(date_value, end_time)
    total_minutes = int((end_dt - start_dt).total_seconds() // 60)
    return total_minutes if total_minutes > 0 else None


def _normalize_action(action: AIAction) -> AIAction:
    if action.action_type != "add_task":
        return action

    if action.is_study is None:
        action.is_study = action.category == "study"
    if action.time_preference is None:
        action.time_preference = _infer_time_preference(action.start_time)

    if action.planned_duration_minutes is None:
        calculated = _duration_from_range(action.date or "2000-01-01", action.start_time, action.end_time)
        action.planned_duration_minutes = calculated or (60 if action.is_study else 30)
    return action


def parse_test_connection_response(raw_text: str) -> AITestConnectionEnvelope:
    payload = extract_json_payload(raw_text)
    _validate_with_schema(payload, AITestConnectionEnvelope)
    return AITestConnectionEnvelope.model_validate(payload)


def parse_parse_response(raw_text: str) -> AIParseEnvelope:
    payload = extract_json_payload(raw_text)
    _validate_with_schema(payload, AIParseEnvelope)
    envelope = AIParseEnvelope.model_validate(payload)
    envelope.actions = [_normalize_action(action) for action in envelope.actions]
    return envelope


def _validate_plan_semantics(
    envelope: AIPlanEnvelope,
    *,
    expected_date: str,
    valid_task_ids: set[int],
    busy_windows: list[tuple[str, str]],
) -> None:
    for option in envelope.plan_options:
        internal_windows: list[tuple[str, str]] = []
        for item in option.items:
            if item.date != expected_date:
                raise AppException(
                    f"Plan item '{item.title}' has date {item.date}, expected {expected_date}.",
                    code=4067,
                    status_code=502,
                )
            if item.item_type == "task_schedule" and item.task_id not in valid_task_ids:
                raise AppException(
                    f"Plan item '{item.title}' references an unknown or non-schedulable task_id.",
                    code=4067,
                    status_code=502,
                )
            for busy_start, busy_end in busy_windows:
                if overlaps(item.start_time, item.end_time, busy_start, busy_end):
                    raise AppException(
                        f"Plan item '{item.title}' overlaps an existing busy time window.",
                        code=4067,
                        status_code=502,
                    )
            for other_start, other_end in internal_windows:
                if overlaps(item.start_time, item.end_time, other_start, other_end):
                    raise AppException(
                        f"Plan option '{option.name}' contains overlapping items.",
                        code=4067,
                        status_code=502,
                    )
            internal_windows.append((item.start_time, item.end_time))


def parse_plan_response(
    raw_text: str,
    *,
    expected_date: str,
    option_count: int,
    valid_task_ids: set[int],
    busy_windows: list[tuple[str, str]],
) -> AIPlanEnvelope:
    payload = extract_json_payload(raw_text)
    _validate_with_schema(payload, AIPlanEnvelope)
    envelope = AIPlanEnvelope.model_validate(payload)
    envelope.plan_options = envelope.plan_options[:option_count]
    _validate_plan_semantics(
        envelope,
        expected_date=expected_date,
        valid_task_ids=valid_task_ids,
        busy_windows=busy_windows,
    )
    return envelope
