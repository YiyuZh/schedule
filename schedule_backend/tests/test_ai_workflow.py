from __future__ import annotations

from typing import Any

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

import app.models  # noqa: F401
from app.core.response import AppException
from app.models.daily_task import DailyTask
from app.models.event import Event
from app.models.ai_log import AILog
from app.models.base import Base
from app.schemas.ai import AIAction, AIParseApplyRequest, AIParseRequest, AIPlanApplyRequest, AIPlanRequest
from app.schemas.common import SettingValueTypeEnum
from app.schemas.daily_task import DailyTaskCreate
from app.schemas.settings import SettingValueUpdate
from app.services.ai_provider_client import AIProviderResult, AIRuntimeConfig, OpenAICompatibleClient
from app.services.ai_service import AIService
from app.services.settings_service import SettingsService


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


def build_runtime_config() -> AIRuntimeConfig:
    return AIRuntimeConfig(
        enabled=True,
        provider="deepseek",
        base_url="https://api.deepseek.com/v1",
        api_key="sk-test",
        model_name="deepseek-chat",
        timeout=60,
        temperature=0.2,
        plan_model_name="deepseek-reasoner",
    )


def seed_ai_config(db: Session) -> None:
    settings_service = SettingsService(db)
    settings_service.upsert_setting(
        "ai_enabled",
        SettingValueUpdate(value=True, value_type=SettingValueTypeEnum.bool, description="Enable AI"),
    )
    settings_service.upsert_setting(
        "ai_provider",
        SettingValueUpdate(value="deepseek", value_type=SettingValueTypeEnum.string, description="Provider"),
    )
    settings_service.upsert_setting(
        "ai_base_url",
        SettingValueUpdate(value="https://api.deepseek.com/v1", value_type=SettingValueTypeEnum.string, description="Base URL"),
    )
    settings_service.upsert_setting(
        "ai_api_key",
        SettingValueUpdate(value="sk-test", value_type=SettingValueTypeEnum.string, description="API key"),
    )
    settings_service.upsert_setting(
        "ai_model_name",
        SettingValueUpdate(value="deepseek-chat", value_type=SettingValueTypeEnum.string, description="Parse model"),
    )
    settings_service.upsert_setting(
        "ai_plan_model_name",
        SettingValueUpdate(
            value="deepseek-reasoner",
            value_type=SettingValueTypeEnum.string,
            description="Plan model",
        ),
    )
    settings_service.upsert_setting(
        "ai_timeout",
        SettingValueUpdate(value=60, value_type=SettingValueTypeEnum.int, description="Timeout"),
    )
    settings_service.upsert_setting(
        "ai_temperature",
        SettingValueUpdate(value=0.2, value_type=SettingValueTypeEnum.float, description="Temperature"),
    )


def stub_ai_response(monkeypatch, raw_text: str, *, reasoning_content: str | None = None) -> None:
    def fake_create_json_completion(self, **kwargs) -> AIProviderResult:  # noqa: ARG001
        return AIProviderResult(
            raw_text=raw_text,
            response_id="resp_test",
            model_name=self.config.model_name,
            finish_reason="stop",
            usage={"total_tokens": 128},
            used_response_format=True,
            reasoning_content=reasoning_content,
        )

    monkeypatch.setattr(OpenAICompatibleClient, "create_json_completion", fake_create_json_completion)


def create_service() -> tuple[Session, AIService]:
    db = build_test_session()
    seed_ai_config(db)
    return db, AIService(db)


def test_parse_and_apply_workflow_creates_task_event_and_marks_log_applied(monkeypatch) -> None:
    db, service = create_service()
    stub_ai_response(
        monkeypatch,
        raw_text=(
            '{"actions": ['
            '{"action_type": "add_task", "title": "英语学习", "date": "2026-04-24", "start_time": "20:00",'
            '"end_time": "21:00", "category": "study", "is_study": true, "planned_duration_minutes": 60},'
            '{"action_type": "add_event", "title": "项目复盘", "date": "2026-04-24", "start_time": "15:00",'
            '"end_time": "16:00", "category": "meeting"}'
            "]}"
        ).strip(),
        reasoning_content="parse reasoning trace",
    )

    try:
        parse_result = service.parse(
            AIParseRequest(text="明天下午开会，晚上学习英语。", date_context="2026-04-24")
        )
        apply_result = service.parse_apply(
            AIParseApplyRequest(log_id=parse_result.raw_log_id, actions=parse_result.actions)
        )

        log = db.get(AILog, parse_result.raw_log_id)
        created_task = db.get(DailyTask, apply_result.created_task_ids[0])
        created_event = db.get(Event, apply_result.created_event_ids[0])

        assert len(parse_result.actions) == 2
        assert apply_result.created_task_ids
        assert apply_result.created_event_ids
        assert log is not None
        assert log.parsed_success is True
        assert log.applied_success is True
        assert "parse reasoning trace" in (log.ai_output_json or "")
        assert created_task is not None
        assert created_task.source == "ai"
        assert created_task.title == "英语学习"
        assert created_event is not None
        assert created_event.source == "ai"
        assert created_event.title == "项目复盘"
    finally:
        db.close()


def test_parse_apply_rejects_type_mismatch_and_duplicate_apply() -> None:
    db, service = create_service()
    runtime_config = build_runtime_config()

    try:
        plan_log = service._create_log(
            log_type="plan",
            user_input="安排今天",
            context={"date": "2026-04-24"},
            output={"plan_options": [{"name": "A", "reason": "test", "items": []}]},
            parsed_success=True,
            config=runtime_config,
        )

        try:
            service.parse_apply(
                AIParseApplyRequest(
                    log_id=plan_log.id,
                    actions=[AIAction(action_type="add_task", title="测试任务", date="2026-04-24")],
                )
            )
        except AppException as exc:
            assert exc.code == 4069
            assert exc.message == "ai log type mismatch: expected parse log"
        else:
            raise AssertionError("expected parse_apply to reject plan log")

        parse_log = service._create_log(
            log_type="parse",
            user_input="创建任务",
            context={"date_context": "2026-04-24"},
            output={"actions": [{"action_type": "add_task", "title": "测试任务", "date": "2026-04-24"}]},
            parsed_success=True,
            config=runtime_config,
        )
        parse_log.applied_success = True
        db.commit()

        try:
            service.parse_apply(
                AIParseApplyRequest(
                    log_id=parse_log.id,
                    actions=[AIAction(action_type="add_task", title="测试任务", date="2026-04-24")],
                )
            )
        except AppException as exc:
            assert exc.code == 4071
            assert exc.message == "ai log has already been applied"
        else:
            raise AssertionError("expected parse_apply to reject duplicate apply")
    finally:
        db.close()


def test_parse_apply_rejects_unsupported_action_and_marks_log_failed() -> None:
    db, service = create_service()
    runtime_config = build_runtime_config()

    try:
        parse_log = service._create_log(
            log_type="parse",
            user_input="安排已有任务",
            context={"date_context": "2026-04-24"},
            output={"actions": [{"action_type": "schedule_task", "task_id": 99}]},
            parsed_success=True,
            config=runtime_config,
        )

        try:
            service.parse_apply(
                AIParseApplyRequest(
                    log_id=parse_log.id,
                    actions=[AIAction(action_type="schedule_task", task_id=99)],
                )
            )
        except AppException as exc:
            assert exc.code == 4072
            assert exc.message == "unsupported parse action_type: schedule_task"
        else:
            raise AssertionError("expected parse_apply to reject unsupported action type")

        refreshed_log = db.get(AILog, parse_log.id)
        assert refreshed_log is not None
        assert refreshed_log.applied_success is False
        assert refreshed_log.error_message == "unsupported parse action_type: schedule_task"
    finally:
        db.close()


def test_plan_and_apply_workflow_schedules_task_and_creates_event(monkeypatch) -> None:
    db, service = create_service()
    task = service.daily_task_service.create_task(
        DailyTaskCreate(
            title="数学复习",
            category="study",
            is_study=True,
            task_date="2026-04-24",
            planned_duration_minutes=90,
            priority=5,
            status="pending",
            source="manual",
            sort_order=1,
        )
    )
    stub_ai_response(
        monkeypatch,
        raw_text=(
            '{"plan_options": ['
            '{"name": "专注学习", "reason": "先安排高优先级学习任务，再补一个收尾事件。", "items": ['
            '{"item_type": "task_schedule", "task_id": %d, "title": "数学复习", "date": "2026-04-24",'
            '"start_time": "19:00", "end_time": "20:30", "category": "study"},'
            '{"item_type": "event", "title": "拉伸放松", "date": "2026-04-24", "start_time": "21:00",'
            '"end_time": "21:20", "category": "health"}'
            "]}"
            "]}"
        )
        % task.id,
        reasoning_content="plan reasoning trace",
    )

    try:
        plan_result = service.plan(
            AIPlanRequest(date="2026-04-24", user_input="帮我安排今天晚上。", include_habits=False, option_count=1)
        )
        apply_result = service.plan_apply(
            AIPlanApplyRequest(log_id=plan_result.raw_log_id, selected_option_index=0)
        )

        log = db.get(AILog, plan_result.raw_log_id)
        refreshed_task = db.get(DailyTask, task.id)
        created_event = db.get(Event, apply_result.created_event_ids[0])

        assert len(plan_result.plan_options) == 1
        assert apply_result.scheduled_task_ids == [task.id]
        assert len(apply_result.created_event_ids) == 1
        assert log is not None
        assert log.applied_success is True
        assert "plan reasoning trace" in (log.ai_output_json or "")
        assert refreshed_task is not None
        assert refreshed_task.start_time == "19:00"
        assert refreshed_task.end_time == "20:30"
        assert created_event is not None
        assert created_event.title == "拉伸放松"
    finally:
        db.close()


def test_plan_apply_rejects_failed_wrong_type_and_duplicate_logs() -> None:
    db, service = create_service()
    runtime_config = build_runtime_config()

    try:
        failed_log = service._create_log(
            log_type="plan",
            user_input="安排今天",
            context={"date": "2026-04-24"},
            output={"plan_options": []},
            parsed_success=False,
            error_message="provider failed",
            config=runtime_config,
        )

        try:
            service.plan_apply(AIPlanApplyRequest(log_id=failed_log.id, selected_option_index=0))
        except AppException as exc:
            assert exc.code == 4070
            assert exc.message == "ai log cannot be applied because parsing did not succeed"
        else:
            raise AssertionError("expected plan_apply to reject failed plan log")

        parse_log = service._create_log(
            log_type="parse",
            user_input="创建任务",
            context={"date_context": "2026-04-24"},
            output={"actions": []},
            parsed_success=True,
            config=runtime_config,
        )

        try:
            service.plan_apply(AIPlanApplyRequest(log_id=parse_log.id, selected_option_index=0))
        except AppException as exc:
            assert exc.code == 4069
            assert exc.message == "ai log type mismatch: expected plan log"
        else:
            raise AssertionError("expected plan_apply to reject parse log")

        duplicate_log = service._create_log(
            log_type="plan",
            user_input="安排今天",
            context={"date": "2026-04-24"},
            output={
                "plan_options": [
                    {
                        "name": "A",
                        "reason": "test",
                        "items": [
                            {
                                "item_type": "event",
                                "title": "专注时间",
                                "date": "2026-04-24",
                                "start_time": "20:00",
                                "end_time": "21:00",
                                "category": "study",
                            }
                        ],
                    }
                ]
            },
            parsed_success=True,
            config=runtime_config,
        )
        duplicate_log.applied_success = True
        db.commit()

        try:
            service.plan_apply(AIPlanApplyRequest(log_id=duplicate_log.id, selected_option_index=0))
        except AppException as exc:
            assert exc.code == 4071
            assert exc.message == "ai log has already been applied"
        else:
            raise AssertionError("expected plan_apply to reject duplicate apply")
    finally:
        db.close()
