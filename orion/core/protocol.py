from __future__ import annotations

import json
import re
from dataclasses import dataclass, field


@dataclass(slots=True)
class AgentDecision:
    response: str
    tool_name: str = ""
    tool_input: dict | None = None
    needs_confirmation: bool = False
    plan: list[str] = field(default_factory=list)
    step: str = ""
    expected: str = ""


def parse_agent_output(text: str) -> AgentDecision:
    """Parse assistant output using fenced JSON directive.

    Expected shape:
    ```json
    {
      "response":"...",
      "plan":["..."],
      "step":"...",
      "expected":"...",
      "tool":{"name":"...","args":{...}},
      "needs_confirmation":false
    }
    ```
    """
    match = re.search(r"```json\s*(\{.*?\})\s*```", text, flags=re.S)
    if not match:
        return AgentDecision(response=text)

    try:
        payload = json.loads(match.group(1))
    except json.JSONDecodeError:
        return AgentDecision(response=text)

    tool = payload.get("tool") or {}
    plan = payload.get("plan")
    return AgentDecision(
        response=payload.get("response", text),
        tool_name=tool.get("name", ""),
        tool_input=tool.get("args", {}),
        needs_confirmation=bool(payload.get("needs_confirmation", False)),
        plan=plan if isinstance(plan, list) else [],
        step=str(payload.get("step", "")),
        expected=str(payload.get("expected", "")),
    )
