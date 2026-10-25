import { api } from "./client";
import type { VerifyResponse } from "@/lib/types";
export const verifyRecord = (token: string) => api<VerifyResponse>("/api/verify", { method: "POST", body: JSON.stringify({ token }) });
export const publicKey = () => api<{algorithm:string;public_key_pem:string}>("/api/verify/public-key");
