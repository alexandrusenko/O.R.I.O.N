from __future__ import annotations

from duckduckgo_search import DDGS
from orion.utils.schema import BaseModel, Field

from orion.tools.base import BaseTool


class WebSearchArgs(BaseModel):
    query: str = Field(..., description="Поисковый запрос")


class WebSearchTool(BaseTool):
    name = "web_search"
    description = "Ищет информацию в интернете и возвращает топ-5 результатов с фрагментами."
    args_schema = WebSearchArgs

    def execute(self, **kwargs) -> str:
        args = self.args_schema(**kwargs)
        with DDGS() as ddgs:
            results = list(ddgs.text(args.query, max_results=5))
        if not results:
            return "По запросу ничего не найдено."

        lines = []
        for item in results:
            lines.append(f"- {item.get('title', 'No title')}\n  {item.get('href', '')}\n  {item.get('body', '')}")
        return "\n".join(lines)
