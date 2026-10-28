"""Database aggregates and deterministic alert refresh (uses the pure functions in anomaly.py).

Capacity is always judged per programme AND academic year, so a new year's admissions never count against last year's.
"""
import json
from statistics import median

from sqlalchemy.orm import Session

from app.models import Alert, Institution, Programme, Student, Upload
from app.services.anomaly import detect_cross_dup_clusters, detect_institution_anomalies, quality_score, risk_score


def list_duplicates(db: Session) -> list[dict]:
    """Same APAAR ID stored at 2+ institutions in the same academic year."""
    groups: dict[tuple[str, str], set[int]] = {}
    for s in db.query(Student.apaar_id, Student.academic_year, Student.institution_id):
        groups.setdefault((s.apaar_id, s.academic_year), set()).add(s.institution_id)
    names = dict(db.query(Institution.id, Institution.name).all())
    return [{"apaar_id": a, "academic_year": y, "institutions": [{"id": i, "name": names[i]} for i in sorted(ids)]}
            for (a, y), ids in sorted(groups.items()) if len(ids) > 1]


def alert_out(a: Alert, institution_names: dict[int, str]) -> dict:
    return {"id": a.id, "institution_id": a.institution_id, "institution_name": institution_names.get(a.institution_id),
            "programme_id": a.programme_id, "rule_code": a.rule_code, "severity": a.severity, "message": a.message,
            "evidence": json.loads(a.evidence_json), "evidence_json": a.evidence_json,
            "upload_id": a.upload_id, "created_at": a.created_at.isoformat()}


def programme_rows(db: Session, institution_id: int) -> list[dict]:
    """One row per programme and academic year that has students (programmes with none show the latest year)."""
    students = db.query(Student).filter_by(institution_id=institution_id).all()
    years = sorted({s.academic_year for s in students})
    rows = []
    for p in db.query(Programme).filter_by(institution_id=institution_id).order_by(Programme.id):
        own_years = sorted({s.academic_year for s in students if s.programme_id == p.id}) or [years[-1] if years else "2026-27"]
        for year in own_years:
            own = [s for s in students if s.programme_id == p.id and s.academic_year == year]
            regular = sum(s.admission_type == "REGULAR" for s in own)
            rows.append({"programme_id": p.id, "code": p.code, "name": p.name, "academic_year": year,
                         "approved_intake": p.approved_intake, "supernumerary_limit": p.supernumerary_limit,
                         "enrolled_regular": regular, "enrolled_supernumerary": len(own) - regular,
                         "fill_pct": round(100 * regular / p.approved_intake),
                         "flagged": sum(s.status == "FLAGGED" for s in own)})
    return rows


def _quality(db: Session, institution_id: int) -> int:
    uploads = db.query(Upload).filter_by(institution_id=institution_id, dry_run=False).all()
    return quality_score(sum(u.accepted for u in uploads), sum(u.flagged for u in uploads), sum(u.total_rows for u in uploads))


def institution_stats(db: Session, institution_id: int) -> dict:
    inst = db.get(Institution, institution_id)
    students = db.query(Student).filter_by(institution_id=institution_id).all()
    programmes = programme_rows(db, institution_id)
    quality = _quality(db, institution_id)
    cross = sum("CROSS_INSTITUTION_DUP" in s.issue_codes for s in students)   # duplicates this institution is responsible for
    alerts = db.query(Alert).filter_by(institution_id=institution_id).order_by(Alert.id.desc()).all()
    anomaly_count = sum(a.rule_code.startswith("ANOM_") for a in alerts)
    over = sum(p["enrolled_regular"] > p["approved_intake"] for p in programmes)
    names = {institution_id: inst.name}
    recent = db.query(Upload).filter_by(institution_id=institution_id, dry_run=False).order_by(Upload.id.desc()).limit(5)
    return {
        "institution": {"id": inst.id, "code": inst.code, "name": inst.name, "state": inst.state, "type": inst.type},
        "quality_score": quality,
        "risk_score": risk_score(over, anomaly_count, cross, quality),
        "programmes": programmes,
        "category_mix": {"regular": sum(s.admission_type == "REGULAR" for s in students),
                         "supernumerary": sum(s.admission_type == "SUPERNUMERARY" for s in students),
                         "nri": sum(s.nri == "Y" for s in students), "oci": sum(s.oci == "Y" for s in students),
                         "fn": sum(s.fn == "Y" for s in students)},
        "recent_uploads": [{"id": u.id, "filename": u.filename, "total_rows": u.total_rows, "accepted": u.accepted,
                            "flagged": u.flagged, "rejected": u.rejected, "created_at": u.created_at.isoformat()} for u in recent],
        "open_alerts": [alert_out(a, names) for a in alerts],
        "cross_dups": cross, "programmes_over_intake": over, "total_students": len(students),
        "flagged_students": sum(s.status == "FLAGGED" for s in students),
    }


def national_summary(db: Session) -> dict:
    institutions = db.query(Institution).order_by(Institution.id).all()
    stats = {i.id: institution_stats(db, i.id) for i in institutions}
    by_state: dict[str, dict] = {}
    comparison = []
    for i in institutions:
        intake = sum(p["approved_intake"] for p in stats[i.id]["programmes"])
        enrolled = stats[i.id]["total_students"]
        comparison.append({"institution": i.name, "intake": intake, "enrolled": enrolled})
        bucket = by_state.setdefault(i.state, {"state": i.state, "intake": 0, "enrolled": 0})
        bucket["intake"] += intake
        bucket["enrolled"] += enrolled
    ranking = sorted(({"institution_id": i.id, "name": i.name, "risk_score": stats[i.id]["risk_score"],
                       "quality_score": stats[i.id]["quality_score"], "alerts": len(stats[i.id]["open_alerts"])}
                      for i in institutions), key=lambda r: (-r["risk_score"], r["name"]))
    uploads = db.query(Upload).filter_by(dry_run=False).all()
    return {"cards": {"institutions": len(institutions), "students": db.query(Student).count(),
                      "flagged": db.query(Student).filter_by(status="FLAGGED").count(),
                      "rejected_rows": sum(u.rejected for u in uploads),
                      "open_critical_alerts": db.query(Alert).filter_by(severity="CRITICAL").count(),
                      "cross_duplicates": len(list_duplicates(db))},
            "by_state": sorted(by_state.values(), key=lambda s: s["state"]),
            "risk_ranking": ranking, "intake_vs_enrolment": comparison}


def refresh_institution_alerts(db: Session, institution_id: int) -> None:
    """Delete and recompute this institution's ANOM_* alerts. INTAKE_EXCEEDED alerts are never touched."""
    db.query(Alert).filter(Alert.institution_id == institution_id, Alert.rule_code.like("ANOM_%")).delete(synchronize_session=False)
    codes = {p.id: p.code for p in db.query(Programme)}
    own = db.query(Student).filter_by(institution_id=institution_id).all()
    students = [{"programme_code": codes[s.programme_id], "admission_type": s.admission_type, "nri": s.nri, "oci": s.oci,
                 "fn": s.fn, "admission_date": s.admission_date.isoformat(), "status": s.status} for s in own]
    peer_shares = []
    for other in db.query(Institution).filter(Institution.id != institution_id):
        rows = db.query(Student).filter_by(institution_id=other.id).all()
        if rows:
            peer_shares.append(sum("Y" in (s.nri, s.oci, s.fn) for s in rows) / len(rows))
    uploads = [{"total_rows": u.total_rows, "rejected": u.rejected}
               for u in db.query(Upload).filter_by(institution_id=institution_id, dry_run=False).order_by(Upload.id)]
    alerts = detect_institution_anomalies(students, [], median(peer_shares) if peer_shares else 0.0, uploads)
    # Cluster alerts go to the institution holding the flagged (later) records, not to the original enrolment.
    flagged = {(s.apaar_id, s.academic_year) for s in own if "CROSS_INSTITUTION_DUP" in s.issue_codes}
    pairs = [{"institution_ids": [institution_id, x["id"]]}
             for d in list_duplicates(db) if (d["apaar_id"], d["academic_year"]) in flagged
             for x in d["institutions"] if x["id"] != institution_id]
    alerts += detect_cross_dup_clusters(pairs)
    programme_ids = {p.code: p.id for p in db.query(Programme).filter_by(institution_id=institution_id)}
    for a in alerts:
        db.add(Alert(institution_id=institution_id, programme_id=programme_ids.get(a.programme_code), rule_code=a.rule_code,
                     severity=a.severity, message=a.message, evidence_json=json.dumps(a.evidence, sort_keys=True)))
    db.commit()


def refresh_alerts_after_upload(db: Session, institution_id: int) -> None:
    """Refresh the uploading institution plus any institution that shares a duplicate with it."""
    involved = {institution_id}
    for d in list_duplicates(db):
        ids = {i["id"] for i in d["institutions"]}
        if institution_id in ids:
            involved |= ids
    for ident in sorted(involved):
        refresh_institution_alerts(db, ident)
