from __future__ import annotations

from typing import TypedDict

from langgraph.graph import END, StateGraph

from orion.core.prompt import SYSTEM_PROMPT_TEMPLATE


class OrionState(TypedDict, total=False):
    user_input: str
    ltm_context: str
    stm_context: str
    llm_output: str
    selected_tool: str
    tool_input: dict
    tool_output: str
    plan: list[str]
    current_step: str
    expected_result: str
    attempts: int
    max_attempts: int
    replan_required: bool


class OrionGraphBuilder:
    def __init__(self, run_agent, run_tool, retrieve_context, update_memory):
        self.run_agent = run_agent
        self.run_tool = run_tool
        self.retrieve_context = retrieve_context
        self.update_memory = update_memory

    def build(self):
        graph = StateGraph(OrionState)
        graph.add_node("retriever_node", self.retriever_node)
        graph.add_node("agent_node", self.agent_node)
        graph.add_node("tool_executor_node", self.tool_executor_node)
        graph.add_node("result_analyzer_node", self.result_analyzer_node)
        graph.add_node("memory_update_node", self.memory_update_node)
        graph.add_node("human_input_node", self.human_input_node)

        graph.set_entry_point("retriever_node")
        graph.add_edge("retriever_node", "agent_node")
        graph.add_conditional_edges(
            "agent_node",
            self._agent_router,
            {"tool": "tool_executor_node", "human": "human_input_node", "done": "memory_update_node"},
        )
        graph.add_edge("tool_executor_node", "result_analyzer_node")
        graph.add_conditional_edges(
            "result_analyzer_node",
            self._result_router,
            {"retry": "agent_node", "replan": "agent_node", "done": "memory_update_node"},
        )
        graph.add_edge("human_input_node", "memory_update_node")
        graph.add_edge("memory_update_node", END)

        return graph.compile()

    def retriever_node(self, state: OrionState) -> OrionState:
        ltm_context, stm_context = self.retrieve_context(state["user_input"])
        return {
            "ltm_context": ltm_context,
            "stm_context": stm_context,
            "attempts": 0,
            "max_attempts": state.get("max_attempts", 4),
            "replan_required": False,
        }

    def agent_node(self, state: OrionState) -> OrionState:
        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
            tools_list="dynamic tool list",
            long_term_memory_context=state.get("ltm_context", ""),
            short_term_memory_context=state.get("stm_context", ""),
        )
        llm_output, selected_tool, tool_input, plan, step, expected = self.run_agent(system_prompt, state)
        return {
            "llm_output": llm_output,
            "selected_tool": selected_tool,
            "tool_input": tool_input,
            "plan": plan,
            "current_step": step,
            "expected_result": expected,
        }

    def tool_executor_node(self, state: OrionState) -> OrionState:
        output = self.run_tool(state.get("selected_tool", ""), state.get("tool_input", {}))
        return {"tool_output": output}

    def result_analyzer_node(self, state: OrionState) -> OrionState:
        output = (state.get("tool_output") or "").lower()
        expected = (state.get("expected_result") or "").strip()
        attempts = int(state.get("attempts", 0)) + 1
        max_attempts = int(state.get("max_attempts", 4))

        blocked_markers = ("blocked", "error", "traceback", "exception", "confirmation required")
        has_error = any(marker in output for marker in blocked_markers)

        if has_error and attempts < max_attempts:
            return {
                "attempts": attempts,
                "replan_required": False,
                "llm_output": f"Шаг неуспешен ({attempts}/{max_attempts}). Нужно исправить и повторить.",
            }

        if has_error and attempts >= max_attempts:
            return {
                "attempts": attempts,
                "replan_required": True,
                "llm_output": "Достигнут лимит повторов. Нужна перестройка плана.",
            }

        if expected and expected.lower() not in output and attempts < max_attempts:
            return {
                "attempts": attempts,
                "replan_required": True,
                "llm_output": "Результат шага не соответствует ожиданию. Перестраиваю план.",
            }

        return {"attempts": attempts, "replan_required": False}

    def memory_update_node(self, state: OrionState) -> OrionState:
        self.update_memory(state)
        return {}

    def human_input_node(self, state: OrionState) -> OrionState:
        return {"tool_output": "Ожидаю подтверждения пользователя."}

    @staticmethod
    def _agent_router(state: OrionState) -> str:
        if state.get("selected_tool"):
            return "tool"
        if "confirm" in (state.get("llm_output") or "").lower() or "подтверж" in (state.get("llm_output") or "").lower():
            return "human"
        return "done"

    @staticmethod
    def _result_router(state: OrionState) -> str:
        text = (state.get("llm_output") or "").lower()
        if "неуспешен" in text:
            return "retry"
        if state.get("replan_required"):
            return "replan"
        return "done"
