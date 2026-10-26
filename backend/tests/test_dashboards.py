"""Regression coverage for the deterministic seeded dashboard data."""
from fastapi.testclient import TestClient

from app.main import app
from seed.load_all import load_all


def _token(client: TestClient, email: str) -> dict[str, str]:
    response = client.post("/api/auth/login", json={"email": email, "password": "Demo@123"})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_seeded_dashboard_aggregates_and_access_controls():
    load_all()
    with TestClient(app) as client:
        aicte = _token(client, "aicte@demo.in")
        dashboard = client.get("/api/dashboard/national", headers=aicte)
        assert dashboard.status_code == 200
        cards = dashboard.json()["cards"]
        assert cards["institutions"] == 5
        assert cards["students"] >= 600
        assert cards["cross_duplicates"] == 8
        assert cards["open_critical_alerts"] >= 1

        second = client.get("/api/dashboard/national", headers=aicte).json()
        assert dashboard.json()["risk_ranking"] == second["risk_ranking"]
        assert len(client.get("/api/duplicates", headers=aicte).json()) == 8

        summary = client.get("/api/institutions/2/summary", headers=aicte).json()
        assert any(item["fill_pct"] > 100 for item in summary["programmes"])
        assert any(item["rule_code"] == "INTAKE_EXCEEDED" for item in summary["open_alerts"])

        institution = _token(client, "inst1@demo.in")
        assert client.get("/api/dashboard/national", headers=institution).status_code == 403
        assert client.get("/api/institutions/2/summary", headers=institution).status_code == 403
        verifier = _token(client, "verifier@demo.in")
        assert client.get("/api/alerts", headers=verifier).status_code == 403
