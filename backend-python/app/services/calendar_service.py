import uuid
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote

import httpx

from app.services.token_service import get_calendar_access_token

CALENDAR_API = "https://www.googleapis.com/calendar/v3"


class CalendarError(RuntimeError):
    pass


async def _request(
    auth_user_id: str,
    method: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    json: dict[str, Any] | None = None,
) -> dict[str, Any]:
    access_token = await get_calendar_access_token(auth_user_id)

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.request(
            method,
            f"{CALENDAR_API}{path}",
            headers={"Authorization": f"Bearer {access_token}"},
            params={k: v for k, v in (params or {}).items() if v is not None},
            json=json,
        )

    if not response.is_success:
        try:
            message = response.json()["error"]["message"]
        except Exception:
            message = response.text or response.reason_phrase
        raise CalendarError(f"Google Calendar error ({response.status_code}): {message}")

    return response.json() if response.content else {}


def _event_path(event_id: str) -> str:
    return f"/calendars/primary/events/{quote(event_id, safe='')}"


def format_event(event: dict[str, Any]) -> dict[str, Any]:
    start = event.get("start") or {}
    end = event.get("end") or {}

    return {
        "id": event.get("id"),
        "title": event.get("summary") or "(no title)",
        "description": (event.get("description") or "").strip() or None,
        "location": (event.get("location") or "").strip() or None,
        "start": start.get("dateTime") or start.get("date"),
        "end": end.get("dateTime") or end.get("date"),
        "htmlLink": event.get("htmlLink"),
        "meetLink": event.get("hangoutLink"),
        "attendees": [
            value
            for person in event.get("attendees") or []
            if (value := person.get("email") or person.get("displayName"))
        ],
    }


async def list_upcoming_meetings(
    auth_user_id: str,
    max_results: int | None = None,
    today_only: bool | None = None,
) -> list[dict[str, Any]]:
    time_min = datetime.now(timezone.utc).isoformat()
    time_max: str | None = None

    if today_only:
        # "Today" in the server's local timezone, same as the Node version.
        now = datetime.now().astimezone()
        time_min = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        time_max = now.replace(hour=23, minute=59, second=59, microsecond=999999).isoformat()

    data = await _request(
        auth_user_id,
        "GET",
        "/calendars/primary/events",
        params={
            "timeMin": time_min,
            "timeMax": time_max,
            "maxResults": max_results or 10,
            "singleEvents": "true",
            "orderBy": "startTime",
        },
    )

    return [format_event(item) for item in data.get("items") or []]


async def create_meeting(
    auth_user_id: str,
    title: str,
    start_iso: str,
    end_iso: str,
    attendee_emails: list[str] | None = None,
    description: str | None = None,
    add_google_meet: bool | None = None,
) -> dict[str, Any]:
    # enabled by default
    with_meet = add_google_meet is not False

    body: dict[str, Any] = {
        "summary": title,
        "start": {"dateTime": start_iso},
        "end": {"dateTime": end_iso},
        "attendees": [{"email": email} for email in attendee_emails or []],
    }

    if description is not None:
        body["description"] = description

    if with_meet:
        body["conferenceData"] = {
            "createRequest": {
                "requestId": str(uuid.uuid4()),
                "conferenceSolutionKey": {"type": "hangoutsMeet"},
            }
        }

    data = await _request(
        auth_user_id,
        "POST",
        "/calendars/primary/events",
        params={"sendUpdates": "all", "conferenceDataVersion": 1 if with_meet else None},
        json=body,
    )

    return {
        **format_event(data),
        "inviteEmailsSent": len(attendee_emails or []) > 0,
        "googleMeetAdded": with_meet,
    }


async def cancel_meeting(auth_user_id: str, event_id: str) -> dict[str, Any]:
    await _request(auth_user_id, "DELETE", _event_path(event_id), params={"sendUpdates": "all"})

    return {"cancelled": True, "eventId": event_id}


async def reschedule_meeting(
    auth_user_id: str, event_id: str, start_iso: str, end_iso: str
) -> dict[str, Any]:
    data = await _request(
        auth_user_id,
        "PATCH",
        _event_path(event_id),
        params={"sendUpdates": "all"},
        json={"start": {"dateTime": start_iso}, "end": {"dateTime": end_iso}},
    )

    return format_event(data)


async def check_calendar_busy(auth_user_id: str, start_iso: str, end_iso: str) -> dict[str, Any]:
    data = await _request(
        auth_user_id,
        "POST",
        "/freeBusy",
        json={"timeMin": start_iso, "timeMax": end_iso, "items": [{"id": "primary"}]},
    )

    busy = ((data.get("calendars") or {}).get("primary") or {}).get("busy") or []

    return {"busy": [{"start": item.get("start"), "end": item.get("end")} for item in busy]}
