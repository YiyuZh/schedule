from __future__ import annotations

from app.utils.datetime_utils import parse_date_str, parse_datetime_str, parse_time_str


def ensure_date_string(value: str) -> str:
    parse_date_str(value)
    return value


def ensure_time_string(value: str) -> str:
    parse_time_str(value)
    return value


def ensure_datetime_string(value: str) -> str:
    parse_datetime_str(value)
    return value


def ensure_priority(value: int) -> int:
    if value < 1 or value > 5:
        raise ValueError("priority must be between 1 and 5")
    return value


def ensure_non_negative(value: int, field_name: str) -> int:
    if value < 0:
        raise ValueError(f"{field_name} must be greater than or equal to 0")
    return value


def ensure_optional_time_range(start_time: str | None, end_time: str | None) -> None:
    if start_time is None and end_time is None:
        return
    if not start_time or not end_time:
        raise ValueError("start_time and end_time must be provided together")
    start = parse_time_str(start_time)
    end = parse_time_str(end_time)
    if start >= end:
        raise ValueError("end_time must be later than start_time")


def ensure_datetime_order(start_at: str, end_at: str) -> None:
    start = parse_datetime_str(start_at)
    end = parse_datetime_str(end_at)
    if start >= end:
        raise ValueError("end_at must be later than start_at")


def ensure_week_list(week_list: list[int]) -> list[int]:
    if not week_list:
        raise ValueError("week_list cannot be empty")
    cleaned = sorted(set(week_list))
    if cleaned[0] < 1:
        raise ValueError("week_list values must be positive integers")
    return cleaned
