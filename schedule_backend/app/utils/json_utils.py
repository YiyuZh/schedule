from __future__ import annotations

import json
from typing import Any


def dumps_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


def loads_json(value: str | None, default: Any = None) -> Any:
    if value in (None, ""):
        return default
    return json.loads(value)
