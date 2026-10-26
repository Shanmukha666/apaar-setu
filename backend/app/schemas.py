"""Pydantic request and response contracts for the API."""
from typing import Any
from pydantic import BaseModel, ConfigDict


class UserOut(BaseModel):
    id: int
    email: str
    name: str
    role: str
    institution_id: int | None

    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserOut


class StudentRow(BaseModel):
    apaar_id: str
    student_ref: str
    name: str
    dob: str
    gender: str
    category: str
    programme_code: str
    academic_year: str
    admission_date: str
    admission_type: str
    nri: str
    oci: str
    fn: str


class IssueOut(BaseModel):
    code: str
    severity: str
    field: str
    message: str


class UploadRowResult(BaseModel):
    row_number: int
    apaar_id: str
    status: str
    issues: list[IssueOut]


class UploadResult(BaseModel):
    upload_id: int | None
    dry_run: bool
    total_rows: int
    accepted: int
    flagged: int
    rejected: int
    rows: list[UploadRowResult]


class StudentBulkRequest(BaseModel):
    rows: list[StudentRow]


class StudentUpdate(BaseModel):
    fields: dict[str, Any]


class ConsentUpdate(BaseModel):
    granted: bool


class VerifyRequest(BaseModel):
    token: str


class VerifyResponse(BaseModel):
    valid: bool
    reason: str | None
    consent_granted: bool
    record: dict[str, Any] | None
