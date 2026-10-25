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
