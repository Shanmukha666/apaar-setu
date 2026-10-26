export type Role = "institution_admin" | "aicte_officer" | "verifier" | "sys_admin";
export interface User { id: number; email: string; name: string; role: Role; institution_id: number | null }
export interface LoginResponse { access_token: string; token_type: string; user: User }
export interface ValidationIssue { code: string; severity: "ERROR" | "WARNING"; field: string; message: string }
export interface UploadRowResult { row_number: number; apaar_id: string; status: "ACCEPTED" | "FLAGGED" | "REJECTED"; issues: ValidationIssue[] }
export interface UploadResult { upload_id: number | null; dry_run: boolean; total_rows: number; accepted: number; flagged: number; rejected: number; rows: UploadRowResult[] }
export interface StudentRow { apaar_id: string; student_ref: string; name: string; dob: string; gender: string; category: string; programme_code: string; academic_year: string; admission_date: string; admission_type: string; nri: string; oci: string; fn: string }
export interface StudentList { items: Record<string, unknown>[]; total: number; page: number; page_size: number }
export interface Institution { id: number; code: string; name: string; state: string; type: string }
export interface InstitutionSummary { institution: Institution; quality_score: number; risk_score: number; programmes: Record<string, unknown>[]; category_mix: Record<string, number>; recent_uploads: Record<string, unknown>[]; open_alerts: Record<string, unknown>[] }
export interface NationalRiskRow { institution_id: number; name: string; risk_score: number; quality_score: number; alerts: number }
export interface NationalIntakeRow { institution: string; intake: number; enrolled: number }
export interface NationalDashboard { cards: Record<string, number>; by_state: { state: string; intake: number; enrolled: number }[]; risk_ranking: NationalRiskRow[]; intake_vs_enrolment: NationalIntakeRow[] }
export interface Alert { id: number; institution_id: number; rule_code: string; severity: string; message: string; evidence_json: string }
export interface Duplicate { apaar_id: string; academic_year: string; institutions: { id: number; name: string }[] }
export interface AuditList { items: Record<string, unknown>[]; total: number; page: number; page_size: number }
export interface AuditVerification { valid: boolean; checked: number; broken_at: number | null }
export interface Consent { apaar_id: string; granted: boolean; purpose: string }
export interface IssuedRecord { token: string; verify_url: string; qr_png_base64: string; payload: Record<string, unknown> }
export interface VerifyResponse { valid: boolean; reason: string | null; consent_granted: boolean; record: Record<string, unknown> | null }
export interface ApaarPerson { apaar_id: string; name: string; dob: string; status: "ACTIVE" | "INACTIVE" }
