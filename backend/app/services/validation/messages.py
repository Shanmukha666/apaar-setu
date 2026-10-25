"""Human-readable templates for every contract validation rule."""
MESSAGES = {
    "APAAR_MISSING": "APAAR ID is required.",
    "APAAR_FORMAT": "APAAR ID '{value}' must contain exactly 12 digits.",
    "APAAR_CHECKSUM": "APAAR ID '{value}' fails the mock Luhn checksum.",
    "DUP_IN_FILE": "APAAR ID '{value}' is duplicated for this academic year in the file.",
    "PROGRAMME_UNKNOWN": "Programme code '{value}' does not belong to this institution.",
    "FIELD_INVALID": "Field '{field}' has invalid value '{value}'.",
    "DATE_FUTURE": "Admission date '{value}' is after the supplied validation date.",
    "INCONSISTENT_FLAGS": "OCI and FN cannot both be Y (received oci='{oci}', fn='{fn}').",
    "APAAR_NOT_FOUND": "APAAR ID '{value}' was not found in the mock registry.",
    "APAAR_INACTIVE": "APAAR ID '{value}' is inactive in the mock registry.",
    "NAME_MISMATCH": "Name '{value}' does not match the mock registry.",
    "DOB_MISMATCH": "Date of birth '{value}' does not match the mock registry.",
    "CROSS_INSTITUTION_DUP": "APAAR ID '{value}' is enrolled at another institution in this academic year.",
    "INTAKE_EXCEEDED": "Regular intake is exceeded for programme '{value}'.",
    "SUPERNUMERARY_EXCEEDED": "Supernumerary intake is exceeded for programme '{value}'.",
}
