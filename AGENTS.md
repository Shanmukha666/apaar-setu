# AGENTS.md — APAAR-Setu

Project: APAAR ID-based student data management and verification platform for AICTE-approved institutions (Smart India Hackathon 2026, problem SIH26263). Prototype with SYNTHETIC data only. All APAAR integration is MOCKED.

Stack (do not change): Next.js (App Router, TypeScript) + Tailwind + shadcn/ui + Recharts frontend; FastAPI (Python 3.11) backend; SQLite via SQLAlchemy 2.0; pytest.

Rules:
1. Read docs/CONTRACT.md first. It is the source of truth for tables, endpoints, rule codes, and demo data. Never invent endpoints or field names; match it exactly.
2. Only edit files in your assigned scope (stated in the task). If you need a change elsewhere, stop and say so.
3. Everything must be deterministic: no random without a fixed seed, no network calls, no dependence on the current date unless the date is injected as a parameter.
4. Keep code simple and commented. Prefer small functions. No unnecessary libraries.
5. Before finishing: run the tests named in the task and report results. Do not claim success if a test fails.
6. Never put real personal data anywhere. All names, IDs and dates are synthetic.

Commands:
- Backend: cd backend && python -m venv .venv && source .venv/bin/activate (Windows: .venv\Scripts\activate) && pip install -r requirements.txt && uvicorn app.main:app --reload --port 8000
- Backend tests: cd backend && pytest -q
- Frontend: cd frontend && npm install && npm run dev (port 3000). Env: NEXT_PUBLIC_API_URL=http://localhost:8000
