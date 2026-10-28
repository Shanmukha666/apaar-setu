"""File-order, pure validation orchestration."""
from dataclasses import replace

from .rules import capacity_check, cross_institution_check, registry_checks, registry_mismatches, structural_checks, issue
from .types import BatchResult, RowResult, ValidationContext


def validate_batch(rows: list[dict], ctx: ValidationContext) -> BatchResult:
    """Validate rows in file order.

    Pass 1 runs every check except capacity (only structural/registry errors reject a row, capacity only warns).
    Pass 2 then applies capacity. Students already stored AND re-submitted in this batch are taken out of the stored
    counts first and re-counted in file order, so re-uploading a corrected file gives the same result as the first upload
    instead of flagging rows against capacity they already occupy.
    """
    seen: set[tuple[str, str]] = set()
    prepared = []  # (row_number, apaar_id, clean, issues, rejected)
    for offset, row in enumerate(rows, start=2):
        clean, errors = structural_checks(row, ctx.programmes, ctx.today)
        apaar_id = clean["apaar_id"]
        duplicate_key = (apaar_id, clean["academic_year"])
        if not errors and duplicate_key in seen:
            errors.append(issue("DUP_IN_FILE", "ERROR", "apaar_id", value=apaar_id))
        if not errors:
            seen.add(duplicate_key)
            record = ctx.apaar_lookup(apaar_id)
            errors.extend(registry_checks(clean, record))
        if errors:
            prepared.append((offset, apaar_id, clean, errors, True))
            continue
        warnings = registry_mismatches(clean, record)
        warnings.extend(cross_institution_check(clean, ctx))
        prepared.append((offset, apaar_id, clean, warnings, False))

    # Stored students that this batch will re-evaluate no longer count as "already there".
    counts = dict(ctx.existing_counts)
    for _, apaar_id, clean, _, rejected in prepared:
        old = ctx.existing_students.get((apaar_id, clean["academic_year"]))
        if old and not rejected:
            key = (old[0], clean["academic_year"], old[1])
            counts[key] = counts.get(key, 0) - 1
    capacity_ctx = replace(ctx, existing_counts=counts, existing_students={})

    results: list[RowResult] = []
    batch_counts: dict[tuple[int, str, str], int] = {}
    accepted = flagged = rejected_total = 0
    for offset, apaar_id, clean, issues, rejected in prepared:
        if rejected:
            results.append(RowResult(offset, apaar_id, "REJECTED", issues, clean))
            rejected_total += 1
            continue
        programme = ctx.programmes[clean["programme_code"]]
        issues.extend(capacity_check(clean, programme, capacity_ctx, batch_counts))
        key = (programme.id, clean["academic_year"], clean["admission_type"])
        batch_counts[key] = batch_counts.get(key, 0) + 1
        status = "FLAGGED" if issues else "ACCEPTED"
        results.append(RowResult(offset, apaar_id, status, issues, clean))
        if issues:
            flagged += 1
        else:
            accepted += 1
    return BatchResult(results, accepted, flagged, rejected_total)
