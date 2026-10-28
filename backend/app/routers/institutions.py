"""Institution list and per-institution summary."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import require_roles
from app.db import get_db
from app.models import Institution
from app.services.insights import institution_stats

router = APIRouter(prefix="/api/institutions", tags=["institutions"])


@router.get("")
def list_institutions(user=Depends(require_roles("aicte_officer", "sys_admin")), db: Session = Depends(get_db)):
    return [{"id": i.id, "code": i.code, "name": i.name, "state": i.state, "type": i.type}
            for i in db.query(Institution).order_by(Institution.id)]


@router.get("/{institution_id}/summary")
def summary(institution_id: int, user=Depends(require_roles("institution_admin", "aicte_officer", "sys_admin")),
            db: Session = Depends(get_db)):
    if user.role == "institution_admin" and user.institution_id != institution_id:
        raise HTTPException(status_code=403, detail="Not permitted")
    if not db.get(Institution, institution_id):
        raise HTTPException(status_code=404, detail="Institution not found")
    return institution_stats(db, institution_id)
