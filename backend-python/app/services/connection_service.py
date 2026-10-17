import os

import httpx

from app.config.descope import (
    CALENDAR_CONNECTION_ID,
    CALENDAR_CONNECTION_LABEL,
    descope_base_url,
    project_id,
)
from app.repositories.connection_repository import (
    get_calendar_connection_status,
    upsert_calendar_connection,
)
from app.services.token_service import fetch_calendar_token


def calendar_app_id() -> str:
    if not CALENDAR_CONNECTION_ID:
        raise RuntimeError("CALENDAR_CONNECTION_ID is not present in env")

    return CALENDAR_CONNECTION_ID


async def get_calendar_connection(user_id: str) -> dict:
    status = await get_calendar_connection_status(user_id)
    return {"label": CALENDAR_CONNECTION_LABEL, "status": status or "disconnected"}


async def create_calendar_connect_url(user_id: str, refresh_token: str, redirect_url: str) -> dict:
    # The Python SDK has no wrapper for the user-facing outbound connect call,
    # so call the endpoint the Node SDK uses (authenticated with the user's refresh token).
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            f"{descope_base_url()}/v1/outbound/oauth/connect",
            headers={"Authorization": f"Bearer {project_id}:{refresh_token}"},
            json={"appId": calendar_app_id(), "options": {"redirectUrl": redirect_url}},
        )

    url = response.json().get("url") if response.is_success else None

    if not url:
        raise RuntimeError("could not start connection")

    await upsert_calendar_connection(user_id, "pending")

    return {"url": url}


async def refresh_calendar_connection(user_id: str, auth_user_id: str) -> dict:
    if not os.getenv("DESCOPE_MANAGEMENT_KEY"):
        raise RuntimeError("DESCOPE_MANAGEMENT_KEY is not set in env file")

    calendar_app_id()
    token = await fetch_calendar_token(auth_user_id)
    status = "connected" if token else "disconnected"

    row_status = await upsert_calendar_connection(user_id, status)

    return {"label": CALENDAR_CONNECTION_LABEL, "status": row_status}
