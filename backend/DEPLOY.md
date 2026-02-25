# Deploy FastAPI Backend: Render or Railway

Your repo already has deployment config for both. **Render** is a good default: free tier, simple Docker deploys, and a single `render.yaml` in the repo.

---

## Option A: Render (recommended)

### 1. Push your code
Ensure your `develop` (or main) branch is pushed to GitHub with the `backend/` folder and `backend/Dockerfile`.

### 2. Create a Render account
- Go to [render.com](https://render.com) and sign up (GitHub login is easiest).

### 3. New Web Service from repo

**Important:** Render does **not** let you change an existing service from Python to Docker in the dashboard (there is no “Settings → Runtime” for existing services). You must either **create a new Web Service** and choose Docker when creating it, or use **Blueprint** (recommended). The **Language** and **Dockerfile Path** options appear only in the **service creation form** (when you click New → Web Service), not under Settings of an existing service.

**Option 3a – Create a new Web Service (choose Docker at creation)**

1. In the Render Dashboard, click **New** → **Web Service** (do not open an existing service’s Settings).
2. **Connect** your GitHub repo (e.g. `ami-krs/AI_DB_Tool`) and click **Next** or **Connect**.
3. In the **creation form** that appears (Name, Region, Branch, etc.):
   - **Name:** e.g. `datamindai-backend`.
   - **Branch:** `develop` (or your branch).
   - **Root Directory:** leave empty.
   - **Language:** In the dropdown, choose **Docker** (not Python). This is the only way to get a Docker build; it may be under the main fields or in a “Runtime” section depending on Render’s current UI.
   - **Advanced:** Expand **Advanced** (or “Show more” / “More options”) and find **Dockerfile Path**. Set it to `backend/Dockerfile`.
   - **Start Command / Docker Command:** Leave blank so the Dockerfile’s `CMD` runs.
4. Choose instance type (e.g. Free), then click **Create Web Service**. After the first deploy, add environment variables (see step 4 below).

**Option 3b – Blueprint (easiest; no Language/Dockerfile form to find)**

- In the Render Dashboard, click **New** → **Blueprint**.
- Connect the same GitHub repo and branch.
- Render reads `backend/render.yaml` and creates the web service with **Docker** and `dockerfilePath: ./backend/Dockerfile` automatically. You don’t set Language or Dockerfile Path in the UI.
- After the Blueprint sync, add environment variables in the new service’s **Environment** tab (see step 4 below).

If you already have a Python service (e.g. datamindai), you can leave it and use the **new** service’s URL for the backend, or delete the old service and keep only the new one.

### 4. Environment variables (Render dashboard)
In your service → **Environment**:
- `OPENAI_API_KEY` = your OpenAI key (secret).
- Optional: `API_AUTH_TOKEN` = a secret token; if set, Streamlit must send it as `X-API-Token`.
- Optional: `CORS_ALLOW_ORIGINS` = `*` or your Streamlit app URL (e.g. `https://your-app.onrender.com`).

### 5. Deploy
- Click **Create Web Service** (or let Blueprint deploy).
- Wait for the build and deploy. The log will show `uvicorn` starting.
- Your API URL will be like: `https://ai-db-tool-backend.onrender.com`.

### 6. Use from Streamlit
In Streamlit (e.g. Streamlit Cloud secrets or local env):
- `USE_BACKEND_API=true`
- `BACKEND_API_URL=https://ai-db-tool-backend.onrender.com`
- `BACKEND_API_TOKEN=<your API_AUTH_TOKEN>` (only if you set `API_AUTH_TOKEN`).

**Render free tier:** Service may spin down after inactivity; first request after idle can take 30–60 seconds.

**Troubleshooting:** If the deploy log shows `/opt/render/project/src/.venv/bin/python` and **No module named uvicorn**, the service was created as **Python**, not Docker (and you can’t change runtime in the dashboard). Fix: create a **new** Web Service and choose **Language: Docker** and **Dockerfile Path: backend/Dockerfile** in the creation form, or use **New → Blueprint** so Render creates the service from `backend/render.yaml` with Docker.

---

## Option B: Railway

### 1. Push your code
Same as Render: have `backend/` and `backend/Dockerfile` on your GitHub branch.

### 2. Create a Railway account
- Go to [railway.app](https://railway.app) and sign up (GitHub login).

### 3. New project from repo
- **New Project** → **Deploy from GitHub repo**.
- Select `AI_DB_Tool` (or your repo) and the branch (e.g. `develop`).

### 4. Use the Dockerfile
- Railway may auto-detect the Dockerfile. If not: **Settings** → **Build** → Builder: **Dockerfile**, Dockerfile path: `backend/Dockerfile`.
- **Settings** → **Deploy** → Root Directory: leave default (repo root). Build context is repo root so `COPY . /app` works.

### 5. Environment variables (Railway dashboard)
In your service → **Variables**:
- `OPENAI_API_KEY` = your OpenAI key.
- Optional: `API_AUTH_TOKEN`, `CORS_ALLOW_ORIGINS` (same as Render).

### 6. Generate domain
- **Settings** → **Networking** → **Generate Domain**.
- You’ll get a URL like `https://your-service.up.railway.app`.

### 7. Use from Streamlit
- `USE_BACKEND_API=true`
- `BACKEND_API_URL=https://your-service.up.railway.app`
- `BACKEND_API_TOKEN` set only if you set `API_AUTH_TOKEN` on Railway.

**Railway free tier:** Limited usage per month; no spin-down like Render.

---

## Quick comparison

| | Render | Railway |
|---|--------|--------|
| **Free tier** | Yes (service may sleep) | Yes (usage limits) |
| **Docker** | Yes | Yes |
| **Config in repo** | `backend/render.yaml` | `backend/railway.json` |
| **Setup** | Blueprint or one web service | One project from GitHub |

**Recommendation:** Use **Render** with the existing `backend/render.yaml` (Blueprint) for the simplest path; use **Railway** if you prefer their dashboard or already use it.

---

## Health check

After deploy, confirm the backend is up:

```bash
curl https://YOUR_BACKEND_URL/health
```

Expected: `{"status":"ok"}`.
