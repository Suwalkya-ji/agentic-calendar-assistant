"""Conversation memory: thread history, thread metadata and per-user working memory.

Everything lives in one local SQLite file (memory.db). Message history is stored by the
OpenAI Agents SDK's SQLiteSession; thread titles/owners and working memory are in our own tables.
"""

import asyncio
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agents import SQLiteSession

DB_PATH = Path.cwd() / "memory.db"

LAST_MESSAGES = 20

WORKING_MEMORY_TEMPLATE = """# Meeting preferences
- Timezone:
- Default meeting length (minutes):
- Preferred meeting hours:
- Usual invitees:
- Notes:
"""


class ThreadSession(SQLiteSession):
    """Session whose history window always starts at a user message.

    A plain "last N items" cut can start in the middle of a turn (e.g. with a tool
    result whose tool call was dropped), which the model API rejects.
    """

    async def get_all_items(self) -> list[Any]:
        return await super().get_items(None)

    async def get_items(self, limit: int | None = None) -> list[Any]:
        items = await self.get_all_items()
        window = limit or LAST_MESSAGES

        start = max(len(items) - window, 0)
        while start > 0 and not _is_user_message(items[start]):
            start -= 1

        return items[start:]


def _is_user_message(item: Any) -> bool:
    return isinstance(item, dict) and item.get("role") == "user"


@contextmanager
def _connect() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        with conn:  # commits on success, rolls back on error
            yield conn
    finally:
        conn.close()


def _init_db() -> None:
    with _connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS threads (
                id TEXT PRIMARY KEY,
                resource_id TEXT NOT NULL,
                title TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS threads_resource_idx ON threads (resource_id, updated_at);

            CREATE TABLE IF NOT EXISTS working_memory (
                resource_id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )


_init_db()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def open_session(thread_id: str) -> ThreadSession:
    return ThreadSession(thread_id, DB_PATH)


async def get_thread(thread_id: str) -> dict[str, Any] | None:
    def run():
        with _connect() as conn:
            row = conn.execute("SELECT * FROM threads WHERE id = ?", (thread_id,)).fetchone()
            return dict(row) if row else None

    return await asyncio.to_thread(run)


async def ensure_thread(thread_id: str, resource_id: str) -> dict[str, Any]:
    """Create the thread for this user if new; refuse a thread owned by someone else."""

    def run():
        with _connect() as conn:
            now = _now()
            conn.execute(
                """
                INSERT INTO threads (id, resource_id, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT (id) DO NOTHING
                """,
                (thread_id, resource_id, now, now),
            )
            return dict(conn.execute("SELECT * FROM threads WHERE id = ?", (thread_id,)).fetchone())

    thread = await asyncio.to_thread(run)

    if thread["resource_id"] != resource_id:
        raise PermissionError("Thread not found")

    return thread


async def touch_thread(thread_id: str, title: str | None = None) -> None:
    def run():
        with _connect() as conn:
            conn.execute(
                """
                UPDATE threads
                SET updated_at = ?, title = COALESCE(NULLIF(TRIM(title), ''), ?)
                WHERE id = ?
                """,
                (_now(), title, thread_id),
            )

    await asyncio.to_thread(run)


async def list_threads(resource_id: str, limit: int = 30) -> list[dict[str, Any]]:
    def run():
        with _connect() as conn:
            rows = conn.execute(
                """
                SELECT id, title, updated_at FROM threads
                WHERE resource_id = ?
                ORDER BY updated_at DESC
                LIMIT ?
                """,
                (resource_id, limit),
            ).fetchall()
            return [dict(row) for row in rows]

    return await asyncio.to_thread(run)


async def get_working_memory(resource_id: str) -> str:
    def run():
        with _connect() as conn:
            row = conn.execute(
                "SELECT content FROM working_memory WHERE resource_id = ?", (resource_id,)
            ).fetchone()
            return row["content"] if row else WORKING_MEMORY_TEMPLATE

    return await asyncio.to_thread(run)


async def set_working_memory(resource_id: str, content: str) -> None:
    def run():
        with _connect() as conn:
            conn.execute(
                """
                INSERT INTO working_memory (resource_id, content, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT (resource_id) DO UPDATE
                SET content = excluded.content, updated_at = excluded.updated_at
                """,
                (resource_id, content, _now()),
            )

    await asyncio.to_thread(run)
