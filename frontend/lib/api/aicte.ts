import { api } from "./client";
import type { Alert, AuditList, AuditVerification, Duplicate, Institution, NationalDashboard } from "@/lib/types";

export const nationalDashboard = () => api<NationalDashboard>("/api/dashboard/national");
export const getInstitutions = () => api<Institution[]>("/api/institutions");
export const getAlerts = (institutionId?: string, severity?: string) => {
  const query = new URLSearchParams();
  if (institutionId) query.set("institution_id", institutionId);
  if (severity) query.set("severity", severity);
  return api<Alert[]>(`/api/alerts?${query}`);
};
export const getDuplicates = () => api<Duplicate[]>("/api/duplicates");
export const getAudit = (action: string, page: number, pageSize = 15) => {
  const query = new URLSearchParams({ page: String(page), page_size: String(pageSize) });
  if (action) query.set("action", action);
  return api<AuditList>(`/api/audit?${query}`);
};
export const verifyAuditChain = () => api<AuditVerification>("/api/audit/verify-chain");
export const simulateTamper = () => api<{ ok: boolean; tampered_id?: number; message: string }>("/api/audit/tamper-simulate", { method: "POST" });
export const restoreTamper = () => api<{ ok: boolean; restored_count: number; status: string }>("/api/audit/tamper-restore", { method: "POST" });
