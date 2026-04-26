from __future__ import annotations

from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.study_session import StudySession
from app.schemas.study_session import (
    StudyCategoryStatItem,
    StudyDayStatItem,
    StudyStatsByCategoryData,
    StudyStatsByDayData,
    StudyStatsByTaskData,
    StudyStatsOverviewData,
    StudyTaskStatItem,
)
from app.utils.datetime_utils import parse_date_str, today_str


class StatsService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _sum_duration(self, start_date: str | None = None, end_date: str | None = None) -> int:
        statement = select(func.coalesce(func.sum(StudySession.duration_minutes), 0))
        if start_date is not None:
            statement = statement.where(StudySession.session_date >= start_date)
        if end_date is not None:
            statement = statement.where(StudySession.session_date <= end_date)
        result = self.db.scalar(statement)
        return int(result or 0)

    def get_overview(self, start_date: str | None = None, end_date: str | None = None) -> StudyStatsOverviewData:
        today = parse_date_str(today_str())
        week_start = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)
        return StudyStatsOverviewData(
            today_minutes=self._sum_duration(today.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")),
            week_minutes=self._sum_duration(week_start.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")),
            month_minutes=self._sum_duration(month_start.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")),
            total_minutes=self._sum_duration(),
            query_total_minutes=self._sum_duration(start_date, end_date),
        )

    def get_by_category(self, start_date: str | None = None, end_date: str | None = None) -> StudyStatsByCategoryData:
        statement = select(
            StudySession.category_snapshot,
            func.coalesce(func.sum(StudySession.duration_minutes), 0),
        ).group_by(StudySession.category_snapshot)
        if start_date is not None:
            statement = statement.where(StudySession.session_date >= start_date)
        if end_date is not None:
            statement = statement.where(StudySession.session_date <= end_date)
        statement = statement.order_by(func.sum(StudySession.duration_minutes).desc())
        rows = self.db.execute(statement).all()
        return StudyStatsByCategoryData(
            items=[
                StudyCategoryStatItem(category=row[0], duration_minutes=int(row[1] or 0))
                for row in rows
            ]
        )

    def get_by_task(self, start_date: str | None = None, end_date: str | None = None) -> StudyStatsByTaskData:
        statement = select(
            StudySession.task_id,
            StudySession.task_title_snapshot,
            func.coalesce(func.sum(StudySession.duration_minutes), 0),
        ).group_by(StudySession.task_id, StudySession.task_title_snapshot)
        if start_date is not None:
            statement = statement.where(StudySession.session_date >= start_date)
        if end_date is not None:
            statement = statement.where(StudySession.session_date <= end_date)
        statement = statement.order_by(func.sum(StudySession.duration_minutes).desc())
        rows = self.db.execute(statement).all()
        return StudyStatsByTaskData(
            items=[
                StudyTaskStatItem(task_id=row[0], task_title=row[1], duration_minutes=int(row[2] or 0))
                for row in rows
            ]
        )

    def get_by_day(self, start_date: str | None = None, end_date: str | None = None) -> StudyStatsByDayData:
        statement = select(
            StudySession.session_date,
            func.coalesce(func.sum(StudySession.duration_minutes), 0),
        ).group_by(StudySession.session_date)
        if start_date is not None:
            statement = statement.where(StudySession.session_date >= start_date)
        if end_date is not None:
            statement = statement.where(StudySession.session_date <= end_date)
        statement = statement.order_by(StudySession.session_date.asc())
        rows = self.db.execute(statement).all()
        return StudyStatsByDayData(
            items=[StudyDayStatItem(session_date=row[0], duration_minutes=int(row[1] or 0)) for row in rows]
        )
