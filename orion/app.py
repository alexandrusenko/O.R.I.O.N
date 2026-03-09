from __future__ import annotations

import json

from orion.config.settings import DEFAULT_SETTINGS
from orion.core.graph import OrionGraphBuilder
from orion.core.llm import LMStudioClient
from orion.core.protocol import parse_agent_output
from orion.memory.ltm import LTMStore
from orion.memory.store import STMStore
from orion.tools.manager import ToolManager
from orion.ui.console import OrionConsoleUI


class OrionApp:
    def __init__(self) -> None:
        self.settings = DEFAULT_SETTINGS
        self.ui = OrionConsoleUI()
        self.llm = LMStudioClient(
            base_url=self.settings.lm_studio_base_url,
            model_name=self.settings.model_name,
        )
        self.stm = STMStore(max_messages=self.settings.stm_max_messages)
        self.ltm = LTMStore()
        self.tool_manager = ToolManager(self.settings.tools_dir)
        self.tool_manager.reload_tools()

        self.graph = OrionGraphBuilder(
            run_agent=self._run_agent,
            run_tool=self._run_tool,
            retrieve_context=self._retrieve_context,
            update_memory=self._update_memory,
        ).build()

    def _tool_specs(self) -> str:
        lines = []
        for tool in self.tool_manager.tools.values():
            fields = []
            schema = getattr(tool, "args_schema", None)
            if schema is not None and hasattr(schema, "model_fields"):
                for name, field in schema.model_fields.items():
                    desc = field.description or "без описания"
                    fields.append(f"{name}: {desc}")
            args_str = ", ".join(fields) if fields else "без аргументов"
            lines.append(f"- {tool.name}: {tool.description} | аргументы: {args_str}")
        return "\n".join(lines)

    def _retrieve_context(self, user_input: str) -> tuple[str, str]:
        facts = self.ltm.retrieve(user_input, top_k=3)
        ltm_context = "\n".join(f"- {f.text}" for f in facts) or "Долговременная память пока пуста."
        stm_context = "\n".join(f"{m.role}: {m.content}" for m in self.stm.recent(6)) or "Недавний контекст отсутствует."
        return ltm_context, stm_context

    def _run_agent(self, system_prompt: str, state: dict):
        full_prompt = system_prompt.replace("dynamic tool list", self._tool_specs())
        user_input = state.get("user_input", "")
        if state.get("tool_output"):
            user_input += (
                "\n\nРезультат предыдущего шага:\n"
                f"{state.get('tool_output')}\n"
                "Проанализируй результат и продолжи выполнение агентного цикла."
            )
        if state.get("replan_required"):
            user_input += "\n\nТребуется перестроить план на основе нового результата."

        text = self.llm.complete(system_prompt=full_prompt, user_input=user_input)
        decision = parse_agent_output(text)
        return (
            decision.response,
            decision.tool_name,
            decision.tool_input or {},
            decision.plan,
            decision.step,
            decision.expected,
        )

    def _run_tool(self, tool_name: str, tool_input: dict) -> str:
        tool = self.tool_manager.tools.get(tool_name)
        if not tool:
            return f"Инструмент не найден: {tool_name}"
        return tool.execute(**tool_input)


    @staticmethod
    def _format_update(node_name: str, update: dict) -> str:
        if node_name == "retriever_node":
            ltm = update.get("ltm_context", "")
            stm = update.get("stm_context", "")
            return "\n".join(
                [
                    "Подтянул контекст памяти.",
                    f"LTM:\n{ltm}",
                    f"STM:\n{stm}",
                ]
            )

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

        if node_name == "result_analyzer_node":
            return "\n".join(
                [
                    "Анализ результата шага.",
                    f"Попытки: {update.get('attempts', '?')}",
                    f"Требуется перестройка плана: {update.get('replan_required', False)}",
                    f"Комментарий: {update.get('llm_output', 'без комментария')}",
                ]
            )

        if node_name == "memory_update_node":
            return "Сессия сохранена в кратковременную и долговременную память."

        if node_name == "human_input_node":
            return update.get("tool_output", "Ожидание подтверждения пользователя.")

        return json.dumps(update, ensure_ascii=False, indent=2)

    def _update_memory(self, state: dict) -> None:
        user = state.get("user_input", "")
        answer = state.get("llm_output", "")
        self.stm.append("user", user)
        self.stm.append("assistant", answer)
        if user and answer:
            self.ltm.add_fact(f"Пользователь спросил: {user} | Ассистент ответил: {answer}")

    def run(self) -> None:
        self.ui.render_boot(model_name=self.settings.model_name)
        while True:
            user_input = self.ui.ask_input().strip()
            if user_input.lower() in {"exit", "quit"}:
                self.ui.render_agent("Всегда к вашим услугам, Сэр.")
                break
            if user_input.lower() == "обнови свои инструменты":
                tools = self.tool_manager.reload_tools()
                self.ui.render_agent(f"Синхронизация завершена. Загружено инструментов: {len(tools)}.")
                continue

            self.ui.render_status(model_name=self.settings.model_name, state="Думаю")
            final_state: dict = {}
            for update in self.graph.stream({"user_input": user_input}):
                for node_name, node_update in update.items():
                    final_state.update(node_update)
                    self.ui.render_trace(node_name, self._format_update(node_name, node_update))

            self.ui.render_agent(final_state.get("tool_output") or final_state.get("llm_output", ""))
            self.ui.render_status(model_name=self.settings.model_name, state="Ожидание")


if __name__ == "__main__":
    OrionApp().run()
