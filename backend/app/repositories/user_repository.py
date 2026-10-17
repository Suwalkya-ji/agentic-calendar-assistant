from dataclasses import dataclass
from datetime import datetime

from app.db.pool import get_pool


@dataclass
class UserRow:
    id: str
    auth_user_id: str
    email: str | None
    created_at: datetime


async def ensure_user(auth_user_id: str, email: str | None = None) -> UserRow:
    pool = await get_pool()
    row = await pool.fetchrow(
        """
        INSERT INTO users (auth_user_id, email)
        VALUES ($1, $2)
        ON CONFLICT (auth_user_id)
        DO UPDATE SET email = COALESCE(EXCLUDED.email, users.email)
        RETURNING id, auth_user_id, email, created_at
        """,
        auth_user_id,
        email,
    )

    return UserRow(
        id=str(row["id"]),
        auth_user_id=row["auth_user_id"],
        email=row["email"],
        created_at=row["created_at"],
    )
