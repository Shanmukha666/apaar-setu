# APAAR-Setu Contract v1 (source of truth; only the Lead changes it)

## 1. Roles and demo accounts (password for all: Demo@123)
Roles: institution_admin, aicte_officer, verifier, sys_admin
aicte@demo.in (aicte_officer), sysadmin@demo.in (sys_admin), verifier@demo.in (verifier),
inst1@demo.in ... inst5@demo.in (institution_admin, institution_id 1..5)

## 2. Fixed institutions (ids fixed; synthetic)
1 DIT001 Deccan Institute of Technology, Telangana, Engineering
2 CCE002 Coastal College of Engineering, Andhra Pradesh, Engineering
3 HSM003 Himalaya School of Management, Uttarakhand, PGDM
4 MIP004 Malwa Institute of Pharmacy, Madhya Pradesh, Pharmacy
5 KPT005 Kaveri Polytechnic, Karnataka, Polytechnic
Each has 3 programmes, code format <INSTCODE>-<SHORT> (e.g. DIT001-CSE). approved_intake 60..120; supernumerary_limit = ceil(10% of intake).

## 3. Tables (SQLAlchemy models, snake_case)
users(id, email unique, password_hash, name, role, institution_id null)
institutions(id, code unique, name, state, type)
programmes(id, institution_id, code unique, name, level, duration_years, approved_intake, supernumerary_limit)
students(id, apaar_id, institution_id, programme_id, student_ref, name, dob, gender, category, academic_year, admission_date, admission_type, nri, oci, fn, status, issue_codes, upload_id, created_at, updated_at); UNIQUE(apaar_id, institution_id, academic_year)
uploads(id, institution_id, user_id, filename, source 'csv'|'api', dry_run, total_rows, accepted, flagged, rejected, created_at)
validation_issues(id, upload_id, row_number, apaar_id, field, code, severity 'ERROR'|'WARNING', message)
alerts(id, institution_id, programme_id null, rule_code, severity 'INFO'|'WARNING'|'CRITICAL', message, evidence_json, upload_id null, created_at)
audit_log(id, ts, actor_id, actor_email, actor_role, action, entity_type, entity_id, details_json, prev_hash, hash)
consents(id, apaar_id unique, granted bool, purpose, updated_at)
apaar_registry(apaar_id PK, name, dob, status 'ACTIVE'|'INACTIVE')   (mock national registry)

## 4. Input row format (CSV header and JSON keys, exactly)
apaar_id,student_ref,name,dob,gender,category,programme_code,academic_year,admission_date,admission_type,nri,oci,fn
dob/admission_date: YYYY-MM-DD | gender: M/F/O | category: GEN/OBC/SC/ST/EWS | academic_year: like 2026-27
admission_type: REGULAR/SUPERNUMERARY | nri/oci/fn: Y/N
APAAR ID = 12 digits; the 12th digit is a Luhn check digit over the first 11 (MOCK rule, label it as mock).

## 5. Validation rules (status per row: ACCEPTED | FLAGGED | REJECTED)
ERROR codes -> REJECTED (row not stored):
APAAR_MISSING, APAAR_FORMAT (not 12 digits), APAAR_CHECKSUM, DUP_IN_FILE (2nd+ occurrence of same apaar_id+academic_year in one file), PROGRAMME_UNKNOWN (code not belonging to this institution), FIELD_INVALID (bad enum/date/Y-N), DATE_FUTURE (admission_date after today), INCONSISTENT_FLAGS (oci=Y and fn=Y), APAAR_NOT_FOUND, APAAR_INACTIVE
WARNING codes -> FLAGGED (row stored, issue_codes saved):
NAME_MISMATCH (vs registry, case/space-insensitive), DOB_MISMATCH, CROSS_INSTITUTION_DUP (same apaar_id stored at another institution in the same academic_year), INTAKE_EXCEEDED (REGULAR rows beyond approved_intake for programme+year), SUPERNUMERARY_EXCEEDED (SUPERNUMERARY rows beyond supernumerary_limit)
Capacity counts follow file order. Re-uploading an existing (apaar_id, institution, academic_year) is an UPDATE and does not double count.
Quality score (institution) = round(100 * (accepted + 0.5*flagged) / total_rows) over all non-dry-run uploads.
Anomaly rule codes: ANOM_SUPERNUMERARY_SHARE, ANOM_FOREIGN_SHARE, ANOM_DATE_BURST, ANOM_REJECT_RATE, ANOM_CROSS_DUP_CLUSTER. INTAKE_EXCEEDED also creates a CRITICAL alert.
Risk score (0-100) = min(100, 30*programmes_over_intake + 10*anomaly_alerts + 5*cross_dups + (100-quality_score)//2)

## 6. Endpoints (JSON; auth = Bearer JWT; errors = FastAPI {"detail": "..."})
GET  /api/health                                  public
POST /api/auth/login {email,password} -> {access_token, token_type, user:{id,email,name,role,institution_id}}
GET  /api/auth/me                                 any
POST /api/uploads?dry_run=bool (multipart "file") institution_admin -> UploadResult
POST /api/students/bulk?dry_run=bool {rows:[...]} institution_admin -> UploadResult
GET  /api/uploads                                 institution_admin(own) / aicte_officer(all) -> list
GET  /api/uploads/{id}                            -> UploadResult
GET  /api/uploads/{id}/issues.csv                 -> CSV file
GET  /api/students?institution_id&programme_id&status&q&page&page_size -> {items,total,page,page_size}
GET  /api/students/{apaar_id}                     institution_admin(own) / aicte_officer
PUT  /api/students/{apaar_id} {fields}            institution_admin(own); revalidates; audit logged
GET  /api/institutions                            aicte_officer, sys_admin
GET  /api/institutions/{id}/summary               -> {institution, quality_score, risk_score, programmes:[{programme_id, code, name, approved_intake, supernumerary_limit, enrolled_regular, enrolled_supernumerary, fill_pct, flagged}], category_mix:{regular,supernumerary,nri,oci,fn}, recent_uploads:[], open_alerts:[]}
GET  /api/dashboard/national                      aicte_officer -> {cards:{institutions,students,flagged,rejected_rows,open_critical_alerts,cross_duplicates}, by_state:[{state,intake,enrolled}], risk_ranking:[{institution_id,name,risk_score,quality_score,alerts}], intake_vs_enrolment:[{institution,intake,enrolled}]}
GET  /api/alerts?institution_id&severity          aicte_officer(all)/institution_admin(own)
GET  /api/duplicates                              aicte_officer -> [{apaar_id, academic_year, institutions:[{id,name}]}]
GET  /api/reports/enrolment.csv?institution_id&academic_year   aicte_officer
GET  /api/audit?action&page&page_size             aicte_officer, sys_admin
GET  /api/audit/verify-chain                      -> {valid, checked, broken_at}
GET/PUT /api/consent/{apaar_id} {granted}         institution_admin(own)/aicte_officer
POST /api/records/{apaar_id}/issue                institution_admin(own)/aicte_officer -> {token, verify_url, qr_png_base64, payload}
GET  /api/records/{apaar_id}/qr.png
POST /api/verify {token}                          verifier, aicte_officer, institution_admin -> {valid, reason, consent_granted, record|null}
GET  /api/verify/public-key
GET  /mock-apaar/v1/persons/{apaar_id}            header X-API-Key: demo-apaar-key -> {apaar_id,name,dob,status} or 404

UploadResult = {upload_id, dry_run, total_rows, accepted, flagged, rejected, rows:[{row_number, apaar_id, status, issues:[{code,severity,field,message}]}]}

## 7. Signed record
token = base64url(canonical JSON payload) + "." + base64url(Ed25519 signature). Payload: {v:1, apaar_id, student_ref, institution_code, programme_code, academic_year, status, issued_at}. Key derived deterministically from env SIGNING_SEED. QR content = {FRONTEND_URL}/verify?t=<token>. If consent not granted, /api/verify returns valid=true but record=null and reason="CONSENT_REQUIRED".

## 8. Audit actions
LOGIN, UPLOAD, UPLOAD_DRY_RUN, STUDENT_UPDATED, CONSENT_CHANGED, RECORD_ISSUED, VERIFY_ATTEMPT. hash = sha256(prev_hash + canonical JSON of the entry).
