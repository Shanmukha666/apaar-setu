"""Signed synthetic student record endpoints."""
import base64
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from app.core.security import require_roles
from app.db import get_db
from app.models import Student, Institution, Programme
from app.core import config as settings
from app.services import signing
from app.services.audit import log_action
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/records", tags=["records"])
ACCESS = require_roles("institution_admin", "aicte_officer")


def _student(db: Session, apaar_id: str, year: str | None, user) -> Student:
    query = db.query(Student).filter_by(apaar_id=apaar_id)
    if year:
        query = query.filter_by(academic_year=year)
    row = query.order_by(Student.academic_year.desc()).first()
    if not row:
        raise HTTPException(status_code=404, detail="Student not found")
    if user.role == "institution_admin" and row.institution_id != user.institution_id:
        raise HTTPException(status_code=403, detail="Not permitted")
    return row


def _token_data(db: Session, row: Student) -> tuple[dict, str, str]:
    inst = db.get(Institution, row.institution_id)
    prog = db.get(Programme, row.programme_id)
    payload = signing.build_payload({"apaar_id": row.apaar_id, "student_ref": row.student_ref, "academic_year": row.academic_year, "status": row.status}, inst.code, prog.code, datetime.now(timezone.utc).isoformat())
    token = signing.sign_payload(payload, settings.SIGNING_SEED)
    return payload, token, signing.make_verify_url(token, settings.FRONTEND_URL)


@router.post("/{apaar_id}/issue")
def issue(apaar_id: str, academic_year: str | None = None, user=Depends(ACCESS), db: Session = Depends(get_db)):
    row = _student(db, apaar_id, academic_year, user)
    payload, token, url = _token_data(db, row)
    log_action(db, user, "RECORD_ISSUED", "student", row.id, {"apaar_id": apaar_id})
    db.commit()
    return {"token": token, "verify_url": url, "qr_png_base64": base64.b64encode(signing.make_qr_png(url)).decode("ascii"), "payload": payload}


@router.get("/{apaar_id}/qr.png")
def qr(apaar_id: str, academic_year: str | None = None, user=Depends(ACCESS), db: Session = Depends(get_db)):
    row = _student(db, apaar_id, academic_year, user)
    _, _, url = _token_data(db, row)
    return Response(content=signing.make_qr_png(url), media_type="image/png")
