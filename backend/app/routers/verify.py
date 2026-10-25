"""Verification of signed synthetic records."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core import config as settings
from app.core.security import require_roles
from app.db import get_db
from app.models import Consent, Institution, Programme, Student
from app.schemas import VerifyRequest, VerifyResponse
from app.services import signing
from app.services.audit import log_action

router = APIRouter(prefix="/api/verify", tags=["verify"])


@router.post("", response_model=VerifyResponse)
def verify(body: VerifyRequest, user=Depends(require_roles("verifier", "aicte_officer", "institution_admin")), db: Session = Depends(get_db)):
    valid, payload, reason = signing.verify_token(body.token, settings.SIGNING_SEED)
    apaar_id = payload.get("apaar_id") if payload else None
    if not valid:
        log_action(db, user, "VERIFY_ATTEMPT", "record", apaar_id or "unknown", {"result": reason})
        db.commit()
        return VerifyResponse(valid=False, reason=reason, consent_granted=False, record=None)
    student = db.query(Student).filter_by(apaar_id=apaar_id, academic_year=payload.get("academic_year")).first()
    if not student:
        log_action(db, user, "VERIFY_ATTEMPT", "record", apaar_id, {"result": "RECORD_NOT_FOUND", "apaar_id": apaar_id})
        db.commit()
        return VerifyResponse(valid=False, reason="RECORD_NOT_FOUND", consent_granted=False, record=None)
    consent = db.query(Consent).filter_by(apaar_id=apaar_id).first()
    if not consent or not consent.granted:
        log_action(db, user, "VERIFY_ATTEMPT", "record", student.id, {"result": "CONSENT_REQUIRED", "apaar_id": apaar_id})
        db.commit()
        return VerifyResponse(valid=True, reason="CONSENT_REQUIRED", consent_granted=False, record=None)
    institution = db.get(Institution, student.institution_id)
    programme = db.get(Programme, student.programme_id)
    record = {"apaar_id": student.apaar_id, "name": student.name, "institution_name": institution.name, "programme_name": programme.name, "academic_year": student.academic_year, "status": student.status, "issued_at": payload["issued_at"]}
    log_action(db, user, "VERIFY_ATTEMPT", "record", student.id, {"result": "OK", "apaar_id": apaar_id})
    db.commit()
    return VerifyResponse(valid=True, reason="OK", consent_granted=True, record=record)


@router.get("/public-key")
def public_key():
    return {"algorithm": "Ed25519", "public_key_pem": signing.get_public_key_pem(settings.SIGNING_SEED)}
