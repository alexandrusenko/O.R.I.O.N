from __future__ import annotations

from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.tools import StructuredTool
from langchain.agents import create_agent

from orion.core.lc_model import LMStudioChatModel
from orion.tools.base import BaseTool

SYSTEM_PROMPT = """Ты — O.R.I.O.N., ассистент для практических задач.

Правила:
- Для запросов с актуальными данными (погода, новости, курсы валют) сначала используй web_search, затем web_content_load.
- Не придумывай факты и цифры.
- Если данных недостаточно или запрос неоднозначен, задай пользователю уточняющий вопрос.
- После чтения источников дай краткую и точную сводку на русском языке.
"""


class LangChainOrionAgent:
    def __init__(self, model_name: str, base_url: str, tools: dict[str, BaseTool]) -> None:
        self.model = LMStudioChatModel(model_name=model_name, base_url=base_url, temperature=0.2)
        self.graph = self._build_graph(tools)

    def _build_graph(self, tools: dict[str, BaseTool]):
        lc_tools = [self._to_langchain_tool(tool) for tool in tools.values()]
        return create_agent(model=self.model, tools=lc_tools, system_prompt=SYSTEM_PROMPT)

    @staticmethod
    def _to_langchain_tool(tool: BaseTool) -> StructuredTool:
        def _run(**kwargs) -> str:
            return tool.execute(**kwargs)

        return StructuredTool.from_function(
            func=_run,
            name=tool.name,
            description=tool.description,
            args_schema=tool.args_schema,
        )

    def reload_tools(self, tools: dict[str, BaseTool]) -> None:
        self.graph = self._build_graph(tools)

    def close(self) -> None:
        self.model.close()

    def invoke(self, user_input: str, ltm_context: str, stm_context: str) -> dict:
        contextualized = (
            f"Контекст LTM:\n{ltm_context}\n\n"
            f"Контекст STM:\n{stm_context}\n\n"
            f"Запрос пользователя:\n{user_input}"
        )
        result = self.graph.invoke({"messages": [("user", contextualized)]})
        messages = result.get("messages", [])
        output = ""
        traces: list[tuple[str, str, str]] = []

        current_tool = None
        current_args = ""
        for message in messages:
            if isinstance(message, AIMessage) and message.tool_calls:
                for call in message.tool_calls:
                    current_tool = call.get("name", "")
                    current_args = str(call.get("args", {}))
            elif isinstance(message, ToolMessage) and current_tool:
                traces.append((current_tool, current_args, str(message.content)))
                current_tool = None
                current_args = ""
            elif isinstance(message, AIMessage):
                output = message.content or output

        return {"output": output, "intermediate_steps": traces}
