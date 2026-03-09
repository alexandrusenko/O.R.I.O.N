from __future__ import annotations

import requests
from bs4 import BeautifulSoup
from orion.utils.schema import BaseModel, Field

from orion.tools.base import BaseTool


class WebContentLoadArgs(BaseModel):
    url: str = Field(..., description="HTTP/HTTPS url")


class WebContentLoadTool(BaseTool):
    name = "web_content_load"
    description = "Load a web page and return cleaned main textual content."
    args_schema = WebContentLoadArgs

    def execute(self, **kwargs) -> str:
        args = self.args_schema(**kwargs)
        response = requests.get(args.url, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        text = " ".join(soup.get_text(separator=" ").split())
        return text[:8000] if text else "No readable text extracted."
