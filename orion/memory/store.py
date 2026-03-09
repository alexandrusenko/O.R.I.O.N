from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class Message:
    role: str
    content: str


class STMStore:
    def __init__(self, db_path: Path = Path("orion_memory.sqlite3"), max_messages: int = 20) -> None:
        self.db_path = db_path
        self.max_messages = max_messages
        self._ensure_db()

    def _ensure_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    def append(self, role: str, content: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT INTO messages(role, content) VALUES (?, ?)", (role, content))
            conn.commit()


    def close(self) -> None:
        """Совместимость с жизненным циклом приложения."""

    def recent(self, limit: int = 6) -> list[Message]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT role, content FROM messages ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        return [Message(role=row[0], content=row[1]) for row in reversed(rows)]
