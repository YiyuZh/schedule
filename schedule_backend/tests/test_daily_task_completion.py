from __future__ import annotations

from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session, sessionmaker

import app.models  # noqa: F401
from app.core.response import AppException
from app.models.base import Base
from app.models.study_session import StudySession
from app.schemas.daily_task import DailyTaskCompleteRequest, DailyTaskCreate
from app.services.daily_task_service import DailyTaskService


def build_test_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", connect_args={"check_same_thread": False})

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    return session_factory()


def test_complete_task_updates_actual_duration_for_non_study_task() -> None:
    db = build_test_session()
    service = DailyTaskService(db)
    task = service.create_task(
        DailyTaskCreate(
            title="健身",
            category="其他",
            is_study=False,
            task_date="2026-04-23",
            planned_duration_minutes=100,
            priority=3,
            status="pending",
            source="manual",
            sort_order=1,
        )
    )

    completed = service.complete_task(
        task.id,
        DailyTaskCompleteRequest(actual_duration_minutes=85, sync_study_session=False),
    )

    assert completed.status == "completed"
    assert completed.actual_duration_minutes == 85
    assert completed.completed_at is not None
    assert db.scalars(select(StudySession)).all() == []
    db.close()


def test_complete_study_task_can_create_manual_study_session() -> None:
    db = build_test_session()
    service = DailyTaskService(db)
    task = service.create_task(
        DailyTaskCreate(
            title="英语阅读",
            category="英语",
            is_study=True,
            task_date="2026-04-23",
            planned_duration_minutes=60,
            priority=3,
            status="pending",
            source="manual",
            sort_order=1,
        )
    )

    completed = service.complete_task(
        task.id,
        DailyTaskCompleteRequest(actual_duration_minutes=50, sync_study_session=True),
    )
    sessions = db.scalars(select(StudySession).where(StudySession.task_id == task.id)).all()

    assert completed.status == "completed"
    assert completed.actual_duration_minutes == 50
    assert len(sessions) == 1
    assert sessions[0].source == "manual"
    assert sessions[0].duration_minutes == 50
    assert sessions[0].session_date == "2026-04-23"
    db.close()


def test_repeated_complete_study_task_replaces_manual_session() -> None:
    db = build_test_session()
    service = DailyTaskService(db)
    task = service.create_task(
        DailyTaskCreate(
            title="Python 瀛︿範",
            category="Python",
            is_study=True,
            task_date="2026-04-23",
            planned_duration_minutes=60,
            priority=3,
            status="pending",
            source="manual",
            sort_order=1,
        )
    )

    service.complete_task(task.id, DailyTaskCompleteRequest(actual_duration_minutes=30, sync_study_session=True))
    completed = service.complete_task(task.id, DailyTaskCompleteRequest(actual_duration_minutes=45, sync_study_session=True))
    sessions = db.scalars(select(StudySession).where(StudySession.task_id == task.id)).all()

    assert completed.actual_duration_minutes == 45
    assert len(sessions) == 1
    assert sessions[0].source == "manual"
    assert sessions[0].duration_minutes == 45
    db.close()


def test_uncomplete_study_task_removes_manual_sessions_but_keeps_timer_sessions() -> None:
    db = build_test_session()
    service = DailyTaskService(db)
    task = service.create_task(
        DailyTaskCreate(
            title="鏁板澶嶄範",
            category="鏁板",
            is_study=True,
            task_date="2026-04-23",
            planned_duration_minutes=80,
            priority=3,
            status="pending",
            source="manual",
            sort_order=1,
        )
    )
    service.complete_task(task.id, DailyTaskCompleteRequest(actual_duration_minutes=50, sync_study_session=True))
    db.add(
        StudySession(
            task_id=task.id,
            task_title_snapshot=task.title,
            category_snapshot=task.category,
            session_date=task.task_date,
            start_at="2026-04-23 09:00:00",
            end_at="2026-04-23 09:20:00",
            duration_minutes=20,
            source="timer",
            note=None,
        )
    )
    db.commit()

    restored = service.uncomplete_task(task.id)
    sessions = db.scalars(select(StudySession).where(StudySession.task_id == task.id)).all()

    assert restored.status == "pending"
    assert restored.actual_duration_minutes == 20
    assert len(sessions) == 1
    assert sessions[0].source == "timer"
    db.close()


def test_complete_study_task_rejects_zero_minutes_when_syncing_session() -> None:
    db = build_test_session()
    service = DailyTaskService(db)
    task = service.create_task(
        DailyTaskCreate(
            title="英语听力",
            category="英语",
            is_study=True,
            task_date="2026-04-23",
            planned_duration_minutes=45,
            priority=3,
            status="pending",
            source="manual",
            sort_order=1,
        )
    )

    try:
        service.complete_task(
            task.id,
            DailyTaskCompleteRequest(actual_duration_minutes=0, sync_study_session=True),
        )
    except AppException as exc:
        assert exc.code == 4017
        assert exc.message == "actual_duration_minutes must be greater than 0 when syncing a study session"
    else:
        raise AssertionError("expected AppException to be raised")
    finally:
        db.close()


def test_complete_task_without_payload_remains_backward_compatible() -> None:
    db = build_test_session()
    service = DailyTaskService(db)
    task = service.create_task(
        DailyTaskCreate(
            title="晚间复盘",
            category="复盘",
            is_study=False,
            task_date="2026-04-23",
            planned_duration_minutes=20,
            priority=3,
            status="pending",
            source="manual",
            sort_order=1,
        )
    )

    completed = service.complete_task(task.id)

    assert completed.status == "completed"
    assert completed.actual_duration_minutes == 0
    assert completed.completed_at is not None
    db.close()
