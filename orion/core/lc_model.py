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

    def close(self) -> None:
        self._client.close()

    def __del__(self) -> None:
        self.close()

    @staticmethod
    def _normalize_content(content: Any) -> str:
        if content is None:
            return ""
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            text_chunks: list[str] = []
            for chunk in content:
                if isinstance(chunk, str):
                    text_chunks.append(chunk)
                    continue
                if isinstance(chunk, dict) and chunk.get("type") == "text":
                    text_chunks.append(str(chunk.get("text", "")))
            return "\n".join(part for part in text_chunks if part)
        return str(content)

    @staticmethod
    def _to_openai_tool_calls(tool_calls: list[dict[str, Any]]) -> list[dict[str, Any]]:
        openai_calls: list[dict[str, Any]] = []
        for call in tool_calls:
            function_block = call.get("function")
            if isinstance(function_block, dict):
                name = function_block.get("name", "")
                arguments = function_block.get("arguments", "{}")
            else:
                name = call.get("name", "")
                raw_args = call.get("args", {})
                arguments = raw_args if isinstance(raw_args, str) else json.dumps(raw_args, ensure_ascii=False)

            openai_calls.append(
                {
                    "id": str(call.get("id", "")),
                    "type": "function",
                    "function": {
                        "name": str(name),
                        "arguments": str(arguments),
                    },
                }
            )
        return openai_calls

    @property
    def _llm_type(self) -> str:
        return "lmstudio-openai"

    def _convert_messages(self, messages: list[BaseMessage]) -> list[dict[str, Any]]:
        payload: list[dict[str, Any]] = []
        for message in messages:
            role = message.type
            if role == "human":
                payload.append({"role": "user", "content": self._normalize_content(message.content)})
            elif role == "ai":
                entry: dict[str, Any] = {"role": "assistant", "content": self._normalize_content(message.content)}
                if getattr(message, "tool_calls", None):
                    entry["tool_calls"] = self._to_openai_tool_calls(message.tool_calls)
                payload.append(entry)
            elif role == "system":
                payload.append({"role": "system", "content": self._normalize_content(message.content)})
            elif role == "tool":
                payload.append(
                    {
                        "role": "tool",
                        "content": self._normalize_content(message.content),
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
