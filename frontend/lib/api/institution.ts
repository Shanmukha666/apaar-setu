import { api } from "./client";
import type { InstitutionSummary, StudentList, UploadResult } from "@/lib/types";
export const getSummary = (id: number) => api<InstitutionSummary>(`/api/institutions/${id}/summary`);
export const getStudents = () => api<StudentList>("/api/students");
export const getUpload = (id: number) => api<UploadResult>(`/api/uploads/${id}`);
export const uploads = () => api<Record<string, unknown>[]>("/api/uploads");
export const students = (query: string) => api<StudentList>(`/api/students?${query}`);
export const uploadFile = (file: File, dryRun: boolean) => { const form=new FormData(); form.append("file",file); return api<UploadResult>(`/api/uploads?dry_run=${dryRun}`,{method:"POST",body:form}); };
