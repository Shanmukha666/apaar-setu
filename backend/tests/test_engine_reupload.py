"""Re-uploading rows that are already stored must not be judged against capacity they already occupy."""
from tests.test_validation_engine import context, valid_row
from app.services.validation.engine import validate_batch

YEAR = "2026-27"


def stored_three():
    """Programme intake is 3 and three students (A, B, C) are already stored."""
    rows = [valid_row(f"1234567890{i}") for i in range(3)]
    existing = {(r["apaar_id"], YEAR): (1, "REGULAR") for r in rows}
    return rows, context(existing_counts={(1, YEAR, "REGULAR"): 3}, existing_students=existing)


def statuses(result):
    return [r.status for r in result.rows]


def test_reuploading_a_full_programme_is_idempotent():
    rows, ctx = stored_three()
    assert statuses(validate_batch(rows, ctx)) == ["ACCEPTED"] * 3     # before the fix: only the first row passed


def test_reupload_plus_new_rows_flags_only_the_excess_in_file_order():
    rows, ctx = stored_three()
    extra = [valid_row("12345678905"), valid_row("12345678906")]
    assert statuses(validate_batch(rows + extra, ctx)) == ["ACCEPTED"] * 3 + ["FLAGGED"] * 2


def test_rejected_row_keeps_its_stored_record_counted():
    rows, ctx = stored_three()
    bad = dict(rows[0], gender="X")                                    # rejected: record A stays stored, still occupies a seat
    new = valid_row("12345678905")
    result = validate_batch([bad, rows[1], rows[2], new], ctx)
    assert statuses(result) == ["REJECTED", "ACCEPTED", "ACCEPTED", "FLAGGED"]


def test_reupload_is_deterministic():
    rows, ctx = stored_three()
    first = [(r.status, [i.code for i in r.issues]) for r in validate_batch(rows, ctx).rows]
    second = [(r.status, [i.code for i in r.issues]) for r in validate_batch(rows, ctx).rows]
    assert first == second
