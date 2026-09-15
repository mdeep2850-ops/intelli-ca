# Intelli-CA

**Intelli-CA is an AI-powered work assistant that automates and assists with document analysis, retrieval, calculations, research and routine professional workflows, while leaving final professional judgment and responsibility with the CA.**

## Architecture & Deployment

Intelli-CA relies on a split-deployment architecture using GitHub as the single source of truth.

```text
Local development
GitHub
   ↓
Vercel → React frontend (Static SPA)
Render → FastAPI backend (Web Service with Persistent Disk)
```

### Local Development

#### Backend
1. `cd backend`
2. `python -m venv venv`
3. Activate environment (`venv/Scripts/activate` on Windows, `source venv/bin/activate` on Unix)
4. `pip install -r requirements.txt`
5. Create `.env` file with `GOOGLE_API_KEY`
6. `uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`

#### Frontend
1. `cd frontend`
2. `npm install`
3. Create `.env` file with `VITE_API_BASE_URL=http://localhost:8000/api/v1`
4. `npm run dev`

### Production Deployment

#### Frontend (Vercel)
- Connect GitHub repo to Vercel.
- Select `frontend` as the Root Directory.
- Framework: Vite.
- Set Environment Variable: `VITE_API_BASE_URL` to your backend's production URL (e.g., `https://backend-name.onrender.com/api/v1`).
- Vercel uses the included `vercel.json` for SPA routing.

#### Backend (Render)
- Connect GitHub repo to Render and create a Web Service.
- Set Root Directory to `backend`.
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Crucial Storage Configuration:** Add a 1GB Persistent Disk mounted at `/opt/render/project/src/backend/data`. This protects the SQLite database (`data/sql_app.db`), uploaded files (`data/uploads`), and ChromaDB (`data/chroma`) from ephemeral storage resets.
- Set Environment Variables:
  - `GOOGLE_API_KEY`: Your Gemini API Key
  - `FRONTEND_URL`: Your Vercel frontend URL (e.g., `https://frontend-name.vercel.app`) for CORS configuration.
  - `PYTHON_VERSION`: `3.11.9`

#### Health Check
The backend exposes `GET /health` to verify runtime health without invoking Gemini APIs.
