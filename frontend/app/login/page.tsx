"use client";

import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { login } from "@/lib/api/auth";
import { setAuth } from "@/lib/auth";
import type { Role } from "@/lib/types";

const landing: Record<Role, string> = {
  institution_admin: "/institution/dashboard", aicte_officer: "/aicte/dashboard",
  verifier: "/verify", sys_admin: "/",
};

function LoginForm() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const router = useRouter();
  const params = useSearchParams();

  async function submit(event: React.FormEvent) {
    event.preventDefault(); setBusy(true); setError("");
    try {
      const response = await login(email, password);
      setAuth(response.access_token, response.user);
      router.push(params.get("next") || landing[response.user.role]);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Login failed");
    } finally { setBusy(false); }
  }
  const demo = (address: string) => { setEmail(address); setPassword("Demo@123"); };
  return <main className="mx-auto mt-16 max-w-md rounded-xl border bg-white p-6 shadow-sm">
    <h1 className="text-2xl font-bold text-[#1e3a8a]">APAAR-Setu</h1>
    <p className="mb-5 text-sm text-slate-500">Prototype - synthetic data only</p>
    <form onSubmit={submit} className="space-y-3">
      <input className="w-full rounded border p-2" placeholder="Email" value={email} onChange={(event) => setEmail(event.target.value)} />
      <input className="w-full rounded border p-2" type="password" placeholder="Password" value={password} onChange={(event) => setPassword(event.target.value)} />
      {error && <p className="text-sm text-red-700">{error}</p>}
      <button disabled={busy} className="w-full rounded bg-[#1e3a8a] p-2 text-white">{busy ? "Signing in..." : "Sign in"}</button>
    </form>
    <section className="mt-6"><h2 className="font-medium">Demo accounts</h2><div className="mt-2 flex flex-wrap gap-2">
      {[["Institution admin", "inst1@demo.in"], ["AICTE officer", "aicte@demo.in"], ["Verifier", "verifier@demo.in"]].map(([name, address]) =>
        <button key={address} onClick={() => demo(address)} className="rounded border px-2 py-1 text-sm">{name}</button>)}
    </div></section>
  </main>;
}

export default function LoginPage() {
  return <Suspense fallback={<p className="p-6">Loading login...</p>}><LoginForm /></Suspense>;
}
