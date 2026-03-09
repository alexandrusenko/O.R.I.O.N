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
        graph.add_node("memory_update_node", self.memory_update_node)
        graph.add_node("human_input_node", self.human_input_node)

        graph.set_entry_point("retriever_node")
        graph.add_edge("retriever_node", "agent_node")
        graph.add_conditional_edges(
            "agent_node",
            self._agent_router,
            {"tool": "tool_executor_node", "human": "human_input_node", "done": "memory_update_node"},
        )
        graph.add_edge("tool_executor_node", "memory_update_node")
        graph.add_edge("human_input_node", "memory_update_node")
        graph.add_edge("memory_update_node", END)

        return graph.compile()

    def retriever_node(self, state: OrionState) -> OrionState:
        ltm_context, stm_context = self.retrieve_context(state["user_input"])
        return {"ltm_context": ltm_context, "stm_context": stm_context}

    def agent_node(self, state: OrionState) -> OrionState:
        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
            tools_list="dynamic tool list",
            long_term_memory_context=state.get("ltm_context", ""),
            short_term_memory_context=state.get("stm_context", ""),
        )
        llm_output, selected_tool, tool_input = self.run_agent(system_prompt, state["user_input"])
        return {
            "llm_output": llm_output,
            "selected_tool": selected_tool,
            "tool_input": tool_input,
        }

    def tool_executor_node(self, state: OrionState) -> OrionState:
        output = self.run_tool(state.get("selected_tool", ""), state.get("tool_input", {}))
        return {"tool_output": output}

    def memory_update_node(self, state: OrionState) -> OrionState:
        self.update_memory(state)
        return {}

    def human_input_node(self, state: OrionState) -> OrionState:
        return {"tool_output": "Awaiting human confirmation."}

    @staticmethod
    def _agent_router(state: OrionState) -> str:
        if state.get("selected_tool"):
            return "tool"
        if "confirm" in (state.get("llm_output") or "").lower():
            return "human"
        return "done"
