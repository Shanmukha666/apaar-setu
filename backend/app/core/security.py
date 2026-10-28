"""PBKDF2 password hashing and Bearer JWT dependencies."""
import hashlib
import hmac
import os
import secrets
from datetime import datetime, timezone, timedelta

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import JWT_SECRET
from app.db import get_db
from app.models import User

# Derive a consistently sized HS256 key from the documented environment value.
JWT_SIGNING_KEY = hashlib.sha256(JWT_SECRET.encode("utf-8")).hexdigest()
LEGACY_SALT = b"apaar-setu-demo-salt"

bearer = HTTPBearer(auto_error=False)


def hash_password(password: str, salt: bytes | None = None) -> str:
    """Store passwords as '$pbkdf2$<hex_salt>$<hex_hash>'. Legacy hashes remain verifiable."""
    if salt is None:
        raw_salt = secrets.token_bytes(16)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), raw_salt, 120_000).hex()
        return f"$pbkdf2${raw_salt.hex()}${digest}"
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 120_000).hex()


def verify_password(password: str, stored_hash: str) -> bool:
    if stored_hash.startswith("$pbkdf2$"):
        parts = stored_hash.split("$")
        if len(parts) == 4:
            salt_hex, expected_digest = parts[2], parts[3]
            computed = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), 120_000).hex()
            return hmac.compare_digest(computed, expected_digest)
    # Legacy fixed-salt verification compatibility
    legacy_computed = hash_password(password, LEGACY_SALT)
    return hmac.compare_digest(legacy_computed, stored_hash)


def create_access_token(user: User, expires_delta: timedelta = timedelta(hours=12)) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user.id),
        "role": user.role,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
    }
    return jwt.encode(payload, JWT_SIGNING_KEY, algorithm="HS256")


def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)) -> User:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = jwt.decode(credentials.credentials, JWT_SIGNING_KEY, algorithms=["HS256"])
        user = db.get(User, int(payload["sub"]))
    except (jwt.PyJWTError, KeyError, TypeError, ValueError):
        user = None
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return user


def require_roles(*roles: str):
    def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
        return user
    return dependency
