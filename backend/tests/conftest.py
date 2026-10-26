"""Shared test setup: one in-memory database for the whole test run."""
import os

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
