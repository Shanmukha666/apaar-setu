"""Authentication endpoints (implemented, not a stub)."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_current_user, verify_password
from app.db import get_db
from app.models import User
from app.schemas import LoginRequest, LoginResponse, UserOut
from app.services.audit import log_action

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    log_action(db, user, "LOGIN", "user", user.id, {"email": user.email})
    db.commit()
    return LoginResponse(access_token=create_access_token(user), token_type="bearer", user=user)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
