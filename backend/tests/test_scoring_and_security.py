"""Regression tests for the audit findings: risk scoring, per-year capacity, the seed login account, deploy guard."""
import pytest

from app.core import config
from app.db import SessionLocal
from app.models import User
from tests.conftest import login
from tests.test_upload_pipeline import post


def ranking(client):
    data = client.get("/api/dashboard/national", headers=login(client, "aicte@demo.in")).json()
    return {r["institution_id"]: r["risk_score"] for r in data["risk_ranking"]}, data


def test_baseline_risk_ranking_matches_the_story(seeded):
    scores, data = ranking(seeded)
    assert scores[1] == 0                                    # the clean institution is not blamed for duplicates it did not create
    assert scores[3] > scores[2] > scores[1]                 # cross-duplicates (3) outrank one over-intake programme (2)
    assert data["cards"]["cross_duplicates"] == 8 and data["cards"]["open_critical_alerts"] == 1
    alerts = seeded.get("/api/alerts?institution_id=1", headers=login(seeded, "aicte@demo.in")).json()
    assert alerts == []                                      # no cluster alert for the original-enrolment institution
    held = [a["rule_code"] for a in seeded.get("/api/alerts?institution_id=3", headers=login(seeded, "aicte@demo.in")).json()]
    assert held == ["ANOM_CROSS_DUP_CLUSTER"]                # ... it goes to the institution holding the flagged records


def test_capacity_is_judged_per_academic_year(seeded):
    h = login(seeded, "inst1@demo.in")
    for name in ("demo_clean", "demo_messy", "demo_overflow"):
        assert post(seeded, h, name).status_code == 200
    summary = seeded.get("/api/institutions/1/summary", headers=h).json()
    rows = {(p["code"], p["academic_year"]): p for p in summary["programmes"]}
    # Before the fix 2026-27 and 2027-28 enrolment were summed, so every programme looked over intake.
    assert rows[("DIT001-CSE", "2026-27")]["enrolled_regular"] + rows[("DIT001-CSE", "2027-28")]["enrolled_regular"] > 60
    assert rows[("DIT001-CSE", "2027-28")]["fill_pct"] < 100 and rows[("DIT001-CSE", "2026-27")]["fill_pct"] < 100
    over = [k for k, p in rows.items() if p["fill_pct"] > 100]
    assert over == [("DIT001-ECE", "2027-28")] and summary["programmes_over_intake"] == 1
    assert 0 < summary["risk_score"] < 100                   # one real problem is not a maximum-risk institution


def test_anomaly_and_critical_alerts_are_counted_separately(seeded):
    from app.services.anomaly import risk_score
    s = seeded.get("/api/institutions/1/summary", headers=login(seeded, "inst1@demo.in")).json()
    anomalies = sum(a["rule_code"].startswith("ANOM_") for a in s["open_alerts"])
    assert s["risk_score"] == risk_score(s["programmes_over_intake"], anomalies, s["cross_dups"], s["quality_score"])


def test_seed_actor_cannot_log_in_even_with_the_old_public_password(seeded):
    for password in ("not-a-login-account", "!", "Demo@123", ""):
        r = seeded.post("/api/auth/login", json={"email": "system@demo.in", "password": password})
        assert r.status_code == 401, password


def test_old_database_with_guessable_seed_password_is_repaired(seeded):
    from app.core.security import hash_password
    from seed.load_all import seed_all
    with SessionLocal() as db:
        db.query(User).filter_by(email="system@demo.in").one().password_hash = hash_password("not-a-login-account")
        db.commit()
        assert seeded.post("/api/auth/login", json={"email": "system@demo.in", "password": "not-a-login-account"}).status_code == 200
        seed_all(db)
    assert seeded.post("/api/auth/login", json={"email": "system@demo.in", "password": "not-a-login-account"}).status_code == 401


def test_deploy_guard_applies_on_vercel_even_without_app_env(monkeypatch):
    monkeypatch.setattr(config, "APP_ENV", "development")
    monkeypatch.setattr(config, "JWT_SECRET", "dev-secret")
    config.validate_deployment_settings()                    # plain local run: allowed
    monkeypatch.setenv("VERCEL", "1")
    with pytest.raises(RuntimeError):
        config.validate_deployment_settings()
