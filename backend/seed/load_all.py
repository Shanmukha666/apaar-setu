"""Create the complete deterministic APAAR-Setu demonstration dataset.

Run from ``backend`` with ``python -m seed.load_all``.  The loader intentionally
uses the same ingestion path as uploads, so seeded data exercises validation,
audit logging, capacity alerts, and the mock registry in one consistent flow.
"""
import argparse
import csv
from datetime import date
from pathlib import Path

from app.core.config import DEMO_TODAY
from app.core.security import hash_password
from app.db import Base, SessionLocal, engine
from app.main import seed_demo_data
from app.models import Consent, Student, User
from app.services.ingest import process_rows
from seed.load_registry import load_registry
from seed.refresh_all import refresh_all


ROOT = Path(__file__).resolve().parent
BASELINE = ROOT / "data" / "students_baseline.csv"


def _system_actor(db):
    """Return the non-login actor used for deterministic seed audit entries."""
    actor = db.query(User).filter_by(email="system@demo.in").first()
    if not actor:
        actor = User(
            email="system@demo.in",
            password_hash=hash_password("not-a-login-account"),
            name="Demo Seed System",
            role="sys_admin",
            institution_id=None,
        )
        db.add(actor)
        db.commit()
    return actor


def _read_baseline() -> dict[int, list[dict[str, str]]]:
    grouped: dict[int, list[dict[str, str]]] = {}
    with BASELINE.open(newline="", encoding="utf-8") as stream:
        for raw in csv.DictReader(stream):
            institution_id = int(raw.pop("institution_id"))
            grouped.setdefault(institution_id, []).append(raw)
    return grouped


def load_all() -> None:
    """Seed an empty database. Repeated calls leave stored students unchanged."""
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_demo_data(db)
        actor = _system_actor(db)
        load_registry(db)
        if not db.query(Student).count():
            today = date.fromisoformat(DEMO_TODAY)
            for institution_id, rows in sorted(_read_baseline().items()):
                process_rows(
                    db, institution_id, actor, rows, "students_baseline.csv", "csv",
                    False, today,
                )

        # Consent state is deterministic and applies to every seeded student.
        for apaar_id, in db.query(Student.apaar_id).distinct().order_by(Student.apaar_id):
            if db.query(Consent).filter_by(apaar_id=apaar_id).first():
                continue
            db.add(Consent(
                apaar_id=apaar_id,
                granted=int(apaar_id) % 5 != 0,
                purpose="verification",
            ))
        db.commit()
        refresh_all(db)
        print(f"Loaded {db.query(Student).count()} synthetic students.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reset", action="store_true", help="remove the default local SQLite database first")
    args = parser.parse_args()
    if args.reset:
        database = Path(__file__).resolve().parents[1] / "apaar_setu.db"
        if database.exists():
            database.unlink()
            print(f"Removed {database.name}.")
    load_all()


if __name__ == "__main__":
    main()
