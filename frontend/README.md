# Concierge — frontend

Next.js 16 app for the agentic calendar assistant: Descope sign-in, Google Calendar connection, and a streaming chat with the agent.

```bash
npm install
cp .env.example .env.local   # NEXT_PUBLIC_API_URL, NEXT_PUBLIC_DESCOPE_PROJECT_ID
npm run dev                  # http://localhost:3000
```

| Path | What it is |
|---|---|
| `src/app/sign-in` | Descope `sign-up-or-in` flow |
| `src/app/dashboard` | Main workspace (auth-guarded) |
| `src/components/dashboard/chat-panel.tsx` | Thread rail, chat, SSE streaming, composer |
| `src/components/dashboard/connection-panel.tsx` | Google Calendar connection card |
| `src/lib/agent.ts` | API client and SSE stream parser |
| `src/app/globals.css` | Design tokens (Executive Concierge design system) |

See the [root README](../README.md) for the full setup, environment variables and deployment.
