from __future__ import annotations

from typing import Any
import json

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.tools import BaseTool
from langchain_core.utils.function_calling import convert_to_openai_tool
from openai import OpenAI


class LMStudioChatModel(BaseChatModel):
    model_name: str
    base_url: str
    temperature: float = 0.2

    def __init__(self, model_name: str, base_url: str, temperature: float = 0.2) -> None:
        super().__init__(model_name=model_name, base_url=base_url, temperature=temperature)
        self._client = OpenAI(base_url=base_url, api_key="lm-studio")

    @property
    def _llm_type(self) -> str:
        return "lmstudio-openai"

    def _convert_messages(self, messages: list[BaseMessage]) -> list[dict[str, Any]]:
        payload: list[dict[str, Any]] = []
        for message in messages:
            role = message.type
            if role == "human":
                payload.append({"role": "user", "content": message.content})
            elif role == "ai":
                entry: dict[str, Any] = {"role": "assistant", "content": message.content}
                if getattr(message, "tool_calls", None):
                    entry["tool_calls"] = message.tool_calls
                payload.append(entry)
            elif role == "system":
                payload.append({"role": "system", "content": message.content})
            elif role == "tool":
                payload.append(
                    {
                        "role": "tool",
                        "content": message.content,
                        "tool_call_id": message.tool_call_id,
                    }
                )
        return payload

    def bind_tools(
        self,
        tools: list[dict[str, Any] | type | BaseTool | Any],
        *,
        tool_choice: str | None = None,
        **kwargs: Any,
    ):
        openai_tools = [convert_to_openai_tool(t) if isinstance(t, BaseTool) else t for t in tools]
        if tool_choice is not None:
            kwargs["tool_choice"] = tool_choice
        return self.bind(tools=openai_tools, **kwargs)

    def _generate(self, messages: list[BaseMessage], stop: list[str] | None = None, **kwargs: Any) -> ChatResult:
        payload = self._convert_messages(messages)
        openai_tools = kwargs.get("tools")

        response = self._client.chat.completions.create(
            model=self.model_name,
            messages=payload,
            temperature=self.temperature,
            tools=openai_tools,
            tool_choice=kwargs.get("tool_choice"),
            stop=stop,
        )
        msg = response.choices[0].message
        tool_calls = []
        for call in msg.tool_calls or []:
            tool_calls.append(
                {
                    "id": call.id,
                    "name": call.function.name,
                    "args": json.loads(call.function.arguments or "{}"),
                    "type": "tool_call",
                }
            )
        ai_message = AIMessage(content=msg.content or "", tool_calls=tool_calls)
        return ChatResult(generations=[ChatGeneration(message=ai_message)])
