"""Dependency-free values passed into and returned from validation."""
from dataclasses import dataclass, field
from datetime import date
from typing import Callable


@dataclass(frozen=True)
class Issue:
    code: str
    severity: str
    field: str
    message: str


@dataclass
class RowResult:
    row_number: int
    apaar_id: str
    status: str
    issues: list[Issue]
    normalized: dict


@dataclass
class BatchResult:
    rows: list[RowResult]
    accepted: int
    flagged: int
    rejected: int


@dataclass(frozen=True)
class ProgrammeInfo:
    id: int
    code: str
    approved_intake: int
    supernumerary_limit: int


@dataclass(frozen=True)
class ApaarRecord:
    apaar_id: str
    name: str
    dob: date
    status: str


@dataclass
class ValidationContext:
    institution_id: int
    programmes: dict[str, ProgrammeInfo]
    existing_counts: dict[tuple[int, str, str], int]
    existing_students: dict[tuple[str, str], tuple[int, str]]
    other_enrolments: dict[str, list[dict]]
    apaar_lookup: Callable[[str], ApaarRecord | None]
    today: date
