from __future__ import annotations

from dataclasses import dataclass


BLACKLIST_PATTERNS = [
    "rm -rf",
    "mkfs",
    "format",
    "/etc",
    "C:\\Windows",
]
WHITELIST_COMMANDS = {"ls", "dir", "pwd", "git status", "whoami"}


@dataclass(slots=True)
class SafetyDecision:
    allowed: bool
    requires_confirmation: bool
    reason: str = ""


class SafetyLayer:
    def evaluate(self, command: str) -> SafetyDecision:
        lowered = command.lower()
        for pattern in BLACKLIST_PATTERNS:
            if pattern.lower() in lowered:
                return SafetyDecision(False, False, f"Паттерн '{pattern}' заблокирован")

        if command.strip() in WHITELIST_COMMANDS:
            return SafetyDecision(True, False, "команда из белого списка")

        return SafetyDecision(True, True, "команда вне белого списка")
