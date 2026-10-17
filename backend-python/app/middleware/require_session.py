from dataclasses import dataclass, field
from typing import Any

from fastapi import HTTPException, Request

from app.config.descope import descope_client
from app.repositories.user_repository import ensure_user


@dataclass
class AuthContext:
    auth_user_id: str
    user_id: str
    email: str | None = None
    name: str | None = None
    token: dict[str, Any] = field(default_factory=dict)


async def require_session(request: Request) -> AuthContext:
    """FastAPI dependency: validates the Descope session token and ensures a local user row."""
    header = request.headers.get("authorization") or ""
    token = header[len("Bearer ") :].strip() if header.startswith("Bearer ") else None

    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        auth_info = await descope_client.validate_session(token)
    except Exception:
        raise HTTPException(status_code=401, detail="session expired")

    claims: dict[str, Any] = auth_info.get("sessionToken") or auth_info
    auth_user_id = str(claims.get("sub") or "")

    if not auth_user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    email = claims.get("email") if isinstance(claims.get("email"), str) else None
    name = claims.get("name") if isinstance(claims.get("name"), str) else None
    user = await ensure_user(auth_user_id, email)

    return AuthContext(
        auth_user_id=auth_user_id,
        user_id=user.id,
        email=email,
        name=name,
        token=claims,
    )
