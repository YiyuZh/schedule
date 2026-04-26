from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import DBSessionDep
from app.core.response import ApiResponse, success_response
from app.schemas.common import DeleteData
from app.schemas.course import (
    CourseCreate,
    CourseDayViewData,
    CourseDayViewQuery,
    CourseListData,
    CourseQuery,
    CourseRead,
    CourseUpdate,
    CourseWeekViewData,
    CourseWeekViewQuery,
)
from app.services.course_service import CourseService

router = APIRouter(prefix="/courses", tags=["courses"])


@router.get("/day-view", response_model=ApiResponse[CourseDayViewData])
def get_day_view(db: DBSessionDep, query: CourseDayViewQuery = Depends()) -> ApiResponse[CourseDayViewData]:
    data = CourseService(db).get_day_view(query.date)
    return success_response(data)


@router.get("/week-view", response_model=ApiResponse[CourseWeekViewData])
def get_week_view(db: DBSessionDep, query: CourseWeekViewQuery = Depends()) -> ApiResponse[CourseWeekViewData]:
    data = CourseService(db).get_week_view(query.start_date, query.end_date)
    return success_response(data)


@router.get("", response_model=ApiResponse[CourseListData])
def list_courses(db: DBSessionDep, query: CourseQuery = Depends()) -> ApiResponse[CourseListData]:
    items = CourseService(db).list_courses(query)
    return success_response(CourseListData(items=items))


@router.post("", response_model=ApiResponse[CourseRead])
def create_course(payload: CourseCreate, db: DBSessionDep) -> ApiResponse[CourseRead]:
    item = CourseService(db).create_course(payload)
    return success_response(item)


@router.get("/{course_id}", response_model=ApiResponse[CourseRead])
def get_course(course_id: int, db: DBSessionDep) -> ApiResponse[CourseRead]:
    item = CourseService(db).get_course(course_id)
    return success_response(item)


@router.put("/{course_id}", response_model=ApiResponse[CourseRead])
def update_course(course_id: int, payload: CourseUpdate, db: DBSessionDep) -> ApiResponse[CourseRead]:
    item = CourseService(db).update_course(course_id, payload)
    return success_response(item)


@router.delete("/{course_id}", response_model=ApiResponse[DeleteData])
def delete_course(course_id: int, db: DBSessionDep) -> ApiResponse[DeleteData]:
    CourseService(db).delete_course(course_id)
    return success_response(DeleteData(id=course_id))
