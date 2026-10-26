"""Audit hash chain: logging works, tampering is detected."""
from fastapi.testclient import TestClient

from app.db import SessionLocal
from app.main import app
from app.models import AuditLog
from app.services.audit import log_action, verify_chain


def test_chain_valid_then_detects_tampering():
    with TestClient(app):
        with SessionLocal() as db:
            first = log_action(db, None, "LOGIN", "user", 1, {"a": 1})
            log_action(db, None, "UPLOAD", "upload", 2, {"rows": 5})
            db.commit()
            assert verify_chain(db)["valid"] is True
            row = db.get(AuditLog, first.id)
            row.details_json = '{"a":999}'
            db.commit()
            result = verify_chain(db)
            assert result == {"valid": False, "checked": result["checked"], "broken_at": first.id}
            row.details_json = '{"a":1}'          # restore so later tests see a clean chain
            db.commit()
            assert verify_chain(db)["valid"] is True


def test_login_is_audited():
    with TestClient(app) as client:
        client.post("/api/auth/login", json={"email": "aicte@demo.in", "password": "Demo@123"})
        with SessionLocal() as db:
            assert db.query(AuditLog).filter_by(action="LOGIN", actor_email="aicte@demo.in").count() >= 1
