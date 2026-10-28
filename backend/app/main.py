"""FastAPI application and deterministic demo-data bootstrap."""
import json
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db import Base, SessionLocal, engine
from app.models import Institution, Programme, User
from app.routers import alerts, audit, auth, consent, dashboard, institutions, mock_apaar, records, reports, students, uploads, verify

PROGRAMMES_FILE = Path(__file__).resolve().parents[1] / "seed" / "data" / "programmes.json"

INSTITUTIONS = [
    (1, "DIT001", "Deccan Institute of Technology", "Telangana", "Engineering"),
    (2, "CCE002", "Coastal College of Engineering", "Andhra Pradesh", "Engineering"),
    (3, "HSM003", "Himalaya School of Management", "Uttarakhand", "PGDM"),
    (4, "MIP004", "Malwa Institute of Pharmacy", "Madhya Pradesh", "Pharmacy"),
    (5, "KPT005", "Kaveri Polytechnic", "Karnataka", "Polytechnic"),
]


def seed_demo_data(db: Session) -> None:
    """Create contract-defined institutions, three programmes each, and eight users."""
    for ident, code, name, state, kind in INSTITUTIONS:
        if not db.get(Institution, ident):
            db.add(Institution(id=ident, code=code, name=name, state=state, type=kind))
    db.flush()
    for spec in json.loads(PROGRAMMES_FILE.read_text(encoding="utf-8")):
        if not db.query(Programme).filter_by(code=spec["code"]).first():
            db.add(Programme(**spec))
    accounts = [
        ("aicte@demo.in", "AICTE Officer", "aicte_officer", None),
        ("sysadmin@demo.in", "System Administrator", "sys_admin", None),
        ("verifier@demo.in", "Demo Verifier", "verifier", None),
        *[(f"inst{i}@demo.in", f"Institution {i} Admin", "institution_admin", i) for i in range(1, 6)],
    ]
    for email, name, role, institution_id in accounts:
        if not db.query(User).filter_by(email=email).first():
            db.add(User(email=email, password_hash=hash_password("Demo@123"), name=name, role=role, institution_id=institution_id))
    db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_demo_data(db)
    yield


app = FastAPI(title="APAAR-Setu API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", tags=["health"])
def health():
    return {"status": "ok"}


for route in (auth.router, uploads.router, students.router, institutions.router, dashboard.router, alerts.router, reports.router, audit.router, consent.router, records.router, verify.router, mock_apaar.router):
    app.include_router(route)
