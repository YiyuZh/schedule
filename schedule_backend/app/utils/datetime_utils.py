from __future__ import annotations

from datetime import date, datetime, timedelta
from math import ceil

DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H:%M"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


def now_local() -> datetime:
    return datetime.now()


def now_datetime_str() -> str:
    return now_local().strftime(DATETIME_FORMAT)


def today_str() -> str:
    return now_local().strftime(DATE_FORMAT)


def parse_date_str(value: str) -> date:
    return datetime.strptime(value, DATE_FORMAT).date()


def parse_time_str(value: str):
    return datetime.strptime(value, TIME_FORMAT).time()


def parse_datetime_str(value: str) -> datetime:
    return datetime.strptime(value, DATETIME_FORMAT)


def combine_date_time(date_value: str, time_value: str) -> datetime:
    return datetime.strptime(f"{date_value} {time_value}:00", DATETIME_FORMAT)


def shift_date(date_value: str, days: int) -> str:
    return (parse_date_str(date_value) + timedelta(days=days)).strftime(DATE_FORMAT)


def iter_date_range(start_date: str, end_date: str) -> list[str]:
    start = parse_date_str(start_date)
    end = parse_date_str(end_date)
    if start > end:
        raise ValueError("start_date must be earlier than or equal to end_date")
    days = (end - start).days
    return [(start + timedelta(days=index)).strftime(DATE_FORMAT) for index in range(days + 1)]


def overlaps(start_a: str, end_a: str, start_b: str, end_b: str) -> bool:
    left_start = parse_time_str(start_a)
    left_end = parse_time_str(end_a)
    right_start = parse_time_str(start_b)
    right_end = parse_time_str(end_b)
    return left_start < right_end and right_start < left_end


def calculate_week_index(term_start_date: str, target_date: str) -> int:
    start = parse_date_str(term_start_date)
    current = parse_date_str(target_date)
    delta_days = (current - start).days
    return (delta_days // 7) + 1


def weekday_from_date(date_value: str) -> int:
    return parse_date_str(date_value).isoweekday()


def minutes_between(start_at: str, end_at: str) -> int:
    start = parse_datetime_str(start_at)
    end = parse_datetime_str(end_at)
    seconds = max(0, int((end - start).total_seconds()))
    return ceil_minutes_from_seconds(seconds)


def ceil_minutes_from_seconds(total_seconds: int) -> int:
    if total_seconds <= 0:
        return 0
    return ceil(total_seconds / 60)
