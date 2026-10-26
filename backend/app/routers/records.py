"""Signed, verifiable student records (QR)."""
import base64
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core import config as settings
from app.core.security import require_roles
from app.db import get_db
from app.models import Institution, Programme, Student
from app.services import signing
from app.services.audit import log_action

router = APIRouter(prefix="/api/records", tags=["records"])
ACCESS = require_roles("institution_admin", "aicte_officer")


def _find_student(db: Session, apaar_id: str, year: str | None, user) -> Student:
    query = db.query(Student).filter_by(apaar_id=apaar_id)
    if year:
        query = query.filter_by(academic_year=year)
    if user.role == "institution_admin":
        # Look only inside the caller's own institution, but distinguish "not found" from "not yours".
        row = query.filter_by(institution_id=user.institution_id).order_by(Student.academic_year.desc()).first()
        if not row and query.first():
            raise HTTPException(status_code=403, detail="Not permitted")
    else:
        row = query.order_by(Student.academic_year.desc()).first()
    if not row:
        raise HTTPException(status_code=404, detail="Student not found")
    return row


def _make_token(db: Session, student: Student) -> dict:
    institution = db.get(Institution, student.institution_id)
    programme = db.get(Programme, student.programme_id)
    payload = signing.build_payload(
        {"apaar_id": student.apaar_id, "student_ref": student.student_ref,
         "academic_year": student.academic_year, "status": student.status},
        institution.code, programme.code, datetime.now(timezone.utc).isoformat())
    token = signing.sign_payload(payload, settings.SIGNING_SEED)
    url = signing.make_verify_url(token, settings.FRONTEND_URL)
    return {"payload": payload, "token": token, "url": url}


@router.post("/{apaar_id}/issue")
def issue(apaar_id: str, academic_year: str | None = None, user=Depends(ACCESS), db: Session = Depends(get_db)):
    student = _find_student(db, apaar_id, academic_year, user)
    made = _make_token(db, student)
    log_action(db, user, "RECORD_ISSUED", "student", student.id, {"apaar_id": apaar_id})
    db.commit()
    png = signing.make_qr_png(made["url"])
    return {"token": made["token"], "verify_url": made["url"],
            "qr_png_base64": base64.b64encode(png).decode(), "payload": made["payload"]}


@router.get("/{apaar_id}/qr.png")
def qr_png(apaar_id: str, academic_year: str | None = None, user=Depends(ACCESS), db: Session = Depends(get_db)):
    student = _find_student(db, apaar_id, academic_year, user)
    return Response(signing.make_qr_png(_make_token(db, student)["url"]), media_type="image/png")
