from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import DBSessionDep
from app.core.response import ApiResponse, success_response
from app.schemas.common import DateRangeQuery
from app.schemas.study_session import (
    StudyStatsByCategoryData,
    StudyStatsByDayData,
    StudyStatsByTaskData,
    StudyStatsOverviewData,
)
from app.services.stats_service import StatsService

router = APIRouter(prefix="/study-stats", tags=["study-stats"])


@router.get("/overview", response_model=ApiResponse[StudyStatsOverviewData])
def get_stats_overview(db: DBSessionDep, query: DateRangeQuery = Depends()) -> ApiResponse[StudyStatsOverviewData]:
    data = StatsService(db).get_overview(query.start_date, query.end_date)
    return success_response(data)


@router.get("/by-category", response_model=ApiResponse[StudyStatsByCategoryData])
def get_stats_by_category(db: DBSessionDep, query: DateRangeQuery = Depends()) -> ApiResponse[StudyStatsByCategoryData]:
    data = StatsService(db).get_by_category(query.start_date, query.end_date)
    return success_response(data)


@router.get("/by-subject", response_model=ApiResponse[StudyStatsByCategoryData])
def get_stats_by_subject(db: DBSessionDep, query: DateRangeQuery = Depends()) -> ApiResponse[StudyStatsByCategoryData]:
    data = StatsService(db).get_by_category(query.start_date, query.end_date)
    return success_response(data)


@router.get("/by-task", response_model=ApiResponse[StudyStatsByTaskData])
def get_stats_by_task(db: DBSessionDep, query: DateRangeQuery = Depends()) -> ApiResponse[StudyStatsByTaskData]:
    data = StatsService(db).get_by_task(query.start_date, query.end_date)
    return success_response(data)


@router.get("/by-day", response_model=ApiResponse[StudyStatsByDayData])
def get_stats_by_day(db: DBSessionDep, query: DateRangeQuery = Depends()) -> ApiResponse[StudyStatsByDayData]:
    data = StatsService(db).get_by_day(query.start_date, query.end_date)
    return success_response(data)
