"""Regression tests for the demo-blocking FIX-1 defects."""
import hashlib
import json
from datetime import date
from pathlib import Path

from fastapi.testclient import TestClient

from app.db import Base, SessionLocal, engine
from app.main import app, seed_demo_data
from app.models import AuditLog, Consent, Programme, Student, User
from app.services.audit import log_action, verify_chain
from app.services.validation.rules import luhn_valid
from seed.generate_seed import ROOT, generate


def test_seed_ids_are_valid_and_generation_is_byte_identical():
    generate()
    paths = sorted(path for path in ROOT.rglob("*") if path.is_file())
    before = {path.relative_to(ROOT): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
    assert all(luhn_valid(item["apaar_id"]) for item in json.loads((ROOT / "apaar_registry.json").read_text()))
    generate()
    after = {path.relative_to(ROOT): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
    assert before == after


def test_audit_chain_round_trip_and_tamper_detection():
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        db.query(AuditLog).delete()
        first = log_action(db, None, "LOGIN", "user", "1", {"a": 1})
        second = log_action(db, None, "UPLOAD", "upload", "2", {"b": 2})
        db.commit()
        assert verify_chain(db) == {"valid": True, "checked": 2, "broken_at": None}
        second.details_json = "{}"
        db.commit()
        assert verify_chain(db)["broken_at"] == second.id


def test_consent_records_and_verify_routes():
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        seed_demo_data(db)
        db.query(Student).delete(); db.query(Consent).delete(); db.query(AuditLog).delete()
        programme = db.query(Programme).filter_by(institution_id=1).first()
        student = Student(apaar_id="100000000009", institution_id=1, programme_id=programme.id, student_ref="SYN-1", name="Synthetic Student", dob=date(2006, 1, 1), gender="F", category="GEN", academic_year="2026-27", admission_date=date(2026, 6, 1), admission_type="REGULAR", nri="N", oci="N", fn="N", status="ACCEPTED", issue_codes="", upload_id=None)
        db.add(student); db.add(Consent(apaar_id=student.apaar_id, granted=True, purpose="verification")); db.commit()
    with TestClient(app) as client:
        token = client.post("/api/auth/login", json={"email": "inst1@demo.in", "password": "Demo@123"}).json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        assert client.get("/api/consent/100000000009", headers=headers).status_code == 200
        issued = client.post("/api/records/100000000009/issue", headers=headers)
        assert issued.status_code == 200
        payload = issued.json(); assert payload["token"] and payload["verify_url"] and payload["qr_png_base64"]
        assert client.post("/api/verify", json={"token": payload["token"]}, headers=headers).json()["reason"] == "OK"
        assert client.post("/api/records/999999999999/issue", headers=headers).status_code == 404
