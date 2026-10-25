"""Upload route stubs owned by P1."""
from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import PlainTextResponse
from app.core.security import require_roles
from app.schemas import UploadResult

router = APIRouter(prefix="/api/uploads", tags=["uploads"])
ADMIN_OR_AICTE = require_roles("institution_admin", "aicte_officer")


def sample(dry_run: bool = False) -> UploadResult:
    return UploadResult(upload_id=1, dry_run=dry_run, total_rows=1, accepted=1, flagged=0, rejected=0, rows=[{"row_number": 1, "apaar_id": "123456789015", "status": "ACCEPTED", "issues": []}])


@router.post("", response_model=UploadResult)
async def upload(file: UploadFile = File(...), dry_run: bool = False, user=Depends(require_roles("institution_admin"))):
    # STUB - owner replaces
    return sample(dry_run)


@router.get("")
def list_uploads(user=Depends(ADMIN_OR_AICTE)):
    # STUB - owner replaces
    return [{"id": 1, "filename": "demo.csv", "source": "csv", "dry_run": False, "total_rows": 1, "accepted": 1, "flagged": 0, "rejected": 0}]


@router.get("/{upload_id}", response_model=UploadResult)
def get_upload(upload_id: int, user=Depends(ADMIN_OR_AICTE)):
    # STUB - owner replaces
    return sample()


@router.get("/{upload_id}/issues.csv", response_class=PlainTextResponse)
def issues_csv(upload_id: int, user=Depends(ADMIN_OR_AICTE)):
    # STUB - owner replaces
    return "row_number,apaar_id,field,code,severity,message\n"
