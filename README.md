# cheerleader

AI-powered recruiting chatbot that answers questions about Jasper Lin's professional background. Live at [hirejasperlin.com](https://hirejasperlin.com).

## Structure

| Directory | Description |
|-----------|-------------|
| [cheerleader-api/](cheerleader-api/) | Django 4.2 backend — handles chat sessions, rate limiting, and Claude API streaming |
| [cheerleader-ui/](cheerleader-ui/) | React 18 + TypeScript frontend — chat UI built with Vite |

## Quick start

**Backend**
```bash
cd cheerleader-api
cp .env.example .env   # add your ANTHROPIC_API_KEY
python manage.py migrate
python manage.py runserver
```

**Frontend**
```bash
cd cheerleader-ui
npm install
npm run dev
```

The UI runs at `localhost:5173` and proxies chat requests to the backend at `localhost:8000`.
