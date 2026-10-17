import os

from app.config.descope import CALENDAR_CONNECTION_ID, descope_client


async def fetch_calendar_token(auth_user_id: str) -> dict | None:
    """Latest Google token Descope holds for this user, or None if there is none."""
    try:
        response = await descope_client.mgmt.outbound_application.fetch_token(
            CALENDAR_CONNECTION_ID, auth_user_id
        )
    except Exception:
        return None

    token = response.get("token") if isinstance(response, dict) else None
    return token if isinstance(token, dict) else None


async def get_calendar_access_token(auth_user_id: str) -> str:
    if not CALENDAR_CONNECTION_ID or not os.getenv("DESCOPE_MANAGEMENT_KEY"):
        raise RuntimeError("connection is not configured")

    token = await fetch_calendar_token(auth_user_id)
    access_token = (token or {}).get("accessToken") or (token or {}).get("token")

    if not access_token:
        raise RuntimeError("Calendar access token is not present, please check or reconnect")

    return access_token
