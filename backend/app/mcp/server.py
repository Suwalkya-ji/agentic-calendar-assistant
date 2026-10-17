"""Descope-protected MCP server (POST /mcp) exposing calendar tools to MCP clients like Cursor."""

import logging
import os
import time
from typing import Any
from urllib.parse import urlparse

import httpx
from fastapi import FastAPI
from fastapi.responses import JSONResponse, Response
from mcp.server.auth.middleware.auth_context import get_access_token
from mcp.server.auth.provider import AccessToken
from mcp.server.auth.settings import AuthSettings
from mcp.server.mcpserver import MCPServer

from app.config.descope import descope_client
from app.services.calendar_service import list_upcoming_meetings

logger = logging.getLogger(__name__)

OPENID_CONFIGURATION_SUFFIX = "/.well-known/openid-configuration"


class DescopeTokenVerifier:
    async def verify_token(self, token: str) -> AccessToken | None:
        try:
            auth_info = await descope_client.validate_session(token)
        except Exception:
            return None

        claims: dict[str, Any] = auth_info.get("sessionToken") or auth_info
        subject = claims.get("sub")

        if not subject:
            return None

        scope = claims.get("scope")
        scopes = scope.split() if isinstance(scope, str) else []
        audience = claims.get("aud")

        return AccessToken(
            token=token,
            client_id=str(claims.get("azp") or claims.get("client_id") or subject),
            scopes=scopes,
            expires_at=claims.get("exp"),
            resource=audience[0] if isinstance(audience, list) and audience else audience,
            subject=str(subject),
            claims=claims,
        )


def _issuer_from_well_known(well_known: str) -> str:
    if not well_known.endswith(OPENID_CONFIGURATION_SUFFIX):
        raise ValueError(f"DESCOPE_MCP_SERVER_WELL_KNOWN_URL must end with {OPENID_CONFIGURATION_SUFFIX}")

    return well_known[: -len(OPENID_CONFIGURATION_SUFFIX)]


def _require_scopes(*required: str) -> str | None:
    token = get_access_token()
    granted = token.scopes if token else []
    missing = [scope for scope in required if scope not in granted]

    if missing:
        return (
            f"Missing required scopes: {', '.join(missing)}. "
            f"User has scopes: {', '.join(granted) or 'none'}"
        )

    return None


def create_mcp_server(server_url: str, well_known: str) -> MCPServer:
    mcp = MCPServer(
        name="descope-mcp-server",
        version="1.0.0",
        token_verifier=DescopeTokenVerifier(),
        auth=AuthSettings(
            issuer_url=_issuer_from_well_known(well_known),
            resource_server_url=server_url,
            # The verifier only checks the Descope signature, like the Node version did.
            validate_token_resource=False,
        ),
    )

    @mcp.tool(name="listUpcomingMeetings")
    async def list_upcoming_meetings_tool(
        maxResults: int | None = None,
        todayOnly: bool | None = None,
    ) -> dict[str, Any]:
        """List Google Calendar events. Set todayOnly=true for today's agenda only.

        Args:
            maxResults: Maximum number of events to return (1-20).
            todayOnly: If true, only return events for today.
        """
        if error := _require_scopes("profile"):
            return {"error": error}

        token = get_access_token()

        if not token or not token.subject:
            return {"error": "MCP token has no user id"}

        if maxResults is not None:
            maxResults = min(max(maxResults, 1), 20)

        try:
            meetings = await list_upcoming_meetings(token.subject, maxResults, todayOnly)
            return {"meetings": meetings}
        except Exception as error:
            return {"error": str(error) or "List Failed"}

    return mcp


_metadata_cache: tuple[float, dict[str, Any]] | None = None


async def _descope_openid_configuration(well_known: str) -> dict[str, Any]:
    global _metadata_cache

    if _metadata_cache and time.monotonic() - _metadata_cache[0] < 3600:
        return _metadata_cache[1]

    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.get(well_known)
        response.raise_for_status()

    _metadata_cache = (time.monotonic(), response.json())
    return _metadata_cache[1]


def mount_mcp_server(app: FastAPI) -> MCPServer | None:
    """Mount the MCP server on the app. Returns the server (its session manager must be run
    in the app lifespan), or None if MCP is not configured."""
    well_known = os.getenv("DESCOPE_MCP_SERVER_WELL_KNOWN_URL")

    if not well_known:
        logger.warning("DESCOPE_MCP_SERVER_WELL_KNOWN_URL is not set; MCP endpoint is disabled")
        return None

    server_url = os.getenv("SERVER_URL") or f"http://localhost:{os.getenv('PORT') or 4000}"
    mcp = create_mcp_server(server_url, well_known)

    # Authorization server metadata, for clients that look it up on the resource server.
    @app.get("/.well-known/oauth-authorization-server", include_in_schema=False)
    async def authorization_server_metadata():
        try:
            config = await _descope_openid_configuration(well_known)
        except Exception:
            logger.exception("could not load Descope OpenID configuration")
            return JSONResponse({"error": "metadata unavailable"}, status_code=502)

        keys = (
            "issuer",
            "authorization_endpoint",
            "token_endpoint",
            "registration_endpoint",
            "revocation_endpoint",
            "jwks_uri",
            "scopes_supported",
            "response_types_supported",
            "grant_types_supported",
            "code_challenge_methods_supported",
            "token_endpoint_auth_methods_supported",
        )
        return {key: config[key] for key in keys if key in config}

    # cursor -> sends GET /mcp
    @app.get("/mcp", include_in_schema=False)
    async def mcp_get():
        return Response("Method not allowed", status_code=405, headers={"Allow": "POST"})

    mcp_app = mcp.streamable_http_app(
        streamable_http_path="/mcp",
        stateless_http=True,
        host=urlparse(server_url).hostname or "127.0.0.1",
    )
    # Mounted last at the root so the app's own routes take precedence;
    # this serves POST /mcp and /.well-known/oauth-protected-resource.
    app.mount("/", mcp_app)

    logger.info("MCP endpoint: POST %s/mcp", server_url)
    return mcp
