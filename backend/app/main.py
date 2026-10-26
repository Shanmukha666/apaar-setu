"""FastAPI application and deterministic demo-data bootstrap."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import AUTO_SEED_FULL, FRONTEND_URL, validate_deployment_settings
from app.db import Base, SessionLocal, engine
from app.routers import alerts, audit, auth, consent, dashboard, institutions, mock_apaar, records, reports, students, uploads, verify
from app.services.bootstrap import seed_demo_data
from seed.load_all import seed_all


@asynccontextmanager
async def lifespan(app: FastAPI):
    validate_deployment_settings()
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        if AUTO_SEED_FULL:
            seed_all(db)
        else:
            seed_demo_data(db)
    yield


app = FastAPI(title="APAAR-Setu API", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=[FRONTEND_URL], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


@app.get("/api/health", tags=["health"])
def health():
    return {"status": "ok"}


for route in (auth.router, uploads.router, students.router, institutions.router, dashboard.router, alerts.router, reports.router, audit.router, consent.router, records.router, verify.router, mock_apaar.router):
    app.include_router(route)
