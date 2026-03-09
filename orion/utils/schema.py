from __future__ import annotations

from typing import Any

try:
    from pydantic import BaseModel, Field
except ModuleNotFoundError:  # pragma: no cover
    class BaseModel:  # type: ignore[override]
        def __init__(self, **data: Any) -> None:
            for key, value in data.items():
                setattr(self, key, value)

    def Field(default: Any = None, **_: Any) -> Any:  # type: ignore[misc]
        return default


__all__ = ["BaseModel", "Field"]
