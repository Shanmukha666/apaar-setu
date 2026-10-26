"""Role-scoped alert feed."""
import json
from fastapi import APIRouter, Depends, HTTPException
from app.core.security import require_roles
from app.db import get_db
from app.models import Alert

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("")
def list_alerts(institution_id: int | None = None, severity: str | None = None, user=Depends(require_roles("aicte_officer", "institution_admin")), db=Depends(get_db)):
    if user.role == "institution_admin":
        if institution_id is not None and institution_id != user.institution_id:
            raise HTTPException(status_code=403, detail="This institution is outside your access scope")
        institution_id = user.institution_id
    query = db.query(Alert)
    if institution_id is not None:
        query = query.filter(Alert.institution_id == institution_id)
    if severity:
        query = query.filter(Alert.severity == severity)
    return [{"id": item.id, "institution_id": item.institution_id, "programme_id": item.programme_id, "rule_code": item.rule_code, "severity": item.severity, "message": item.message, "evidence": json.loads(item.evidence_json), "upload_id": item.upload_id, "created_at": item.created_at.isoformat()} for item in query.order_by(Alert.id.desc())]
