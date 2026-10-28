"""Shared test setup: one in-memory database for the whole test run."""
import os

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["AUTO_SEED_FULL"] = "false"

import pytest
from fastapi.testclient import TestClient

from app.db import Base, engine
from app.main import app


def login(client, email: str) -> dict:
    r = client.post("/api/auth/login", json={"email": email, "password": "Demo@123"})
    assert r.status_code == 200, r.text
    return {"Authorization": "Bearer " + r.json()["access_token"]}


@pytest.fixture(scope="module")
def seeded():
    """Fresh database + the full synthetic baseline, once per test module (tests in a module share state, in file order)."""
    from seed.load_all import load_all
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    load_all()
    with TestClient(app) as client:
        yield client
