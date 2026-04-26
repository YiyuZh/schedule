from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.response import AppException
from app.models.course import Course
from app.schemas.course import (
    CourseCreate,
    CourseDayViewData,
    CourseOccurrence,
    CourseQuery,
    CourseRead,
    CourseUpdate,
    CourseWeekViewData,
)
from app.utils.datetime_utils import calculate_week_index, iter_date_range, weekday_from_date
from app.utils.json_utils import dumps_json


def _safe_enqueue_course_change(db: Session, course: Course) -> None:
    from app.services.sync_service import SyncService

    SyncService(db).safe_enqueue_change("course", course.id, "upsert", model=course)


def _safe_enqueue_course_delete(db: Session, course_id: int, sync_id: str | None, sync_version: int | None) -> None:
    from app.services.sync_service import SyncService

    SyncService(db).safe_enqueue_delete("course", entity_id=course_id, sync_id=sync_id, sync_version=sync_version)


class CourseService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_courses(self, query: CourseQuery) -> list[CourseRead]:
        statement = select(Course)
        if query.term_name is not None:
            statement = statement.where(Course.term_name == query.term_name)
        if query.weekday is not None:
            statement = statement.where(Course.weekday == query.weekday)
        if query.batch_id is not None:
            statement = statement.where(Course.batch_id == query.batch_id)
        statement = statement.order_by(Course.weekday.asc(), Course.start_time.asc())
        courses = self.db.scalars(statement).all()
        return [CourseRead.model_validate(course) for course in courses]

    def get_course_model(self, course_id: int) -> Course:
        course = self.db.get(Course, course_id)
        if course is None:
            raise AppException("course not found", code=4048, status_code=404)
        return course

    def get_course(self, course_id: int) -> CourseRead:
        return CourseRead.model_validate(self.get_course_model(course_id))

    def _apply_payload(self, course: Course, payload: CourseCreate | CourseUpdate) -> None:
        course.batch_id = payload.batch_id
        course.course_name = payload.course_name
        course.weekday = payload.weekday
        course.start_time = payload.start_time
        course.end_time = payload.end_time
        course.location = payload.location
        course.teacher = payload.teacher
        course.term_name = payload.term_name
        course.term_start_date = payload.term_start_date
        course.term_end_date = payload.term_end_date
        course.week_list_json = dumps_json(payload.week_list)
        course.color = payload.color
        course.notes = payload.notes

    def create_course(self, payload: CourseCreate) -> CourseRead:
        course = Course()
        self._apply_payload(course, payload)
        self.db.add(course)
        self.db.commit()
        self.db.refresh(course)
        _safe_enqueue_course_change(self.db, course)
        return CourseRead.model_validate(course)

    def update_course(self, course_id: int, payload: CourseUpdate) -> CourseRead:
        course = self.get_course_model(course_id)
        self._apply_payload(course, payload)
        self.db.commit()
        self.db.refresh(course)
        _safe_enqueue_course_change(self.db, course)
        return CourseRead.model_validate(course)

    def delete_course(self, course_id: int) -> None:
        course = self.get_course_model(course_id)
        sync_id = course.sync_id
        sync_version = course.sync_version
        self.db.delete(course)
        self.db.commit()
        _safe_enqueue_course_delete(self.db, course_id, sync_id, sync_version)

    def get_course_occurrences_for_date(self, date_value: str) -> list[CourseOccurrence]:
        weekday = weekday_from_date(date_value)
        statement = (
            select(Course)
            .where(Course.weekday == weekday)
            .where(Course.term_start_date <= date_value)
            .where(Course.term_end_date >= date_value)
            .order_by(Course.start_time.asc())
        )
        courses = self.db.scalars(statement).all()
        occurrences: list[CourseOccurrence] = []
        for course in courses:
            week_index = calculate_week_index(course.term_start_date, date_value)
            if week_index not in course.week_list:
                continue
            occurrences.append(
                CourseOccurrence(
                    course_id=course.id,
                    course_name=course.course_name,
                    date=date_value,
                    weekday=course.weekday,
                    start_time=course.start_time,
                    end_time=course.end_time,
                    location=course.location,
                    teacher=course.teacher,
                    term_name=course.term_name,
                    week_index=week_index,
                    batch_id=course.batch_id,
                    color=course.color,
                    notes=course.notes,
                )
            )
        return occurrences

    def get_day_view(self, date_value: str) -> CourseDayViewData:
        return CourseDayViewData(date=date_value, items=self.get_course_occurrences_for_date(date_value))

    def get_week_view(self, start_date: str, end_date: str) -> CourseWeekViewData:
        items: list[CourseOccurrence] = []
        for date_value in iter_date_range(start_date, end_date):
            items.extend(self.get_course_occurrences_for_date(date_value))
        items.sort(key=lambda item: (item.date, item.start_time, item.course_name))
        return CourseWeekViewData(start_date=start_date, end_date=end_date, items=items)
