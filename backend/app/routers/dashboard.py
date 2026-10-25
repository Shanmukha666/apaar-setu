"""National dashboard and duplicate route stubs owned by P4."""
from fastapi import APIRouter, Depends
from app.core.security import require_roles

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/dashboard/national")
def national(user=Depends(require_roles("aicte_officer"))):
    # STUB - owner replaces
    return {"cards": {"institutions": 5, "students": 0, "flagged": 0, "rejected_rows": 0, "open_critical_alerts": 0, "cross_duplicates": 0}, "by_state": [{"state": "Telangana", "intake": 60, "enrolled": 0}], "risk_ranking": [{"institution_id": 1, "name": "Deccan Institute of Technology", "risk_score": 0, "quality_score": 100, "alerts": 0}], "intake_vs_enrolment": [{"institution": "Deccan Institute of Technology", "intake": 60, "enrolled": 0}]}


@router.get("/duplicates")
def duplicates(user=Depends(require_roles("aicte_officer"))):
    # STUB - owner replaces
    return [{"apaar_id": "123456789015", "academic_year": "2026-27", "institutions": [{"id": 1, "name": "Deccan Institute of Technology"}]}]
