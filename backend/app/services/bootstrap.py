"""Contract-defined institutions, programmes, and demo login accounts."""
import json
from pathlib import Path

from app.core.security import hash_password
from app.models import Institution, Programme, User

PROGRAMMES_FILE = Path(__file__).resolve().parents[2] / "seed" / "data" / "programmes.json"

INSTITUTIONS = [
    (1, "DIT001", "Deccan Institute of Technology", "Telangana", "Engineering"),
    (2, "CCE002", "Coastal College of Engineering", "Andhra Pradesh", "Engineering"),
    (3, "HSM003", "Himalaya School of Management", "Uttarakhand", "PGDM"),
    (4, "MIP004", "Malwa Institute of Pharmacy", "Madhya Pradesh", "Pharmacy"),
    (5, "KPT005", "Kaveri Polytechnic", "Karnataka", "Polytechnic"),
]


def seed_demo_data(db) -> None:
    """Create the fixed contract records; safe to call repeatedly."""
    for ident, code, name, state, kind in INSTITUTIONS:
        if not db.get(Institution, ident):
            db.add(Institution(id=ident, code=code, name=name, state=state, type=kind))
    db.flush()
    for spec in json.loads(PROGRAMMES_FILE.read_text(encoding="utf-8")):
        if not db.query(Programme).filter_by(code=spec["code"]).first():
            db.add(Programme(**spec))
    accounts = [
        ("aicte@demo.in", "AICTE Officer", "aicte_officer", None),
        ("sysadmin@demo.in", "System Administrator", "sys_admin", None),
        ("verifier@demo.in", "Demo Verifier", "verifier", None),
        *[(f"inst{i}@demo.in", f"Institution {i} Admin", "institution_admin", i) for i in range(1, 6)],
    ]
    for email, name, role, institution_id in accounts:
        if not db.query(User).filter_by(email=email).first():
            db.add(User(email=email, password_hash=hash_password("Demo@123"), name=name,
                        role=role, institution_id=institution_id))
    db.commit()
