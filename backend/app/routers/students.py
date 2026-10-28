"""Student endpoints: bulk JSON upload, searchable list, per-student detail."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from datetime import date

from app.core.config import DEMO_TODAY
from app.core.security import require_roles
from app.db import get_db
from app.models import Institution, Programme, Student
from app.schemas import StudentBulkRequest, StudentUpdate, UploadResult
from app.services.ingest import process_rows

router = APIRouter(prefix="/api/students", tags=["students"])
ACCESS = require_roles("institution_admin", "aicte_officer")


def _out(s: Student, programme_code: str, institution_name: str) -> dict:
    return {"id": s.id, "apaar_id": s.apaar_id, "student_ref": s.student_ref, "name": s.name, "dob": s.dob.isoformat(),
            "gender": s.gender, "category": s.category, "academic_year": s.academic_year,
            "admission_date": s.admission_date.isoformat(), "admission_type": s.admission_type,
            "nri": s.nri, "oci": s.oci, "fn": s.fn, "status": s.status,
            "issue_codes": [c for c in s.issue_codes.split(",") if c], "institution_id": s.institution_id,
            "institution_name": institution_name, "programme_id": s.programme_id, "programme_code": programme_code}


@router.post("/bulk", response_model=UploadResult)
def bulk(body: StudentBulkRequest, dry_run: bool = False, user=Depends(require_roles("institution_admin")),
         db: Session = Depends(get_db)):
    rows = [r.model_dump() for r in body.rows]
    return process_rows(db, user.institution_id, user, rows, "api-bulk", "api", dry_run, date.fromisoformat(DEMO_TODAY))


@router.get("")
def list_students(institution_id: int | None = None, programme_id: int | None = None, status: str | None = None,
                  q: str | None = None, page: int = 1, page_size: int = 20, user=Depends(ACCESS),
                  db: Session = Depends(get_db)):
    page, page_size = max(page, 1), min(max(page_size, 1), 100)
    query = db.query(Student, Programme.code, Institution.name).join(Programme, Programme.id == Student.programme_id) \
        .join(Institution, Institution.id == Student.institution_id)
    if user.role == "institution_admin":
        if institution_id is not None and institution_id != user.institution_id:
            raise HTTPException(status_code=403, detail="Not permitted")
        institution_id = user.institution_id          # always restricted to own institution
    if institution_id:
        query = query.filter(Student.institution_id == institution_id)
    if programme_id:
        query = query.filter(Student.programme_id == programme_id)
    if status:
        query = query.filter(Student.status == status)
    if q:
        like = f"%{q.strip()}%"
        query = query.filter(or_(Student.apaar_id.like(like), Student.name.ilike(like), Student.student_ref.ilike(like)))
    total = query.count()
    rows = query.order_by(Student.id).offset((page - 1) * page_size).limit(page_size).all()
    return {"items": [_out(s, code, name) for s, code, name in rows], "total": total, "page": page, "page_size": page_size}


@router.get("/{apaar_id}")
def get_student(apaar_id: str, user=Depends(ACCESS), db: Session = Depends(get_db)):
    query = db.query(Student, Programme.code, Institution.name).join(Programme, Programme.id == Student.programme_id) \
        .join(Institution, Institution.id == Student.institution_id).filter(Student.apaar_id == apaar_id)
    if user.role == "institution_admin":
        query = query.filter(Student.institution_id == user.institution_id)
    rows = query.order_by(Student.academic_year.desc()).all()
    if not rows:
        raise HTTPException(status_code=404, detail="Student not found")
    return {"apaar_id": apaar_id, "records": [_out(s, code, name) for s, code, name in rows]}


@router.put("/{apaar_id}")
def update_student(apaar_id: str, body: StudentUpdate, user=Depends(require_roles("institution_admin"))):
    raise HTTPException(status_code=501, detail="Editing a single student is not part of this prototype; re-upload the corrected row.")
