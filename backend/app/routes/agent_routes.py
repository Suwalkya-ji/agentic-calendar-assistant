import asyncio
import json
import logging
from uuid import UUID

from fastapi import APIRouter, Body, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field, ValidationError, field_validator

from app.middleware.require_session import AuthContext, require_session
from app.services.agent_service import (
    AgentEvent,
    get_thread_messages,
    list_user_threads,
    stream_agent_reply,
)
from app.services.error_utils import format_agent_error

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agent", dependencies=[Depends(require_session)])


class ChatBody(BaseModel):
    message: str = Field(min_length=1, max_length=5000)
    threadId: UUID

    @field_validator("message", mode="before")
    @classmethod
    def strip_message(cls, value):
        return value.strip() if isinstance(value, str) else value


@router.get("/threads")
async def threads(auth: AuthContext = Depends(require_session)):
    try:
        return {"threads": await list_user_threads(auth.auth_user_id)}
    except Exception as error:
        logger.exception("failed to list threads")
        return JSONResponse({"error": str(error) or "failed to list threads"}, status_code=500)


@router.get("/threads/{thread_id}")
async def thread_messages(thread_id: str, auth: AuthContext = Depends(require_session)):
    try:
        parsed = str(UUID(thread_id))
    except ValueError:
        return JSONResponse({"error": "Invalid threadId"}, status_code=400)

    try:
        messages = await get_thread_messages(auth.auth_user_id, parsed)
    except Exception as error:
        logger.exception("failed to load thread")
        return JSONResponse({"error": str(error) or "failed to load thread"}, status_code=500)

    if messages is None:
        return JSONResponse({"error": "Thread not found"}, status_code=404)

    return {"threadId": parsed, "messages": messages}


@router.post("/chat")
async def chat(
    raw_body: dict | None = Body(default=None),
    auth: AuthContext = Depends(require_session),
):
    try:
        body = ChatBody.model_validate(raw_body or {})
    except ValidationError:
        return JSONResponse({"error": "Invalid chat body"}, status_code=400)

    queue: asyncio.Queue[AgentEvent | None] = asyncio.Queue()

    async def on_event(event: AgentEvent) -> None:
        await queue.put(event)

    async def run_agent() -> None:
        try:
            await stream_agent_reply(
                auth_user_id=auth.auth_user_id,
                thread_id=str(body.threadId),
                message=body.message,
                on_event=on_event,
            )
        except PermissionError as error:
            await queue.put({"type": "error", "message": format_agent_error(error)})
        except Exception as error:
            logger.exception("chat failed: %s", error)
            await queue.put({"type": "error", "message": format_agent_error(error)})
        finally:
            await queue.put(None)

    async def event_stream():
        task = asyncio.create_task(run_agent())
        try:
            while (event := await queue.get()) is not None:
                yield f"data: {json.dumps(event)}\n\n"
        finally:
            if not task.done():
                task.cancel()

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache, no-transform", "Connection": "keep-alive"},
    )
