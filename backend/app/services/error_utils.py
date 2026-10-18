import re


def format_agent_error(error: Exception | str) -> str:
    """Translate raw API or model errors into user-friendly messages."""
    raw = str(error)
    lower = raw.lower()

    # 1. Quota / Rate limit (Gemini 429 RESOURCE_EXHAUSTED / OpenAI 429)
    if any(k in lower for k in ("resource_exhausted", "429", "quota exceeded", "rate limit", "ratelimit")):
        retry_match = re.search(r"retry\s+(?:in|after)\s+([0-9a-zA-Z\.]+)", raw, re.IGNORECASE)
        if retry_match:
            time_raw = retry_match.group(1).rstrip(".")
            h = re.search(r"(\d+)\s*h", time_raw)
            m = re.search(r"(\d+)\s*m", time_raw)
            s = re.search(r"(\d+)(?:\.\d+)?\s*s", time_raw)

            parts: list[str] = []
            if h:
                val = int(h.group(1))
                parts.append(f"{val} hour{'s' if val != 1 else ''}")
            if m:
                val = int(m.group(1))
                parts.append(f"{val} minute{'s' if val != 1 else ''}")
            if not h and not m and s:
                val = int(s.group(1))
                parts.append(f"{val} second{'s' if val != 1 else ''}")

            if parts:
                duration = " and ".join(parts)
                return (
                    "⏳ **Daily Request Limit Reached**\n\n"
                    f"You have reached the free tier quota for this AI model. Please retry in **{duration}**."
                )
            if time_raw:
                return (
                    "⏳ **Daily Request Limit Reached**\n\n"
                    f"You have reached the free tier quota for this AI model. Please retry in **{time_raw}**."
                )

        return (
            "⏳ **Daily Request Limit Reached**\n\n"
            "You have reached the free tier request quota for the AI model. Please wait a while before sending another message."
        )

    # 2. Authentication or API key issue
    if any(k in lower for k in ("invalid_api_key", "api_key_invalid", "401", "unauthorized")):
        return (
            "🔑 **AI Configuration Error**\n\n"
            "The configured AI provider API key is invalid or expired. Please check your backend configuration."
        )

    # 3. Calendar Permission error
    if isinstance(error, PermissionError) or "permission" in lower:
        return f"🔒 **Permission Notice:** {raw}"

    # 4. Long raw JSON or dump fallback
    if len(raw) > 200 and ("{" in raw or "[" in raw):
        return "⚠️ An unexpected error occurred while communicating with the AI service. Please try again shortly."

    return raw
