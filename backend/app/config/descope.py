import os

from descope import DescopeClientAsync

project_id = os.getenv("DESCOPE_PROJECT_ID")
management_key = os.getenv("DESCOPE_MANAGEMENT_KEY")

if not project_id:
    # The Python SDK cannot be created without a project id.
    raise RuntimeError("DESCOPE_PROJECT_ID is not set (add it to backend-python/.env)")

descope_client = DescopeClientAsync(
    project_id=project_id,
    management_key=management_key or None,
)

CALENDAR_CONNECTION_ID = os.getenv("DESCOPE_CALENDAR_CONNECTION_ID") or "google-calendar"

CALENDAR_CONNECTION_LABEL = "Google Calendar"


def descope_base_url() -> str:
    # The SDK derives the (possibly regional) API base URL from the project id.
    return descope_client._auth_http.base_url
