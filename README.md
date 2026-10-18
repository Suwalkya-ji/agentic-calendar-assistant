# Concierge — Agentic Calendar Assistant

An AI meeting assistant for Google Calendar. Sign in, connect your calendar, and manage your day in plain language:
*"What's on today?"*, *"Find a free slot tomorrow morning"*, *"Move the design review to Friday at 3pm"*.
Replies stream in as they are written. Meetings are created with Google Meet links, and invitations are sent to the attendees.

**Live:** [agentic-calendar-assistant-kappa.vercel.app](https://agentic-calendar-assistant-kappa.vercel.app)

## Features

- **Natural-language scheduling:** list, create, reschedule and cancel events, and check free/busy before booking.
- **Google Meet and invites:** new meetings get a Meet link by default, and attendees receive calendar invitations.
- **Streaming chat:** token-by-token replies over Server-Sent Events, with a live status line while tools run ("Reviewing your calendar…").
- **Memory:** conversation threads, plus long-term preferences (timezone, default meeting length, usual invitees) that the assistant saves when you mention them.
- **Secure by design:** Descope handles login and the Google OAuth connection. The app never stores Google tokens, each user can only see their own threads, and Row Level Security is on for every table.
- **MCP server:** the same calendar tools are available to AI IDEs (Antigravity, Cursor, …) at `/mcp`, protected by Descope OAuth.
- **Responsive UI:** a premium, minimalist design (the "Executive Concierge" design system) that works on desktop, tablet and phone.

## How it works

```
Browser (Next.js on Vercel)
   │  Descope login → session token
   │  REST + SSE (Authorization: Bearer <token>)
   ▼
FastAPI backend (Render) ──── Descope: validate session, fetch the user's Google token
   │
   ├── Agent (OpenAI Agents SDK) ── Gemini (OpenAI-compatible API)
   │       └── tools ── Google Calendar API v3
   │
   └── PostgreSQL (Supabase): users, connections, threads, messages, preferences
```

1. The user signs in with Descope. The frontend sends the session token with every API call.
2. **Connect Google Calendar** starts Descope's outbound OAuth flow. Descope stores and refreshes the Google token.
3. A chat message goes to `/api/agent/chat`. The agent loads the thread history and the user's saved preferences, then calls calendar tools as needed. The reply streams back as SSE events.

## Tech stack

| Area | Technology |
|---|---|
| Frontend | Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS 4, shadcn/ui, lucide icons, react-markdown |
| Backend | Python 3.11+, FastAPI, Uvicorn, Pydantic, asyncpg, httpx |
| AI | Google Gemini via the OpenAI Agents SDK (tool calling, sessions, streaming). OpenAI as a fallback |
| Auth | Descope (sessions, JWT, outbound OAuth for Google, MCP authorization) |
| Calendar | Google Calendar API v3 |
| Database | PostgreSQL (Supabase in production, Docker locally) |
| AI tooling | MCP (Model Context Protocol) server |
| Hosting | Vercel (frontend), Render (backend), Supabase (database) |

## Project structure

```
.
├── backend/                 FastAPI app (see backend/README.md)
│   ├── app/
│   │   ├── main.py          app setup, CORS, /health, routers, MCP
│   │   ├── config/          Descope client, agent prompt, chat memory
│   │   ├── db/pool.py       asyncpg pool (Supabase-pooler friendly)
│   │   ├── middleware/      Descope session check
│   │   ├── repositories/    users / connections SQL
│   │   ├── routes/          /api/connections, /api/agent
│   │   ├── services/        agent, tools, calendar, connection, tokens
│   │   └── mcp/server.py    Descope-protected MCP server
│   ├── scripts/migrate.py   runs sql/*.sql in order
│   ├── sql/                 schema migrations
│   └── requirements.txt
├── frontend/                Next.js app
│   └── src/
│       ├── app/             /sign-in, /dashboard
│       ├── components/      chat panel, connection card, markdown, ui
│       └── lib/             API client, SSE streaming, connections
├── docker-compose.yml       local Postgres (port 5442)
└── render.yaml              Render blueprint for the backend
```

## Getting started (local)

### Prerequisites

- Python 3.11+ and Node.js 20+ (LTS)
- Docker, for the local database (or use a Supabase connection string)
- A [Descope](https://www.descope.com) project
- A Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey)

### 1. Set up Descope

1. Create a project and note its **Project ID**.
2. Create a **Management Key** (Company settings → Management Keys).
3. Under **Connections** (Outbound Apps), add **Google Calendar** with the scope `https://www.googleapis.com/auth/calendar`, and enter your Google OAuth client ID and secret.
   - In Google Cloud Console, add the callback URL that Descope shows to the OAuth client's **Authorized redirect URIs**.
   - Note the connection ID (for example `google-calendar`).
4. Make sure the `sign-up-or-in` flow exists (it does by default).

### 2. Start the database

```bash
docker compose up -d        # Postgres on localhost:5442
```

### 3. Run the backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env               # fill in the values (see below)

python -m scripts.migrate          # create the tables
uvicorn app.main:app --reload --port 4000
```

Check it at http://localhost:4000/health (it should say `"database":"up"`). The interactive API docs are at http://localhost:4000/docs.

### 4. Run the frontend

```bash
cd frontend
npm install
cp .env.example .env.local         # fill in the values (see below)
npm run dev
```

Open http://localhost:3000, sign in, click **Connect Google Calendar**, and ask *"What's on today?"*.

## Environment variables

Never commit real values. `.env` files are git-ignored; only the `.env.example` files belong in the repo.

### Backend (`backend/.env`)

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | ✅ | Postgres connection string. For Supabase, use the **pooler** string (Connect → Connection pooling), not `db.<ref>.supabase.co`, which is IPv6-only |
| `DESCOPE_PROJECT_ID` | ✅ | Descope project ID |
| `DESCOPE_MANAGEMENT_KEY` | ✅ | Descope management key (used to fetch users' Google tokens) |
| `DESCOPE_CALENDAR_CONNECTION_ID` | ✅ | The Google Calendar connection ID in Descope (default `google-calendar`) |
| `GEMINI_API_KEY` | ✅ | Gemini API key |
| `AI_MODEL` | | Model name (Gemini default is set in code). Use a model listed in Google AI Studio |
| `OPENAI_API_KEY` | | Used only when `GEMINI_API_KEY` is empty |
| `APP_URL` | ✅ | Frontend origin(s) allowed by CORS, comma-separated, e.g. `http://localhost:3000,https://your-app.vercel.app` |
| `PORT` | | Local port (default `4000`) |
| `DB_POOL_MAX_SIZE` | | Max database connections (default `5`) |
| `SERVER_URL` | | Public URL of the backend. Needed for MCP |
| `DESCOPE_MCP_SERVER_WELL_KNOWN_URL` | | Descope MCP server `.well-known/openid-configuration` URL. Enables `/mcp` |

### Frontend (`frontend/.env.local`)

| Variable | Description |
|---|---|
| `NEXT_PUBLIC_API_URL` | Backend URL (`http://localhost:4000` locally, your Render URL in production) |
| `NEXT_PUBLIC_DESCOPE_PROJECT_ID` | The same Descope project ID as the backend |

## API

All `/api/*` routes need `Authorization: Bearer <Descope session token>`.

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Service and database status |
| GET | `/api/connections` | Google Calendar connection status |
| POST | `/api/connections/connect` | `{ refreshToken, redirectUrl? }` → `{ url }` to start Google OAuth |
| POST | `/api/connections/refresh-status` | Re-check the connection with Descope |
| GET | `/api/agent/threads` | The user's recent threads |
| GET | `/api/agent/threads/{threadId}` | Messages in a thread (404 if it isn't yours) |
| POST | `/api/agent/chat` | `{ message, threadId }` → SSE stream: `started`, `progress`, `token`, `completed`, `error` |
| POST | `/mcp` | MCP endpoint (Descope OAuth), when configured |

## Deployment

### Database: Supabase

1. Create a project and copy the **pooler** connection string (port `6543` or `5432` on `*.pooler.supabase.com`).
2. The Render build runs the migrations automatically. You can also run `python -m scripts.migrate` with `DATABASE_URL` set.
3. Row Level Security is enabled on all tables (`sql/004_enable_rls.sql`), so Supabase's public REST API can't read them. The backend connects as the table owner and is unaffected.

### Backend: Render

`render.yaml` defines the web service: `rootDir: backend`, the build installs requirements and runs migrations, and the start command is `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
Set the environment variables from the backend table in the Render dashboard. `APP_URL` must include your Vercel URL.

> On the free plan the service sleeps after about 15 minutes idle. The first request after that takes around a minute.

### Frontend: Vercel

Import the repo, set the **Root Directory** to `frontend`, and add `NEXT_PUBLIC_API_URL` (your Render URL) and `NEXT_PUBLIC_DESCOPE_PROJECT_ID`.

## Using the MCP server (Antigravity, Cursor, …)

1. Create an MCP server in Descope (Agentic Identity Hub → MCP Servers) and copy its well-known URL into `DESCOPE_MCP_SERVER_WELL_KNOWN_URL`.
2. Set `SERVER_URL` to the backend's public URL. For local testing, expose it with `ngrok http 4000`.
3. Add `https://<your-backend>/mcp` as a remote MCP server in your IDE. It opens a Descope login on first use.

The MCP endpoint offers `listUpcomingMeetings`. Creating, rescheduling and cancelling are available in the web chat.

## Troubleshooting

| Symptom | Fix |
|---|---|
| Browser shows a CORS error | Add the frontend URL to `APP_URL` on the backend (no trailing slash) |
| `Database unavailable (…)` | Check `DATABASE_URL`. Use Supabase's pooler string. The name in brackets is the underlying error |
| `401 session expired` | The frontend and backend use different Descope project IDs, or the session expired |
| `Calendar access token is not present` | Connect Google Calendar again from the sidebar |
| "Daily Request Limit Reached" in chat | The Gemini free-tier quota is used up. Wait, or use a paid key |
| `Cannot find module '../lightningcss.win32-x64-msvc.node'` (Windows) | Delete `frontend/node_modules`, `.next` and `package-lock.json`, then run `npm install` |

## Security notes

- Rotate any key that has ever been committed. Git history keeps it.
- Google tokens stay in Descope and are fetched per request.
- Users can only read and write their own threads. Requests for another user's thread return 404.
