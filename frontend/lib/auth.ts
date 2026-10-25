import type { User } from "@/lib/types";
const TOKEN_KEY = "apaar_setu_token";
const USER_KEY = "apaar_setu_user";
export function getToken(): string | null { return typeof window === "undefined" ? null : localStorage.getItem(TOKEN_KEY); }
export function getUser(): User | null { if (typeof window === "undefined") return null; const raw = localStorage.getItem(USER_KEY); return raw ? JSON.parse(raw) as User : null; }
export function setAuth(token: string, user: User) { localStorage.setItem(TOKEN_KEY, token); localStorage.setItem(USER_KEY, JSON.stringify(user)); }
export function logout() { localStorage.removeItem(TOKEN_KEY); localStorage.removeItem(USER_KEY); }
