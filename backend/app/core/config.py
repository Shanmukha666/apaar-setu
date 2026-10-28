"""Environment-backed settings with safe local defaults."""
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./apaar_setu.db")
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret")
SIGNING_SEED = os.getenv("SIGNING_SEED", "apaar-setu-demo")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
APAAR_MODE = os.getenv("APAAR_MODE", "mock")
DEMO_TODAY = os.getenv("DEMO_TODAY", "2027-12-31")
APP_ENV = os.getenv("APP_ENV", "development")
AUTO_SEED_FULL = os.getenv("AUTO_SEED_FULL", "true").lower() == "true"


def validate_deployment_settings() -> None:
    """Prevent public deployments from silently using known demo signing keys."""
    deployed = APP_ENV.lower() in {"production", "staging"} or bool(os.getenv("VERCEL"))
    if deployed:
        if JWT_SECRET == "dev-secret" or SIGNING_SEED == "apaar-setu-demo":
            raise RuntimeError("Set unique JWT_SECRET and SIGNING_SEED before staging or production startup (also required whenever running on Vercel)")
        if FRONTEND_URL == "http://localhost:3000":
            raise RuntimeError("Set FRONTEND_URL to the deployed frontend URL before staging or production startup")
