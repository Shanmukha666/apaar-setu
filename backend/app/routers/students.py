"""Student route stubs owned by P1."""
from fastapi import APIRouter, Depends
from app.core.security import require_roles
from app.schemas import StudentBulkRequest, StudentUpdate, UploadResult
from app.routers.uploads import sample

router = APIRouter(prefix="/api/students", tags=["students"])
ACCESS = require_roles("institution_admin", "aicte_officer")


@router.post("/bulk", response_model=UploadResult)
def bulk(body: StudentBulkRequest, dry_run: bool = False, user=Depends(require_roles("institution_admin"))):
    # STUB - owner replaces
    return sample(dry_run)


@router.get("")
def list_students(institution_id: int | None = None, programme_id: int | None = None, status: str | None = None, q: str | None = None, page: int = 1, page_size: int = 20, user=Depends(ACCESS)):
    # STUB - owner replaces
    return {"items": [], "total": 0, "page": page, "page_size": page_size}


@router.get("/{apaar_id}")
def get_student(apaar_id: str, user=Depends(ACCESS)):
    # STUB - owner replaces
    return {"apaar_id": apaar_id, "student_ref": "SYN-001", "status": "ACCEPTED"}


@router.put("/{apaar_id}")
def update_student(apaar_id: str, body: StudentUpdate, user=Depends(require_roles("institution_admin"))):
    # STUB - owner replaces
    return {"apaar_id": apaar_id, "fields": body.fields, "status": "ACCEPTED"}
