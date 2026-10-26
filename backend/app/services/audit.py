"""Tamper-evident audit log helpers (hash chain)."""
import hashlib
import json
from datetime import datetime, timezone

from app.models import AuditLog

GENESIS = "0" * 64


def _canonical(entry: dict) -> str:
    return json.dumps(entry, sort_keys=True, separators=(",", ":"), default=str)


def _hash(previous: str, entry: dict) -> str:
    return hashlib.sha256((previous + _canonical(entry)).encode("utf-8")).hexdigest()


def _entry_of(row) -> dict:
    return {"ts": row.ts, "actor_id": row.actor_id, "actor_email": row.actor_email, "actor_role": row.actor_role,
            "action": row.action, "entity_type": row.entity_type, "entity_id": str(row.entity_id),
            "details_json": row.details_json}


def log_action(db, actor, action, entity_type, entity_id, details: dict, ts: datetime | None = None):
    """Append one entry. The caller commits. ts is stored as a UTC ISO string so hashing is exact."""
    timestamp = (ts or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat()
    previous = db.query(AuditLog).order_by(AuditLog.id.desc()).first()
    prev_hash = previous.hash if previous else GENESIS
    record = {"ts": timestamp, "actor_id": getattr(actor, "id", 0), "actor_email": getattr(actor, "email", "system@demo.in"),
              "actor_role": getattr(actor, "role", "sys_admin"), "action": action, "entity_type": entity_type,
              "entity_id": str(entity_id), "details_json": _canonical(details)}
    row = AuditLog(**record, prev_hash=prev_hash, hash=_hash(prev_hash, record))
    db.add(row)
    db.flush()
    return row


def verify_chain(db) -> dict:
    previous, checked = GENESIS, 0
    for row in db.query(AuditLog).order_by(AuditLog.id):
        if row.prev_hash != previous or row.hash != _hash(previous, _entry_of(row)):
            return {"valid": False, "checked": checked, "broken_at": row.id}
        previous = row.hash
        checked += 1
    return {"valid": True, "checked": checked, "broken_at": None}
