from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.tools import StructuredTool

from orion.core.lc_model import LMStudioChatModel


def test_bind_tools_returns_runnable_binding() -> None:
    model = LMStudioChatModel(model_name="local-model", base_url="http://localhost:1234/v1")

    tool = StructuredTool.from_function(
        func=lambda query: query,
        name="web_search",
        description="search",
    )

    bound = model.bind_tools([tool])

    assert hasattr(bound, "invoke")


def test_convert_messages_formats_tool_calls_for_openai() -> None:
    model = LMStudioChatModel(model_name="local-model", base_url="http://localhost:1234/v1")
    messages = [
        HumanMessage(content="Какая погода?"),
        AIMessage(content="Запрашиваю данные.", tool_calls=[{"id": "call_1", "name": "web_search", "args": {"query": "weather"}}]),
        ToolMessage(content="ok", tool_call_id="call_1"),
    ]

    payload = model._convert_messages(messages)

    assert payload[1]["tool_calls"][0]["function"]["name"] == "web_search"
    assert payload[1]["tool_calls"][0]["function"]["arguments"] == '{"query": "weather"}'
    assert payload[2]["role"] == "tool"
