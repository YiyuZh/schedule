from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint_returns_success() -> None:
    with TestClient(app) as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == 0
    assert payload["data"]["status"] == "ok"


def test_system_info_endpoint_returns_runtime_snapshot() -> None:
    with TestClient(app) as client:
        response = client.get("/api/system/info")

    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == 0
    assert "app_name" in payload["data"]
    assert "python_version" in payload["data"]
    assert payload["data"]["database_status"] in {"ok", "error"}


def test_ai_config_endpoint_returns_current_config_shape() -> None:
    with TestClient(app) as client:
        response = client.get("/api/ai/config")

    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == 0
    assert {
        "enabled",
        "provider",
        "model_name",
        "plan_model_name",
        "base_url",
        "has_api_key",
        "timeout",
        "temperature",
    } <= payload["data"].keys()


def test_ai_logs_endpoint_returns_paged_list() -> None:
    with TestClient(app) as client:
        response = client.get("/api/ai/logs")

    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == 0
    assert {"items", "total", "page", "page_size"} <= payload["data"].keys()
    assert isinstance(payload["data"]["items"], list)
