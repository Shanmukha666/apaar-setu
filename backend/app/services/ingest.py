"""Database-backed validation and upload ingestion."""
import json
from collections import defaultdict
from datetime import date

from sqlalchemy import func

from app.models import Alert, Programme, Student, Upload, ValidationIssue
from app.schemas import UploadResult
from app.services.apaar_adapter import make_validation_lookup
from app.services.audit import log_action
from app.services.validation.engine import validate_batch
from app.services.validation.types import ProgrammeInfo, ValidationContext


def process_rows(db, institution_id, actor, rows, filename, source, dry_run, today: date) -> UploadResult:
    programmes = db.query(Programme).filter_by(institution_id=institution_id).all()
    programme_map = {p.code: ProgrammeInfo(p.id, p.code, p.approved_intake, p.supernumerary_limit) for p in programmes}
    existing_counts = {(pid, year, kind): count for pid, year, kind, count in db.query(Student.programme_id, Student.academic_year, Student.admission_type, func.count(Student.id)).group_by(Student.programme_id, Student.academic_year, Student.admission_type)}
    existing_students = {(s.apaar_id, s.academic_year): (s.programme_id, s.admission_type) for s in db.query(Student).filter_by(institution_id=institution_id)}
    ids = {str(row.get("apaar_id", "")).strip() for row in rows}
    other = defaultdict(list)
    for s in db.query(Student).filter(Student.institution_id != institution_id, Student.apaar_id.in_(ids)):
        other[s.apaar_id].append({"institution_id": s.institution_id, "academic_year": s.academic_year})
    ctx = ValidationContext(institution_id, programme_map, existing_counts, existing_students, dict(other), make_validation_lookup(db), today)
    result = validate_batch(rows, ctx)
    upload = Upload(institution_id=institution_id, user_id=actor.id, filename=filename, source=source, dry_run=dry_run, total_rows=len(rows), accepted=result.accepted, flagged=result.flagged, rejected=result.rejected)
    db.add(upload); db.flush()
    for row in result.rows:
        for issue in row.issues:
            db.add(ValidationIssue(upload_id=upload.id, row_number=row.row_number, apaar_id=row.apaar_id, field=issue.field, code=issue.code, severity=issue.severity, message=issue.message))
    if not dry_run:
        for row in result.rows:
            if row.status == "REJECTED": continue
            clean, programme = row.normalized, programme_map[row.normalized["programme_code"]]
            student = db.query(Student).filter_by(apaar_id=row.apaar_id, institution_id=institution_id, academic_year=clean["academic_year"]).first()
            values = {"programme_id": programme.id, "student_ref": clean["student_ref"], "name": clean["name"], "dob": date.fromisoformat(clean["dob"]), "gender": clean["gender"], "category": clean["category"], "admission_date": date.fromisoformat(clean["admission_date"]), "admission_type": clean["admission_type"], "nri": "Y" if clean["nri"] else "N", "oci": "Y" if clean["oci"] else "N", "fn": "Y" if clean["fn"] else "N", "status": row.status, "issue_codes": ",".join(i.code for i in row.issues), "upload_id": upload.id}
            if student:
                for key, value in values.items(): setattr(student, key, value)
            else:
                db.add(Student(apaar_id=row.apaar_id, institution_id=institution_id, academic_year=clean["academic_year"], **values))
        # One critical alert is retained for every programme/year whose rows crossed
        # regular capacity in this upload.  The validation warning remains on each
        # student row as the detailed evidence.
        alerted_programmes = set()
        for row in result.rows:
            if "INTAKE_EXCEEDED" not in {issue.code for issue in row.issues}:
                continue
            clean = row.normalized
            programme = programme_map[clean["programme_code"]]
            if programme.id not in alerted_programmes:
                alerted_programmes.add(programme.id)
                db.add(Alert(institution_id=institution_id, programme_id=programme.id,
                             rule_code="INTAKE_EXCEEDED", severity="CRITICAL",
                             message=f"Regular enrolment exceeds approved intake for {programme.code} in {clean['academic_year']}.",
                             evidence_json=json.dumps({"programme_code": programme.code,
                                                       "academic_year": clean["academic_year"],
                                                       "approved_intake": programme.approved_intake}, sort_keys=True),
                             upload_id=upload.id))
        log_action(db, actor, "UPLOAD", "upload", upload.id, {"filename": filename})
    else:
        log_action(db, actor, "UPLOAD_DRY_RUN", "upload", upload.id, {"filename": filename})
    db.commit()
    if not dry_run:
        # Refresh derived anomaly alerts after student records are durable. Cross
        # duplicate warnings can affect the uploading institution and its peers.
        from app.services.insights import list_duplicates, refresh_institution_alerts
        affected = {institution_id}
        for duplicate in list_duplicates(db):
            ids = {item["id"] for item in duplicate["institutions"]}
            if institution_id in ids:
                affected.update(ids)
        for affected_id in sorted(affected):
            refresh_institution_alerts(db, affected_id)
    return UploadResult(upload_id=upload.id, dry_run=dry_run, total_rows=result.accepted + result.flagged + result.rejected, accepted=result.accepted, flagged=result.flagged, rejected=result.rejected, rows=[{"row_number":r.row_number,"apaar_id":r.apaar_id,"status":r.status,"issues":[{"code":i.code,"severity":i.severity,"field":i.field,"message":i.message} for i in r.issues]} for r in result.rows])
