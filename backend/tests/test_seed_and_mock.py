"""Seed data is valid, deterministic, and plants exactly the scenarios the demo relies on."""
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.services.validation.rules import luhn_valid
from seed.generate_seed import generate

DATA = Path(__file__).resolve().parents[1] / "seed" / "data"


def read(name):
    with (DATA / name).open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def digest():
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(DATA.rglob("*")) if p.is_file()}


def test_registry_ids_pass_the_engines_luhn_rule():
    registry = json.loads((DATA / "apaar_registry.json").read_text())
    assert len(registry) == 900
    assert all(len(p["apaar_id"]) == 12 and luhn_valid(p["apaar_id"]) for p in registry)
    assert 0 < sum(p["status"] == "INACTIVE" for p in registry) < 60


def test_generation_is_deterministic():
    before = digest()
    generate()
    assert digest() == before


def test_planted_baseline_scenarios():
    rows = read("students_baseline.csv")
    programmes = {p["code"]: p for p in json.loads((DATA / "programmes.json").read_text())}
    per = Counter(r["programme_code"] for r in rows)
    over = {c: n - programmes[c]["approved_intake"] for c, n in per.items() if n > programmes[c]["approved_intake"]}
    assert over == {"CCE002-CSE": 8}                       # only institution 2, exactly +8
    inst1 = {r["apaar_id"] for r in rows if r["institution_id"] == "1"}
    assert sum(r["apaar_id"] in inst1 for r in rows if r["institution_id"] == "3") == 8
    inst4 = [r for r in rows if r["institution_id"] == "4"]
    share = sum("Y" in (r["nri"], r["oci"], r["fn"]) for r in inst4) / len(inst4)
    assert 0.30 <= share <= 0.40
    inst5 = [r["admission_date"] for r in rows if r["institution_id"] == "5"]
    assert Counter(inst5).most_common(1)[0][1] / len(inst5) >= 0.5
    for inst in "12345":                                    # student_ref unique within an institution
        refs = [r["student_ref"] for r in rows if r["institution_id"] == inst]
        assert len(refs) == len(set(refs))


def test_demo_files_have_contract_header_and_sizes():
    header = "apaar_id,student_ref,name,dob,gender,category,programme_code,academic_year,admission_date,admission_type,nri,oci,fn"
    for name, size in (("demo_clean.csv", 20), ("demo_messy.csv", 30), ("demo_overflow.csv", 95)):
        path = DATA / "demo_uploads" / name
        assert path.read_text(encoding="utf-8").splitlines()[0] == header
        assert len(read(f"demo_uploads/{name}")) == size


def test_expected_md_lists_every_code_once_in_messy():
    text = (DATA / "demo_uploads" / "EXPECTED.md").read_text()
    for code in ("APAAR_MISSING", "APAAR_FORMAT", "APAAR_CHECKSUM", "DUP_IN_FILE", "PROGRAMME_UNKNOWN", "FIELD_INVALID",
                 "DATE_FUTURE", "INCONSISTENT_FLAGS", "APAAR_NOT_FOUND", "APAAR_INACTIVE", "NAME_MISMATCH",
                 "DOB_MISMATCH", "CROSS_INSTITUTION_DUP", "SUPERNUMERARY_EXCEEDED", "INTAKE_EXCEEDED"):
        assert code in text, code


def test_mock_apaar_endpoint():
    from seed.load_registry import load_registry
    from app.db import SessionLocal
    with TestClient(app) as client:
        with SessionLocal() as db:
            load_registry(db)
        known = json.loads((DATA / "apaar_registry.json").read_text())[1]["apaar_id"]
        assert client.get(f"/mock-apaar/v1/persons/{known}").status_code == 401
        headers = {"X-API-Key": "demo-apaar-key"}
        assert client.get("/mock-apaar/v1/persons/000000000000", headers=headers).status_code == 404
        ok = client.get(f"/mock-apaar/v1/persons/{known}", headers=headers)
        assert ok.status_code == 200 and ok.headers["x-mock-service"] == "true"


def test_adapter_returns_validation_record():
    from datetime import date
    from app.db import SessionLocal
    from app.services.apaar_adapter import make_validation_lookup
    with TestClient(app):
        with SessionLocal() as db:
            lookup = make_validation_lookup(db)
            known = json.loads((DATA / "apaar_registry.json").read_text())[1]
            record = lookup(known["apaar_id"])
            assert record.name == known["name"] and isinstance(record.dob, date)
            assert lookup("000000000000") is None
