# FastAPI Backend (Separate Deployment)

This backend service lets you run AI + DB logic outside Streamlit Cloud while keeping Streamlit as UI.

## Run locally

```bash
pip install -r backend/requirements.txt
uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload
```

## Required environment variables

- `OPENAI_API_KEY` (or `ANTHROPIC_API_KEY`)

## Optional environment variables

- `API_AUTH_TOKEN` - if set, clients must send `X-API-Token`
- `CORS_ALLOW_ORIGINS` - comma-separated origins (default `*`)
- `PORT` - service port (default `8000`)
- `AUTH_DB_PATH` - path to SQLite auth DB (default `/data/auth.db`; use a persistent disk path in production)
- **Password reset email (SMTP):** `SMTP_HOST`, `SMTP_PORT` (default `587`), `SMTP_USER`, `SMTP_PASSWORD`, `EMAIL_FROM`, `FRONTEND_URL` (base URL for reset links, e.g. `https://yourapp.com`). If SMTP is not set, reset links are only logged (suitable for development).

## Endpoints

- `GET /health`
- `POST /v1/chat`
- `POST /v1/query/execute`
- `POST /v1/schema`

## Streamlit frontend integration

Set in Streamlit environment:

- `USE_BACKEND_API=true`
- `BACKEND_API_URL=http://<your-api-host>:8000`
- `BACKEND_API_TOKEN=<same as API_AUTH_TOKEN>` (only if token enabled)

With these set, Streamlit uses backend API for:
- Chatbot responses
- SQL query execution
- Schema/table metadata fetch

Fallback behavior: if API mode is off, Streamlit keeps current in-process behavior.

## Deployment manifests included

- `backend/Dockerfile`
- `backend/render.yaml`
- `backend/railway.json`
