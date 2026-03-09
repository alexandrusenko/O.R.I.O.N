from __future__ import annotations

from duckduckgo_search import DDGS
from orion.utils.schema import BaseModel, Field

from orion.tools.base import BaseTool


class WebSearchArgs(BaseModel):
    query: str = Field(..., description="Search query")


class WebSearchTool(BaseTool):
    name = "web_search"
    description = "Search the web and return top-5 results with snippets."
    args_schema = WebSearchArgs

    def execute(self, **kwargs) -> str:
        args = self.args_schema(**kwargs)
        with DDGS() as ddgs:
            results = list(ddgs.text(args.query, max_results=5))
        if not results:
            return "No search results found."

        lines = []
        for item in results:
            lines.append(f"- {item.get('title', 'No title')}\n  {item.get('href', '')}\n  {item.get('body', '')}")
        return "\n".join(lines)
