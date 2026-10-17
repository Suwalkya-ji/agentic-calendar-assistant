"""Run every sql/*.sql file in order. Usage (from backend-python/): python -m scripts.migrate"""

import asyncio
import os
from pathlib import Path

import asyncpg
from dotenv import load_dotenv

load_dotenv(Path.cwd() / ".env")


async def main() -> None:
    connection_string = os.getenv("DATABASE_URL")

    if not connection_string:
        raise SystemExit("DATABASE_URL is not set")

    sql_dir = Path.cwd() / "sql"
    conn = await asyncpg.connect(connection_string)

    try:
        for file in sorted(sql_dir.glob("*.sql")):
            await conn.execute(file.read_text(encoding="utf-8"))
            print(f"Migrated: sql/{file.name}")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
