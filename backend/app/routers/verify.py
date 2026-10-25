"""Record verification route stubs owned by P6."""
from fastapi import APIRouter, Depends
from app.core.security import require_roles
from app.schemas import VerifyRequest, VerifyResponse

router = APIRouter(prefix="/api/verify", tags=["verify"])


@router.post("", response_model=VerifyResponse)
def verify(body: VerifyRequest, user=Depends(require_roles("verifier", "aicte_officer", "institution_admin"))):
    # STUB - owner replaces
    return VerifyResponse(valid=True, reason="CONSENT_REQUIRED", consent_granted=False, record=None)


@router.get("/public-key")
def public_key():
    # STUB - owner replaces
    return {"public_key": ""}
