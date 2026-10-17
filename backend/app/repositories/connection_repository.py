from typing import Literal

from app.db.pool import get_pool

ConnectionStatus = Literal["connected", "disconnected", "pending"]


async def get_calendar_connection_status(user_id: str) -> ConnectionStatus | None:
    pool = await get_pool()
    return await pool.fetchval(
        """
        SELECT status
        FROM connections
        WHERE user_id = $1 AND provider = 'calendar'
        """,
        user_id,
    )


async def upsert_calendar_connection(user_id: str, status: ConnectionStatus) -> ConnectionStatus:
    pool = await get_pool()
    return await pool.fetchval(
        """
        INSERT INTO connections (user_id, provider, status)
        VALUES ($1, 'calendar', $2)
        ON CONFLICT (user_id, provider)
        DO UPDATE SET status = EXCLUDED.status
        RETURNING status
        """,
        user_id,
        status,
    )
