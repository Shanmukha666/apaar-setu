"""Recompute derived anomaly alerts for every fixed demo institution."""
from app.db import SessionLocal
from app.services.insights import refresh_institution_alerts


def refresh_all(db=None) -> None:
    """Refresh using a supplied session, or open a short-lived CLI session."""
    if db is not None:
        for institution_id in range(1, 6):
            refresh_institution_alerts(db, institution_id)
        return
    with SessionLocal() as session:
        refresh_all(session)


if __name__ == "__main__":
    refresh_all()
