"""Idempotent mock registry loader."""
import json
from datetime import date
from pathlib import Path
from app.models import ApaarRegistry

def load_registry(session):
    data=json.loads((Path(__file__).parent/"data"/"apaar_registry.json").read_text(encoding="utf-8"))
    for item in data:
        if not session.get(ApaarRegistry,item["apaar_id"]): session.add(ApaarRegistry(apaar_id=item["apaar_id"],name=item["name"],dob=date.fromisoformat(item["dob"]),status=item["status"]))
    session.commit()
