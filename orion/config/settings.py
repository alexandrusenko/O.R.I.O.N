from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class OrionSettings:
    model_name: str = "local-model"
    lm_studio_base_url: str = "http://localhost:1234/v1"
    workspace_dir: Path = Path("workspace")
    tools_dir: Path = Path("orion/tools")
    stm_max_messages: int = 20
    ltm_collection_name: str = "orion_memory"
    safe_commands: set[str] = field(
        default_factory=lambda: {"ls", "dir", "pwd", "git status", "whoami"}
    )


DEFAULT_SETTINGS = OrionSettings()
