"""File-order, pure validation orchestration."""
from .rules import capacity_check, cross_institution_check, registry_checks, registry_mismatches, structural_checks, issue
from .types import BatchResult, RowResult, ValidationContext


def validate_batch(rows: list[dict], ctx: ValidationContext) -> BatchResult:
    results: list[RowResult] = []
    seen: set[tuple[str, str]] = set()
    batch_counts: dict[tuple[int, str, str], int] = {}
    accepted = flagged = rejected = 0
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
        else:
            record = None
        if errors:
            results.append(RowResult(offset, apaar_id, "REJECTED", errors, clean)); rejected += 1; continue
        warnings = registry_mismatches(clean, record)
        warnings.extend(cross_institution_check(clean, ctx))
        programme = ctx.programmes[clean["programme_code"]]
        warnings.extend(capacity_check(clean, programme, ctx, batch_counts))
        key = (programme.id, clean["academic_year"], clean["admission_type"])
        batch_counts[key] = batch_counts.get(key, 0) + 1
        status = "FLAGGED" if warnings else "ACCEPTED"
        results.append(RowResult(offset, apaar_id, status, warnings, clean))
        if warnings: flagged += 1
        else: accepted += 1
    return BatchResult(results, accepted, flagged, rejected)
