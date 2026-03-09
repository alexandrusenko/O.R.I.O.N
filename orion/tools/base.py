from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

try:
    from orion.utils.schema import BaseModel
except ModuleNotFoundError:  # fallback for restricted environments
    class BaseModel:  # type: ignore[override]
        def __init__(self, **data: Any) -> None:
            for key, value in data.items():
                setattr(self, key, value)


class ToolArgs(BaseModel):
    """Базовая схема аргументов инструментов."""


class BaseTool(ABC):
    name: str
    description: str
    args_schema: type[BaseModel]

    @abstractmethod
    def execute(self, **kwargs) -> str:
        """Выполняет инструмент и возвращает строковый результат."""

    def as_llm_spec(self) -> str:
        return f"{self.name}: {self.description}"
