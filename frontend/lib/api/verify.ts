import { api } from "./client";
import type { IssuedRecord, PublicKey, VerifyResponse } from "@/lib/types";

export const verifyRecord = (token: string) =>
  api<VerifyResponse>("/api/verify", { method: "POST", body: JSON.stringify({ token }) });
export const getPublicKey = () => api<PublicKey>("/api/verify/public-key");
export const issueRecord = (apaarId: string, academicYear: string) =>
  api<IssuedRecord>(`/api/records/${apaarId}/issue?academic_year=${encodeURIComponent(academicYear)}`, { method: "POST" });
