"""Verify a signed record token. The signature proves authenticity; consent controls what is revealed."""
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


def _respond(db, user, reason, valid, consent=False, record=None, apaar_id=None):
    log_action(db, user, "VERIFY_ATTEMPT", "record", apaar_id or "unknown", {"result": reason, "apaar_id": apaar_id})
    db.commit()
    return VerifyResponse(valid=valid, reason=reason, consent_granted=consent, record=record)


@router.post("", response_model=VerifyResponse)
def verify(body: VerifyRequest, user=Depends(require_roles("verifier", "aicte_officer", "institution_admin")),
           db: Session = Depends(get_db)):
    ok, payload, reason = signing.verify_token(body.token.strip(), settings.SIGNING_SEED)
    if not ok:
        return _respond(db, user, reason, False)
    apaar_id = payload["apaar_id"]
    student = (db.query(Student).join(Institution, Institution.id == Student.institution_id)
               .filter(Student.apaar_id == apaar_id, Student.academic_year == payload["academic_year"],
                       Institution.code == payload["institution_code"]).first())
    if not student:
        return _respond(db, user, "RECORD_NOT_FOUND", False, apaar_id=apaar_id)
    consent = db.query(Consent).filter_by(apaar_id=apaar_id).first()
    if not (consent and consent.granted):
        return _respond(db, user, "CONSENT_REQUIRED", True, False, None, apaar_id)
    institution = db.get(Institution, student.institution_id)
    programme = db.get(Programme, student.programme_id)
    record = {"apaar_id": apaar_id, "name": student.name, "institution_name": institution.name,
              "programme_name": programme.name, "academic_year": student.academic_year,
              "status": student.status, "issued_at": payload["issued_at"]}
    return _respond(db, user, "OK", True, True, record, apaar_id)


@router.get("/public-key")
def public_key():
    return {"algorithm": "Ed25519", "public_key_pem": signing.get_public_key_pem(settings.SIGNING_SEED)}
