"""Recompute anomaly alerts for institutions 1..5.  Run from backend/: python -m seed.refresh_all"""
from app.db import SessionLocal
from app.services.insights import refresh_institution_alerts


def refresh_all(db):
    """Recompute anomaly alerts for institutions 1..5."""
    for institution_id in range(1, 6):
        refresh_institution_alerts(db, institution_id)
    db.commit()


if __name__ == "__main__":
    with SessionLocal() as db:
        refresh_all(db)
    print("Alerts refreshed.")
