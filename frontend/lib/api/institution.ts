import { api, apiBlob } from "./client";
import type { InstitutionSummary, StudentDetail, StudentList, UploadListItem, UploadResult } from "@/lib/types";

export const getSummary = (institutionId: number) => api<InstitutionSummary>(`/api/institutions/${institutionId}/summary`);
export const getUploads = () => api<UploadListItem[]>("/api/uploads");
export const uploadFile = (file: File, dryRun: boolean) => {
  const form = new FormData();
  form.append("file", file);
  return api<UploadResult>(`/api/uploads?dry_run=${dryRun}`, { method: "POST", body: form });
};
export const downloadIssuesCsv = (uploadId: number) => apiBlob(`/api/uploads/${uploadId}/issues.csv`);
export const getStudents = (params: Record<string, string | number>) => {
  const query = new URLSearchParams(Object.entries(params).filter(([, v]) => v !== "").map(([k, v]) => [k, String(v)]));
  return api<StudentList>(`/api/students?${query}`);
};
export const getStudentRecords = (apaarId: string) => api<StudentDetail>(`/api/students/${apaarId}`);
export const getConsent = (apaarId: string) => api<{ apaar_id: string; granted: boolean; purpose: string; updated_at: string }>(`/api/consent/${apaarId}`);
export const updateConsent = (apaarId: string, granted: boolean) => api<{ apaar_id: string; granted: boolean; purpose: string; updated_at: string }>(`/api/consent/${apaarId}`, { method: "PUT", body: JSON.stringify({ granted }) });
