"""Small pure functions grouped by validation concern."""
from datetime import date

from .messages import MESSAGES
from .types import ApaarRecord, Issue, ProgrammeInfo, ValidationContext


def issue(code: str, severity: str, field: str, **values: str) -> Issue:
    return Issue(code, severity, field, MESSAGES[code].format(field=field, **values))


def is_valid_apaar_format(value: str) -> bool:
    return len(value) == 12 and value.isdigit()


def luhn_valid(value: str) -> bool:
    if not value or not value.isdigit():
        return False
    total = 0
    for index, digit in enumerate(reversed(value)):
        number = int(digit)
        if index % 2 == 1:
            number *= 2
            if number > 9:
                number -= 9
        total += number
    return total % 10 == 0


def make_valid_apaar(prefix11: str) -> str:
    """Append the mock Luhn check digit to an 11-digit APAAR prefix."""
    if len(prefix11) != 11 or not prefix11.isdigit():
        raise ValueError("prefix11 must contain exactly 11 digits")
    for check in range(10):
        candidate = prefix11 + str(check)
        if luhn_valid(candidate):
            return candidate
    raise AssertionError("a Luhn check digit always exists")


def structural_checks(row: dict, programmes: dict[str, ProgrammeInfo], today: date) -> tuple[dict, list[Issue]]:
    """Clean input and return all structural errors, without registry work."""
    clean = {key: str(row.get(key, "")).strip() for key in ("apaar_id", "student_ref", "name", "dob", "gender", "category", "programme_code", "academic_year", "admission_date", "admission_type", "nri", "oci", "fn")}
    errors: list[Issue] = []
    apaar_id = clean["apaar_id"]
    if not apaar_id:
        errors.append(issue("APAAR_MISSING", "ERROR", "apaar_id"))
    elif not is_valid_apaar_format(apaar_id):
        errors.append(issue("APAAR_FORMAT", "ERROR", "apaar_id", value=apaar_id))
    elif not luhn_valid(apaar_id):
        errors.append(issue("APAAR_CHECKSUM", "ERROR", "apaar_id", value=apaar_id))
    if clean["programme_code"] not in programmes:
        errors.append(issue("PROGRAMME_UNKNOWN", "ERROR", "programme_code", value=clean["programme_code"]))
    parsed_dates: dict[str, date] = {}
    for field in ("dob", "admission_date"):
        try:
            parsed_dates[field] = date.fromisoformat(clean[field])
        except ValueError:
            errors.append(issue("FIELD_INVALID", "ERROR", field, value=clean[field]))
    enum_rules = {"gender": {"M", "F", "O"}, "category": {"GEN", "OBC", "SC", "ST", "EWS"}, "admission_type": {"REGULAR", "SUPERNUMERARY"}, "nri": {"Y", "N"}, "oci": {"Y", "N"}, "fn": {"Y", "N"}}
    for field, allowed in enum_rules.items():
        if clean[field] not in allowed:
            errors.append(issue("FIELD_INVALID", "ERROR", field, value=clean[field]))
    if "admission_date" in parsed_dates and parsed_dates["admission_date"] > today:
        errors.append(issue("DATE_FUTURE", "ERROR", "admission_date", value=clean["admission_date"]))
    if clean["oci"] == "Y" and clean["fn"] == "Y":
        errors.append(issue("INCONSISTENT_FLAGS", "ERROR", "oci", oci=clean["oci"], fn=clean["fn"]))
    clean.update({"nri": clean["nri"] == "Y", "oci": clean["oci"] == "Y", "fn": clean["fn"] == "Y"})
    return clean, errors


def registry_checks(clean: dict, record: ApaarRecord | None) -> list[Issue]:
    if record is None:
        return [issue("APAAR_NOT_FOUND", "ERROR", "apaar_id", value=clean["apaar_id"])]
    if record.status != "ACTIVE":
        return [issue("APAAR_INACTIVE", "ERROR", "apaar_id", value=clean["apaar_id"])]
    return []


def registry_mismatches(clean: dict, record: ApaarRecord) -> list[Issue]:
    normalized_name = " ".join(clean["name"].casefold().split())
    registry_name = " ".join(record.name.casefold().split())
    warnings = []
    if normalized_name != registry_name:
        warnings.append(issue("NAME_MISMATCH", "WARNING", "name", value=clean["name"]))
    if clean["dob"] != record.dob.isoformat():
        warnings.append(issue("DOB_MISMATCH", "WARNING", "dob", value=clean["dob"]))
    return warnings


def cross_institution_check(clean: dict, ctx: ValidationContext) -> list[Issue]:
    for enrolment in ctx.other_enrolments.get(clean["apaar_id"], []):
        if enrolment.get("academic_year") == clean["academic_year"] and enrolment.get("institution_id") != ctx.institution_id:
            return [issue("CROSS_INSTITUTION_DUP", "WARNING", "apaar_id", value=clean["apaar_id"])]
    return []


def capacity_check(clean: dict, programme: ProgrammeInfo, ctx: ValidationContext, batch_counts: dict[tuple[int, str, str], int]) -> list[Issue]:
    admission_type = clean["admission_type"]
    key = (programme.id, clean["academic_year"], admission_type)
    stored = ctx.existing_counts.get(key, 0)
    existing = ctx.existing_students.get((clean["apaar_id"], clean["academic_year"]))
    if existing == (programme.id, admission_type):
        stored -= 1
    projected = stored + batch_counts.get(key, 0) + 1
    limit = programme.approved_intake if admission_type == "REGULAR" else programme.supernumerary_limit
    if projected > limit:
        code = "INTAKE_EXCEEDED" if admission_type == "REGULAR" else "SUPERNUMERARY_EXCEEDED"
        return [issue(code, "WARNING", "admission_type", value=programme.code)]
    return []
