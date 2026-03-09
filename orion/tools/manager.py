from __future__ import annotations

import importlib.util
import inspect
from pathlib import Path

from orion.tools.base import BaseTool


class ToolManager:
    def __init__(self, tools_dir: Path) -> None:
        self.tools_dir = tools_dir
        self._tools: dict[str, BaseTool] = {}

    @property
    def tools(self) -> dict[str, BaseTool]:
        return self._tools

    def reload_tools(self) -> dict[str, BaseTool]:
        loaded: dict[str, BaseTool] = {}
        for path in self.tools_dir.glob("*.py"):
            if path.name in {"__init__.py", "base.py", "manager.py"}:
                continue
            module = self._import_module(path)
            for _, cls in inspect.getmembers(module, inspect.isclass):
                if cls is BaseTool or not issubclass(cls, BaseTool):
                    continue
                instance = cls()
                loaded[instance.name] = instance
        self._tools = loaded
        return loaded

    def _import_module(self, file_path: Path):
        spec = importlib.util.spec_from_file_location(file_path.stem, file_path)
        if not spec or not spec.loader:
            raise RuntimeError(f"Cannot load tool module: {file_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
