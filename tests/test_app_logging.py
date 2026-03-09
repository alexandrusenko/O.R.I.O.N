from orion.app import OrionApp


def test_format_update_includes_tool_invocation_details() -> None:
    update = {
        "plan": ["step 1", "step 2"],
        "current_step": "step 1",
        "expected_result": "ok",
        "selected_tool": "exec_command",
        "tool_input": {"cmd": "echo test"},
        "llm_output": "working",
    }

    result = OrionApp._format_update("agent_node", update)

    assert "Вызов инструмента: exec_command" in result
    assert '"cmd": "echo test"' in result
    assert "План:" in result
    assert "Ответ/размышление агента:" in result


def test_format_update_for_tool_executor() -> None:
    result = OrionApp._format_update("tool_executor_node", {"tool_output": "done"})

    assert "Результат выполнения инструмента" in result
    assert "done" in result
