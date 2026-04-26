from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _env_str(name: str, default: str) -> str:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    return value.strip()


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    try:
        return int(value.strip())
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    app_name: str = "schedule-backend"
    app_version: str = "0.1.0"
    api_prefix: str = "/api"
    host: str = _env_str("SCHEDULE_HOST", "127.0.0.1")
    port: int = _env_int("SCHEDULE_PORT", 8000)

    @property
    def base_dir(self) -> Path:
        return Path(__file__).resolve().parents[2]

    @property
    def data_dir(self) -> Path:
        env_data_dir = os.getenv("SCHEDULE_DATA_DIR")
        if env_data_dir and env_data_dir.strip():
            return Path(env_data_dir.strip()).expanduser() / "data"
        return self.base_dir / "data"

    @property
    def database_path(self) -> Path:
        return self.data_dir / "app.db"

    @property
    def database_url(self) -> str:
        return f"sqlite:///{self.database_path.as_posix()}"


settings = Settings()
