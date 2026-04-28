# cheerleader-api

Django 4.2 backend for the Cheerleader recruiting chatbot.

## Setup

### Local

Requires Python 3.11.

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in required values
python manage.py migrate
python manage.py runserver
```

Dev server runs at `localhost:8000`.

### Docker

```bash
docker build -t cheerleader-api .
docker run -p 8000:8000 --env-file .env cheerleader-api
```

The entrypoint runs `migrate` and then starts Gunicorn on port 8000.

## Environment variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | Yes | — | Claude API key |
| `MODEL_NAME` | No | `claude-haiku-4-5-20251001` | Any `langchain-anthropic`-compatible model ID |
| `PROMPT_FILE_PATH` | No | `chat/prompt.txt` | Path to the system prompt file |
| `MAX_USER_MESSAGE_COUNT` | No | `3` | Per-session message limit |
| `EMAIL_ADDRESS` | No | — | Contact email injected into the prompt |
| `PHONE_NUMBER` | No | — | Contact phone injected into the prompt |
| `ENV` | No | — | Set to `dev` to allow `localhost:5173` CORS and relaxed cookie settings |

## API

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/chat/bot-response/` | Send a user message; returns an SSE stream of tokens |
| `GET` | `/chat/history/` | Return the session's conversation history as JSON |

### POST `/chat/bot-response/`

**Request body:**
```json
{ "role": "user", "time": "<iso timestamp>", "message": "your question" }
```

**Response:** `text/event-stream`

Each event is `data: <json>\n\n`:
- Token: `{"token": "..."}`
- End: `{"done": true, "time": "<iso timestamp>"}`

## Architecture

- `chat/views.py` — validates the request, enforces the per-session message limit, and returns a `StreamingHttpResponse`
- `chat/utils.py` — builds a LangGraph `StateGraph` with a `MemorySaver` checkpointer and streams tokens from the Claude model
- `chat/prompt.txt` — Jasper's resume; used as the system prompt with Python string template substitution for the current date and contact info

Conversation history and message count live in Django sessions (no database persistence for chat). Sessions expire after 24 hours.
