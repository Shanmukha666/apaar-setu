"""Consent endpoints: who has agreed to share their record with verifiers."""
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


def _check_access(db: Session, apaar_id: str, user) -> None:
    """An institution admin may only touch consent of their own students."""
    if user.role == "institution_admin":
        own = db.query(Student).filter_by(apaar_id=apaar_id, institution_id=user.institution_id).first()
        if not own:
            raise HTTPException(status_code=403, detail="Not permitted")


def _out(row: Consent) -> dict:
    return {"apaar_id": row.apaar_id, "granted": row.granted, "purpose": row.purpose,
            "updated_at": row.updated_at.isoformat()}


@router.get("/{apaar_id}")
def get_consent(apaar_id: str, user=Depends(ACCESS), db: Session = Depends(get_db)):
    _check_access(db, apaar_id, user)
    row = db.query(Consent).filter_by(apaar_id=apaar_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Consent not found")
    return _out(row)


@router.put("/{apaar_id}")
def put_consent(apaar_id: str, body: ConsentUpdate, user=Depends(ACCESS), db: Session = Depends(get_db)):
    _check_access(db, apaar_id, user)
    row = db.query(Consent).filter_by(apaar_id=apaar_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Consent not found")
    row.granted = body.granted
    row.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    log_action(db, user, "CONSENT_CHANGED", "consent", apaar_id, {"granted": body.granted})
    db.commit()
    return _out(row)
