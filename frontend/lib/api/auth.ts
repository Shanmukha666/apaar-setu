import { api } from "./client";
import type { LoginResponse, User } from "@/lib/types";
export const login = (email: string, password: string) => api<LoginResponse>("/api/auth/login", { method: "POST", body: JSON.stringify({ email, password }) });
export const me = () => api<User>("/api/auth/me");
