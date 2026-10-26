# Vercel-only staging deployment

This prototype runs both the Next.js frontend and FastAPI backend on Vercel. Persistent data is supplied by a PostgreSQL integration created from the Vercel Marketplace; Vercel Functions cannot safely retain the local SQLite file between invocations.

All demo names, IDs, and records are synthetic. Keep `APAAR_MODE=mock`.

## Projects in Vercel

Create two Vercel projects from this one GitHub repository:

| Project | Root Directory | Framework |
|---|---|---|
| `apaar-setu-web` | `frontend` | Next.js |
| `apaar-setu-api` | `backend` | Other / FastAPI auto-detection |

The backend uses Vercel's Python 3.12 runtime. It creates the tables and idempotently seeds the synthetic demo dataset on a cold start.

## Deployment order

1. Import and deploy `apaar-setu-web` first. It may use a temporary value for `NEXT_PUBLIC_API_URL`; its purpose is to obtain the permanent Vercel URL.
2. In the Vercel Marketplace, add a serverless PostgreSQL integration such as Neon or Prisma Postgres to the same Vercel team. Attach the generated database URL to **apaar-setu-api** as `DATABASE_URL`. Prefer the provider's pooled/serverless connection URL.
3. Import and deploy `apaar-setu-api` with the environment variables below. Set `FRONTEND_URL` to the HTTPS URL from step 1.
4. Copy the API project's HTTPS URL. Set it as `NEXT_PUBLIC_API_URL` on **apaar-setu-web**, then redeploy the frontend.

## Backend environment variables

Set these in the Vercel dashboard for Preview and Production. Never commit their real values.

```text
APP_ENV=staging
DATABASE_URL=<Vercel Marketplace PostgreSQL pooled URL>
JWT_SECRET=<unique random secret>
SIGNING_SEED=<different unique random secret>
FRONTEND_URL=https://<apaar-setu-web>.vercel.app
APAAR_MODE=mock
DEMO_TODAY=2027-12-31
```

Generate `JWT_SECRET` and `SIGNING_SEED` locally and paste them only into Vercel's encrypted environment-variable fields:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48)); print(secrets.token_urlsafe(48))"
```

## Frontend environment variable

```text
NEXT_PUBLIC_API_URL=https://<apaar-setu-api>.vercel.app
```

## Verify after deployment

1. Open `https://<apaar-setu-api>.vercel.app/api/health` and expect `{"status":"ok"}`.
2. Open the frontend, log in as `inst1@demo.in` with `Demo@123`.
3. Run a dry validation using `backend/seed/data/demo_uploads/demo_messy.csv`.
4. Sign in as `aicte@demo.in`, verify dashboard alerts, duplicates, and the audit chain.
5. Issue a certificate and verify it as `verifier@demo.in`.

If either Vercel URL changes, update `FRONTEND_URL` on the backend and `NEXT_PUBLIC_API_URL` on the frontend, then redeploy both projects.
