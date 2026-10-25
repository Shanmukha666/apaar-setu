"""Institution route stubs owned by P4."""
from fastapi import APIRouter, Depends
from app.core.security import require_roles

router = APIRouter(prefix="/api/institutions", tags=["institutions"])


@router.get("")
def list_institutions(user=Depends(require_roles("aicte_officer", "sys_admin"))):
    # STUB - owner replaces
    return [{"id": 1, "code": "DIT001", "name": "Deccan Institute of Technology", "state": "Telangana", "type": "Engineering"}]


@router.get("/{institution_id}/summary")
def summary(institution_id: int, user=Depends(require_roles("institution_admin", "aicte_officer", "sys_admin"))):
    # STUB - owner replaces
    return {"institution": {"id": institution_id, "code": "DIT001", "name": "Deccan Institute of Technology"}, "quality_score": 100, "risk_score": 0, "programmes": [{"programme_id": 1, "code": "DIT001-CSE", "name": "Computer Science", "approved_intake": 60, "supernumerary_limit": 6, "enrolled_regular": 0, "enrolled_supernumerary": 0, "fill_pct": 0, "flagged": 0}], "category_mix": {"regular": 0, "supernumerary": 0, "nri": 0, "oci": 0, "fn": 0}, "recent_uploads": [], "open_alerts": []}
