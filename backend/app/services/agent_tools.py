from dataclasses import dataclass
from typing import Any

from agents import RunContextWrapper, function_tool

from app.config import memory
from app.services import calendar_service


@dataclass
class AgentContext:
    auth_user_id: str


@function_tool
async def list_upcoming_meetings(
    ctx: RunContextWrapper[AgentContext],
    max_results: int | None = None,
    today_only: bool | None = None,
) -> list[dict[str, Any]]:
    """List Google Calendar events. Set today_only=true for today's agenda only.

    Args:
        max_results: Maximum number of events to return (1-20).
        today_only: If true, only return events for today.
    """
    if max_results is not None:
        max_results = min(max(max_results, 1), 20)

    return await calendar_service.list_upcoming_meetings(
        ctx.context.auth_user_id, max_results, today_only
    )


@function_tool
async def check_calendar_busy(
    ctx: RunContextWrapper[AgentContext], start_iso: str, end_iso: str
) -> dict[str, Any]:
    """Check if the user is busy between two ISO datetimes using Google freebusy.

    Args:
        start_iso: Start time as ISO-8601 datetime.
        end_iso: End time as ISO-8601 datetime.
    """
    return await calendar_service.check_calendar_busy(ctx.context.auth_user_id, start_iso, end_iso)


@function_tool
async def create_meeting(
    ctx: RunContextWrapper[AgentContext],
    title: str,
    start_iso: str,
    end_iso: str,
    attendee_emails: list[str] | None = None,
    description: str | None = None,
    add_google_meet: bool | None = None,
) -> dict[str, Any]:
    """Create a Google Calendar event. Adds a Google Meet link by default. Emails invitees when attendee_emails are set.

    Args:
        title: Event title.
        start_iso: Start time as ISO-8601 datetime.
        end_iso: End time as ISO-8601 datetime.
        attendee_emails: Invite these emails; Google sends calendar invites.
        description: Optional event description / agenda.
        add_google_meet: Default true. Set false to skip Google Meet link.
    """
    return await calendar_service.create_meeting(
        ctx.context.auth_user_id,
        title,
        start_iso,
        end_iso,
        attendee_emails,
        description,
        add_google_meet,
    )


@function_tool
async def reschedule_meeting(
    ctx: RunContextWrapper[AgentContext], event_id: str, start_iso: str, end_iso: str
) -> dict[str, Any]:
    """Move an existing event to a new start/end time and email invitees.

    Args:
        event_id: Google Calendar event id.
        start_iso: New start time as ISO-8601 datetime.
        end_iso: New end time as ISO-8601 datetime.
    """
    return await calendar_service.reschedule_meeting(
        ctx.context.auth_user_id, event_id, start_iso, end_iso
    )


@function_tool
async def cancel_meeting(ctx: RunContextWrapper[AgentContext], event_id: str) -> dict[str, Any]:
    """Cancel a Google Calendar event by id and email attendees about the cancellation.

    Args:
        event_id: Google Calendar event id.
    """
    return await calendar_service.cancel_meeting(ctx.context.auth_user_id, event_id)


@function_tool
async def update_working_memory(ctx: RunContextWrapper[AgentContext], content: str) -> str:
    """Replace the user's working memory (lasting meeting preferences) with updated Markdown.

    Args:
        content: The full working memory Markdown, including unchanged lines.
    """
    await memory.set_working_memory(ctx.context.auth_user_id, content)
    return "Working memory updated"


CALENDAR_TOOLS = [
    list_upcoming_meetings,
    check_calendar_busy,
    create_meeting,
    reschedule_meeting,
    cancel_meeting,
    update_working_memory,
]
