import asyncio
import os

import asyncpg

_pool: asyncpg.Pool | None = None
_lock = asyncio.Lock()


async def get_pool() -> asyncpg.Pool:
    global _pool

    if _pool is None:
        async with _lock:
            if _pool is None:
                connection_string = os.getenv("DATABASE_URL")

                if not connection_string:
                    raise RuntimeError("DATABASE_URL is not set")

                _pool = await asyncpg.create_pool(connection_string)

    return _pool


async def close_pool() -> None:
    global _pool

    if _pool is not None:
        await _pool.close()
        _pool = None
