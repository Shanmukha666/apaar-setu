"""Consent endpoints for stored synthetic students."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import require_roles
from app.db import get_db
from app.models import Consent, Student
from app.schemas import ConsentUpdate
from app.services.audit import log_action

router = APIRouter(prefix="/api/consent", tags=["consent"])
ACCESS = require_roles("institution_admin", "aicte_officer")


def _ensure_access(db: Session, apaar_id: str, user) -> None:
    if user.role == "institution_admin":
        student = db.query(Student).filter_by(apaar_id=apaar_id, institution_id=user.institution_id).first()
        if not student:
            raise HTTPException(status_code=403, detail="Not permitted")


@router.get("/{apaar_id}")
def get_consent(apaar_id: str, user=Depends(ACCESS), db: Session = Depends(get_db)):
    _ensure_access(db, apaar_id, user)
    consent = db.query(Consent).filter_by(apaar_id=apaar_id).first()
    if not consent:
        raise HTTPException(status_code=404, detail="Consent not found")
    return {"apaar_id": consent.apaar_id, "granted": consent.granted, "purpose": consent.purpose, "updated_at": consent.updated_at.isoformat()}


@router.put("/{apaar_id}")
def put_consent(apaar_id: str, body: ConsentUpdate, user=Depends(ACCESS), db: Session = Depends(get_db)):
    _ensure_access(db, apaar_id, user)
    consent = db.query(Consent).filter_by(apaar_id=apaar_id).first()
    if not consent:
        raise HTTPException(status_code=404, detail="Consent not found")
    consent.granted = body.granted
    consent.updated_at = datetime.now(timezone.utc)
    log_action(db, user, "CONSENT_CHANGED", "consent", apaar_id, {"granted": body.granted})
    db.commit()
    return {"apaar_id": consent.apaar_id, "granted": consent.granted, "purpose": consent.purpose, "updated_at": consent.updated_at.isoformat()}
