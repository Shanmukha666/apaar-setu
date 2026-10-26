"""Institution aggregates and summary endpoints."""
import json
from fastapi import APIRouter, Depends, HTTPException
from app.core.security import require_roles
from app.db import get_db
from app.models import Alert, Institution, Upload
from app.services.insights import institution_stats

router = APIRouter(prefix="/api/institutions", tags=["institutions"])


@router.get("")
def list_institutions(user=Depends(require_roles("aicte_officer", "sys_admin")), db=Depends(get_db)):
    return [{"id": item.id, "code": item.code, "name": item.name, "state": item.state, "type": item.type}
            for item in db.query(Institution).order_by(Institution.id)]


@router.get("/{institution_id}/summary")
def summary(institution_id: int, user=Depends(require_roles("institution_admin", "aicte_officer", "sys_admin")), db=Depends(get_db)):
    institution = db.get(Institution, institution_id)
    if not institution:
        raise HTTPException(status_code=404, detail="Institution not found")
    if user.role == "institution_admin" and user.institution_id != institution_id:
        raise HTTPException(status_code=403, detail="This institution is outside your access scope")
    stats = institution_stats(db, institution_id)
    uploads = db.query(Upload).filter_by(institution_id=institution_id, dry_run=False).order_by(Upload.id.desc()).limit(5)
    alerts = db.query(Alert).filter_by(institution_id=institution_id).order_by(Alert.id.desc())
    return {"institution": {"id": institution.id, "code": institution.code, "name": institution.name, "state": institution.state, "type": institution.type},
            "quality_score": stats["quality_score"], "risk_score": stats["risk_score"], "programmes": stats["programmes"], "category_mix": stats["category_mix"],
            "recent_uploads": [{"id": upload.id, "filename": upload.filename, "total_rows": upload.total_rows, "accepted": upload.accepted, "flagged": upload.flagged, "rejected": upload.rejected, "created_at": upload.created_at.isoformat()} for upload in uploads],
            "open_alerts": [{"id": alert.id, "rule_code": alert.rule_code, "severity": alert.severity, "message": alert.message, "evidence": json.loads(alert.evidence_json)} for alert in alerts]}
