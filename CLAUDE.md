# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Cheerleader is an AI-powered recruiting chatbot that answers questions about Jasper Lin's professional background. Users get a 3-question limit per session before being prompted to contact Jasper directly. It's deployed at `hirejasperlin.com`.

## Monorepo Structure

Two independent services:
- `cheerleader-api/` — Django 4.2 backend (Python 3.11)
- `cheerleader-ui/` — React 18 + TypeScript frontend (Vite)

## Commands

### Frontend (`cheerleader-ui/`)
```bash
npm run dev       # Dev server at localhost:5173
npm run build     # TypeScript compile + Vite production build
npm run lint      # ESLint (strict — warnings treated as errors)
npm run preview   # Preview production build
```

### Backend (`cheerleader-api/`)
```bash
python manage.py migrate       # Apply migrations
python manage.py runserver     # Dev server at localhost:8000
```

### Docker (backend)
```bash
docker build -t cheerleader-api .
docker run -p 8000:8000 --env-file .env cheerleader-api
```
The entrypoint runs `migrate` then starts Gunicorn on port 8000.

## Architecture

**Request flow:**
1. React UI (`App.tsx`) sends `POST /chat/bot-response/` with session cookies using `fetch`
2. Django view (`chat/views.py`) validates the JSON payload, checks/increments the session message count (limit: `MAX_USER_MESSAGE_COUNT`, default 3), and returns a `StreamingHttpResponse`
3. `chat/utils.py` builds a LangGraph `StateGraph` with a `MemorySaver` checkpointer, invokes the configured Claude model with the system prompt from `chat/prompt.txt`, and yields tokens as they arrive
4. The frontend reads the SSE stream and appends tokens to the message in real time
5. After streaming completes, the full response and conversation history are saved to the Django session

**SSE format:** Each event is `data: <json>\n\n`. Token events: `{"token": "..."}`. End event: `{"done": true, "time": "<iso timestamp>"}`.

**State management:** Conversation history (`chat_messages`) and message count live entirely in Django sessions (no database persistence for chat). Sessions expire after 24 hours. `message_count` is incremented before the response starts streaming so the session cookie is set in the response headers.

**System prompt:** `chat/prompt.txt` contains Jasper's full resume. The AI is instructed to answer only from that content. The prompt uses Python string template substitution to inject the current date.

## Key Configuration

**Backend environment variables** (`.env` in `cheerleader-api/`):
- `ANTHROPIC_API_KEY` — required for Claude API access
- `MODEL_NAME` (default: `claude-haiku-4-5-20251001`) — any `langchain-anthropic`-compatible model ID
- `PROMPT_FILE_PATH` — path to system prompt file (default: `chat/prompt.txt`)
- `MAX_USER_MESSAGE_COUNT` — session message limit (default: 3)
- `EMAIL_ADDRESS`, `PHONE_NUMBER` — injected into prompt for contact info
- `ENV` — set to `dev` for local development (affects CORS and cookie settings)

**Frontend environment variables** (`.env.local` in `cheerleader-ui/`):
- `VITE_API_URL` — backend base URL (default: `http://localhost:8000`)
- `VITE_LINKEDIN_URL`, `VITE_GITHUB_URL`, `VITE_RESUME_URL` — header links (defaults to Jasper's public profiles)

**CORS & sessions:** In dev (`ENV=dev`), the backend allows `localhost:5173`. In production, it allows `*.hirejasperlin.com`. Session cookies use `SameSite=Lax`, which works when the frontend and backend share a registrable domain (`hirejasperlin.com`). The backend must be served under a `hirejasperlin.com` subdomain (e.g. `api.hirejasperlin.com`) — the raw Render URL is not in the allowlist.

## Unused Code

- `cheerleader-ui/src/components/Chat.tsx` — alternate chat component with commented-out WebSocket implementation
- `react-use-websocket` dependency is installed but unused

## Deployment

Both services are deployed on Render. Custom domain: `hirejasperlin.com`. The backend must be accessible via a `hirejasperlin.com` subdomain (e.g. `api.hirejasperlin.com`) for CORS and session cookies to work in production.
