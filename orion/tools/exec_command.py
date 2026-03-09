from __future__ import annotations

import subprocess

from orion.utils.schema import BaseModel, Field

from orion.safety.layer import SafetyLayer
from orion.tools.base import BaseTool


class ExecCommandArgs(BaseModel):
    command: str = Field(..., description="Shell command")


class ExecCommandTool(BaseTool):
    name = "exec_command"
    description = "Execute shell command after safety checks."
    args_schema = ExecCommandArgs

    def __init__(self) -> None:
        self.safety = SafetyLayer()

    def execute(self, **kwargs) -> str:
        args = self.args_schema(**kwargs)
        decision = self.safety.evaluate(args.command)
        if not decision.allowed:
            return f"Blocked by safety layer: {decision.reason}"
        if decision.requires_confirmation:
            return (
                f"Confirmation required: Sir, I am about to execute `{args.command}`. "
                "Please confirm with y/n."
            )

        completed = subprocess.run(
            args.command,
            shell=True,
            check=False,
            capture_output=True,
            text=True,
        )
        return f"exit_code={completed.returncode}\nstdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
