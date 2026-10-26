# Staging deployment

This prototype is safe to demonstrate publicly only with its supplied **synthetic** seed data and mock APAAR mode.

## Architecture

Deploy the Next.js app in `frontend/` to Vercel. Deploy the FastAPI app in `backend/` to a persistent service such as Render or Railway. Do not deploy the current SQLite-backed FastAPI app as a Vercel serverless function: its filesystem is ephemeral and seeded data would not persist.

## 1. Deploy the backend

Create a service with `backend` as its root directory.

- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

Set these environment variables in the backend host's secret manager:

```text
APP_ENV=staging
DATABASE_URL=sqlite:///./apaar_setu.db
JWT_SECRET=<unique random secret>
SIGNING_SEED=<different unique random secret>
FRONTEND_URL=https://<your-vercel-project>.vercel.app
APAAR_MODE=mock
DEMO_TODAY=2027-12-31
```

Generate secrets locally; never put their output in Git, chat, or a client-side variable:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48)); print(secrets.token_urlsafe(48))"
```

After the first deployment, open the service shell once and run `python -m seed.load_all`. For a restartable public demo, use a persistent disk. SQLite is adequate for a short, single-instance demo only; replace it with managed PostgreSQL before any multi-instance or production use.

## 2. Deploy the frontend to Vercel

Import the GitHub repository in Vercel and set **Root Directory** to `frontend`.

Set this Vercel environment variable for Preview and Production:

```text
NEXT_PUBLIC_API_URL=https://<your-backend-host>
```

Deploy, copy the Vercel URL, and set it as `FRONTEND_URL` on the backend. Redeploy or restart the backend after changing it so CORS permits the site.

## 3. Verify before sharing

1. Visit `/api/health` on the backend.
2. Open the Vercel URL and log in as `inst1@demo.in` using `Demo@123`.
3. Upload `backend/seed/data/demo_uploads/demo_messy.csv` as a dry run.
4. Sign in as `aicte@demo.in`, verify the dashboard and audit chain.
5. Issue and verify a consented certificate.

Never switch `APAAR_MODE` away from `mock` without legal approval, a security design review, and real API credentials.
