from __future__ import annotations

from typing import Any

import httpx


class SyncClientError(Exception):
    pass


class SyncClient:
    def __init__(self, server_url: str, timeout: float = 10.0) -> None:
        self.server_url = server_url.rstrip("/")
        self.timeout = timeout

    def _request(self, method: str, path: str, *, token: str | None = None, json: dict[str, Any] | None = None) -> dict[str, Any]:
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.request(method, f"{self.server_url}{path}", headers=headers, json=json)
                try:
                    payload = response.json()
                except ValueError as exc:
                    response.raise_for_status()
                    raise SyncClientError("云同步服务器返回了无法解析的 JSON") from exc
                if response.status_code >= 400:
                    if isinstance(payload, dict) and payload.get("message"):
                        raise SyncClientError(str(payload["message"]))
                    response.raise_for_status()
        except httpx.RequestError as exc:
            message = str(exc)
            if "TLSV1_ALERT_INTERNAL_ERROR" in message or "tlsv1 alert internal error" in message:
                raise SyncClientError(
                    "无法连接云同步服务器：HTTPS/TLS 握手失败。"
                    "这通常是云服务器 Caddy 站点证书未签发、未 reload 或网关配置未生效，"
                    "请在服务器运行 deploy/diagnose-gateway.sh 检查 schedule-sync.zenithy.art。"
                ) from exc
            raise SyncClientError(f"无法连接云同步服务器：{exc}") from exc
        except httpx.HTTPStatusError as exc:
            raise SyncClientError(f"云同步服务器返回错误：HTTP {exc.response.status_code}") from exc

        if isinstance(payload, dict) and "code" in payload:
            if payload.get("code") != 0:
                raise SyncClientError(str(payload.get("message") or "云同步请求失败"))
            data = payload.get("data")
            return data if isinstance(data, dict) else {}

        if not isinstance(payload, dict):
            raise SyncClientError("云同步服务器返回格式不正确")
        return payload

    def login(self, *, email: str, password: str, device_id: str, device_name: str) -> dict[str, Any]:
        return self._request(
            "POST",
            "/api/auth/login",
            json={
                "email": email,
                "password": password,
                "device_id": device_id,
                "device_name": device_name,
            },
        )

    def refresh(self, *, refresh_token: str, device_id: str) -> dict[str, Any]:
        return self._request(
            "POST",
            "/api/auth/refresh",
            json={"refresh_token": refresh_token, "device_id": device_id},
        )

    def register(self, *, email: str, password: str, display_name: str | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {"email": email, "password": password}
        if display_name:
            payload["display_name"] = display_name
        return self._request("POST", "/api/auth/register", json=payload)

    def push(self, *, token: str, device_id: str, changes: list[dict[str, Any]]) -> dict[str, Any]:
        return self._request(
            "POST",
            "/api/sync/push",
            token=token,
            json={"device_id": device_id, "changes": changes},
        )

    def pull(self, *, token: str, device_id: str, since_change_id: int) -> dict[str, Any]:
        return self._request(
            "POST",
            "/api/sync/pull",
            token=token,
            json={"device_id": device_id, "since_change_id": since_change_id},
        )

    def bootstrap(self, *, token: str, page: int = 1, page_size: int = 500) -> dict[str, Any]:
        return self._request(
            "GET",
            f"/api/sync/bootstrap?page={page}&page_size={page_size}",
            token=token,
        )
