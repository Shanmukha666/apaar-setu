"""Environment-backed settings with safe local defaults."""
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./apaar_setu.db")
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret")
SIGNING_SEED = os.getenv("SIGNING_SEED", "apaar-setu-demo")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
APAAR_MODE = os.getenv("APAAR_MODE", "mock")
DEMO_TODAY = os.getenv("DEMO_TODAY", "2027-12-31")
