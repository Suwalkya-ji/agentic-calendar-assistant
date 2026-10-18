# Agentic Calendar Assistant — backend

Python (FastAPI) backend, ported from the original Node/Express backend with the same HTTP API. See the [root README](../README.md) for the full project overview, setup and deployment.

| Node backend | Python backend |
|---|---|
| Express 5 | FastAPI + uvicorn |
| `pg` | `asyncpg` |
| Mastra agent + memory (`mastra.db`) | OpenAI Agents SDK running Gemini (or OpenAI), with history in Postgres |
| `googleapis` | Google Calendar REST API through `httpx` |
| `@descope/node-sdk` | `descope` (async client) |
| `@descope/mcp-express` | `mcp` SDK (`MCPServer`) with a Descope token verifier |

## Run

```bash
docker compose up -d            # from the repo root: Postgres on localhost:5442

cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # then fill in the Descope values and GEMINI_API_KEY

python -m scripts.migrate       # create tables
uvicorn app.main:app --reload --port 4000
```

Check it's up with `curl http://localhost:4000/health`. Interactive API docs are at http://localhost:4000/docs.

## API

All `/api/*` routes need `Authorization: Bearer <Descope session token>`.

| Method | Path | Notes |
|---|---|---|
| GET | `/health` | Database check |
| GET | `/api/connections` | Google Calendar connection status |
| POST | `/api/connections/connect` | `{refreshToken, redirectUrl?}` → `{url}` (Descope outbound OAuth) |
| POST | `/api/connections/refresh-status` | Re-checks Descope for a Google token |
| GET | `/api/agent/threads` | The user's chat threads |
| GET | `/api/agent/threads/{threadId}` | Messages in a thread (404 if it isn't the user's) |
| POST | `/api/agent/chat` | `{message, threadId}` → SSE stream of `started` / `progress` / `token` / `completed` / `error` |
| POST | `/mcp` | MCP endpoint (only when `DESCOPE_MCP_SERVER_WELL_KNOWN_URL` is set) |

## Layout

```
app/
  main.py                    FastAPI app, CORS, /health, router + MCP mounting
  config/                    descope client, agent instructions, chat memory (Postgres)
  db/pool.py                 asyncpg pool (small, no statement cache: works with Supabase's pooler)
  middleware/require_session.py   Descope session check (FastAPI dependency)
  repositories/              users / connections SQL
  routes/                    connection + agent routes
  services/                  agent, agent tools, calendar, connection, token
  mcp/server.py              Descope-protected MCP server
scripts/migrate.py           runs sql/*.sql in order (all migrations are idempotent)
sql/                         users, connections, agent memory, row level security
```

## AI model

Set `GEMINI_API_KEY` to use Google Gemini (change the model with `AI_MODEL`).
If `GEMINI_API_KEY` is empty and `OPENAI_API_KEY` is set, OpenAI is used instead (default `gpt-4o-mini`).

## Differences from the Node version

- Agent tool names and arguments are snake_case (`list_upcoming_meetings`, `today_only`, …). The MCP tool keeps its `listUpcomingMeetings` name and camelCase arguments.
- Working memory (meeting preferences) is saved by an `update_working_memory` tool and injected into the instructions on each request.
- Chat history uses the last 20 items, and the window always starts at a user message.
- `/chat` refuses a `threadId` that belongs to another user.
- `/connect` returns 400 properly when `refreshToken` is missing.
- The app refuses to start without `DESCOPE_PROJECT_ID`, because the Python Descope SDK requires it.
- Chat threads, messages and working memory are stored in Postgres (`agent_threads`, `agent_messages`, `working_memory`), so they survive restarts and redeploys.
