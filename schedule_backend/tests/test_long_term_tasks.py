from __future__ import annotations

from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session, sessionmaker

import app.models  # noqa: F401
from app.models.base import Base
from app.models.daily_task import DailyTask
from app.models.long_term_task import LongTermSubtask
from app.models.study_session import StudySession
from app.schemas.long_term_task import (
    LongTermSubtaskCreate,
    LongTermSubtaskCreateDailyTaskRequest,
    LongTermTaskCreate,
)
from app.services.long_term_task_service import LongTermTaskService
from app.services.stats_service import StatsService


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


def test_long_term_task_progress_updates_when_subtask_completed() -> None:
    db = build_test_session()
    service = LongTermTaskService(db)
    task = service.create_task(
        LongTermTaskCreate(
            title="本月完成项目升级",
            category="项目",
            start_date="2026-04-01",
            due_date="2026-04-30",
            priority=5,
        )
    )
    first = service.create_subtask(
        task.id,
        LongTermSubtaskCreate(title="完成 PRD 设计", category="设计", planned_duration_minutes=60),
    )
    service.create_subtask(
        task.id,
        LongTermSubtaskCreate(title="完成前端联调", category="开发", planned_duration_minutes=120),
    )

    service.complete_subtask(first.id)
    refreshed = service.get_task(task.id)

    assert refreshed.subtask_count == 2
    assert refreshed.completed_subtask_count == 1
    assert refreshed.progress_percent == 50
    db.close()


def test_long_term_subtask_can_create_daily_task() -> None:
    db = build_test_session()
    service = LongTermTaskService(db)
    task = service.create_task(LongTermTaskCreate(title="学习 Python 项目", category="学习", priority=3))
    subtask = service.create_subtask(
        task.id,
        LongTermSubtaskCreate(
            title="完成 Python 文件 IO 练习",
            category="Python",
            is_study=True,
            planned_duration_minutes=45,
            priority=5,
        ),
    )

    result = service.create_daily_task_from_subtask(
        subtask.id,
        LongTermSubtaskCreateDailyTaskRequest(task_date="2026-04-24"),
    )
    daily_task = db.get(DailyTask, result.daily_task.id)

    assert daily_task is not None
    assert daily_task.title == "完成 Python 文件 IO 练习"
    assert daily_task.category == "Python"
    assert daily_task.is_study is True
    assert daily_task.task_date == "2026-04-24"
    assert result.subtask.linked_daily_task_id == daily_task.id
    db.close()


def test_deleting_long_term_task_cascades_subtasks() -> None:
    db = build_test_session()
    service = LongTermTaskService(db)
    task = service.create_task(LongTermTaskCreate(title="项目升级", category="项目", priority=3))
    service.create_subtask(task.id, LongTermSubtaskCreate(title="数据库设计", category="开发"))

    service.delete_task(task.id)

    assert db.scalars(select(LongTermSubtask)).all() == []
    db.close()


def test_study_stats_by_category_can_represent_subjects() -> None:
    db = build_test_session()
    db.add_all(
        [
            StudySession(
                task_id=None,
                task_title_snapshot="数学刷题",
                category_snapshot="数学",
                session_date="2026-04-24",
                start_at="2026-04-24 08:00:00",
                end_at="2026-04-24 09:00:00",
                duration_minutes=60,
                source="manual",
            ),
            StudySession(
                task_id=None,
                task_title_snapshot="Python 练习",
                category_snapshot="Python",
                session_date="2026-04-24",
                start_at="2026-04-24 10:00:00",
                end_at="2026-04-24 10:45:00",
                duration_minutes=45,
                source="manual",
            ),
            StudySession(
                task_id=None,
                task_title_snapshot="数学复盘",
                category_snapshot="数学",
                session_date="2026-04-24",
                start_at="2026-04-24 11:00:00",
                end_at="2026-04-24 11:30:00",
                duration_minutes=30,
                source="manual",
            ),
        ]
    )
    db.commit()

    stats = StatsService(db).get_by_category("2026-04-24", "2026-04-24")
    stat_map = {item.category: item.duration_minutes for item in stats.items}

    assert stat_map["数学"] == 90
    assert stat_map["Python"] == 45
    db.close()
