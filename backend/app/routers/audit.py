"""AICTE audit-log views and hash-chain verification."""
import json
from fastapi import APIRouter, Depends, HTTPException
from app.core.security import require_roles
from app.db import get_db
from app.models import AuditLog
from app.services.audit import verify_chain as verify_audit_chain

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("")
def list_audit(action: str | None = None, page: int = 1, page_size: int = 20, user=Depends(require_roles("aicte_officer", "sys_admin")), db=Depends(get_db)):
    if page < 1 or page_size < 1 or page_size > 100:
        raise HTTPException(status_code=422, detail="page must be positive and page_size must be 1..100")
    query = db.query(AuditLog)
    if action:
        query = query.filter(AuditLog.action == action)
    total = query.count()
    rows = query.order_by(AuditLog.id.desc()).offset((page - 1) * page_size).limit(page_size)
    return {"items": [{"id": row.id, "ts": row.ts, "actor_id": row.actor_id, "actor_email": row.actor_email, "actor_role": row.actor_role, "action": row.action, "entity_type": row.entity_type, "entity_id": row.entity_id, "details": json.loads(row.details_json), "prev_hash": row.prev_hash, "hash": row.hash} for row in rows], "total": total, "page": page, "page_size": page_size}


@router.get("/verify-chain")
def verify_chain(user=Depends(require_roles("aicte_officer", "sys_admin")), db=Depends(get_db)):
    return verify_audit_chain(db)
