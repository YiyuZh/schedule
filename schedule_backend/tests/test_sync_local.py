from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import create_engine, event, select, text
from sqlalchemy.orm import Session, sessionmaker

import app.models  # noqa: F401
from app.core.response import AppException
from app.core.sync_schema import ensure_sync_schema
from app.models.base import Base
from app.models.daily_task import DailyTask
from app.models.long_term_task import LongTermSubtask, LongTermTask
from app.models.study_session import StudySession
from app.models.sync import SyncQueue
from app.schemas.daily_task import DailyTaskCreate
from app.schemas.sync import SyncConfigUpdate, SyncLoginRequest, SyncRegisterRequest
from app.services.daily_task_service import DailyTaskService
from app.services.sync_client import SyncClientError
from app.services.sync_service import SyncService


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


def test_sync_status_is_stable_when_unconfigured() -> None:
    db = build_test_session()
    status = SyncService(db).get_status()

    assert status.enabled is True
    assert status.configured is True
    assert status.logged_in is False
    assert status.server_url == "https://schedule-sync.zenithy.art"
    assert status.pending_count == 0
    assert status.device_id
    db.close()


def test_sync_config_saves_server_url_and_device_name() -> None:
    db = build_test_session()
    status = SyncService(db).save_config(
        SyncConfigUpdate(server_url="https://sync.example.com/", device_name="Work PC", enabled=True)
    )

    assert status.enabled is True
    assert status.server_url == "https://sync.example.com"
    assert status.device_name == "Work PC"
    db.close()


def test_daily_task_write_adds_sync_queue_without_ai_key() -> None:
    db = build_test_session()
    task = DailyTaskService(db).create_task(
        DailyTaskCreate(
            title="项目复盘",
            category="工作",
            is_study=False,
            task_date="2026-04-24",
            planned_duration_minutes=30,
            priority=3,
        )
    )

    queue_items = db.scalars(select(SyncQueue)).all()

    assert task.id is not None
    assert len(queue_items) == 1
    assert queue_items[0].entity_type == "daily_task"
    assert queue_items[0].operation == "upsert"
    assert "ai_api_key" not in queue_items[0].payload_json
    db.close()


def test_login_unreachable_server_returns_clear_error(monkeypatch: pytest.MonkeyPatch) -> None:
    class BrokenClient:
        def __init__(self, _server_url: str) -> None:
            pass

        def login(self, **_kwargs):
            raise SyncClientError("无法连接云同步服务器：connection refused")

    monkeypatch.setattr("app.services.sync_service.SyncClient", BrokenClient)

    db = build_test_session()
    service = SyncService(db)

    with pytest.raises(AppException) as exc:
        service.login(
            SyncLoginRequest(
                email="user@example.com",
                password="secret",
                server_url="https://sync.example.com",
                device_name="Work PC",
            )
        )

    assert "无法连接云同步服务器" in exc.value.message
    assert service.get_status().last_error == "无法连接云同步服务器：connection refused"
    db.close()


def test_register_account_calls_cloud_register_and_login(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeClient:
        def __init__(self, _server_url: str) -> None:
            pass

        def register(self, **kwargs):
            assert kwargs["email"] == "new@example.com"
            return {"id": 1, "email": kwargs["email"]}

        def login(self, **kwargs):
            return {"access_token": "access-token", "refresh_token": "refresh-token"}

        def bootstrap(self, **_kwargs):
            return {"items": [], "latest_change_id": 9}

    monkeypatch.setattr("app.services.sync_service.SyncClient", FakeClient)

    db = build_test_session()
    status = SyncService(db).register_account(
        SyncRegisterRequest(
            email="new@example.com",
            password="password123",
            display_name="New User",
            server_url="https://sync.example.com",
            device_name="Work PC",
        )
    )

    assert status.logged_in is True
    assert status.user_email == "new@example.com"
    assert status.last_pull_at is not None
    db.close()


def test_push_keeps_rejected_queue_items(monkeypatch: pytest.MonkeyPatch) -> None:
    class RejectingClient:
        def __init__(self, _server_url: str) -> None:
            pass

        def push(self, **kwargs):
            queue_id = kwargs["changes"][0]["queue_id"]
            return {
                "accepted_count": 0,
                "rejected_count": 1,
                "accepted_queue_ids": [],
                "rejected_items": [{"queue_id": queue_id, "message": "云端版本已更新"}],
            }

    monkeypatch.setattr("app.services.sync_service.SyncClient", RejectingClient)

    db = build_test_session()
    DailyTaskService(db).create_task(
        DailyTaskCreate(title="同步冲突", category="工作", task_date="2026-04-24")
    )
    state = SyncService(db).get_or_create_state()
    state.server_url = "https://sync.example.com"
    state.access_token = "token"
    db.commit()

    result = SyncService(db).push()
    queue_items = db.scalars(select(SyncQueue)).all()

    assert result.error_count == 1
    assert len(queue_items) == 1
    assert queue_items[0].last_error == "云端版本已更新"
    db.close()


def test_push_deletes_only_accepted_queue_items(monkeypatch: pytest.MonkeyPatch) -> None:
    class AcceptingClient:
        def __init__(self, _server_url: str) -> None:
            pass

        def push(self, **kwargs):
            change = kwargs["changes"][0]
            payload = change["payload"]
            return {
                "accepted_count": 1,
                "rejected_count": 0,
                "accepted_queue_ids": [change["queue_id"]],
                "accepted_items": [
                    {
                        "queue_id": change["queue_id"],
                        "entity_type": change["entity_type"],
                        "entity_id": payload["sync_id"],
                        "sync_version": 7,
                    }
                ],
            }

    monkeypatch.setattr("app.services.sync_service.SyncClient", AcceptingClient)

    db = build_test_session()
    DailyTaskService(db).create_task(
        DailyTaskCreate(title="同步成功", category="工作", task_date="2026-04-24")
    )
    state = SyncService(db).get_or_create_state()
    state.server_url = "https://sync.example.com"
    state.access_token = "token"
    db.commit()

    result = SyncService(db).push()
    queue_items = db.scalars(select(SyncQueue)).all()
    task = db.scalar(select(DailyTask))

    assert result.error_count == 0
    assert result.push_count == 1
    assert queue_items == []
    assert task is not None
    assert task.sync_dirty is False
    assert task.sync_version == 7
    assert task.last_synced_at is not None
    db.close()


def test_ensure_sync_schema_adds_columns_and_backfills_sync_id(tmp_path: Path) -> None:
    db_path = tmp_path / "legacy.db"
    engine = create_engine(f"sqlite+pysqlite:///{db_path}")
    with engine.begin() as connection:
        for table_name in ("daily_tasks", "long_term_tasks", "long_term_subtasks"):
            connection.execute(text(f"CREATE TABLE {table_name} (id INTEGER PRIMARY KEY AUTOINCREMENT)"))
            connection.execute(text(f"INSERT INTO {table_name} DEFAULT VALUES"))

    ensure_sync_schema(engine)

    with engine.connect() as connection:
        rows = connection.execute(text("PRAGMA table_info(daily_tasks)")).mappings().all()
        columns = {row["name"] for row in rows}
        sync_id = connection.execute(text("SELECT sync_id FROM daily_tasks WHERE id = 1")).scalar_one()

    assert {"sync_id", "sync_version", "sync_dirty", "sync_deleted", "last_synced_at", "updated_by_device_id"} <= columns
    assert sync_id


def test_pull_applies_remote_daily_task_to_business_table(monkeypatch: pytest.MonkeyPatch) -> None:
    class PullingClient:
        def __init__(self, _server_url: str) -> None:
            pass

        def pull(self, **_kwargs):
            return {
                "latest_change_id": 1,
                "changes": [
                    {
                        "change_id": 1,
                        "entity_type": "daily_task",
                        "entity_id": "task-sync-1",
                        "operation": "upsert",
                        "remote_version": 2,
                        "payload": {
                            "sync_id": "task-sync-1",
                            "sync_version": 2,
                            "title": "手机创建任务",
                            "category": "Python",
                            "is_study": True,
                            "task_date": "2026-04-25",
                            "planned_duration_minutes": 45,
                            "actual_duration_minutes": 0,
                            "priority": "high",
                            "status": "pending",
                            "source": "mobile",
                            "sort_order": 1,
                        },
                    }
                ],
            }

    monkeypatch.setattr("app.services.sync_service.SyncClient", PullingClient)
    db = build_test_session()
    state = SyncService(db).get_or_create_state()
    state.server_url = "https://sync.example.com"
    state.access_token = "token"
    db.commit()

    result = SyncService(db).pull()
    task = db.scalar(select(DailyTask).where(DailyTask.sync_id == "task-sync-1"))

    assert result.conflict_count == 0
    assert task is not None
    assert task.title == "手机创建任务"
    assert task.priority == 5
    assert task.source == "manual"
    db.close()


def test_pull_resolves_long_term_subtask_relation_by_sync_id(monkeypatch: pytest.MonkeyPatch) -> None:
    class PullingClient:
        def __init__(self, _server_url: str) -> None:
            pass

        def pull(self, **_kwargs):
            return {
                "latest_change_id": 2,
                "changes": [
                    {
                        "change_id": 1,
                        "entity_type": "long_term_task",
                        "entity_id": "goal-sync-1",
                        "operation": "upsert",
                        "remote_version": 1,
                        "payload": {
                            "entity_type": "long_term_task",
                            "sync_id": "goal-sync-1",
                            "sync_version": 1,
                            "data": {
                                "sync_id": "goal-sync-1",
                                "title": "本月项目升级",
                                "category": "项目",
                                "status": "active",
                                "priority": "medium",
                                "progress_percent": 0,
                                "sort_order": 1,
                            },
                        },
                    },
                    {
                        "change_id": 2,
                        "entity_type": "long_term_subtask",
                        "entity_id": "sub-sync-1",
                        "operation": "upsert",
                        "remote_version": 1,
                        "payload": {
                            "entity_type": "long_term_subtask",
                            "sync_id": "sub-sync-1",
                            "sync_version": 1,
                            "relation_sync_ids": {"long_task_sync_id": "goal-sync-1"},
                            "data": {
                                "sync_id": "sub-sync-1",
                                "long_task_id": "goal-sync-1",
                                "title": "完成 PRD 设计",
                                "category": "项目",
                                "is_study": False,
                                "planned_duration_minutes": 60,
                                "status": "pending",
                                "priority": "high",
                                "sort_order": 1,
                            },
                        },
                    },
                ],
            }

    monkeypatch.setattr("app.services.sync_service.SyncClient", PullingClient)
    db = build_test_session()
    state = SyncService(db).get_or_create_state()
    state.server_url = "https://sync.example.com"
    state.access_token = "token"
    db.commit()

    result = SyncService(db).pull()
    goal = db.scalar(select(LongTermTask).where(LongTermTask.sync_id == "goal-sync-1"))
    subtask = db.scalar(select(LongTermSubtask).where(LongTermSubtask.sync_id == "sub-sync-1"))

    assert result.conflict_count == 0
    assert goal is not None
    assert subtask is not None
    assert subtask.long_task_id == goal.id
    db.close()


def test_pull_applies_remote_study_session_with_task_relation(monkeypatch: pytest.MonkeyPatch) -> None:
    class PullingClient:
        def __init__(self, _server_url: str) -> None:
            pass

        def pull(self, **_kwargs):
            return {
                "latest_change_id": 2,
                "changes": [
                    {
                        "change_id": 1,
                        "entity_type": "daily_task",
                        "entity_id": "study-task-sync",
                        "operation": "upsert",
                        "remote_version": 1,
                        "payload": {
                            "sync_id": "study-task-sync",
                            "title": "学习 Python",
                            "category": "Python",
                            "is_study": True,
                            "task_date": "2026-04-25",
                            "planned_duration_minutes": 30,
                            "actual_duration_minutes": 30,
                            "priority": "medium",
                            "status": "completed",
                            "source": "manual",
                            "sort_order": 1,
                        },
                    },
                    {
                        "change_id": 2,
                        "entity_type": "study_session",
                        "entity_id": "session-sync-1",
                        "operation": "upsert",
                        "remote_version": 1,
                        "payload": {
                            "sync_id": "session-sync-1",
                            "relation_sync_ids": {"task_sync_id": "study-task-sync"},
                            "data": {
                                "sync_id": "session-sync-1",
                                "task_id": "study-task-sync",
                                "task_title_snapshot": "学习 Python",
                                "category_snapshot": "Python",
                                "session_date": "2026-04-25",
                                "start_at": "2026-04-25 09:00:00",
                                "end_at": "2026-04-25 09:30:00",
                                "duration_minutes": 30,
                                "source": "manual",
                            },
                        },
                    },
                ],
            }

    monkeypatch.setattr("app.services.sync_service.SyncClient", PullingClient)
    db = build_test_session()
    state = SyncService(db).get_or_create_state()
    state.server_url = "https://sync.example.com"
    state.access_token = "token"
    db.commit()

    result = SyncService(db).pull()
    task = db.scalar(select(DailyTask).where(DailyTask.sync_id == "study-task-sync"))
    session = db.scalar(select(StudySession).where(StudySession.sync_id == "session-sync-1"))

    assert result.conflict_count == 0
    assert task is not None
    assert session is not None
    assert session.task_id == task.id
    db.close()
