from __future__ import annotations

import json
import socket
from dataclasses import dataclass
from typing import Any
from urllib import error, parse, request

from app.core.response import AppException
from app.utils.json_utils import dumps_json

LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1"}


@dataclass(slots=True)
class AIRuntimeConfig:
    enabled: bool
    provider: str
    base_url: str
    api_key: str
    model_name: str
    timeout: int
    temperature: float
    plan_model_name: str | None = None

    @property
    def provider_label(self) -> str:
        value = self.provider.strip().replace("-", "_")
        if not value or value == "mock":
            return "openai_compatible"
        return value

    @property
    def effective_plan_model_name(self) -> str:
        return (self.plan_model_name or self.model_name).strip()

    @property
    def is_deepseek_provider(self) -> bool:
        return self.provider_label == "deepseek"

    @property
    def is_reasoning_model(self) -> bool:
        return self.is_deepseek_provider and self.model_name.strip() == "deepseek-reasoner"

    @property
    def endpoint_url(self) -> str:
        base_url = self.base_url.strip().rstrip("/")
        if not base_url:
            raise AppException("AI base URL is not configured.", code=4061, status_code=400)
        if base_url.endswith("/chat/completions"):
            return base_url
        return f"{base_url}/chat/completions"

    @property
    def requires_api_key(self) -> bool:
        if self.provider_label in {"local", "local_openai", "lmstudio", "ollama"}:
            return False
        hostname = parse.urlparse(self.base_url).hostname or ""
        hostname = hostname.lower()
        return hostname not in LOCAL_HOSTS and not hostname.endswith(".local")

    def clone_for_model(self, model_name: str) -> "AIRuntimeConfig":
        return AIRuntimeConfig(
            enabled=self.enabled,
            provider=self.provider_label,
            base_url=self.base_url,
            api_key=self.api_key,
            model_name=model_name.strip(),
            timeout=self.timeout,
            temperature=self.temperature,
            plan_model_name=self.effective_plan_model_name,
        )


@dataclass(slots=True)
class AIProviderResult:
    raw_text: str
    response_id: str | None
    model_name: str | None
    finish_reason: str | None
    usage: dict[str, Any] | None
    used_response_format: bool
    reasoning_content: str | None


class OpenAICompatibleClient:
    def __init__(self, config: AIRuntimeConfig) -> None:
        self.config = config

    def _build_headers(self) -> dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "schedule-backend/0.1.0",
        }
        if self.config.api_key.strip():
            headers["Authorization"] = f"Bearer {self.config.api_key.strip()}"
        return headers

    def _extract_error_message(self, raw_text: str) -> str:
        try:
            payload = json.loads(raw_text)
        except json.JSONDecodeError:
            return raw_text.strip() or "Unknown provider error."

        if isinstance(payload, dict):
            error_obj = payload.get("error")
            if isinstance(error_obj, dict):
                message = error_obj.get("message")
                if isinstance(message, str) and message.strip():
                    return message.strip()
            message = payload.get("message")
            if isinstance(message, str) and message.strip():
                return message.strip()
        return raw_text.strip() or "Unknown provider error."

    def _post(self, payload: dict[str, Any]) -> dict[str, Any]:
        body = dumps_json(payload).encode("utf-8")
        http_request = request.Request(
            self.config.endpoint_url,
            data=body,
            headers=self._build_headers(),
            method="POST",
        )

        try:
            with request.urlopen(http_request, timeout=self.config.timeout) as response:
                raw_text = response.read().decode("utf-8")
        except error.HTTPError as exc:
            raw_text = exc.read().decode("utf-8", errors="replace")
            message = self._extract_error_message(raw_text)
            raise AppException(
                f"AI provider returned HTTP {exc.code}: {message}",
                code=4064,
                status_code=502,
            ) from exc
        except error.URLError as exc:
            reason = str(exc.reason) if exc.reason else "Unable to reach AI provider."
            raise AppException(
                f"Failed to connect to AI provider: {reason}",
                code=4064,
                status_code=502,
            ) from exc
        except socket.timeout as exc:
            raise AppException(
                f"AI request timed out after {self.config.timeout} seconds.",
                code=4064,
                status_code=504,
            ) from exc

        try:
            payload = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise AppException(
                "AI provider returned a non-JSON HTTP response.",
                code=4065,
                status_code=502,
            ) from exc

        if not isinstance(payload, dict):
            raise AppException("AI provider returned an unexpected response payload.", code=4065, status_code=502)
        return payload

    def _should_retry_without_response_format(self, message: str) -> bool:
        lowered = message.lower()
        markers = [
            "response_format",
            "json_object",
            "unsupported",
            "unknown field",
            "extra inputs are not permitted",
            "unrecognized request argument",
        ]
        return any(marker in lowered for marker in markers)

    def _extract_text_content(self, value: Any) -> str | None:
        if isinstance(value, str):
            text = value.strip()
            return text or None
        if isinstance(value, list):
            parts: list[str] = []
            for part in value:
                if isinstance(part, dict):
                    text = part.get("text")
                    if isinstance(text, str) and text.strip():
                        parts.append(text.strip())
            if parts:
                return "".join(parts)
        return None

    def _extract_message_text(self, payload: dict[str, Any]) -> tuple[str, str | None, str | None]:
        choices = payload.get("choices")
        if not isinstance(choices, list) or not choices:
            raise AppException("AI provider returned no choices.", code=4065, status_code=502)

        first_choice = choices[0]
        if not isinstance(first_choice, dict):
            raise AppException("AI provider returned an invalid choice object.", code=4065, status_code=502)

        message = first_choice.get("message")
        if not isinstance(message, dict):
            raise AppException("AI provider returned no assistant message.", code=4065, status_code=502)

        finish_reason = first_choice.get("finish_reason")
        content = self._extract_text_content(message.get("content"))
        reasoning_content = self._extract_text_content(message.get("reasoning_content"))
        if content:
            return content, finish_reason, reasoning_content

        raise AppException("AI provider returned an empty assistant message.", code=4065, status_code=502)

    def create_json_completion(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float | None = None,
        max_tokens: int = 1200,
    ) -> AIProviderResult:
        payload = {
            "model": self.config.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"},
        }
        if not self.config.is_reasoning_model:
            payload["temperature"] = self.config.temperature if temperature is None else temperature

        used_response_format = True
        try:
            response_payload = self._post(payload)
        except AppException as exc:
            if not self._should_retry_without_response_format(exc.message):
                raise
            payload.pop("response_format", None)
            used_response_format = False
            response_payload = self._post(payload)

        raw_text, finish_reason, reasoning_content = self._extract_message_text(response_payload)
        usage = response_payload.get("usage")
        return AIProviderResult(
            raw_text=raw_text,
            response_id=response_payload.get("id"),
            model_name=response_payload.get("model"),
            finish_reason=finish_reason,
            usage=usage if isinstance(usage, dict) else None,
            used_response_format=used_response_format,
            reasoning_content=reasoning_content,
        )
