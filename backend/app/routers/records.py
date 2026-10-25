"""Signed-record route stubs owned by P6."""
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


@router.post("/{apaar_id}/issue")
def _student(db,apaar_id,year,user):
    q=db.query(Student).filter_by(apaar_id=apaar_id)
    if year:q=q.filter_by(academic_year=year)
    row=q.order_by(Student.academic_year.desc()).first()
    if not row:raise HTTPException(404,"Student not found")
    if user.role=="institution_admin" and row.institution_id!=user.institution_id:raise HTTPException(403,"Not permitted")
    return row
@router.post("/{apaar_id}/issue")
def issue(apaar_id: str, academic_year: str|None=None, user=Depends(require_roles("institution_admin", "aicte_officer")), db:Session=Depends(get_db)):
    row=_student(db,apaar_id,academic_year,user); inst=db.get(Institution,row.institution_id); prog=db.get(Programme,row.programme_id)
    payload=signing.build_payload({"apaar_id":row.apaar_id,"student_ref":row.student_ref,"academic_year":row.academic_year,"status":row.status},inst.code,prog.code,datetime.now(timezone.utc).isoformat()); token=signing.sign_payload(payload,settings.SIGNING_SEED); url=signing.make_verify_url(token,settings.FRONTEND_URL); log_action(db,user,"RECORD_ISSUED","student",row.id,{"apaar_id":apaar_id}); db.commit()
    return {"token":token,"verify_url":url,"qr_png_base64":base64.b64encode(signing.make_qr_png(url)).decode(),"payload":payload}


@router.get("/{apaar_id}/qr.png")
def qr(apaar_id: str, academic_year: str|None=None, user=Depends(require_roles("institution_admin", "aicte_officer")), db:Session=Depends(get_db)):
    row=_student(db,apaar_id,academic_year,user); inst=db.get(Institution,row.institution_id); prog=db.get(Programme,row.programme_id); p=signing.build_payload({"apaar_id":row.apaar_id,"student_ref":row.student_ref,"academic_year":row.academic_year,"status":row.status},inst.code,prog.code,datetime.now(timezone.utc).isoformat()); return Response(signing.make_qr_png(signing.make_verify_url(signing.sign_payload(p,settings.SIGNING_SEED),settings.FRONTEND_URL)),media_type="image/png")
