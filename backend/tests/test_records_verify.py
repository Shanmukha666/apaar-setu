"""Consent, signed records and verification, using students inserted directly (no ingest needed)."""
from datetime import date, datetime

import pytest
from fastapi.testclient import TestClient

from app.db import SessionLocal
from app.main import app
from app.models import AuditLog, Consent, Student
from app.services.audit import verify_chain

CONSENTED, NOT_CONSENTED = "100000000002", "100000000010"


def login(client, email):
    r = client.post("/api/auth/login", json={"email": email, "password": "Demo@123"})
    return {"Authorization": "Bearer " + r.json()["access_token"]}


@pytest.fixture()
def client():
    with TestClient(app) as c:
        with SessionLocal() as db:
            for apaar, granted, ref in ((CONSENTED, True, "T-1"), (NOT_CONSENTED, False, "T-2")):
                if not db.query(Student).filter_by(apaar_id=apaar, institution_id=1).first():
                    db.add(Student(apaar_id=apaar, institution_id=1, programme_id=1, student_ref=ref, name="Test Student",
                                   dob=date(2005, 1, 1), gender="F", category="GEN", academic_year="2026-27",
                                   admission_date=date(2026, 6, 15), admission_type="REGULAR", nri="N", oci="N",
                                   fn="N", status="ACCEPTED", issue_codes="", created_at=datetime(2026, 6, 15),
                                   updated_at=datetime(2026, 6, 15)))
                row = db.query(Consent).filter_by(apaar_id=apaar).first()
                if row:
                    row.granted = granted
                else:
                    db.add(Consent(apaar_id=apaar, granted=granted, purpose="verification"))
            db.commit()
        yield c


def test_issue_returns_token_and_qr(client):
    r = client.post(f"/api/records/{CONSENTED}/issue", headers=login(client, "inst1@demo.in"))
    assert r.status_code == 200
    body = r.json()
    assert body["verify_url"].startswith("http://localhost:3000/verify?t=") and body["qr_png_base64"]
    assert body["payload"]["apaar_id"] == CONSENTED
    png = client.get(f"/api/records/{CONSENTED}/qr.png", headers=login(client, "inst1@demo.in"))
    assert png.content.startswith(b"\x89PNG")


def test_record_access_rules(client):
    assert client.post(f"/api/records/{CONSENTED}/issue", headers=login(client, "inst2@demo.in")).status_code == 403
    assert client.post("/api/records/999999999999/issue", headers=login(client, "inst1@demo.in")).status_code == 404
    assert client.post(f"/api/records/{CONSENTED}/issue").status_code == 401


def test_verify_ok_consent_required_and_tampering(client):
    inst, verifier = login(client, "inst1@demo.in"), login(client, "verifier@demo.in")
    good = client.post(f"/api/records/{CONSENTED}/issue", headers=inst).json()["token"]
    r = client.post("/api/verify", json={"token": good}, headers=verifier).json()
    assert r["valid"] and r["reason"] == "OK" and r["record"]["name"] == "Test Student"

    locked = client.post(f"/api/records/{NOT_CONSENTED}/issue", headers=inst).json()["token"]
    r = client.post("/api/verify", json={"token": locked}, headers=verifier).json()
    assert r["valid"] and r["reason"] == "CONSENT_REQUIRED" and r["record"] is None

    assert client.put(f"/api/consent/{NOT_CONSENTED}", json={"granted": True}, headers=login(client, "aicte@demo.in")).status_code == 200
    assert client.post("/api/verify", json={"token": locked}, headers=verifier).json()["reason"] == "OK"
    client.put(f"/api/consent/{NOT_CONSENTED}", json={"granted": False}, headers=login(client, "aicte@demo.in"))

    head, sig = good.split(".")
    flipped = sig[:-2] + ("A" if sig[-2] != "A" else "B") + sig[-1]
    assert client.post("/api/verify", json={"token": f"{head}.{flipped}"}, headers=verifier).json()["reason"] == "BAD_SIGNATURE"
    assert client.post("/api/verify", json={"token": "garbage"}, headers=verifier).json()["reason"] == "MALFORMED"


def test_consent_endpoints_and_roles(client):
    inst1, inst2 = login(client, "inst1@demo.in"), login(client, "inst2@demo.in")
    assert client.get(f"/api/consent/{CONSENTED}", headers=inst1).json()["granted"] is True
    assert client.get(f"/api/consent/{CONSENTED}", headers=inst2).status_code == 403
    assert client.get("/api/consent/999999999999", headers=login(client, "aicte@demo.in")).status_code == 404
    assert client.post("/api/verify", json={"token": "x"}).status_code == 401
    assert client.post("/api/verify", json={"token": "x"}, headers=login(client, "sysadmin@demo.in")).status_code == 403


def test_public_key_and_audit_trail(client):
    key = client.get("/api/verify/public-key").json()
    assert key["algorithm"] == "Ed25519" and "BEGIN PUBLIC KEY" in key["public_key_pem"]
    token = client.post(f"/api/records/{CONSENTED}/issue", headers=login(client, "inst1@demo.in")).json()["token"]
    client.post("/api/verify", json={"token": token}, headers=login(client, "verifier@demo.in"))
    client.put(f"/api/consent/{CONSENTED}", json={"granted": True}, headers=login(client, "aicte@demo.in"))
    with SessionLocal() as db:
        actions = {a for (a,) in db.query(AuditLog.action).distinct()}
        assert {"LOGIN", "RECORD_ISSUED", "VERIFY_ATTEMPT", "CONSENT_CHANGED"} <= actions
        assert verify_chain(db)["valid"] is True
