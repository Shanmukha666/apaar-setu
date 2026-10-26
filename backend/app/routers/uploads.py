"""CSV upload endpoints."""
import csv
from datetime import date
from io import StringIO
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from app.core.config import DEMO_TODAY
from app.core.security import require_roles
from app.db import get_db
from app.models import Upload, ValidationIssue
from app.schemas import UploadResult
from app.services.ingest import process_rows

router = APIRouter(prefix="/api/uploads", tags=["uploads"])
ADMIN_OR_AICTE = require_roles("institution_admin", "aicte_officer")


HEADER = ["apaar_id","student_ref","name","dob","gender","category","programme_code","academic_year","admission_date","admission_type","nri","oci","fn"]


def sample(dry_run: bool = False) -> UploadResult:
    """Temporary compatibility response used by the still-stubbed bulk route."""
    return UploadResult(upload_id=None, dry_run=dry_run, total_rows=0, accepted=0, flagged=0, rejected=0, rows=[])

def _result(db, upload):
    issues = {}
    for issue in db.query(ValidationIssue).filter_by(upload_id=upload.id).order_by(ValidationIssue.row_number):
        issues.setdefault(issue.row_number, []).append({"apaar_id":issue.apaar_id,"code":issue.code,"severity":issue.severity,"field":issue.field,"message":issue.message})
    rows = [{"row_number":n,"apaar_id":group[0]["apaar_id"],"status":"REJECTED" if any(x["severity"]=="ERROR" for x in group) else "FLAGGED","issues":[{"code":x["code"],"severity":x["severity"],"field":x["field"],"message":x["message"]} for x in group]} for n,group in issues.items()]
    return UploadResult(upload_id=upload.id,dry_run=upload.dry_run,total_rows=upload.total_rows,accepted=upload.accepted,flagged=upload.flagged,rejected=upload.rejected,rows=rows)


@router.post("", response_model=UploadResult)
async def upload(file: UploadFile = File(...), dry_run: bool = False, user=Depends(require_roles("institution_admin")), db: Session = Depends(get_db)):
    text = (await file.read()).decode("utf-8-sig")
    reader = csv.DictReader(StringIO(text))
    if reader.fieldnames != HEADER: raise HTTPException(400, "CSV header must match the contract header exactly")
    rows = list(reader)
    if len(rows) > 5000: raise HTTPException(413, "CSV may contain at most 5000 rows")
    return process_rows(db,user.institution_id,user,rows,file.filename or "upload.csv","csv",dry_run,date.fromisoformat(DEMO_TODAY))


@router.get("")
def list_uploads(user=Depends(ADMIN_OR_AICTE), db: Session = Depends(get_db)):
    query=db.query(Upload)
    if user.role=="institution_admin": query=query.filter_by(institution_id=user.institution_id)
    return [{"id":u.id,"filename":u.filename,"source":u.source,"dry_run":u.dry_run,"total_rows":u.total_rows,"accepted":u.accepted,"flagged":u.flagged,"rejected":u.rejected} for u in query.order_by(Upload.id.desc())]


@router.get("/{upload_id}", response_model=UploadResult)
def get_upload(upload_id: int, user=Depends(ADMIN_OR_AICTE), db: Session = Depends(get_db)):
    upload=db.get(Upload,upload_id)
    if not upload: raise HTTPException(404,"Upload not found")
    if user.role=="institution_admin" and upload.institution_id!=user.institution_id: raise HTTPException(403,"Not permitted")
    return _result(db,upload)


@router.get("/{upload_id}/issues.csv", response_class=PlainTextResponse)
def issues_csv(upload_id: int, user=Depends(ADMIN_OR_AICTE), db: Session = Depends(get_db)):
    upload=db.get(Upload,upload_id)
    if not upload: raise HTTPException(404,"Upload not found")
    if user.role=="institution_admin" and upload.institution_id!=user.institution_id: raise HTTPException(403,"Not permitted")
    lines=["row_number,apaar_id,status,code,severity,field,message"]
    for x in db.query(ValidationIssue).filter_by(upload_id=upload_id).order_by(ValidationIssue.row_number): lines.append(f'{x.row_number},{x.apaar_id},,{x.code},{x.severity},{x.field},"{x.message}"')
    return "\n".join(lines)+"\n"
