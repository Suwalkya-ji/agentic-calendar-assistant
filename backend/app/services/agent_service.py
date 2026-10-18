import os
from collections.abc import Awaitable, Callable
from typing import Any, Literal, TypedDict

from agents import Agent, Model, OpenAIChatCompletionsModel, Runner, set_tracing_disabled
from agents.items import ToolCallItem
from openai import AsyncOpenAI

from app.config import memory
from app.config.agent_instructions import get_agent_instructions
from app.services.agent_tools import CALENDAR_TOOLS, AgentContext


class AgentEvent(TypedDict, total=False):
    type: Literal["started", "progress", "token", "completed", "error"]
    message: str
    token: str


OnEvent = Callable[[AgentEvent], Awaitable[None]]


GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"

_gemini_client: AsyncOpenAI | None = None


def build_model() -> Model | str:
    """Gemini (through its OpenAI-compatible API) when GEMINI_API_KEY is set, else OpenAI."""
    global _gemini_client

    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_GEMINI_API_KEY")

    if gemini_key:
        if _gemini_client is None:
            _gemini_client = AsyncOpenAI(api_key=gemini_key, base_url=GEMINI_BASE_URL)
            # Traces are uploaded to OpenAI, which needs an OpenAI key.
            set_tracing_disabled(True)

        return OpenAIChatCompletionsModel(
            model=os.getenv("AI_MODEL") or "gemini-3.8-flash",
            openai_client=_gemini_client,
        )

    if os.getenv("OPENAI_API_KEY"):
        return os.getenv("AI_MODEL") or "gpt-4o-mini"

    raise RuntimeError("GEMINI_API_KEY is not set in env")


def message_text(item: Any) -> str:
    """Plain text of a stored user/assistant message item ("" for tool calls etc.)."""
    if not isinstance(item, dict):
        return ""

    content = item.get("content")

    if isinstance(content, str):
        return content.strip()

    if not isinstance(content, list):
        return ""

    return "\n".join(
        part["text"].strip()
        for part in content
        if isinstance(part, dict)
        and part.get("type") in ("input_text", "output_text", "text")
        and isinstance(part.get("text"), str)
        and part["text"].strip()
    ).strip()


async def list_user_threads(auth_user_id: str) -> list[dict[str, str]]:
    threads = await memory.list_threads(auth_user_id, limit=30)

    return [
        {
            "id": thread["id"],
            "title": (thread["title"] or "").strip() or "Untitled Chat",
            "updatedAt": thread["updated_at"],
        }
        for thread in threads
    ]


async def get_thread_messages(auth_user_id: str, thread_id: str) -> list[dict[str, str]] | None:
    thread = await memory.get_thread(thread_id)

    if not thread or thread["resource_id"] != auth_user_id:
        return None

    items = await memory.open_session(thread_id).get_all_items()

    messages: list[dict[str, str]] = []

    for index, item in enumerate(items):
        role = item.get("role") if isinstance(item, dict) else None
        if role not in ("user", "assistant", "system"):
            continue

        content = message_text(item)
        if not content:
            continue

        # Position-based ids: providers like Gemini give every message the same placeholder id.
        messages.append({"id": f"{thread_id}-{index}", "role": role, "content": content})

    return messages


async def stream_agent_reply(
    auth_user_id: str, thread_id: str, message: str, on_event: OnEvent
) -> None:
    model = build_model()

    await memory.ensure_thread(thread_id, auth_user_id)

    await on_event({"type": "started", "message": "Agent is planning"})

    agent = Agent[AgentContext](
        name="Meeting Assistant",
        instructions=get_agent_instructions(await memory.get_working_memory(auth_user_id)),
        model=model,
        tools=CALENDAR_TOOLS,
    )

    result = Runner.run_streamed(
        agent,
        message,
        context=AgentContext(auth_user_id=auth_user_id),
        session=memory.open_session(thread_id),
    )

    async for event in result.stream_events():
        if event.type == "run_item_stream_event" and isinstance(event.item, ToolCallItem):
            tool_name = getattr(event.item.raw_item, "name", None) or "tool"
            await on_event({"type": "progress", "message": f"Running {tool_name}"})
            continue

        if event.type == "raw_response_event" and event.data.type == "response.output_text.delta":
            if event.data.delta:
                await on_event({"type": "token", "token": event.data.delta})

    # streaming finished
    await memory.touch_thread(thread_id, title=message[:80])

    await on_event({"type": "completed", "message": "done"})
