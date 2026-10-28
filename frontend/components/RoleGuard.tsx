"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { getToken, LANDING, useAuth, wasLoggedOutOnPurpose } from "@/lib/auth";
import type { Role } from "@/lib/types";

/** Renders children only for the allowed roles; otherwise sends the person to login (or to their own home page). */
export function RoleGuard({ roles, children }: { roles: Role[]; children: React.ReactNode }) {
  const router = useRouter();
  const { user, ready } = useAuth();
  const allowed = !!user && !!getToken() && roles.includes(user.role);

  useEffect(() => {
    if (!ready) return;
    if (!user || !getToken()) {
      // Remember where the person was going, unless they just chose to log out.
      const next = window.location.pathname + window.location.search;   // read at redirect time, client side only
      router.replace(wasLoggedOutOnPurpose() ? "/login" : `/login?next=${encodeURIComponent(next)}`);
    } else if (!roles.includes(user.role)) {
      router.replace(LANDING[user.role]);
    }
  }, [ready, user, roles, router]);

  return allowed ? <>{children}</> : <p className="py-8 text-center text-sm text-slate-500" role="status">Checking your session…</p>;
}
