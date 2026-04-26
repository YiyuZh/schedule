from __future__ import annotations

from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.response import AppException
from app.models.daily_task import DailyTask
from app.models.study_session import StudySession
from app.models.timer_state import TimerState
from app.schemas.timer import TimerCurrentData, TimerOperationData, TimerStartRequest, TimerStopRequest, TimerSwitchRequest
from app.services.daily_task_service import sync_task_actual_duration
from app.utils.datetime_utils import DATETIME_FORMAT, ceil_minutes_from_seconds, now_datetime_str, parse_datetime_str


class TimerService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _get_current_timer_model(self) -> TimerState | None:
        statement = select(TimerState).order_by(TimerState.id.desc())
        return self.db.scalars(statement).first()

    def _serialize_timer(self, timer: TimerState | None) -> TimerCurrentData:
        if timer is None:
            return TimerCurrentData(has_active_timer=False)
        task_title = timer.task.title if timer.task is not None else None
        return TimerCurrentData(
            has_active_timer=True,
            task_id=timer.task_id,
            task_title=task_title,
            started_at=timer.started_at,
            paused_at=timer.paused_at,
            accumulated_seconds=timer.accumulated_seconds,
            status=timer.status,
            created_at=timer.created_at,
            updated_at=timer.updated_at,
        )

    def get_current_timer(self) -> TimerCurrentData:
        return self._serialize_timer(self._get_current_timer_model())

    def _get_task(self, task_id: int) -> DailyTask:
        task = self.db.get(DailyTask, task_id)
        if task is None:
            raise AppException("task not found", code=4051, status_code=404)
        if not task.is_study:
            raise AppException("timer can only be started for study tasks", code=4009, status_code=400)
        return task

    def _elapsed_seconds(self, timer: TimerState, ended_at: str) -> int:
        start_at = parse_datetime_str(timer.started_at)
        end_at = parse_datetime_str(ended_at)
        return max(0, int((end_at - start_at).total_seconds()))

    def start_timer(self, payload: TimerStartRequest) -> TimerOperationData:
        current_timer = self._get_current_timer_model()
        if current_timer is not None:
            raise AppException("an active timer already exists", code=4010, status_code=400)
        task = self._get_task(payload.task_id)
        now = now_datetime_str()
        timer = TimerState(
            task_id=task.id,
            started_at=now,
            paused_at=None,
            accumulated_seconds=0,
            status="running",
        )
        task.status = "running"
        self.db.add(timer)
        self.db.commit()
        self.db.refresh(timer)
        return TimerOperationData(timer=self._serialize_timer(timer), message="timer started")

    def pause_timer(self) -> TimerOperationData:
        timer = self._get_current_timer_model()
        if timer is None:
            raise AppException("no active timer found", code=4052, status_code=404)
        if timer.status != "running":
            raise AppException("timer is already paused", code=4011, status_code=400)
        now = now_datetime_str()
        timer.accumulated_seconds += self._elapsed_seconds(timer, now)
        timer.paused_at = now
        timer.started_at = now
        timer.status = "paused"
        self.db.commit()
        self.db.refresh(timer)
        return TimerOperationData(timer=self._serialize_timer(timer), message="timer paused")

    def resume_timer(self) -> TimerOperationData:
        timer = self._get_current_timer_model()
        if timer is None:
            raise AppException("no active timer found", code=4052, status_code=404)
        if timer.status != "paused":
            raise AppException("timer is already running", code=4012, status_code=400)
        now = now_datetime_str()
        timer.started_at = now
        timer.paused_at = None
        timer.status = "running"
        if timer.task is not None:
            timer.task.status = "running"
        self.db.commit()
        self.db.refresh(timer)
        return TimerOperationData(timer=self._serialize_timer(timer), message="timer resumed")

    def stop_timer(self, payload: TimerStopRequest) -> TimerOperationData:
        timer = self._get_current_timer_model()
        if timer is None:
            raise AppException("no active timer found", code=4052, status_code=404)
        now = now_datetime_str()
        start_at = parse_datetime_str(timer.created_at)
        end_at = parse_datetime_str(now)
        if end_at <= start_at:
            end_at = start_at + timedelta(seconds=1)
            now = end_at.strftime(DATETIME_FORMAT)
        total_seconds = timer.accumulated_seconds
        if timer.status == "running":
            total_seconds += self._elapsed_seconds(timer, now)

        task = self._get_task(timer.task_id)
        session = StudySession(
            task_id=task.id,
            task_title_snapshot=task.title,
            category_snapshot=task.category,
            session_date=timer.created_at[:10],
            start_at=timer.created_at,
            end_at=now,
            duration_minutes=ceil_minutes_from_seconds(total_seconds),
            source="timer",
            note=payload.note,
        )
        self.db.add(session)
        self.db.delete(timer)
        if task.status == "running":
            task.status = "pending"
        self.db.commit()
        self.db.refresh(session)
        sync_task_actual_duration(self.db, task.id)
        return TimerOperationData(
            timer=TimerCurrentData(has_active_timer=False),
            generated_session_id=session.id,
            message="timer stopped",
        )

    def discard_timer(self) -> TimerOperationData:
        timer = self._get_current_timer_model()
        if timer is None:
            raise AppException("no active timer found", code=4052, status_code=404)
        task = timer.task
        self.db.delete(timer)
        if task is not None and task.status == "running":
            task.status = "pending"
        self.db.commit()
        return TimerOperationData(timer=TimerCurrentData(has_active_timer=False), message="timer discarded")

    def switch_timer(self, payload: TimerSwitchRequest) -> TimerOperationData:
        current_timer = self._get_current_timer_model()
        generated_session_id: int | None = None
        if current_timer is not None:
            if current_timer.task_id == payload.new_task_id:
                raise AppException("new_task_id must be different from the active timer task", code=4013, status_code=400)
            if payload.save_current_session:
                stop_result = self.stop_timer(TimerStopRequest(note=payload.note))
                generated_session_id = stop_result.generated_session_id
            else:
                self.discard_timer()

        start_result = self.start_timer(TimerStartRequest(task_id=payload.new_task_id))
        return TimerOperationData(
            timer=start_result.timer,
            generated_session_id=generated_session_id,
            message="timer switched",
        )
