from __future__ import annotations

import json

from orion.config.settings import DEFAULT_SETTINGS
from orion.core.agent import LangChainOrionAgent
from orion.memory.ltm import LTMStore
from orion.memory.store import STMStore
from orion.tools.manager import ToolManager
from orion.ui.console import OrionConsoleUI


class OrionApp:
    def __init__(self) -> None:
        self.settings = DEFAULT_SETTINGS
        self.ui = OrionConsoleUI()
        self.stm = STMStore(max_messages=self.settings.stm_max_messages)
        self.ltm = LTMStore()
        self.tool_manager = ToolManager(self.settings.tools_dir)
        self.tool_manager.reload_tools()
        self.agent = LangChainOrionAgent(
            model_name=self.settings.model_name,
            base_url=self.settings.lm_studio_base_url,
            tools=self.tool_manager.tools,
        )

    def _retrieve_context(self, user_input: str) -> tuple[str, str]:
        facts = self.ltm.retrieve(user_input, top_k=3)
        ltm_context = "\n".join(f"- {f.text}" for f in facts) or "Долговременная память пока пуста."
        stm_context = "\n".join(f"{m.role}: {m.content}" for m in self.stm.recent(6)) or "Недавний контекст отсутствует."
        return ltm_context, stm_context

    @staticmethod
    def _format_update(node_name: str, update: dict) -> str:
        if node_name == "agent_node":
            fragments = ["Новый шаг планирования от агента."]
            plan = update.get("plan") or []
            if plan:
                fragments.append("План:\n" + "\n".join(f"- {item}" for item in plan))
            if update.get("current_step"):
                fragments.append(f"Текущий шаг: {update['current_step']}")
            if update.get("expected_result"):
                fragments.append(f"Ожидаемый результат: {update['expected_result']}")
            if update.get("selected_tool"):
                tool_input = json.dumps(update.get("tool_input", {}), ensure_ascii=False, indent=2)
                fragments.append(f"Вызов инструмента: {update['selected_tool']}\nАргументы:\n{tool_input}")
            if update.get("llm_output"):
                fragments.append(f"Ответ/размышление агента:\n{update['llm_output']}")
            return "\n\n".join(fragments)

        if node_name == "tool_executor_node":
            return f"Результат выполнения инструмента:\n{update.get('tool_output', '')}"

        return json.dumps(update, ensure_ascii=False, indent=2)

    def close(self) -> None:
        self.agent.close()
        self.stm.close()
        self.ltm.close()

    def _update_memory(self, user_input: str, answer: str) -> None:
        self.stm.append("user", user_input)
        self.stm.append("assistant", answer)
        if user_input and answer:
            self.ltm.add_fact(f"Пользователь спросил: {user_input} | Ассистент ответил: {answer}")

    def run(self) -> None:
        self.ui.render_boot(model_name=self.settings.model_name)
        try:
            while True:
                user_input = self.ui.ask_input().strip()
                if user_input.lower() in {"exit", "quit"}:
                    self.ui.render_agent("Всегда к вашим услугам, Сэр.")
                    break
                if user_input.lower() == "обнови свои инструменты":
                    tools = self.tool_manager.reload_tools()
                    self.agent.reload_tools(tools)
                    self.ui.render_agent(f"Синхронизация завершена. Загружено инструментов: {len(tools)}.")
                    continue

                self.ui.render_status(model_name=self.settings.model_name, state="Думаю")
                ltm_context, stm_context = self._retrieve_context(user_input)
                result = self.agent.invoke(user_input=user_input, ltm_context=ltm_context, stm_context=stm_context)

                for tool_name, tool_args, observation in result.get("intermediate_steps", []):
                    self.ui.render_trace(
                        "agent_node",
                        self._format_update(
                            "agent_node",
                            {
                                "selected_tool": tool_name,
                                "tool_input": {"raw": tool_args},
                                "llm_output": "Инструмент выбран ReAct-агентом.",
                            },
                        ),
                    )
                    self.ui.render_trace("tool_executor_node", self._format_update("tool_executor_node", {"tool_output": observation}))

                answer = result.get("output", "")
                self._update_memory(user_input, answer)
                self.ui.render_agent(answer)
                self.ui.render_status(model_name=self.settings.model_name, state="Ожидание")
        finally:
            self.close()


if __name__ == "__main__":
    OrionApp().run()
