import { api } from "./client";
import type { Alert, AuditList, Institution, NationalDashboard } from "@/lib/types";
export const nationalDashboard = () => api<NationalDashboard>("/api/dashboard/national");
export const institutions = () => api<Institution[]>("/api/institutions");
export const alerts = () => api<Alert[]>("/api/alerts");
export const audit = () => api<AuditList>("/api/audit");
export const duplicates = () => api<{apaar_id:string;academic_year:string;institutions:{id:number;name:string}[]}[]>("/api/duplicates");
export const verifyAuditChain = () => api<{valid:boolean;checked:number;broken_at:number|null}>("/api/audit/verify-chain");
