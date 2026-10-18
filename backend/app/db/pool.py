import asyncio
import os
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import asyncpg

_pool: asyncpg.Pool | None = None
_lock = asyncio.Lock()

# Query parameters some providers put in connection strings for other drivers
# (e.g. Prisma's ?pgbouncer=true on Supabase). asyncpg would send them to the
# server as settings, which Postgres rejects.
_UNSUPPORTED_PARAMS = {"pgbouncer", "connection_limit", "pool_timeout", "schema"}


def database_url() -> str:
    url = os.getenv("DATABASE_URL")

    if not url:
        raise RuntimeError("DATABASE_URL is not set")

    parts = urlsplit(url.strip())
    query = [(k, v) for k, v in parse_qsl(parts.query) if k not in _UNSUPPORTED_PARAMS]
    return urlunsplit(parts._replace(query=urlencode(query)))


def connect_options() -> dict[str, Any]:
    # Supabase's pooler (Supavisor/PgBouncer in transaction mode, port 6543) does not
    # support prepared statements, so asyncpg's statement cache must be off.
    return {"dsn": database_url(), "statement_cache_size": 0}


async def get_pool() -> asyncpg.Pool:
    global _pool

    if _pool is None:
        async with _lock:
            if _pool is None:
                _pool = await asyncpg.create_pool(**connect_options())

    return _pool


async def close_pool() -> None:
    global _pool

    if _pool is not None:
        await _pool.close()
        _pool = None
