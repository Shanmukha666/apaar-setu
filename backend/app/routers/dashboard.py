"""AICTE aggregate dashboard endpoints."""
from collections import defaultdict
from fastapi import APIRouter, Depends
from app.core.security import require_roles
from app.db import get_db
from app.models import Alert, Institution, Student, Upload
from app.services.insights import institution_stats, list_duplicates

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/dashboard/national")
def national(user=Depends(require_roles("aicte_officer")), db=Depends(get_db)):
    institutions = db.query(Institution).order_by(Institution.id).all()
    state_rows = defaultdict(lambda: {"intake": 0, "enrolled": 0})
    ranking, comparison = [], []
    for institution in institutions:
        item = institution_stats(db, institution.id)
        intake = sum(programme["approved_intake"] for programme in item["programmes"])
        enrolled = sum(programme["enrolled_regular"] + programme["enrolled_supernumerary"] for programme in item["programmes"])
        state_rows[institution.state]["intake"] += intake
        state_rows[institution.state]["enrolled"] += enrolled
        ranking.append({"institution_id": institution.id, "name": institution.name, "risk_score": item["risk_score"], "quality_score": item["quality_score"], "alerts": db.query(Alert).filter_by(institution_id=institution.id).count()})
        comparison.append({"institution": institution.name, "intake": intake, "enrolled": enrolled})
    uploads = db.query(Upload).filter_by(dry_run=False).all()
    return {"cards": {"institutions": len(institutions), "students": db.query(Student).count(), "flagged": db.query(Student).filter_by(status="FLAGGED").count(), "rejected_rows": sum(upload.rejected for upload in uploads), "open_critical_alerts": db.query(Alert).filter_by(severity="CRITICAL").count(), "cross_duplicates": len(list_duplicates(db))}, "by_state": [{"state": state, **values} for state, values in sorted(state_rows.items())], "risk_ranking": sorted(ranking, key=lambda row: (-row["risk_score"], row["name"])), "intake_vs_enrolment": comparison}


@router.get("/duplicates")
def duplicates(user=Depends(require_roles("aicte_officer")), db=Depends(get_db)):
    return list_duplicates(db)
