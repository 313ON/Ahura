import sqlite3
import pathlib
import datetime
from typing import List, Dict


class StorageManager:
    def __init__(self, db_path: pathlib.Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    token_count INTEGER,
                    provider TEXT,
                    model TEXT,
                    FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE CASCADE
                )
                """
            )

    def create_session(self, name: str) -> int:
        with self._get_connection() as conn:
            cur = conn.execute(
                "INSERT INTO sessions (name) VALUES (?)",
                (name,),
            )
            return int(cur.lastrowid)

    def add_message(
        self,
        session_id: int,
        role: str,
        content: str,
        token_count: int | None = None,
        provider: str | None = None,
        model: str | None = None,
    ) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO messages (
                    session_id,
                    role,
                    content,
                    timestamp,
                    token_count,
                    provider,
                    model
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    role,
                    content,
                    datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    token_count,
                    provider,
                    model,
                ),
            )

    def get_session_history(self, session_id: int) -> List[Dict]:
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT role, content, timestamp, token_count, provider, model
                FROM messages
                WHERE session_id = ?
                ORDER BY id
                """,
                (session_id,),
            )
            return [dict(row) for row in rows]

    def list_sessions(self) -> List[Dict]:
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT id, name, created_at
                FROM sessions
                ORDER BY id DESC
                """
            )
            return [dict(row) for row in rows]

    def delete_session(self, session_id: int) -> None:
        with self._get_connection() as conn:
            conn.execute(
                "DELETE FROM sessions WHERE id = ?",
                (session_id,),
            )

    def export_session_markdown(self, session_id: int) -> str:
        history = self.get_session_history(session_id)
        lines = [f"# Session {session_id}", ""]
        for item in history:
            role = item["role"].capitalize()
            content = item["content"]
            lines.append(f"## {role}")
            lines.append("")
            lines.append(content)
            lines.append("")
        return "\n".join(lines)
