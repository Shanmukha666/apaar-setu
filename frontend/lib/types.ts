// Shapes returned by the FastAPI backend (see docs/CONTRACT.md and backend/app/routers/*.py).
export type Role = "institution_admin" | "aicte_officer" | "verifier" | "sys_admin";
export interface User { id: number; email: string; name: string; role: Role; institution_id: number | null }
export interface LoginResponse { access_token: string; token_type: string; user: User }

export type RowStatus = "ACCEPTED" | "FLAGGED" | "REJECTED";
export interface ValidationIssue { code: string; severity: "ERROR" | "WARNING"; field: string; message: string }
export interface UploadRowResult { row_number: number; apaar_id: string; status: RowStatus; issues: ValidationIssue[] }
export interface UploadResult {
  upload_id: number | null; dry_run: boolean; total_rows: number;
  accepted: number; flagged: number; rejected: number; rows: UploadRowResult[];
}
export interface UploadListItem {
  id: number; institution_id: number; filename: string; source: string; dry_run: boolean;
  total_rows: number; accepted: number; flagged: number; rejected: number; created_at: string;
}

export interface StudentItem {
  id: number; apaar_id: string; student_ref: string; name: string; dob: string; gender: string; category: string;
  academic_year: string; admission_date: string; admission_type: string; nri: string; oci: string; fn: string;
  status: RowStatus; issue_codes: string[]; institution_id: number; institution_name: string;
  programme_id: number; programme_code: string;
}
export interface StudentList { items: StudentItem[]; total: number; page: number; page_size: number }
export interface StudentDetail { apaar_id: string; records: StudentItem[] }

export interface Institution { id: number; code: string; name: string; state: string; type: string }
export type Severity = "INFO" | "WARNING" | "CRITICAL";
export interface Alert {
  id: number; institution_id: number; institution_name: string | null; programme_id: number | null;
  rule_code: string; severity: Severity; message: string;
  evidence: Record<string, string | number | boolean | null>; evidence_json: string; created_at: string;
}
export interface ProgrammeRow {
  programme_id: number; code: string; name: string; academic_year: string; approved_intake: number;
  supernumerary_limit: number; enrolled_regular: number; enrolled_supernumerary: number; fill_pct: number; flagged: number;
}
export interface RecentUpload { id: number; filename: string; total_rows: number; accepted: number; flagged: number; rejected: number; created_at: string }
export interface InstitutionSummary {
  institution: Institution; quality_score: number; risk_score: number; programmes: ProgrammeRow[];
  category_mix: { regular: number; supernumerary: number; nri: number; oci: number; fn: number };
  recent_uploads: RecentUpload[]; open_alerts: Alert[];
  cross_dups: number; programmes_over_intake: number; total_students: number; flagged_students: number;
}
export interface NationalDashboard {
  cards: { institutions: number; students: number; flagged: number; rejected_rows: number; open_critical_alerts: number; cross_duplicates: number };
  by_state: { state: string; intake: number; enrolled: number }[];
  risk_ranking: { institution_id: number; name: string; risk_score: number; quality_score: number; alerts: number }[];
  intake_vs_enrolment: { institution: string; intake: number; enrolled: number }[];
}
export interface Duplicate { apaar_id: string; academic_year: string; institutions: { id: number; name: string }[] }
export interface AuditItem {
  id: number; ts: string; actor_email: string; actor_role: string; action: string; entity_type: string; entity_id: string;
  details: Record<string, unknown>; hash: string; prev_hash: string;
}
export interface AuditList { items: AuditItem[]; total: number; page: number; page_size: number }
export interface AuditVerification { valid: boolean; checked: number; broken_at: number | null }
export interface IssuedRecord { token: string; verify_url: string; qr_png_base64: string; payload: Record<string, string> }
export interface VerifyResponse { valid: boolean; reason: string | null; consent_granted: boolean; record: Record<string, string> | null }
export interface PublicKey { algorithm: string; public_key_pem: string }
