"""Alert route stub owned by P2."""
from fastapi import APIRouter, Depends
from app.core.security import require_roles

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("")
def list_alerts(institution_id: int | None = None, severity: str | None = None, user=Depends(require_roles("aicte_officer", "institution_admin"))):
    # STUB - owner replaces
    return [{"id": 1, "institution_id": institution_id or 1, "rule_code": "ANOM_REJECT_RATE", "severity": severity or "WARNING", "message": "Synthetic sample alert", "evidence_json": "{}"}]
