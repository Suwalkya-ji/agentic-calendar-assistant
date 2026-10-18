"""Conversation memory: thread history, thread metadata and per-user working memory.

Stored in Postgres (sql/003_agent_memory.sql) so it survives restarts and redeploys.
"""

import json
from typing import Any

from agents.memory import SessionSettings

from app.db.pool import get_pool

LAST_MESSAGES = 20

WORKING_MEMORY_TEMPLATE = """# Meeting preferences
- Timezone:
- Default meeting length (minutes):
- Preferred meeting hours:
- Usual invitees:
- Notes:
"""


class ThreadSession:
    """OpenAI Agents SDK session backed by the agent_messages table.

    The history window always starts at a user message: a plain "last N items" cut can
    start in the middle of a turn (e.g. with a tool result whose tool call was dropped),
    which the model API rejects.
    """

    session_settings: SessionSettings | None = None

    def __init__(self, session_id: str):
        self.session_id = session_id

    async def get_all_items(self) -> list[Any]:
        pool = await get_pool()
        rows = await pool.fetch(
            "SELECT item FROM agent_messages WHERE thread_id = $1 ORDER BY id",
            self.session_id,
        )
        return [json.loads(row["item"]) for row in rows]

    async def get_items(self, limit: int | None = None) -> list[Any]:
        items = await self.get_all_items()
        window = limit or LAST_MESSAGES

        start = max(len(items) - window, 0)
        while start > 0 and not _is_user_message(items[start]):
            start -= 1

        return items[start:]

    async def add_items(self, items: list[Any]) -> None:
        if not items:
            return

        pool = await get_pool()
        await pool.executemany(
            "INSERT INTO agent_messages (thread_id, item) VALUES ($1, $2::jsonb)",
            [(self.session_id, json.dumps(item)) for item in items],
        )

    async def pop_item(self) -> Any | None:
        pool = await get_pool()
        item = await pool.fetchval(
            """
            DELETE FROM agent_messages
            WHERE id = (SELECT MAX(id) FROM agent_messages WHERE thread_id = $1)
            RETURNING item
            """,
            self.session_id,
        )
        return json.loads(item) if item is not None else None

    async def clear_session(self) -> None:
        pool = await get_pool()
        await pool.execute("DELETE FROM agent_messages WHERE thread_id = $1", self.session_id)


def _is_user_message(item: Any) -> bool:
    return isinstance(item, dict) and item.get("role") == "user"


def open_session(thread_id: str) -> ThreadSession:
    return ThreadSession(thread_id)


def _thread_dict(row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "resource_id": row["resource_id"],
        "title": row["title"],
        "updated_at": row["updated_at"].isoformat(),
    }


async def get_thread(thread_id: str) -> dict[str, Any] | None:
    pool = await get_pool()
    row = await pool.fetchrow(
        "SELECT id, resource_id, title, updated_at FROM agent_threads WHERE id = $1",
        thread_id,
    )
    return _thread_dict(row) if row else None


async def ensure_thread(thread_id: str, resource_id: str) -> dict[str, Any]:
    """Create the thread for this user if new; refuse a thread owned by someone else."""
    pool = await get_pool()
    await pool.execute(
        """
        INSERT INTO agent_threads (id, resource_id)
        VALUES ($1, $2)
        ON CONFLICT (id) DO NOTHING
        """,
        thread_id,
        resource_id,
    )
    thread = await get_thread(thread_id)

    if thread is None or thread["resource_id"] != resource_id:
        raise PermissionError("Thread not found")

    return thread


async def touch_thread(thread_id: str, title: str | None = None) -> None:
    pool = await get_pool()
    await pool.execute(
        """
        UPDATE agent_threads
        SET updated_at = NOW(), title = COALESCE(NULLIF(TRIM(title), ''), $2)
        WHERE id = $1
        """,
        thread_id,
        title,
    )


async def list_threads(resource_id: str, limit: int = 30) -> list[dict[str, Any]]:
    pool = await get_pool()
    rows = await pool.fetch(
        """
        SELECT id, resource_id, title, updated_at FROM agent_threads
        WHERE resource_id = $1
        ORDER BY updated_at DESC
        LIMIT $2
        """,
        resource_id,
        limit,
    )
    return [_thread_dict(row) for row in rows]


async def get_working_memory(resource_id: str) -> str:
    pool = await get_pool()
    content = await pool.fetchval(
        "SELECT content FROM working_memory WHERE resource_id = $1", resource_id
    )
    return content or WORKING_MEMORY_TEMPLATE


async def set_working_memory(resource_id: str, content: str) -> None:
    pool = await get_pool()
    await pool.execute(
        """
        INSERT INTO working_memory (resource_id, content, updated_at)
        VALUES ($1, $2, NOW())
        ON CONFLICT (resource_id) DO UPDATE
        SET content = EXCLUDED.content, updated_at = EXCLUDED.updated_at
        """,
        resource_id,
        content,
    )
