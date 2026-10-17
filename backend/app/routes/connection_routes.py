import logging
import os
from typing import Any

from fastapi import APIRouter, Body, Depends
from fastapi.responses import JSONResponse

from app.middleware.require_session import AuthContext, require_session
from app.services.connection_service import (
    create_calendar_connect_url,
    get_calendar_connection,
    refresh_calendar_connection,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/connections", dependencies=[Depends(require_session)])


@router.get("")
@router.get("/", include_in_schema=False)
async def get_connection(auth: AuthContext = Depends(require_session)):
    try:
        return {"connection": await get_calendar_connection(auth.user_id)}
    except Exception:
        logger.exception("could not load connections")
        return JSONResponse({"error": "could not load connections"}, status_code=500)


@router.post("/connect")
async def connect(
    body: dict[str, Any] | None = Body(default=None),
    auth: AuthContext = Depends(require_session),
):
    body = body or {}
    refresh_token = body.get("refreshToken") if isinstance(body.get("refreshToken"), str) else ""

    if not refresh_token:
        return JSONResponse({"error": "Refresh token required"}, status_code=400)

    redirect_url = (
        body["redirectUrl"]
        if isinstance(body.get("redirectUrl"), str)
        else f"{os.getenv('APP_URL') or 'http://localhost:3000'}/dashboard"
    )

    try:
        return await create_calendar_connect_url(auth.user_id, refresh_token, redirect_url)
    except Exception:
        logger.exception("could not start connection")
        return JSONResponse({"error": "could not start connection"}, status_code=500)


@router.post("/refresh-status")
async def refresh_status(auth: AuthContext = Depends(require_session)):
    try:
        connection = await refresh_calendar_connection(auth.user_id, auth.auth_user_id)
        return {"connection": connection}
    except Exception:
        logger.exception("failed to refresh the status")
        return JSONResponse({"error": "failed to refresh the status"}, status_code=500)
