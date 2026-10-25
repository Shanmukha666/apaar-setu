from datetime import date

from app.services.validation.engine import validate_batch
from app.services.validation.rules import make_valid_apaar
from app.services.validation.types import ApaarRecord, ProgrammeInfo, ValidationContext

TODAY = date(2026, 10, 1)


def valid_row(number="12345678901", **changes):
    apaar_id = make_valid_apaar(number)
    row = {"apaar_id": apaar_id, "student_ref": "SYN-1", "name": "Synthetic Student", "dob": "2006-01-01", "gender": "F", "category": "GEN", "programme_code": "DIT001-CSE", "academic_year": "2026-27", "admission_date": "2026-06-01", "admission_type": "REGULAR", "nri": "N", "oci": "N", "fn": "N"}
    row.update(changes)
    return row


def context(**changes):
    programme = ProgrammeInfo(1, "DIT001-CSE", 3, 1)
    def lookup(apaar_id):
        if apaar_id.startswith("999"):
            return None
        return ApaarRecord(apaar_id, "Synthetic Student", date(2006, 1, 1), "ACTIVE")
    value = ValidationContext(1, {programme.code: programme}, {}, {}, {}, lookup, TODAY)
    for key, item in changes.items(): setattr(value, key, item)
    return value


def codes(result): return [i.code for i in result.rows[0].issues]


def test_valid_and_structural_apaar_errors():
    assert validate_batch([valid_row()], context()).rows[0].status == "ACCEPTED"
    assert "APAAR_MISSING" in codes(validate_batch([valid_row(apaar_id="")], context()))
    assert "APAAR_FORMAT" in codes(validate_batch([valid_row(apaar_id="12345678901")], context()))
    assert "APAAR_CHECKSUM" in codes(validate_batch([valid_row(apaar_id="123456789010")], context()))


def test_duplicate_registry_and_structural_rules():
    row = valid_row(); result = validate_batch([row, row], context())
    assert [r.status for r in result.rows] == ["ACCEPTED", "REJECTED"] and result.rows[1].issues[0].code == "DUP_IN_FILE"
    assert "APAAR_NOT_FOUND" in codes(validate_batch([valid_row("99999999999")], context()))
    inactive = ApaarRecord(row["apaar_id"], "Synthetic Student", date(2006, 1, 1), "INACTIVE")
    assert "APAAR_INACTIVE" in codes(validate_batch([row], context(apaar_lookup=lambda _: inactive)))
    for changed, code in [(dict(programme_code="NOPE"), "PROGRAMME_UNKNOWN"), (dict(gender="X"), "FIELD_INVALID"), (dict(admission_date="2026-10-02"), "DATE_FUTURE"), (dict(oci="Y", fn="Y"), "INCONSISTENT_FLAGS")]:
        assert code in codes(validate_batch([valid_row(**changed)], context()))


def test_warnings_cross_institution_and_capacity():
    assert validate_batch([valid_row(name=" synthetic   student ")], context()).rows[0].status == "ACCEPTED"
    assert "NAME_MISMATCH" in codes(validate_batch([valid_row(name="Other")], context()))
    assert "DOB_MISMATCH" in codes(validate_batch([valid_row(dob="2005-01-01")], context()))
    row = valid_row(); other = {row["apaar_id"]: [{"institution_id": 2, "institution_name": "Other", "academic_year": "2026-27"}]}
    assert "CROSS_INSTITUTION_DUP" in codes(validate_batch([row], context(other_enrolments=other)))
    rows = [valid_row(f"1234567890{i}") for i in range(5)]
    result = validate_batch(rows, context())
    assert [r.status for r in result.rows] == ["ACCEPTED", "ACCEPTED", "ACCEPTED", "FLAGGED", "FLAGGED"]
    assert "INTAKE_EXCEEDED" in [i.code for i in result.rows[3].issues]


def test_supernumerary_updates_rejections_and_determinism():
    first, second = valid_row("12345678901", admission_type="SUPERNUMERARY"), valid_row("12345678902", admission_type="SUPERNUMERARY")
    result = validate_batch([first, second], context())
    assert result.rows[1].status == "FLAGGED" and result.rows[1].issues[0].code == "SUPERNUMERARY_EXCEEDED"
    row = valid_row(); ctx = context(existing_counts={(1, "2026-27", "REGULAR"): 3}, existing_students={(row["apaar_id"], "2026-27"): (1, "REGULAR")})
    assert validate_batch([row], ctx).rows[0].status == "ACCEPTED"
    bad, good = valid_row(gender="X"), valid_row("12345678902")
    assert validate_batch([bad, good], context()).rows[1].status == "ACCEPTED"
    assert validate_batch([good], context()) == validate_batch([good], context())
