# O.R.I.O.N.

O.R.I.O.N. (Omni-Resourceful Intelligent Operations Network) is a local-first AI assistant built around LangGraph, modular tools, safety controls, and terminal UX.

## Current implementation

- Modular architecture (`core`, `tools`, `memory`, `safety`, `ui`, `config`).
- LangGraph nodes implemented: `retriever_node`, `agent_node`, `tool_executor_node`, `memory_update_node`, `human_input_node`.
- Dynamic tool loading from `orion/tools` with runtime reload command.
- Tools: `web_search`, `web_content_load`, `create_file`, `exec_command`, `get_system_info`.
- Safety layer:
  - blacklist for destructive commands,
  - whitelist for safe read-only commands,
  - confirmation gate for non-whitelisted commands.
- Memory:
  - STM in SQLite (conversation log),
  - LTM in SQLite with local semantic scoring retrieval.
- Prompt protocol + parser for structured tool decisions in JSON blocks.
- Interactive Rich + prompt_toolkit console app.

## Interactive run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
python -m orion.app
```

Exit commands: `exit` / `quit`.
Reload tools at runtime: `Обнови свои инструменты`.

## LM Studio

Default endpoint: `http://localhost:1234/v1`.
Model and runtime settings are defined in `orion/config/settings.py`.
