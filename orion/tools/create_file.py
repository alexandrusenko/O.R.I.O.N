from __future__ import annotations

from pathlib import Path

from orion.utils.schema import BaseModel, Field

from orion.tools.base import BaseTool


class CreateFileArgs(BaseModel):
    filename: str = Field(..., description="Путь относительно workspace")
    content: str = Field(..., description="Содержимое файла")


class CreateFileTool(BaseTool):
    name = "create_file"
    description = "Создаёт файл внутри workspace с указанным содержимым."
    args_schema = CreateFileArgs

    def execute(self, **kwargs) -> str:
        args = self.args_schema(**kwargs)
        base = Path("workspace").resolve()
        base.mkdir(parents=True, exist_ok=True)
        target = (base / args.filename).resolve()

        if base not in target.parents and target != base:
            raise ValueError("Обнаружен выход за пределы пути: файл должен оставаться в workspace.")

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(args.content, encoding="utf-8")
        return f"Файл создан: {target}"
