from __future__ import annotations

from datetime import datetime

from prompt_toolkit import prompt
from rich.console import Console
from rich.panel import Panel
from rich.table import Table


ASCII_LOGO = r"""
  ____  ____  ___ ___  ____
 / __ \/ __ \/ _ \\_  |/ __ \
/ /_/ / /_/ /  __/ / / / / /
\____/\____/\___/ /_/_/ /_/
"""


class OrionConsoleUI:
    def __init__(self) -> None:
        self.console = Console()

    def render_boot(self, model_name: str) -> None:
        self.console.print(Panel.fit(ASCII_LOGO, title="O.R.I.O.N.", border_style="cyan"))
        self.console.print("[bold white]Omni-Resourceful Intelligent Operations Network активирован.[/]")
        self.render_status(model_name=model_name, state="Idle")

    def render_user(self, text: str) -> None:
        self.console.print(Panel(text, title="Пользователь", border_style="gold1"))

    def render_agent(self, text: str) -> None:
        self.console.print(Panel(text, title="O.R.I.O.N.", border_style="cyan"))

    def render_status(self, model_name: str, state: str) -> None:
        table = Table(show_header=False, box=None)
        table.add_row("[cyan]Время[/]", datetime.now().strftime("%H:%M:%S"))
        table.add_row("[cyan]Модель[/]", model_name)
        table.add_row("[cyan]Состояние[/]", state)
        self.console.print(Panel(table, border_style="white"))

    def ask_input(self) -> str:
        return prompt("[Вы]> ")
