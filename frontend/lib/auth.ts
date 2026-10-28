"use client";
// Token + user live in localStorage (prototype). Components must read them through useAuth(), never during render
// via getUser(): the server has no localStorage, so reading it in render makes server and client HTML differ
// (React hydration error #418). useAuth() reports `ready: false` until the browser has hydrated.
import { useMemo, useSyncExternalStore } from "react";
import type { Role, User } from "@/lib/types";

const TOKEN_KEY = "apaar_setu_token";
const USER_KEY = "apaar_setu_user";
const CHANGE_EVENT = "apaar-auth-change";

// True between an explicit logout and the next login, so route guards do not add a stale "?next=" to /login.
let loggedOutOnPurpose = false;
export const wasLoggedOutOnPurpose = () => loggedOutOnPurpose;

export function getToken(): string | null {
  return typeof window === "undefined" ? null : window.localStorage.getItem(TOKEN_KEY);
}

export function getUser(): User | null {
  if (typeof window === "undefined") return null;
  const raw = window.localStorage.getItem(USER_KEY);
  try { return raw ? (JSON.parse(raw) as User) : null; } catch { return null; }
}

export function setAuth(token: string, user: User): void {
  window.localStorage.setItem(TOKEN_KEY, token);
  window.localStorage.setItem(USER_KEY, JSON.stringify(user));
  loggedOutOnPurpose = false;
  window.dispatchEvent(new Event(CHANGE_EVENT));
}

export function logout(): void {
  loggedOutOnPurpose = true;
  window.localStorage.removeItem(TOKEN_KEY);
  window.localStorage.removeItem(USER_KEY);
  window.dispatchEvent(new Event(CHANGE_EVENT));
}

function subscribe(callback: () => void): () => void {
  window.addEventListener(CHANGE_EVENT, callback);
  window.addEventListener("storage", callback);
  return () => {
    window.removeEventListener(CHANGE_EVENT, callback);
    window.removeEventListener("storage", callback);
  };
}

const noopSubscribe = () => () => {};

export function useAuth(): { user: User | null; ready: boolean } {
  const raw = useSyncExternalStore(subscribe, () => window.localStorage.getItem(USER_KEY), () => null);
  const ready = useSyncExternalStore(noopSubscribe, () => true, () => false);
  const user = useMemo<User | null>(() => {
    if (!raw) return null;
    try { return JSON.parse(raw) as User; } catch { return null; }
  }, [raw]);
  return { user, ready };
}

export const LANDING: Record<Role, string> = {
  institution_admin: "/institution/dashboard",
  aicte_officer: "/aicte/dashboard",
  verifier: "/verify",
  sys_admin: "/aicte/audit",
};

export function homeFor(role: Role): string {
  return LANDING[role] ?? "/login";
}
