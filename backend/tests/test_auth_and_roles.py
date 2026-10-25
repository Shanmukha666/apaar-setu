"""Acceptance tests for authentication, role guards, and endpoint registration."""
import os

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from fastapi.testclient import TestClient
from app.main import app

ACCOUNTS = {
    "aicte@demo.in": "aicte_officer", "sysadmin@demo.in": "sys_admin", "verifier@demo.in": "verifier",
    **{f"inst{i}@demo.in": "institution_admin" for i in range(1, 6)},
}


def login(client, email):
    response = client.post("/api/auth/login", json={"email": email, "password": "Demo@123"})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_health():
    with TestClient(app) as client:
        assert client.get("/api/health").status_code == 200


def test_all_demo_accounts_login_with_expected_roles():
    with TestClient(app) as client:
        for email, role in ACCOUNTS.items():
            response = client.post("/api/auth/login", json={"email": email, "password": "Demo@123"})
            assert response.status_code == 200
            assert response.json()["access_token"]
            assert response.json()["user"]["role"] == role


def test_wrong_password_is_unauthorized():
    with TestClient(app) as client:
        assert client.post("/api/auth/login", json={"email": "aicte@demo.in", "password": "wrong"}).status_code == 401


def test_me_requires_and_returns_token_user():
    with TestClient(app) as client:
        assert client.get("/api/auth/me").status_code == 401
        token = login(client, "inst1@demo.in")
        response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        assert response.json()["email"] == "inst1@demo.in"


def test_dashboard_role_guard():
    with TestClient(app) as client:
        institution_token = login(client, "inst1@demo.in")
        aicte_token = login(client, "aicte@demo.in")
        assert client.get("/api/dashboard/national", headers={"Authorization": f"Bearer {institution_token}"}).status_code == 403
        assert client.get("/api/dashboard/national", headers={"Authorization": f"Bearer {aicte_token}"}).status_code == 200


def test_docs_include_contract_paths():
    with TestClient(app) as client:
        paths = client.get("/openapi.json").json()["paths"]
    expected = ["/api/health", "/api/auth/login", "/api/auth/me", "/api/uploads", "/api/students/bulk", "/api/students", "/api/institutions", "/api/dashboard/national", "/api/duplicates", "/api/alerts", "/api/reports/enrolment.csv", "/api/audit", "/api/audit/verify-chain", "/api/consent/{apaar_id}", "/api/records/{apaar_id}/issue", "/api/records/{apaar_id}/qr.png", "/api/verify", "/api/verify/public-key", "/mock-apaar/v1/persons/{apaar_id}"]
    for path in expected:
        assert path in paths
