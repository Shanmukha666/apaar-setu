"""Report route stub owned by P4."""
from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse
from app.core.security import require_roles

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/enrolment.csv", response_class=PlainTextResponse)
def enrolment(institution_id: int, academic_year: str, user=Depends(require_roles("aicte_officer"))):
    # STUB - owner replaces
    return "institution_id,academic_year,enrolled\n%s,%s,0\n" % (institution_id, academic_year)
