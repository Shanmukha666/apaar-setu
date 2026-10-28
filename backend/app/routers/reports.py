"""Statutory AICTE Enrolment and Compliance Reports."""
import csv
from io import StringIO

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.core.security import require_roles
from app.db import get_db
from app.models import Institution, Programme, Student
from app.routers.uploads import _safe
from app.services.audit import log_action

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/enrolment.csv", response_class=PlainTextResponse)
def enrolment(institution_id: int, academic_year: str, user=Depends(require_roles("aicte_officer")), db: Session = Depends(get_db)):
    institution = db.get(Institution, institution_id)
    if not institution:
        raise HTTPException(status_code=404, detail="Institution not found")
    
    log_action(db, user, "REPORT_EXPORTED", "report", institution_id, {"institution_id": institution_id, "academic_year": academic_year, "format": "csv"})
    db.commit()
    
    out = StringIO()
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow([
        "institution_code", "institution_name", "programme_code", "programme_name",
        "academic_year", "apaar_id", "student_ref", "name", "dob", "gender",
        "category", "admission_date", "admission_type", "nri", "oci", "fn",
        "status", "issue_codes"
    ])
    
    query = (
        db.query(Student, Programme)
        .join(Programme, Programme.id == Student.programme_id)
        .filter(Student.institution_id == institution_id, Student.academic_year == academic_year)
        .order_by(Programme.code, Student.id)
    )
    
    for student, programme in query:
        writer.writerow([
            institution.code,
            _safe(institution.name),
            programme.code,
            _safe(programme.name),
            student.academic_year,
            _safe(student.apaar_id),
            _safe(student.student_ref),
            _safe(student.name),
            student.dob.isoformat(),
            student.gender,
            student.category,
            student.admission_date.isoformat(),
            student.admission_type,
            student.nri,
            student.oci,
            student.fn,
            student.status,
            _safe(student.issue_codes),
        ])
    
    return out.getvalue()
