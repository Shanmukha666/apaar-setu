"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { getToken, getUser } from "@/lib/auth";
import type { Role } from "@/lib/types";
export function RoleGuard({ roles, children }: { roles: Role[]; children: React.ReactNode }) {
  const router = useRouter();
  const user = getUser();
  useEffect(() => { if (!getToken() || !user || !roles.includes(user.role)) router.replace("/login"); }, [router, user, roles]);
  return user && roles.includes(user.role) ? <>{children}</> : null;
}
