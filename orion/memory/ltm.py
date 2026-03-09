from __future__ import annotations

import json
import math
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class MemoryFact:
    text: str
    metadata: dict


class LTMStore:
    """Persistent local long-term memory with lightweight semantic retrieval.

    Stores normalized text chunks in SQLite and uses cosine similarity over
    sparse term-frequency vectors for retrieval when vector DB is unavailable.
    """

    def __init__(self, db_path: Path = Path("orion_ltm.sqlite3")) -> None:
        self.db_path = db_path
        self._ensure_db()

    def _ensure_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS facts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    text TEXT NOT NULL,
                    metadata TEXT NOT NULL,
                    tokens TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    def add_fact(self, text: str, metadata: dict | None = None) -> None:
        tokens = self._tokenize(text)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO facts(text, metadata, tokens) VALUES (?, ?, ?)",
                (text, json.dumps(metadata or {}, ensure_ascii=False), json.dumps(tokens)),
            )
            conn.commit()

    def retrieve(self, query: str, top_k: int = 3) -> list[MemoryFact]:
        q_vec = self._tf(self._tokenize(query))
        scored: list[tuple[float, MemoryFact]] = []

        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("SELECT text, metadata, tokens FROM facts").fetchall()

        for text, metadata, tokens in rows:
            token_list = json.loads(tokens)
            score = self._cosine(q_vec, self._tf(token_list))
            scored.append((score, MemoryFact(text=text, metadata=json.loads(metadata))))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [fact for score, fact in scored[:top_k] if score > 0] or [fact for _, fact in scored[-top_k:]]


    def close(self) -> None:
        """Совместимость с жизненным циклом приложения."""

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return re.findall(r"[a-zA-Zа-яА-Я0-9_]+", text.lower())

    @staticmethod
    def _tf(tokens: list[str]) -> dict[str, float]:
        if not tokens:
            return {}
        total = len(tokens)
        out: dict[str, float] = {}
        for token in tokens:
            out[token] = out.get(token, 0.0) + 1.0 / total
        return out

    @staticmethod
    def _cosine(a: dict[str, float], b: dict[str, float]) -> float:
        if not a or not b:
            return 0.0
        dot = sum(v * b.get(k, 0.0) for k, v in a.items())
        norm_a = math.sqrt(sum(v * v for v in a.values()))
        norm_b = math.sqrt(sum(v * v for v in b.values()))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)
