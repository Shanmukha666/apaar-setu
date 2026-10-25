"""Audit route stubs owned by P1."""
from fastapi import APIRouter, Depends
from app.core.security import require_roles

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("")
def list_audit(action: str | None = None, page: int = 1, page_size: int = 20, user=Depends(require_roles("aicte_officer", "sys_admin"))):
    # STUB - owner replaces
    return {"items": [], "total": 0, "page": page, "page_size": page_size}


@router.get("/verify-chain")
def verify_chain(user=Depends(require_roles("aicte_officer", "sys_admin"))):
    # STUB - owner replaces
    return {"valid": True, "checked": 0, "broken_at": None}
