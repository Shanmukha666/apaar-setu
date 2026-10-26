"""Student query and batch-ingestion endpoints."""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_

from app.core.config import DEMO_TODAY
from app.core.security import require_roles
from app.db import get_db
from app.models import Programme, Student
from app.schemas import StudentBulkRequest, StudentUpdate, UploadResult
from app.services.ingest import process_rows

router = APIRouter(prefix="/api/students", tags=["students"])
ACCESS = require_roles("institution_admin", "aicte_officer")


def _student_out(student: Student, programme: Programme) -> dict:
    return {"id": student.id, "apaar_id": student.apaar_id, "institution_id": student.institution_id,
            "programme_id": student.programme_id, "programme_code": programme.code,
            "programme_name": programme.name, "student_ref": student.student_ref, "name": student.name,
            "dob": student.dob.isoformat(), "gender": student.gender, "category": student.category,
            "academic_year": student.academic_year, "admission_date": student.admission_date.isoformat(),
            "admission_type": student.admission_type, "nri": student.nri, "oci": student.oci,
            "fn": student.fn, "status": student.status,
            "issue_codes": [code for code in student.issue_codes.split(",") if code]}


def _require_own_institution(user, institution_id: int) -> None:
    if user.role == "institution_admin" and user.institution_id != institution_id:
        raise HTTPException(status_code=403, detail="This institution is outside your access scope")


@router.post("/bulk", response_model=UploadResult)
def bulk(body: StudentBulkRequest, dry_run: bool = False, user=Depends(require_roles("institution_admin")), db=Depends(get_db)):
    return process_rows(db, user.institution_id, user, [row.model_dump() for row in body.rows],
                        "api-bulk.json", "api", dry_run, date.fromisoformat(DEMO_TODAY))


@router.get("")
def list_students(institution_id: int | None = None, programme_id: int | None = None, status: str | None = None,
                  q: str | None = None, page: int = 1, page_size: int = 20,
                  user=Depends(ACCESS), db=Depends(get_db)):
    if page < 1 or page_size < 1 or page_size > 100:
        raise HTTPException(status_code=422, detail="page must be positive and page_size must be 1..100")
    target_institution = user.institution_id if user.role == "institution_admin" else institution_id
    if institution_id is not None:
        _require_own_institution(user, institution_id)
        target_institution = institution_id
    query = db.query(Student, Programme).join(Programme, Student.programme_id == Programme.id)
    if target_institution is not None:
        query = query.filter(Student.institution_id == target_institution)
    if programme_id is not None:
        query = query.filter(Student.programme_id == programme_id)
    if status:
        query = query.filter(Student.status == status)
    if q and q.strip():
        needle = f"%{q.strip()}%"
        query = query.filter(or_(Student.apaar_id.like(needle), Student.name.ilike(needle), Student.student_ref.ilike(needle)))
    total = query.count()
    rows = query.order_by(Student.name, Student.id).offset((page - 1) * page_size).limit(page_size).all()
    return {"items": [_student_out(student, programme) for student, programme in rows], "total": total,
            "page": page, "page_size": page_size}


@router.get("/{apaar_id}")
def get_student(apaar_id: str, user=Depends(ACCESS), db=Depends(get_db)):
    query = db.query(Student, Programme).join(Programme, Student.programme_id == Programme.id).filter(Student.apaar_id == apaar_id)
    if user.role == "institution_admin":
        query = query.filter(Student.institution_id == user.institution_id)
    rows = query.order_by(Student.academic_year.desc(), Student.id.desc()).all()
    if not rows:
        raise HTTPException(status_code=404, detail="Student not found")
    return {"items": [_student_out(student, programme) for student, programme in rows]}


@router.put("/{apaar_id}")
def update_student(apaar_id: str, body: StudentUpdate, user=Depends(require_roles("institution_admin"))):
    # The addendum cuts editing from this prototype; retain a clear, safe API response.
    raise HTTPException(status_code=501, detail="Student updates are not included in this prototype")
