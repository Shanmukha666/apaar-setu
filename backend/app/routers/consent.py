"""Consent route stubs owned by P6."""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import Consent, Student
from app.services.audit import log_action
from app.core.security import require_roles
from app.schemas import ConsentUpdate

router = APIRouter(prefix="/api/consent", tags=["consent"])
ACCESS = require_roles("institution_admin", "aicte_officer")


@router.get("/{apaar_id}")
def _allowed(db, apaar_id, user):
    if user.role == "institution_admin" and not db.query(Student).filter_by(apaar_id=apaar_id,institution_id=user.institution_id).first(): raise HTTPException(403,"Not permitted")
def get_consent(apaar_id: str, user=Depends(ACCESS), db: Session=Depends(get_db)):
    _allowed(db,apaar_id,user); row=db.query(Consent).filter_by(apaar_id=apaar_id).first()
    if not row: raise HTTPException(404,"Consent not found")
    return {"apaar_id":row.apaar_id,"granted":row.granted,"purpose":row.purpose,"updated_at":row.updated_at.isoformat()}


@router.put("/{apaar_id}")
def put_consent(apaar_id: str, body: ConsentUpdate, user=Depends(ACCESS), db: Session=Depends(get_db)):
    _allowed(db,apaar_id,user); row=db.query(Consent).filter_by(apaar_id=apaar_id).first()
    if not row: raise HTTPException(404,"Consent not found")
    row.granted=body.granted; row.updated_at=datetime.now(timezone.utc); log_action(db,user,"CONSENT_CHANGED","consent",apaar_id,{"granted":body.granted}); db.commit()
    return {"apaar_id":row.apaar_id,"granted":row.granted,"purpose":row.purpose,"updated_at":row.updated_at.isoformat()}
