"""Dashboards, alerts and risk ranking on the freshly seeded baseline."""
from tests.conftest import login


def national(client):
    return client.get("/api/dashboard/national", headers=login(client, "aicte@demo.in")).json()


def test_national_cards(seeded):
    cards = national(seeded)["cards"]
    assert cards["institutions"] == 5 and cards["students"] == 700
    assert cards["cross_duplicates"] == 8 and cards["open_critical_alerts"] == 1 and cards["flagged"] == 16


def test_institution_2_is_over_intake_with_critical_alert(seeded):
    s = seeded.get("/api/institutions/2/summary", headers=login(seeded, "aicte@demo.in")).json()
    over = [p for p in s["programmes"] if p["fill_pct"] > 100]
    assert len(over) == 1 and over[0]["enrolled_regular"] - over[0]["approved_intake"] == 8
    critical = [a for a in s["open_alerts"] if a["severity"] == "CRITICAL"]
    assert len(critical) == 1 and critical[0]["rule_code"] == "INTAKE_EXCEEDED" and critical[0]["evidence"]["excess"] == 8


def test_institution_1_is_clean(seeded):
    s = seeded.get("/api/institutions/1/summary", headers=login(seeded, "inst1@demo.in")).json()
    assert s["quality_score"] >= 90 and s["risk_score"] == 0
    assert not [a for a in s["open_alerts"] if a["severity"] == "CRITICAL"]


def test_anomaly_alerts_explain_themselves(seeded):
    ha = login(seeded, "aicte@demo.in")
    foreign = seeded.get("/api/alerts?institution_id=4", headers=ha).json()
    burst = seeded.get("/api/alerts?institution_id=5", headers=ha).json()
    assert foreign[0]["rule_code"] == "ANOM_FOREIGN_SHARE" and "24 of 65" in foreign[0]["message"] and foreign[0]["evidence"]["foreign"] == 24
    assert burst[0]["rule_code"] == "ANOM_DATE_BURST" and isinstance(burst[0]["evidence"], dict)
    cluster = seeded.get("/api/alerts?institution_id=3", headers=ha).json()
    assert cluster[0]["rule_code"] == "ANOM_CROSS_DUP_CLUSTER"


def test_risk_ranking_sorted_and_sensible(seeded):
    ranking = national(seeded)["risk_ranking"]
    scores = [r["risk_score"] for r in ranking]
    assert scores == sorted(scores, reverse=True)
    by_id = {r["institution_id"]: r["risk_score"] for r in ranking}
    assert by_id[1] == min(scores) and by_id[3] > by_id[2] > by_id[1]
    assert national(seeded)["risk_ranking"] == ranking          # stable across calls


def test_duplicates_list(seeded):
    dups = seeded.get("/api/duplicates", headers=login(seeded, "aicte@demo.in")).json()
    assert len(dups) == 8 and all({i["id"] for i in d["institutions"]} == {1, 3} for d in dups)


def test_roles(seeded):
    inst1, verifier = login(seeded, "inst1@demo.in"), login(seeded, "verifier@demo.in")
    assert seeded.get("/api/dashboard/national", headers=inst1).status_code == 403
    assert seeded.get("/api/institutions/2/summary", headers=inst1).status_code == 403
    assert seeded.get("/api/institutions/1/summary", headers=inst1).status_code == 200
    for path in ("/api/dashboard/national", "/api/institutions", "/api/alerts", "/api/duplicates", "/api/institutions/1/summary"):
        assert seeded.get(path, headers=verifier).status_code == 403, path
    assert len(seeded.get("/api/alerts", headers=inst1).json()) == 0          # inst 1 has no alerts


def test_refresh_is_idempotent(seeded):
    from app.db import SessionLocal
    from app.services.insights import refresh_institution_alerts
    before = seeded.get("/api/alerts", headers=login(seeded, "aicte@demo.in")).json()
    with SessionLocal() as db:
        for i in range(1, 6):
            refresh_institution_alerts(db, i)
        db.commit()
    after = seeded.get("/api/alerts", headers=login(seeded, "aicte@demo.in")).json()
    assert sorted((a["institution_id"], a["rule_code"], a["message"]) for a in before) == sorted((a["institution_id"], a["rule_code"], a["message"]) for a in after)
