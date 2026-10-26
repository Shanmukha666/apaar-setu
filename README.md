# APAAR-Setu

Synthetic-data APAAR ID student management and verification prototype. The APAAR integration is mocked.

## Backend

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Run tests with `cd backend; pytest -q`.

## Frontend

```powershell
cd frontend
npm install
Copy-Item .env.local.example .env.local
npm run dev
```

The frontend runs on port 3000 and expects the backend at `http://localhost:8000`.

## Vercel staging deployment

Deploy both the Next.js frontend and FastAPI backend as separate Vercel projects, backed by a Vercel Marketplace PostgreSQL integration. The full sequence, environment variables, and verification checklist are in [docs/VERCEL_DEPLOYMENT.md](docs/VERCEL_DEPLOYMENT.md).
