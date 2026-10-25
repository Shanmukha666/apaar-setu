"""Mock APAAR registry endpoint owned by P3."""
from fastapi import APIRouter, Depends, Header, HTTPException, Response
from sqlalchemy.orm import Session
from app.db import get_db
from app.services.apaar_adapter import MockApaarClient

router = APIRouter(prefix="/mock-apaar/v1", tags=["mock-apaar"])


@router.get("/persons/{apaar_id}")
def person(apaar_id: str, response: Response, x_api_key: str | None = Header(default=None), db: Session = Depends(get_db)):
    if x_api_key != "demo-apaar-key":
        raise HTTPException(status_code=401, detail="Invalid API key")
    record = MockApaarClient(db).lookup(apaar_id)
    if record is None:
        raise HTTPException(status_code=404, detail="APAAR ID not found")
    response.headers["X-Mock-Service"] = "true"
    return record
