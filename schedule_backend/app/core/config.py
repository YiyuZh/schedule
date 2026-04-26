from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    app_name: str = "schedule-backend"
    app_version: str = "0.1.0"
    api_prefix: str = "/api"
    host: str = "127.0.0.1"
    port: int = 8000

    @property
    def base_dir(self) -> Path:
        return Path(__file__).resolve().parents[2]

    @property
    def data_dir(self) -> Path:
        return self.base_dir / "data"

    @property
    def database_path(self) -> Path:
        return self.data_dir / "app.db"

    @property
    def database_url(self) -> str:
        return f"sqlite:///{self.database_path.as_posix()}"


settings = Settings()
