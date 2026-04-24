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
1. React UI (`App.tsx`) sends `POST /chat/bot-response/` via Axios with session cookies
2. Django view (`chat/views.py`) validates the JSON payload, checks/increments the session message count (limit: `MAX_USER_MESSAGE_COUNT`, default 3)
3. `chat/utils.py` builds a LangGraph `StateGraph` with an in-memory checkpointer, invokes `gpt-4o-mini` with the system prompt from `chat/prompt.txt`
4. The full AI response is stored in the Django session alongside conversation history
5. Response JSON `{role, time, message}` is returned to the frontend

**State management:** Conversation history and message count live entirely in Django sessions (no database persistence for chat). Sessions expire after 24 hours.

**System prompt:** `chat/prompt.txt` contains Jasper's full resume. The AI is instructed to answer only from that content. The prompt uses Python string template substitution to inject the current date.

## Key Configuration

**Backend environment variables** (`.env` in `cheerleader-api/`):
- `OPENAI_API_KEY`, `OPENAI_MODEL_NAME` (default: `gpt-4o-mini`)
- `PROMPTLAYER_API_KEY` — prompt versioning/monitoring via PromptLayer
- `PROMPT_FILE_PATH` — path to system prompt file (default: `chat/prompt.txt`)
- `MAX_USER_MESSAGE_COUNT` — session message limit (default: 3)
- `EMAIL_ADDRESS`, `PHONE_NUMBER` — injected into prompt for contact info
- `ENV` — set to `dev` for local development (affects CORS and cookie settings)

**CORS & sessions:** In dev (`ENV=dev`), the backend allows `localhost:5173`. In production, it allows `*.hirejasperlin.com` and `cheerleader-api.onrender.com`. Session cookies use `SameSite=None; Secure` in production for cross-origin credential sharing.

## Unused Code

- `chat/chat_consumer.py` and `chat/routing.py` — WebSocket consumer, not wired up
- `cheerleader-ui/src/components/Chat.tsx` — alternate chat component with commented-out WebSocket implementation
- `react-use-websocket` dependency is installed but unused

## Deployment

Both services are deployed on Render. Frontend: `cheerleader-ui.onrender.com`. Backend: `cheerleader-api.onrender.com`. Custom domain: `hirejasperlin.com`.
