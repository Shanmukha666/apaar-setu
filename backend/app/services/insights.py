"""Database aggregates and deterministic alert refreshes."""
import json
from statistics import median
from sqlalchemy import func
from app.models import Alert, Institution, Programme, Student, Upload
from app.services.anomaly import detect_cross_dup_clusters, detect_institution_anomalies, quality_score, risk_score

def list_duplicates(db):
    grouped={}
    for s in db.query(Student).all(): grouped.setdefault((s.apaar_id,s.academic_year),set()).add(s.institution_id)
    ids={i: n for i,n in db.query(Institution.id,Institution.name)}
    return [{"apaar_id":a,"academic_year":y,"institutions":[{"id":i,"name":ids[i]} for i in sorted(group)]} for (a,y),group in sorted(grouped.items()) if len(group)>1]

def institution_stats(db, institution_id):
    programmes=db.query(Programme).filter_by(institution_id=institution_id).all(); students=db.query(Student).filter_by(institution_id=institution_id).all()
    details=[]
    for p in programmes:
        own=[s for s in students if s.programme_id==p.id]; regular=sum(s.admission_type=="REGULAR" for s in own); sup=sum(s.admission_type=="SUPERNUMERARY" for s in own)
        details.append({"programme_id":p.id,"code":p.code,"name":p.name,"approved_intake":p.approved_intake,"supernumerary_limit":p.supernumerary_limit,"enrolled_regular":regular,"enrolled_supernumerary":sup,"fill_pct":round(100*regular/p.approved_intake) if p.approved_intake else 0,"flagged":sum(s.status=="FLAGGED" for s in own)})
    uploads=db.query(Upload).filter_by(institution_id=institution_id,dry_run=False).all(); total=sum(u.total_rows for u in uploads); quality=quality_score(sum(u.accepted for u in uploads),sum(u.flagged for u in uploads),total)
    duplicates=list_duplicates(db); cross=sum(institution_id in [x["id"] for x in d["institutions"]] for d in duplicates); alerts=db.query(Alert).filter_by(institution_id=institution_id).count()
    mix={"regular":sum(s.admission_type=="REGULAR" for s in students),"supernumerary":sum(s.admission_type=="SUPERNUMERARY" for s in students),"nri":sum(s.nri=="Y" for s in students),"oci":sum(s.oci=="Y" for s in students),"fn":sum(s.fn=="Y" for s in students)}
    over=sum(x["enrolled_regular"]>x["approved_intake"] for x in details)
    return {"programmes":details,"category_mix":mix,"quality_score":quality,"cross_dups":cross,"programmes_over_intake":over,"risk_score":risk_score(over,alerts,cross,quality)}

def refresh_institution_alerts(db,institution_id):
    db.query(Alert).filter(Alert.institution_id==institution_id,Alert.rule_code.like("ANOM_%")).delete(synchronize_session=False)
    students=db.query(Student).filter_by(institution_id=institution_id).all(); inst_students=[{"programme_code":db.get(Programme,s.programme_id).code,"admission_type":s.admission_type,"nri":s.nri,"oci":s.oci,"fn":s.fn,"admission_date":s.admission_date.isoformat(),"status":s.status} for s in students]
    shares=[]
    for other in db.query(Institution).filter(Institution.id!=institution_id):
        rows=db.query(Student).filter_by(institution_id=other.id).all(); shares.append(sum(any(getattr(s,f)=="Y" for f in("nri","oci","fn")) for s in rows)/len(rows) if rows else 0)
    uploads=[{"total_rows":u.total_rows,"rejected":u.rejected} for u in db.query(Upload).filter_by(institution_id=institution_id,dry_run=False)]
    alerts=detect_institution_anomalies(inst_students,[],median(shares) if shares else 0,uploads)
    duplicate_pairs=[]
    for d in list_duplicates(db):
        ids=[x["id"] for x in d["institutions"]]
        if institution_id in ids:
            for x in ids:
                if x!=institution_id: duplicate_pairs.append({"institution_ids":[institution_id,x]})
    alerts+=detect_cross_dup_clusters(duplicate_pairs)
    codes={p.code:p.id for p in db.query(Programme).filter_by(institution_id=institution_id)}
    for a in alerts: db.add(Alert(institution_id=institution_id,programme_id=codes.get(a.programme_code),rule_code=a.rule_code,severity=a.severity,message=a.message,evidence_json=json.dumps(a.evidence,sort_keys=True),upload_id=None))
    db.commit()
