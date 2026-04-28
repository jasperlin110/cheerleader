# cheerleader-ui

React 18 + TypeScript frontend for the Cheerleader recruiting chatbot. Built with Vite.

## Setup

Requires Node 18+.

```bash
npm install
cp .env.local.example .env.local   # set VITE_API_URL if not using the default
npm run dev
```

Dev server runs at `localhost:5173`. The backend must be running at `localhost:8000` (or whatever `VITE_API_URL` is set to).

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_API_URL` | `http://localhost:8000` | Backend base URL |
| `VITE_LINKEDIN_URL` | Jasper's LinkedIn | LinkedIn link in the header |
| `VITE_GITHUB_URL` | Jasper's GitHub | GitHub link in the header |
| `VITE_RESUME_URL` | Jasper's resume | Resume link in the header |

## Commands

```bash
npm run dev      # dev server with HMR at localhost:5173
npm run build    # TypeScript check + production build to dist/
npm run lint     # ESLint (warnings treated as errors)
npm run preview  # serve the production build locally
npm test         # run unit tests with Vitest (or: make test-ui from the repo root)
```

## Architecture

- `src/App.tsx` — main component; manages chat state, sends `POST /chat/bot-response/`, and reads the SSE token stream to render responses character by character
- `src/components/` — UI sub-components

The frontend uses session cookies for continuity — the backend associates conversation history and the message count with the session.
