from __future__ import annotations

import os
import sys


def ensure_stdio() -> None:
    """PyInstaller windowed sidecars may not have stdout/stderr."""
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w", encoding="utf-8")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w", encoding="utf-8")


ensure_stdio()

import uvicorn

from app.core.config import settings
from app.main import app


if __name__ == "__main__":
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        reload=False,
        access_log=False,
    )
