from __future__ import annotations

from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session, sessionmaker

import app.models  # noqa: F401
from app.models.ai_log import AILog
from app.models.base import Base
from app.models.daily_task import DailyTask
from app.models.event import Event
from app.schemas.ai import AIAction, AIParseApplyRequest
from app.services.ai_service import AIService
from app.utils.json_utils import dumps_json


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


def create_parse_log(db: Session, date_context: str | None = "2026-04-23") -> AILog:
    log = AILog(
        log_type="parse",
        provider="deepseek",
        model_name="deepseek-chat",
        user_input="明天开会并学习 Python",
        context_json=dumps_json({"date_context": date_context}),
        ai_output_json=dumps_json({"actions": []}),
        parsed_success=True,
        applied_success=False,
        error_message=None,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def test_parse_apply_uses_date_context_and_allows_missing_time_or_location() -> None:
    db = build_test_session()
    log = create_parse_log(db)

    result = AIService(db).parse_apply(
        AIParseApplyRequest(
            log_id=log.id,
            actions=[
                AIAction(action_type="add_task", title="学习 Python", is_study=True, start_time="08:00"),
                AIAction(action_type="add_event", title="项目沟通", location=None),
            ],
        )
    )

    task = db.scalars(select(DailyTask)).one()
    event = db.scalars(select(Event)).one()

    assert result.created_task_ids == [task.id]
    assert result.created_event_ids == [event.id]
    assert task.task_date == "2026-04-23"
    assert task.start_time is None
    assert task.end_time is None
    assert event.event_date == "2026-04-23"
    assert event.start_time is None
    assert event.end_time is None
    assert event.location is None
    db.close()


def test_parse_apply_still_requires_title_for_task_or_event() -> None:
    db = build_test_session()
    log = create_parse_log(db)

    try:
        AIParseApplyRequest(log_id=log.id, actions=[AIAction(action_type="add_task", date="2026-04-23")])
    except Exception:
        pass
    else:
        raise AssertionError("expected AIAction validation to require a title")
    finally:
        db.close()
