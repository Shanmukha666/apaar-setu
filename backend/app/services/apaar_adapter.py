"""Mock APAAR adapter. Owner: P3."""
from typing import Protocol
from app.core import config as settings
from app.models import ApaarRegistry

class ApaarClient(Protocol):
    def lookup(self, apaar_id: str) -> dict | None: ...

class MockApaarClient:
    def __init__(self, session): self.session = session
    def lookup(self, apaar_id: str) -> dict | None:
        row = self.session.get(ApaarRegistry, apaar_id)
        return None if row is None else {"apaar_id": row.apaar_id, "name": row.name, "dob": row.dob.isoformat(), "status": row.status}

class HttpApaarClient:
    def lookup(self, apaar_id: str) -> dict | None:
        # This is where the real APAAR/DigiLocker call goes.
        raise NotImplementedError("Real APAAR integration is not enabled")

def get_apaar_client(session):
    return MockApaarClient(session) if settings.APAAR_MODE == "mock" else HttpApaarClient()
