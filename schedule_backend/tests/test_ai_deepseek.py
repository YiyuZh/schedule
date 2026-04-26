from __future__ import annotations

from app.services.ai_provider_client import AIRuntimeConfig, OpenAICompatibleClient
from app.services.ai_service import AIExecutionMeta, AIService


class StubSettingsService:
    def __init__(self, values: dict[str, object]) -> None:
        self.values = values

    def get_settings_map(self, keys: list[str] | None = None) -> dict[str, object]:
        if not keys:
            return dict(self.values)
        return {key: self.values[key] for key in keys if key in self.values}


def build_service(values: dict[str, object]) -> AIService:
    service = object.__new__(AIService)
    service.settings_service = StubSettingsService(values)
    return service


def test_runtime_config_falls_back_plan_model_to_chat_model_when_setting_is_missing() -> None:
    service = build_service(
        {
            "ai_enabled": False,
            "ai_provider": "deepseek",
            "ai_base_url": "https://api.deepseek.com/v1",
            "ai_api_key": "",
            "ai_model_name": "deepseek-chat",
            "ai_timeout": 60,
            "ai_temperature": 0.2,
        }
    )

    config = AIService._load_runtime_config(service, require_enabled=False)

    assert config.model_name == "deepseek-chat"
    assert config.plan_model_name == "deepseek-chat"
    assert config.effective_plan_model_name == "deepseek-chat"


def test_deepseek_test_connection_checks_chat_and_reasoner_models(monkeypatch) -> None:
    service = build_service(
        {
            "ai_enabled": True,
            "ai_provider": "deepseek",
            "ai_base_url": "https://api.deepseek.com/v1",
            "ai_api_key": "sk-test",
            "ai_model_name": "deepseek-chat",
            "ai_plan_model_name": "deepseek-reasoner",
            "ai_timeout": 60,
            "ai_temperature": 0.2,
        }
    )
    calls: list[str] = []

    def fake_run(_self: AIService, config: AIRuntimeConfig) -> tuple[bool, str]:
        calls.append(config.model_name)
        return True, f"{config.model_name} ok"

    monkeypatch.setattr(AIService, "_run_test_connection_check", fake_run)

    result = AIService.test_connection(service)

    assert result.ok is True
    assert calls == ["deepseek-chat", "deepseek-reasoner"]
    assert "chat (deepseek-chat)" in result.message
    assert "reasoner (deepseek-reasoner)" in result.message


def test_deepseek_reasoner_payload_omits_temperature_and_keeps_reasoning_content(monkeypatch) -> None:
    payloads: list[dict[str, object]] = []
    client = OpenAICompatibleClient(
        AIRuntimeConfig(
            enabled=True,
            provider="deepseek",
            base_url="https://api.deepseek.com/v1",
            api_key="sk-test",
            model_name="deepseek-reasoner",
            plan_model_name="deepseek-reasoner",
            timeout=60,
            temperature=0.2,
        )
    )

    def fake_post(payload: dict[str, object]) -> dict[str, object]:
        payloads.append(dict(payload))
        return {
            "id": "resp_123",
            "model": "deepseek-reasoner",
            "choices": [
                {
                    "finish_reason": "stop",
                    "message": {
                        "content": '{"ok": true}',
                        "reasoning_content": "analysis trace",
                    },
                }
            ],
            "usage": {"total_tokens": 42},
        }

    monkeypatch.setattr(client, "_post", fake_post)

    result = client.create_json_completion(system_prompt="test", user_prompt="ping", temperature=0.0)

    assert payloads
    assert "temperature" not in payloads[0]
    assert result.reasoning_content == "analysis trace"


def test_execution_meta_serializes_reasoning_content_into_log_metadata() -> None:
    meta = AIExecutionMeta(
        initial_raw_text='{"ok": true}',
        response_id="resp_123",
        response_model="deepseek-reasoner",
        finish_reason="stop",
        usage={"total_tokens": 42},
        used_response_format=True,
        reasoning_content="analysis trace",
    )

    payload = meta.to_log_dict()

    assert payload["_meta"]["reasoning_content"] == "analysis trace"
