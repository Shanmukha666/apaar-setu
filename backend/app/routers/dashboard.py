"""National dashboard and cross-institution duplicates (AICTE only)."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import require_roles
from app.db import get_db
from app.services.insights import list_duplicates, national_summary

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/dashboard/national")
def national(user=Depends(require_roles("aicte_officer")), db: Session = Depends(get_db)):
    return national_summary(db)


@router.get("/duplicates")
def duplicates(user=Depends(require_roles("aicte_officer")), db: Session = Depends(get_db)):
    return list_duplicates(db)
