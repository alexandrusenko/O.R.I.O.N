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
