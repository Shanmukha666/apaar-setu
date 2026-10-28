"""Alert feed. AICTE sees all; an institution admin sees only their own."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import require_roles
from app.db import get_db
from app.models import Alert, Institution
from app.services.insights import alert_out

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("")
def list_alerts(institution_id: int | None = None, severity: str | None = None,
                user=Depends(require_roles("aicte_officer", "institution_admin")), db: Session = Depends(get_db)):
    query = db.query(Alert)
    if user.role == "institution_admin":
        if institution_id is not None and institution_id != user.institution_id:
            raise HTTPException(status_code=403, detail="This institution is outside your access scope")
        institution_id = user.institution_id
    if institution_id:
        query = query.filter(Alert.institution_id == institution_id)
    if severity:
        query = query.filter(Alert.severity == severity)
    names = dict(db.query(Institution.id, Institution.name).all())
    return [alert_out(a, names) for a in query.order_by(Alert.id.desc()).limit(200)]
