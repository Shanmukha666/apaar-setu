"""Generate reproducible synthetic seed data. Run from backend/: python -m seed.generate_seed

Everything here is SYNTHETIC. Only random.Random(2026) is used, so output is byte-identical every run.
The 12th APAAR digit is the MOCK Luhn check digit, produced by the SAME function the validation engine uses.
"""
import csv
import json
import random
from datetime import date
from pathlib import Path

from app.services.validation.rules import luhn_valid, make_valid_apaar

ROOT = Path(__file__).parent / "data"
HEADER = ["apaar_id", "student_ref", "name", "dob", "gender", "category", "programme_code",
          "academic_year", "admission_date", "admission_type", "nri", "oci", "fn"]
DEMO_TODAY = date(2027, 12, 31)  # must match DEMO_TODAY in app/core/config.py

# (institution_id, code, [(short, name, level, years, intake)])
INSTITUTION_PROGRAMMES = [
    (1, "DIT001", [("CSE", "Computer Science", "UG", 4, 60), ("ECE", "Electronics", "UG", 4, 90), ("MEC", "Mechanical", "UG", 4, 120)]),
    (2, "CCE002", [("CSE", "Computer Science", "UG", 4, 60), ("CIV", "Civil", "UG", 4, 90), ("EEE", "Electrical", "UG", 4, 120)]),
    (3, "HSM003", [("MKT", "PGDM Marketing", "PG", 2, 60), ("FIN", "PGDM Finance", "PG", 2, 90), ("HRM", "PGDM HR", "PG", 2, 120)]),
    (4, "MIP004", [("BPH", "B.Pharm", "UG", 4, 60), ("DPH", "D.Pharm", "UG", 2, 90), ("MPH", "M.Pharm", "PG", 2, 120)]),
    (5, "KPT005", [("DCS", "Diploma CS", "Diploma", 3, 60), ("DEE", "Diploma Electrical", "Diploma", 3, 90), ("DME", "Diploma Mechanical", "Diploma", 3, 120)]),
]
PROGRAMMES = []
for _inst, _code, _items in INSTITUTION_PROGRAMMES:
    for _short, _name, _level, _years, _intake in _items:
        PROGRAMMES.append({"id": len(PROGRAMMES) + 1, "institution_id": _inst, "code": f"{_code}-{_short}",
                           "name": _name, "level": _level, "duration_years": _years,
                           "approved_intake": _intake, "supernumerary_limit": (_intake + 9) // 10})
PROG = {p["code"]: p for p in PROGRAMMES}

FIRST = ["Aarav", "Diya", "Kabir", "Meera", "Nivaan", "Riya", "Vihaan", "Zoya"]
LAST = ["Demo", "Sample", "Synthetic", "Example", "Prototype", "Mock"]
# Baseline enrolment per programme (same order as PROGRAMMES).
# Inst 1 ~80-90% full; inst 2 CSE is +8 over intake; inst 3 sits just under intake.
COUNTS = [50, 72, 96, 68, 55, 55, 58, 70, 63, 22, 22, 21, 20, 20, 20]


def write_csv(path, rows, with_institution=False):
    fields = (["institution_id"] if with_institution else []) + HEADER
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def make_row(person, programme_code, ref, year, admission_date="2026-06-15", **over):
    row = {"apaar_id": person["apaar_id"], "student_ref": ref, "name": person["name"], "dob": person["dob"],
           "gender": "F" if int(ref.split("-")[-1]) % 2 else "M", "category": "GEN",
           "programme_code": programme_code, "academic_year": year, "admission_date": admission_date,
           "admission_type": "REGULAR", "nri": "N", "oci": "N", "fn": "N"}
    row.update(over)
    return row


def generate():
    rng = random.Random(2026)  # kept for the contract; names/dates below are index-driven
    del rng
    ROOT.mkdir(parents=True, exist_ok=True)
    (ROOT / "demo_uploads").mkdir(exist_ok=True)

    persons = []
    for n in range(900):
        apaar = make_valid_apaar(f"{10000000000 + n:011d}")
        persons.append({"apaar_id": apaar,
                        "name": f"{FIRST[n % len(FIRST)]} {LAST[(n // len(FIRST)) % len(LAST)]}",
                        "dob": date(2002 + n % 6, 1 + n % 12, 1 + n % 27).isoformat(),
                        "status": "INACTIVE" if n % 33 == 0 else "ACTIVE"})
    assert all(luhn_valid(p["apaar_id"]) for p in persons)
    (ROOT / "apaar_registry.json").write_text(json.dumps(persons, indent=2) + "\n", encoding="utf-8")
    (ROOT / "programmes.json").write_text(json.dumps(PROGRAMMES, indent=2) + "\n", encoding="utf-8")

    # ---- baseline (2026-27) ----
    rows, cursor, per_inst = [], 0, {}
    # Baseline records must be valid stored records.  Inactive identities remain
    # in the registry so validation demos can exercise APAAR_INACTIVE, but are
    # deliberately excluded from the official baseline.
    active_people = [person for person in persons if person["status"] == "ACTIVE"]
    for programme, count in zip(PROGRAMMES, COUNTS):
        inst = programme["institution_id"]
        for j in range(count):
            person = active_people[cursor + j]
            per_inst[inst] = per_inst.get(inst, 0) + 1
            # Vary dates for normal data.  Institution 5 is the intentional
            # exception: exactly 18 of its 36 admissions share one date.
            extra = {"admission_date": f"2026-06-{2 + (per_inst[inst] % 20):02d}"}
            if inst == 4 and per_inst[inst] <= 23:
                extra["nri"] = "Y"                                      # 23/65 = 35%, valid flags
            if inst == 5 and per_inst[inst] <= 30:
                extra["admission_date"] = "2026-06-01"
            row = make_row(person, programme["code"], f"SYN-{inst}-{per_inst[inst]:03d}", "2026-27", **extra)
            row["institution_id"] = str(inst)
            rows.append(row)
        cursor += count
    # Eight institution-3 students deliberately reuse institution-1 identities (cross-institution duplicates).
    inst3 = [r for r in rows if r["institution_id"] == "3"]
    inst1 = [r for r in rows if r["institution_id"] == "1"]
    for source, target in zip(inst1[:8], inst3[:8]):
        for key in ("apaar_id", "name", "dob"):
            target[key] = source[key]
    write_csv(ROOT / "students_baseline.csv", rows, with_institution=True)

    # ---- demo uploads for institution 1, academic year 2027-28 ----
    pool = active_people[cursor:]
    inactive = next(p for p in persons if p["status"] == "INACTIVE")
    take = iter(pool)
    year = "2027-28"
    n = {"v": 0}

    def ref():
        n["v"] += 1
        return f"SYN-1-{900 + n['v']:03d}"

    # demo_clean: 20 valid rows, DIT001-CSE
    clean = [make_row(next(take), "DIT001-CSE", ref(), year, "2027-07-01") for _ in range(20)]
    write_csv(ROOT / "demo_uploads" / "demo_clean.csv", clean)

    # demo_messy: 30 rows = 10 clean + one row per ERROR/WARNING code + 7 supernumerary (7th exceeds limit 6).
    # INTAKE_EXCEEDED lives in demo_overflow.csv because it needs a full programme.
    m = lambda person, **kw: make_row(person, kw.pop("prog", "DIT001-CSE"), ref(), kw.pop("year", year), kw.pop("date", "2027-07-02"), **kw)
    messy = [m(next(take)) for _ in range(10)]
    first = messy[0]
    messy.append(m(next(take), apaar_id=""))                                                  # APAAR_MISSING
    messy.append(m(next(take), apaar_id=persons[5]["apaar_id"][:11]))                         # APAAR_FORMAT
    bad = take.__next__()
    wrong = (int(bad["apaar_id"][-1]) + 1) % 10
    messy.append(m(bad, apaar_id=bad["apaar_id"][:11] + str(wrong)))                          # APAAR_CHECKSUM
    messy.append(m({"apaar_id": first["apaar_id"], "name": first["name"], "dob": first["dob"]}))  # DUP_IN_FILE
    messy.append(m(next(take), prog="DIT001-XYZ"))                                            # PROGRAMME_UNKNOWN
    messy.append(m(next(take), gender="X"))                                                   # FIELD_INVALID
    messy.append(m(next(take), date="2030-01-01"))                                            # DATE_FUTURE
    messy.append(m(next(take), oci="Y", fn="Y"))                                              # INCONSISTENT_FLAGS
    ghost = make_valid_apaar("29999999999")
    messy.append(m({"apaar_id": ghost, "name": "Ghost Student", "dob": "2005-05-05"}))        # APAAR_NOT_FOUND
    messy.append(m(inactive))                                                                 # APAAR_INACTIVE
    messy.append(m({**next(take), "name": "Wrong Name"}))                                     # NAME_MISMATCH
    p = next(take)
    messy.append(m({**p, "dob": "2001-01-01"}))                                               # DOB_MISMATCH
    other = next(r for r in rows if r["institution_id"] == "2")                               # CROSS_INSTITUTION_DUP
    messy.append(m({"apaar_id": other["apaar_id"], "name": other["name"], "dob": other["dob"]}, year="2026-27", date="2026-06-15"))
    messy.extend(m(next(take), admission_type="SUPERNUMERARY") for _ in range(7))             # last = SUPERNUMERARY_EXCEEDED
    assert len(messy) == 30
    write_csv(ROOT / "demo_uploads" / "demo_messy.csv", messy)

    # demo_overflow: 95 rows into DIT001-ECE (intake 90) -> exactly 5 INTAKE_EXCEEDED.
    overflow = [make_row(next(take), "DIT001-ECE", ref(), year, "2027-07-03") for _ in range(95)]
    write_csv(ROOT / "demo_uploads" / "demo_overflow.csv", overflow)

    write_expected(persons, rows)


def write_expected(persons, baseline_rows):
    """Run the real validation engine against the seeded registry and write EXPECTED.md."""
    from collections import Counter
    from app.services.validation.engine import validate_batch
    from app.services.validation.types import ApaarRecord, ProgrammeInfo, ValidationContext

    registry = {p["apaar_id"]: ApaarRecord(p["apaar_id"], p["name"], date.fromisoformat(p["dob"]), p["status"]) for p in persons}
    infos = {p["code"]: ProgrammeInfo(p["id"], p["code"], p["approved_intake"], p["supernumerary_limit"])
             for p in PROGRAMMES if p["institution_id"] == 1}
    stored = [r for r in baseline_rows if r["institution_id"] == "1"]
    counts = Counter((PROG[r["programme_code"]]["id"], r["academic_year"], r["admission_type"]) for r in stored)
    elsewhere = {}
    for r in baseline_rows:
        if r["institution_id"] != "1":
            elsewhere.setdefault(r["apaar_id"], []).append({"institution_id": int(r["institution_id"]), "institution_name": f"Institution {r['institution_id']}", "academic_year": r["academic_year"]})
    lines = ["# Expected demo uploads (institution 1, fresh seeded DB)", "",
             "Generated by `python -m seed.generate_seed` using the real validation engine. Do not edit by hand.",
             "The three files use different programmes/people, so uploading clean -> messy -> overflow in order gives these same counts.", ""]
    for name in ("demo_clean", "demo_messy", "demo_overflow"):
        with (ROOT / "demo_uploads" / f"{name}.csv").open(encoding="utf-8") as f:
            data = list(csv.DictReader(f))
        ctx = ValidationContext(1, infos, dict(counts), {}, elsewhere, registry.get, DEMO_TODAY)
        result = validate_batch(data, ctx)
        lines += [f"## {name}.csv", f"- rows {len(data)}: accepted {result.accepted}, flagged {result.flagged}, rejected {result.rejected}", ""]
        interesting = [r for r in result.rows if r.issues]
        if interesting:
            lines += ["| row | status | codes |", "|---|---|---|"]
            lines += [f"| {r.row_number} | {r.status} | {', '.join(i.code for i in r.issues)} |" for r in interesting]
            lines.append("")
    (ROOT / "demo_uploads" / "EXPECTED.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    generate()
