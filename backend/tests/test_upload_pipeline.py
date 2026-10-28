"""Upload pipeline against the seeded demo DB. Tests run in file order and share state (clean -> messy -> overflow)."""
import re
from pathlib import Path

from app.db import SessionLocal
from app.models import Alert, AuditLog, Student, Upload
from app.routers.uploads import _safe
from app.services.audit import verify_chain
from tests.conftest import login

DEMO = Path(__file__).resolve().parents[1] / "seed" / "data" / "demo_uploads"


def expected():
    """Parse EXPECTED.md into {file: [counts, {row: codes}]}."""
    out, current = {}, None
    for line in (DEMO / "EXPECTED.md").read_text().splitlines():
        m = re.match(r"## (\w+)\.csv", line)
        if m:
            current = out.setdefault(m.group(1), [None, {}])
        m = re.search(r"accepted (\d+), flagged (\d+), rejected (\d+)", line)
        if m and current:
            current[0] = tuple(int(x) for x in m.groups())
        m = re.match(r"\| (\d+) \| \w+ \| (.+) \|", line)
        if m and current:
            current[1][int(m.group(1))] = sorted(m.group(2).split(", "))
    return out


def post(client, headers, name, dry_run=False):
    data = (DEMO / f"{name}.csv").read_bytes()
    return client.post(f"/api/uploads?dry_run={str(dry_run).lower()}", files={"file": (f"{name}.csv", data, "text/csv")}, headers=headers)


def check(body, name):
    counts, rows = expected()[name]
    assert (body["accepted"], body["flagged"], body["rejected"]) == counts
    got = {r["row_number"]: sorted(i["code"] for i in r["issues"]) for r in body["rows"] if r["issues"]}
    assert got == rows


def n_students():
    with SessionLocal() as db:
        return db.query(Student).count()


def n_alerts():
    with SessionLocal() as db:
        return db.query(Alert).count()


def test_dry_run_saves_report_but_no_students_or_alerts(seeded):
    h = login(seeded, "inst1@demo.in")
    s0, a0 = n_students(), n_alerts()
    body = post(seeded, h, "demo_messy", dry_run=True).json()
    check(body, "demo_messy")
    assert body["dry_run"] is True and n_students() == s0 and n_alerts() == a0
    with SessionLocal() as db:
        assert db.get(Upload, body["upload_id"]).dry_run is True


def test_clean_upload_then_reupload_is_an_update(seeded):
    h = login(seeded, "inst1@demo.in")
    before = n_students()
    check(post(seeded, h, "demo_clean").json(), "demo_clean")
    assert n_students() == before + 20
    check(post(seeded, h, "demo_clean").json(), "demo_clean")
    assert n_students() == before + 20            # update, not duplicate


def test_messy_upload_matches_expected_codes(seeded):
    h = login(seeded, "inst1@demo.in")
    before = n_students()
    body = post(seeded, h, "demo_messy").json()
    check(body, "demo_messy")
    assert n_students() == before + body["accepted"] + body["flagged"]        # rejected rows are never stored
    with SessionLocal() as db:
        assert db.query(Student).filter(Student.issue_codes.like("%APAAR_%")).count() == 0


def test_overflow_creates_one_critical_alert_and_reupload_does_not_stack(seeded):
    h = login(seeded, "inst1@demo.in")
    check(post(seeded, h, "demo_overflow").json(), "demo_overflow")
    check(post(seeded, h, "demo_overflow").json(), "demo_overflow")           # same file again: 90 accepted rows are updates
    with SessionLocal() as db:
        found = db.query(Alert).filter_by(institution_id=1, rule_code="INTAKE_EXCEEDED").all()
    assert len(found) == 1 and found[0].severity == "CRITICAL"
    assert '"excess": 5' in found[0].evidence_json and '"enrolled_regular": 95' in found[0].evidence_json


def test_baseline_has_8_cross_institution_dups_at_institution_3(seeded):
    with SessionLocal() as db:
        n = db.query(Student).filter(Student.institution_id == 3, Student.issue_codes.like("%CROSS_INSTITUTION_DUP%")).count()
    assert n == 8


def test_issues_csv_and_access_control(seeded):
    h1, h2 = login(seeded, "inst1@demo.in"), login(seeded, "inst2@demo.in")
    uploads = seeded.get("/api/uploads", headers=h1).json()
    upload_id = max(u["id"] for u in uploads if not u["dry_run"] and u["filename"] == "demo_messy.csv")
    lines = seeded.get(f"/api/uploads/{upload_id}/issues.csv", headers=h1).text.strip().splitlines()
    assert lines[0] == "row_number,apaar_id,status,code,severity,field,message" and len(lines) == 1 + 14
    assert seeded.get(f"/api/uploads/{upload_id}", headers=h2).status_code == 403
    assert seeded.get(f"/api/uploads/{upload_id}/issues.csv", headers=h2).status_code == 403
    assert seeded.get(f"/api/uploads/{upload_id}").status_code == 401
    assert seeded.get("/api/uploads", headers=login(seeded, "verifier@demo.in")).status_code == 403
    assert _safe("=1+1") == "'=1+1" and _safe("Normal") == "Normal"       # spreadsheet formula injection guard


def test_wrong_header_is_rejected_with_400(seeded):
    h = login(seeded, "inst1@demo.in")
    r = seeded.post("/api/uploads", files={"file": ("x.csv", b"bad,header\n1,2\n", "text/csv")}, headers=h)
    assert r.status_code == 400 and "header" in r.json()["detail"]


def test_json_bulk_api(seeded):
    h = login(seeded, "inst1@demo.in")
    row = dict(apaar_id="", student_ref="X", name="N", dob="2005-01-01", gender="M", category="GEN", programme_code="DIT001-CSE",
               academic_year="2027-28", admission_date="2027-07-01", admission_type="REGULAR", nri="N", oci="N", fn="N")
    body = seeded.post("/api/students/bulk?dry_run=true", json={"rows": [row]}, headers=h).json()
    assert body["rejected"] == 1 and body["rows"][0]["issues"][0]["code"] == "APAAR_MISSING"


def test_student_list_is_scoped_and_searchable(seeded):
    h1, ha = login(seeded, "inst1@demo.in"), login(seeded, "aicte@demo.in")
    assert seeded.get("/api/students?institution_id=2", headers=h1).status_code == 403     # another institution: refused
    mine = seeded.get("/api/students?page_size=5", headers=h1).json()                   # no filter: always scoped to own
    assert mine["total"] > 0 and all(s["institution_id"] == 1 for s in mine["items"]) and len(mine["items"]) == 5
    assert seeded.get("/api/students?page_size=1", headers=ha).json()["total"] > mine["total"]
    first = mine["items"][0]["apaar_id"]
    assert seeded.get(f"/api/students?q={first}", headers=ha).json()["total"] >= 1
    assert seeded.get("/api/students?status=FLAGGED", headers=ha).json()["total"] >= 16
    assert seeded.get(f"/api/students/{first}", headers=h1).json()["records"][0]["apaar_id"] == first


def test_audit_chain_valid_then_detects_tampering(seeded):
    ha = login(seeded, "aicte@demo.in")
    actions = {a["action"] for a in seeded.get("/api/audit?page_size=100", headers=ha).json()["items"]}
    assert {"UPLOAD", "UPLOAD_DRY_RUN", "LOGIN"} <= actions
    ok = seeded.get("/api/audit/verify-chain", headers=ha).json()
    assert ok["valid"] is True and ok["checked"] >= 10
    with SessionLocal() as db:
        row = db.query(AuditLog).filter_by(action="UPLOAD").first()
        original, row_id = row.details_json, row.id
        row.details_json = original.replace("filename", "filenameX")
        db.commit()
    bad = seeded.get("/api/audit/verify-chain", headers=ha).json()
    assert bad["valid"] is False and bad["broken_at"] == row_id
    with SessionLocal() as db:
        db.get(AuditLog, row_id).details_json = original
        db.commit()
        assert verify_chain(db)["valid"] is True
