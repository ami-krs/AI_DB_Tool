# AI DB Tool – Next.js Frontend

Next.js 14 + Tailwind CSS frontend for the AI Database Tool. It talks to the existing FastAPI backend (Render or local).

## Setup

1. **Install dependencies**
   ```bash
   cd frontend && npm install
   ```

2. **Environment**
   - Copy `.env.local.example` to `.env.local`
   - Set `NEXT_PUBLIC_BACKEND_API_URL` to your backend URL (e.g. `https://datamindai.onrender.com` or `http://localhost:8000`)
   - Optionally set `NEXT_PUBLIC_BACKEND_API_TOKEN` if the backend uses `API_AUTH_TOKEN`

3. **Run**
   ```bash
   npm run dev
   ```
   Open [http://localhost:3000](http://localhost:3000).

## Pages

- **Home** – Connect to a database (config is stored in the browser and sent to the backend for schema/query/chat).
- **Chat** – AI chatbot; uses backend `/v1/chat` with optional schema context.
- **SQL Editor** – Run SQL via backend `/v1/query/execute`.
- **Explorer** – View tables and columns from backend `/v1/schema`.

## Note on SQLite

For SQLite, the "database file path" is used by the **backend** when it runs queries. So it only works if the backend can read that path (e.g. backend running locally with a path on the same machine). For a deployed backend (e.g. Render), use PostgreSQL or another remote DB.
