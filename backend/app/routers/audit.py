"""Audit trail endpoints."""
import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import require_roles
from app.db import get_db
from app.models import AuditLog
from app.services import audit as audit_service

router = APIRouter(prefix="/api/audit", tags=["audit"])
ROLES = require_roles("aicte_officer", "sys_admin")


@router.get("")
def list_audit(action: str | None = None, page: int = 1, page_size: int = 20, user=Depends(ROLES), db: Session = Depends(get_db)):
    page, page_size = max(page, 1), min(max(page_size, 1), 100)
    query = db.query(AuditLog)
    if action:
        query = query.filter(AuditLog.action == action)
    total = query.count()
    rows = query.order_by(AuditLog.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    items = [{"id": r.id, "ts": r.ts, "actor_email": r.actor_email, "actor_role": r.actor_role, "action": r.action,
              "entity_type": r.entity_type, "entity_id": r.entity_id, "details": json.loads(r.details_json),
              "hash": r.hash, "prev_hash": r.prev_hash} for r in rows]
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/verify-chain")
def verify_chain(user=Depends(ROLES), db: Session = Depends(get_db)):
    return audit_service.verify_chain(db)


@router.post("/tamper-simulate")
def tamper_simulate(user=Depends(ROLES), db: Session = Depends(get_db)):
    """Developer/Judge demonstration endpoint: intentionally corrupts one record's payload details to demonstrate instant chain tamper detection."""
    target = db.query(AuditLog).order_by(AuditLog.id.desc()).offset(2).first()
    if not target:
        target = db.query(AuditLog).order_by(AuditLog.id.desc()).first()
    if not target:
        return {"ok": False, "message": "No audit entries to tamper"}
    
    # Save original if not already tampered
    details = json.loads(target.details_json)
    if "_tampered" in details:
        return {"ok": False, "message": f"Entry #{target.id} is already tampered"}
    
    details["_tampered"] = True
    details["_original_note"] = "SIMULATED BREACH: unauthorized byte change"
    target.details_json = json.dumps(details, sort_keys=True)
    db.commit()
    return {"ok": True, "tampered_id": target.id, "message": f"Simulated tamper on Audit Entry #{target.id}"}


@router.post("/tamper-restore")
def tamper_restore(user=Depends(ROLES), db: Session = Depends(get_db)):
    """Restores any simulated tampering in audit records back to pristine verifiable state."""
    restored = 0
    for entry in db.query(AuditLog).all():
        try:
            details = json.loads(entry.details_json)
            if "_tampered" in details:
                del details["_tampered"]
                if "_original_note" in details:
                    del details["_original_note"]
                entry.details_json = json.dumps(details, sort_keys=True, separators=(",", ":"))
                restored += 1
        except Exception:
            pass
    db.commit()
    return {"ok": True, "restored_count": restored, "status": "Chain restored"}
