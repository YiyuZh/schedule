from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.response import AppException
from app.models.ai_log import AILog
from app.models.daily_task import DailyTask
from app.schemas.ai import (
    AIAction,
    AIConfigRead,
    AIConfigUpdate,
    AILogListData,
    AILogQuery,
    AILogRead,
    AIParseApplyData,
    AIParseApplyRequest,
    AIParseData,
    AIParseRequest,
    AIPlanApplyData,
    AIPlanApplyRequest,
    AIPlanData,
    AIPlanItem,
    AIPlanRequest,
    AITestConnectionData,
)
from app.schemas.common import AILogTypeEnum, EventSourceEnum, TaskSourceEnum, TaskStatusEnum
from app.schemas.course import CourseCreate
from app.schemas.daily_task import DailyTaskCreate, DailyTaskPatch, DailyTaskQuery
from app.schemas.event import EventCreate, EventQuery
from app.services.ai_prompt_builder import (
    build_parse_prompts,
    build_parse_repair_prompts,
    build_plan_prompts,
    build_plan_repair_prompts,
    build_test_connection_prompts,
)
from app.services.ai_provider_client import AIRuntimeConfig, OpenAICompatibleClient
from app.services.ai_response_parser import (
    AITestConnectionEnvelope,
    parse_parse_response,
    parse_plan_response,
    parse_test_connection_response,
    get_parse_schema,
    get_plan_schema,
    get_test_connection_schema,
)
from app.services.course_service import CourseService
from app.services.daily_task_service import DailyTaskService
from app.services.event_service import EventService
from app.services.settings_service import SettingsService
from app.services.stats_service import StatsService
from app.utils.datetime_utils import shift_date, today_str
from app.utils.json_utils import dumps_json, loads_json


class AIWorkflowException(AppException):
    def __init__(
        self,
        message: str,
        *,
        log_output: dict[str, Any] | None = None,
        code: int = 4068,
        status_code: int = 502,
    ) -> None:
        super().__init__(message, code=code, status_code=status_code)
        self.log_output = log_output or {}


@dataclass(slots=True)
class AIExecutionMeta:
    initial_raw_text: str
    response_id: str | None
    response_model: str | None
    finish_reason: str | None
    usage: dict[str, Any] | None
    used_response_format: bool
    reasoning_content: str | None = None
    repair_attempted: bool = False
    repair_raw_text: str | None = None
    repair_response_id: str | None = None
    repair_response_model: str | None = None
    repair_finish_reason: str | None = None
    repair_usage: dict[str, Any] | None = None
    repair_reasoning_content: str | None = None
    validation_error: str | None = None

    def to_log_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "_meta": {
                "response_id": self.response_id,
                "response_model": self.response_model,
                "finish_reason": self.finish_reason,
                "usage": self.usage,
                "used_response_format": self.used_response_format,
                "reasoning_content": self.reasoning_content,
                "repair_attempted": self.repair_attempted,
                "validation_error": self.validation_error,
            },
            "_raw_text": self.initial_raw_text,
        }
        if self.repair_attempted:
            payload["_repair"] = {
                "raw_text": self.repair_raw_text,
                "response_id": self.repair_response_id,
                "response_model": self.repair_response_model,
                "finish_reason": self.repair_finish_reason,
                "usage": self.repair_usage,
                "reasoning_content": self.repair_reasoning_content,
            }
        return payload


class AIService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.settings_service = SettingsService(db)
        self.daily_task_service = DailyTaskService(db)
        self.event_service = EventService(db)
        self.course_service = CourseService(db)
        self.stats_service = StatsService(db)

    def _build_setting_update(self, value: Any, value_type: str, description: str):
        from app.schemas.common import SettingValueTypeEnum
        from app.schemas.settings import SettingValueUpdate

        return SettingValueUpdate(value=value, value_type=SettingValueTypeEnum(value_type), description=description)

    def _normalize_provider(self, provider: str) -> str:
        value = provider.strip().replace("-", "_")
        if not value or value == "mock":
            return "openai_compatible"
        return value

    def _load_runtime_config(self, *, require_enabled: bool) -> AIRuntimeConfig:
        values = self.settings_service.get_settings_map(
            [
                "ai_enabled",
                "ai_provider",
                "ai_base_url",
                "ai_api_key",
                "ai_model_name",
                "ai_plan_model_name",
                "ai_timeout",
                "ai_temperature",
            ]
        )

        provider = self._normalize_provider(str(values.get("ai_provider") or "deepseek"))

        model_name = str(values.get("ai_model_name") or "").strip()
        plan_model_name = str(values.get("ai_plan_model_name") or "").strip() or model_name
        base_url = str(values.get("ai_base_url") or "").strip()
        api_key = str(values.get("ai_api_key") or "").strip()

        config = AIRuntimeConfig(
            enabled=bool(values.get("ai_enabled", False)),
            provider=provider,
            base_url=base_url,
            api_key=api_key,
            model_name=model_name,
            timeout=max(1, int(values.get("ai_timeout", 60) or 60)),
            temperature=float(values.get("ai_temperature", 0.2) or 0.2),
            plan_model_name=plan_model_name,
        )

        if require_enabled and not config.enabled:
            raise AppException("AI is disabled. Enable ai_enabled before using AI features.", code=4060, status_code=400)
        if require_enabled and not config.base_url:
            raise AppException("AI base URL is not configured.", code=4061, status_code=400)
        if require_enabled and (not config.model_name or config.model_name.startswith("mock-")):
            raise AppException("AI model name is not configured.", code=4062, status_code=400)
        if require_enabled and config.requires_api_key and not config.api_key:
            raise AppException(
                "AI API key is missing. Set ai_api_key before calling the AI provider.",
                code=4063,
                status_code=400,
            )
        return config

    def _build_client(self, config: AIRuntimeConfig) -> OpenAICompatibleClient:
        return OpenAICompatibleClient(config)

    def _get_parse_client(self) -> tuple[AIRuntimeConfig, OpenAICompatibleClient]:
        config = self._load_runtime_config(require_enabled=True)
        parse_config = config.clone_for_model(config.model_name)
        return parse_config, self._build_client(parse_config)

    def _get_plan_client(self) -> tuple[AIRuntimeConfig, OpenAICompatibleClient]:
        config = self._load_runtime_config(require_enabled=True)
        plan_config = config.clone_for_model(config.effective_plan_model_name)
        return plan_config, self._build_client(plan_config)

    def get_config(self) -> AIConfigRead:
        config = self._load_runtime_config(require_enabled=False)
        return AIConfigRead(
            enabled=config.enabled,
            provider=config.provider_label,
            model_name=config.model_name,
            plan_model_name=config.effective_plan_model_name,
            base_url=config.base_url,
            has_api_key=bool(config.api_key),
            timeout=config.timeout,
            temperature=config.temperature,
        )

    def update_config(self, payload: AIConfigUpdate) -> AIConfigRead:
        provider = self._normalize_provider(payload.provider.strip() or "deepseek")
        self.settings_service.upsert_setting("ai_enabled", self._build_setting_update(payload.enabled, "bool", "Enable AI"))
        self.settings_service.upsert_setting("ai_provider", self._build_setting_update(provider, "string", "AI provider label"))
        self.settings_service.upsert_setting(
            "ai_base_url",
            self._build_setting_update(payload.base_url.strip(), "string", "OpenAI-compatible base URL"),
        )
        if payload.api_key is not None:
            self.settings_service.upsert_setting(
                "ai_api_key",
                self._build_setting_update(payload.api_key.strip(), "string", "AI provider API key"),
            )
        self.settings_service.upsert_setting(
            "ai_model_name",
            self._build_setting_update(payload.model_name.strip(), "string", "AI chat / parse model name"),
        )
        self.settings_service.upsert_setting(
            "ai_plan_model_name",
            self._build_setting_update(payload.plan_model_name.strip(), "string", "AI planning / reasoning model name"),
        )
        self.settings_service.upsert_setting("ai_timeout", self._build_setting_update(payload.timeout, "int", "AI timeout seconds"))
        self.settings_service.upsert_setting(
            "ai_temperature",
            self._build_setting_update(payload.temperature, "float", "AI generation temperature"),
        )
        return self.get_config()

    def _create_log(
        self,
        *,
        log_type: str,
        user_input: str,
        context: dict[str, Any],
        output: dict[str, Any],
        parsed_success: bool,
        error_message: str | None = None,
        config: AIRuntimeConfig | None = None,
    ) -> AILog:
        runtime_config = config or self._load_runtime_config(require_enabled=False)
        log = AILog(
            log_type=log_type,
            provider=runtime_config.provider_label,
            model_name=runtime_config.model_name or None,
            user_input=user_input,
            context_json=dumps_json(context),
            ai_output_json=dumps_json(output),
            parsed_success=parsed_success,
            applied_success=False,
            error_message=error_message,
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    def _mark_log_apply_failed(self, log: AILog, message: str) -> None:
        log.applied_success = False
        log.error_message = message
        self.db.commit()

    def _get_applicable_log(self, log_id: int, *, expected_type: AILogTypeEnum) -> AILog:
        log = self._get_log_model(log_id)
        if log.log_type != expected_type.value:
            raise AppException(
                f"ai log type mismatch: expected {expected_type.value} log",
                code=4069,
                status_code=400,
            )
        if not log.parsed_success:
            raise AppException(
                "ai log cannot be applied because parsing did not succeed",
                code=4070,
                status_code=400,
            )
        if log.applied_success:
            raise AppException("ai log has already been applied", code=4071, status_code=409)
        return log

    def _execute_structured_generation(
        self,
        *,
        client: OpenAICompatibleClient,
        system_prompt: str,
        user_prompt: str,
        parser: Callable[[str], Any],
        repair_prompt_builder: Callable[[str, str], tuple[str, str]],
        max_tokens: int,
    ) -> tuple[Any, AIExecutionMeta]:
        initial_response = client.create_json_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=max_tokens,
        )
        meta = AIExecutionMeta(
            initial_raw_text=initial_response.raw_text,
            response_id=initial_response.response_id,
            response_model=initial_response.model_name,
            finish_reason=initial_response.finish_reason,
            usage=initial_response.usage,
            used_response_format=initial_response.used_response_format,
            reasoning_content=initial_response.reasoning_content,
        )

        try:
            parsed = parser(initial_response.raw_text)
            return parsed, meta
        except AppException as first_error:
            meta.repair_attempted = True
            meta.validation_error = first_error.message

        repair_system_prompt, repair_user_prompt = repair_prompt_builder(meta.initial_raw_text, meta.validation_error or "Invalid JSON")
        try:
            repair_response = client.create_json_completion(
                system_prompt=repair_system_prompt,
                user_prompt=repair_user_prompt,
                temperature=0.0,
                max_tokens=max_tokens,
            )
        except AppException as exc:
            raise AIWorkflowException(
                exc.message,
                log_output=meta.to_log_dict(),
                code=exc.code,
                status_code=exc.status_code,
            ) from exc

        meta.repair_raw_text = repair_response.raw_text
        meta.repair_response_id = repair_response.response_id
        meta.repair_response_model = repair_response.model_name
        meta.repair_finish_reason = repair_response.finish_reason
        meta.repair_usage = repair_response.usage
        meta.repair_reasoning_content = repair_response.reasoning_content

        try:
            parsed = parser(repair_response.raw_text)
            return parsed, meta
        except AppException as repair_error:
            raise AIWorkflowException(
                f"AI returned invalid JSON after repair: {repair_error.message}",
                log_output=meta.to_log_dict(),
                code=4068,
                status_code=502,
            ) from repair_error

    def _run_test_connection_check(self, config: AIRuntimeConfig) -> tuple[bool, str]:
        client = self._build_client(config)
        system_prompt, user_prompt = build_test_connection_prompts(get_test_connection_schema())
        try:
            response = client.create_json_completion(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.0,
                max_tokens=120,
            )
            result: AITestConnectionEnvelope = parse_test_connection_response(response.raw_text)
        except AppException as exc:
            return False, exc.message

        return True, result.message or f"Connected to {config.provider_label}/{config.model_name}."

    def test_connection(self) -> AITestConnectionData:
        config = self._load_runtime_config(require_enabled=True)
        parse_config = config.clone_for_model(config.model_name)

        if config.provider_label == "deepseek":
            plan_config = config.clone_for_model(config.effective_plan_model_name)
            chat_ok, chat_message = self._run_test_connection_check(parse_config)
            plan_ok, plan_message = self._run_test_connection_check(plan_config)
            return AITestConnectionData(
                ok=chat_ok and plan_ok,
                message=(
                    f"chat ({parse_config.model_name}): {chat_message} | "
                    f"reasoner ({plan_config.model_name}): {plan_message}"
                ),
            )

        ok, message = self._run_test_connection_check(parse_config)
        return AITestConnectionData(ok=ok, message=message)

    def parse(self, payload: AIParseRequest) -> AIParseData:
        context = {"date_context": payload.date_context}
        base_config = self._load_runtime_config(require_enabled=False)
        config = base_config.clone_for_model(base_config.model_name)
        try:
            config, client = self._get_parse_client()
            system_prompt, user_prompt = build_parse_prompts(
                text=payload.text,
                date_context=payload.date_context,
                schema=get_parse_schema(),
            )
            parsed, meta = self._execute_structured_generation(
                client=client,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                parser=parse_parse_response,
                repair_prompt_builder=lambda raw_text, error_message: build_parse_repair_prompts(
                    invalid_response=raw_text,
                    validation_error=error_message,
                    schema=get_parse_schema(),
                ),
                max_tokens=1400,
            )
        except AppException as exc:
            log_output = exc.log_output if isinstance(exc, AIWorkflowException) else {}
            self._create_log(
                log_type=AILogTypeEnum.parse.value,
                user_input=payload.text,
                context=context,
                output=log_output,
                parsed_success=False,
                error_message=exc.message,
                config=config,
            )
            raise

        output = parsed.model_dump()
        output.update(meta.to_log_dict())
        log = self._create_log(
            log_type=AILogTypeEnum.parse.value,
            user_input=payload.text,
            context=context,
            output=output,
            parsed_success=True,
            config=config,
        )
        return AIParseData(actions=parsed.actions, raw_log_id=log.id)

    def parse_apply(self, payload: AIParseApplyRequest) -> AIParseApplyData:
        log = self._get_applicable_log(payload.log_id, expected_type=AILogTypeEnum.parse)
        created_task_ids: list[int] = []
        created_event_ids: list[int] = []
        created_course_ids: list[int] = []
        context = loads_json(log.context_json, default={}) or {}
        default_date = str(context.get("date_context") or today_str())

        try:
            for action in payload.actions:
                action_date = action.date or default_date
                start_time, end_time = self._normalize_optional_time_pair(action.start_time, action.end_time)
                if action.action_type == "add_task":
                    task = self.daily_task_service.create_task(
                        DailyTaskCreate(
                            template_id=None,
                            title=action.title or "New Task",
                            category=action.category or "other",
                            is_study=bool(action.is_study),
                            task_date=action_date,
                            start_time=start_time,
                            end_time=end_time,
                            planned_duration_minutes=action.planned_duration_minutes or 30,
                            priority=3,
                            status=TaskStatusEnum.pending,
                            source=TaskSourceEnum.ai,
                            sort_order=0,
                            notes=None,
                        )
                    )
                    created_task_ids.append(task.id)
                elif action.action_type == "add_event":
                    event = self.event_service.create_event(
                        EventCreate(
                            title=action.title or "New Event",
                            category=action.category or "other",
                            event_date=action_date,
                            start_time=start_time,
                            end_time=end_time,
                            location=action.location,
                            priority=3,
                            status="scheduled",
                            source=EventSourceEnum.ai,
                            linked_task_id=None,
                            notes=None,
                        )
                    )
                    created_event_ids.append(event.id)
                elif action.action_type == "add_course":
                    course = self.course_service.create_course(
                        CourseCreate(
                            batch_id=None,
                            course_name=action.title or "AI Course",
                            weekday=action.weekday or 1,
                            start_time=action.start_time or "08:00",
                            end_time=action.end_time or "09:00",
                            location=action.location,
                            teacher=action.teacher,
                            term_name=action.term_name or "AI Imported Term",
                            term_start_date=action.term_start_date or (action.date or today_str()),
                            term_end_date=action.term_end_date or (action.date or today_str()),
                            week_list=action.week_list or [1],
                            color=None,
                            notes=None,
                        )
                    )
                    created_course_ids.append(course.id)
                else:
                    raise AppException(
                        f"unsupported parse action_type: {action.action_type}",
                        code=4072,
                        status_code=400,
                    )
        except AppException as exc:
            self._mark_log_apply_failed(log, exc.message)
            raise
        except Exception as exc:  # pragma: no cover - defensive
            self._mark_log_apply_failed(log, str(exc))
            raise AppException(str(exc), code=5000, status_code=500) from exc

        log.applied_success = True
        log.error_message = None
        self.db.commit()
        return AIParseApplyData(
            created_task_ids=created_task_ids,
            created_event_ids=created_event_ids,
            created_course_ids=created_course_ids,
        )

    def _normalize_optional_time_pair(self, start_time: str | None, end_time: str | None) -> tuple[str | None, str | None]:
        if start_time and end_time:
            return start_time, end_time
        return None, None

    def _time_preference_from_hour(self, start_time: str | None) -> str | None:
        if not start_time:
            return None
        hour = int(start_time.split(":", maxsplit=1)[0])
        if 5 <= hour < 12:
            return "morning"
        if 12 <= hour < 18:
            return "afternoon"
        if 18 <= hour < 22:
            return "evening"
        return "night"

    def _build_habit_snapshot(self, date_value: str) -> dict[str, Any]:
        lookback_start = shift_date(date_value, -13)
        day_stats = self.stats_service.get_by_day(lookback_start, date_value).items
        active_dates = {item.session_date for item in day_stats if item.duration_minutes > 0}

        streak = 0
        cursor = date_value
        while cursor in active_dates:
            streak += 1
            cursor = shift_date(cursor, -1)

        recent_study_tasks = self.db.scalars(
            select(DailyTask)
            .where(DailyTask.task_date >= lookback_start)
            .where(DailyTask.task_date <= date_value)
            .where(DailyTask.is_study.is_(True))
        ).all()

        completed_study_tasks = sum(task.status == TaskStatusEnum.completed.value for task in recent_study_tasks)
        time_preferences: dict[str, int] = {}
        for task in recent_study_tasks:
            bucket = self._time_preference_from_hour(task.start_time)
            if bucket is None:
                continue
            time_preferences[bucket] = time_preferences.get(bucket, 0) + 1

        preferred_window = None
        if time_preferences:
            preferred_window = max(time_preferences.items(), key=lambda item: item[1])[0]

        return {
            "study_active_days_last_14d": len(active_dates),
            "current_study_streak_days": streak,
            "completed_study_tasks_last_14d": completed_study_tasks,
            "preferred_study_window": preferred_window,
        }

    def _build_plan_context(self, payload: AIPlanRequest) -> tuple[dict[str, Any], set[int], list[tuple[str, str]]]:
        daily_tasks = self.daily_task_service.list_tasks(DailyTaskQuery(date=payload.date))
        events = self.event_service.list_events(EventQuery(date=payload.date))
        courses = self.course_service.get_course_occurrences_for_date(payload.date)

        schedulable_task_ids: set[int] = set()
        busy_windows: list[tuple[str, str]] = []

        task_items: list[dict[str, Any]] = []
        for task in daily_tasks:
            task_items.append(
                {
                    "id": task.id,
                    "title": task.title,
                    "category": task.category,
                    "status": task.status,
                    "priority": task.priority,
                    "is_study": task.is_study,
                    "planned_duration_minutes": task.planned_duration_minutes,
                    "start_time": task.start_time,
                    "end_time": task.end_time,
                }
            )
            if task.start_time and task.end_time:
                busy_windows.append((task.start_time, task.end_time))
            if task.status in {TaskStatusEnum.pending, TaskStatusEnum.running} and not (task.start_time and task.end_time):
                schedulable_task_ids.add(task.id)

        event_items: list[dict[str, Any]] = []
        for event in events:
            event_items.append(
                {
                    "id": event.id,
                    "title": event.title,
                    "category": event.category,
                    "status": event.status,
                    "start_time": event.start_time,
                    "end_time": event.end_time,
                    "location": event.location,
                }
            )
            if event.start_time and event.end_time:
                busy_windows.append((event.start_time, event.end_time))

        course_items: list[dict[str, Any]] = []
        for course in courses:
            course_items.append(
                {
                    "course_id": course.course_id,
                    "course_name": course.course_name,
                    "start_time": course.start_time,
                    "end_time": course.end_time,
                    "location": course.location,
                    "teacher": course.teacher,
                    "term_name": course.term_name,
                    "week_index": course.week_index,
                }
            )
            busy_windows.append((course.start_time, course.end_time))

        lookback_start = shift_date(payload.date, -13)
        study_overview = self.stats_service.get_overview(lookback_start, payload.date).model_dump()
        study_by_category = [
            item.model_dump()
            for item in self.stats_service.get_by_category(lookback_start, payload.date).items[:5]
        ]

        planning_context: dict[str, Any] = {
            "date": payload.date,
            "user_input": payload.user_input,
            "option_count": payload.option_count,
            "daily_tasks": task_items,
            "events": event_items,
            "courses": course_items,
            "schedulable_task_ids": sorted(schedulable_task_ids),
            "study_overview_last_14d": study_overview,
            "study_by_category_last_14d": study_by_category,
            "planning_rules": {
                "avoid_overlaps": True,
                "default_buffer_minutes": 10,
                "prefer_high_priority_tasks": True,
                "prefer_existing_task_ids_for_task_schedule": True,
            },
        }
        if payload.include_habits:
            planning_context["habit_snapshot"] = self._build_habit_snapshot(payload.date)
        return planning_context, schedulable_task_ids, busy_windows

    def plan(self, payload: AIPlanRequest) -> AIPlanData:
        base_config = self._load_runtime_config(require_enabled=False)
        config = base_config.clone_for_model(base_config.effective_plan_model_name)
        planning_context, schedulable_task_ids, busy_windows = self._build_plan_context(payload)
        try:
            config, client = self._get_plan_client()
            system_prompt, user_prompt = build_plan_prompts(
                schema=get_plan_schema(),
                planning_context=planning_context,
            )
            parsed, meta = self._execute_structured_generation(
                client=client,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                parser=lambda raw_text: parse_plan_response(
                    raw_text,
                    expected_date=payload.date,
                    option_count=payload.option_count,
                    valid_task_ids=schedulable_task_ids,
                    busy_windows=busy_windows,
                ),
                repair_prompt_builder=lambda raw_text, error_message: build_plan_repair_prompts(
                    invalid_response=raw_text,
                    validation_error=error_message,
                    schema=get_plan_schema(),
                ),
                max_tokens=2200,
            )
        except AppException as exc:
            log_output = exc.log_output if isinstance(exc, AIWorkflowException) else {}
            self._create_log(
                log_type=AILogTypeEnum.plan.value,
                user_input=payload.user_input,
                context=planning_context,
                output=log_output,
                parsed_success=False,
                error_message=exc.message,
                config=config,
            )
            raise

        output = parsed.model_dump()
        output.update(meta.to_log_dict())
        log = self._create_log(
            log_type=AILogTypeEnum.plan.value,
            user_input=payload.user_input,
            context=planning_context,
            output=output,
            parsed_success=True,
            config=config,
        )
        return AIPlanData(plan_options=parsed.plan_options, raw_log_id=log.id)

    def plan_apply(self, payload: AIPlanApplyRequest) -> AIPlanApplyData:
        log = self._get_applicable_log(payload.log_id, expected_type=AILogTypeEnum.plan)
        ai_output = loads_json(log.ai_output_json, default={}) or {}
        options = ai_output.get("plan_options", [])
        if payload.selected_option_index >= len(options):
            raise AppException("selected_option_index is out of range", code=4014, status_code=400)

        selected_option = options[payload.selected_option_index]
        created_event_ids: list[int] = []
        scheduled_task_ids: list[int] = []

        try:
            for raw_item in selected_option.get("items", []):
                item = AIPlanItem.model_validate(raw_item)
                if item.item_type == "event":
                    event = self.event_service.create_event(
                        EventCreate(
                            title=item.title,
                            category=item.category or "planned",
                            event_date=item.date,
                            start_time=item.start_time,
                            end_time=item.end_time,
                            location=None,
                            priority=3,
                            status="scheduled",
                            source=EventSourceEnum.ai,
                            linked_task_id=None,
                            notes=None,
                        )
                    )
                    created_event_ids.append(event.id)
                elif item.item_type == "task_schedule" and item.task_id is not None:
                    task = self.daily_task_service.patch_task(
                        item.task_id,
                        DailyTaskPatch(start_time=item.start_time, end_time=item.end_time, status=TaskStatusEnum.pending),
                    )
                    scheduled_task_ids.append(task.id)
        except AppException as exc:
            self._mark_log_apply_failed(log, exc.message)
            raise
        except Exception as exc:  # pragma: no cover - defensive
            self._mark_log_apply_failed(log, str(exc))
            raise AppException(str(exc), code=5000, status_code=500) from exc

        log.applied_success = True
        log.error_message = None
        self.db.commit()
        return AIPlanApplyData(created_event_ids=created_event_ids, scheduled_task_ids=scheduled_task_ids)

    def list_logs(self, query: AILogQuery) -> AILogListData:
        statement = select(AILog)
        if query.log_type is not None:
            statement = statement.where(AILog.log_type == query.log_type.value)

        total = len(self.db.scalars(statement).all())
        logs = self.db.scalars(
            statement.order_by(desc(AILog.created_at))
            .offset((query.page - 1) * query.page_size)
            .limit(query.page_size)
        ).all()
        return AILogListData(
            items=[AILogRead.model_validate(log) for log in logs],
            total=total,
            page=query.page,
            page_size=query.page_size,
        )

    def _get_log_model(self, log_id: int) -> AILog:
        log = self.db.get(AILog, log_id)
        if log is None:
            raise AppException("ai log not found", code=4053, status_code=404)
        return log

    def get_log(self, log_id: int) -> AILogRead:
        return AILogRead.model_validate(self._get_log_model(log_id))

    def delete_log(self, log_id: int) -> None:
        log = self._get_log_model(log_id)
        self.db.delete(log)
        self.db.commit()
