"use client";

import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { login } from "@/lib/api/auth";
import { setAuth } from "@/lib/auth";
import type { Role } from "@/lib/types";

const landing: Record<Role, string> = {
  institution_admin: "/institution/dashboard",
  aicte_officer: "/aicte/dashboard",
  verifier: "/verify",
  sys_admin: "/aicte/audit",
};

const DEMO_PRESETS = [
  { label: "Institution Admin", email: "inst1@demo.in", desc: "Deccan Inst. of Tech (DIT001)", role: "institution_admin", color: "border-blue-200 bg-blue-50/50 hover:bg-blue-100/60 text-blue-900" },
  { label: "AICTE Regulatory Officer", email: "aicte@demo.in", desc: "National oversight & audit", role: "aicte_officer", color: "border-amber-200 bg-amber-50/50 hover:bg-amber-100/60 text-amber-900" },
  { label: "Public Verifier", email: "verifier@demo.in", desc: "Autonomous credential checker", role: "verifier", color: "border-emerald-200 bg-emerald-50/50 hover:bg-emerald-100/60 text-emerald-900" },
];

function LoginForm() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const router = useRouter();
  const params = useSearchParams();

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const response = await login(email, password);
      setAuth(response.access_token, response.user);
      const next = params.get("next");
      router.push(next && next.startsWith("/") && !next.startsWith("//") ? next : landing[response.user.role]);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Authentication failed");
    } finally {
      setBusy(false);
    }
  }

  const fillPreset = (address: string) => {
    setEmail(address);
    setPassword("Demo@123");
  };

  return (
    <div className="min-h-screen bg-slate-50 bg-grid-pattern flex flex-col justify-center items-center p-4">
      <div className="w-full max-w-md">
        {/* Gov Header emblem */}
        <div className="text-center mb-6">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-tr from-[#1e3a8a] to-[#2563eb] text-white font-black text-lg shadow-md mb-3">
            AS
          </div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight">APAAR-Setu</h1>
          <p className="text-xs text-slate-500 font-medium mt-1">
            Ministry of Education · AICTE Autonomous Verification Portal
          </p>
        </div>

        {/* Login Card */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-xl shadow-slate-200/50 p-6 sm:p-8">
          <div className="border-b border-slate-100 pb-4 mb-5">
            <h2 className="text-base font-bold text-slate-800">Secure Sign In</h2>
            <p className="text-xs text-slate-500 mt-0.5">Use your statutory institutional or officer credentials</p>
          </div>

          <form onSubmit={submit} className="space-y-4">
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1.5">Official Email</label>
              <input
                className="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-sm text-slate-800 focus:border-[#1e3a8a] focus:ring-2 focus:ring-[#1e3a8a]/10 outline-none transition"
                placeholder="name@demo.in"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1.5">Password</label>
              <input
                className="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-sm text-slate-800 focus:border-[#1e3a8a] focus:ring-2 focus:ring-[#1e3a8a]/10 outline-none transition"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>

            {error && (
              <div className="rounded-xl border border-red-200 bg-red-50 p-3 text-xs font-medium text-red-700 animate-in fade-in">
                {error}
              </div>
            )}

            <button
              disabled={busy}
              className="w-full rounded-xl bg-gradient-to-r from-[#1e3a8a] to-[#2563eb] py-2.5 text-sm font-bold text-white shadow-md hover:opacity-95 disabled:opacity-50 transition active:scale-[0.99]"
            >
              {busy ? "Authenticating session..." : "Access Portal"}
            </button>
          </form>

          {/* Quick Demo Credentials */}
          <div className="mt-6 pt-5 border-t border-slate-100">
            <p className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-2.5">
              1-Click Demo Evaluation Profiles
            </p>
            <div className="space-y-2">
              {DEMO_PRESETS.map((preset) => (
                <button
                  key={preset.email}
                  type="button"
                  onClick={() => fillPreset(preset.email)}
                  className={`w-full text-left p-2.5 rounded-xl border transition flex items-center justify-between text-xs ${preset.color}`}
                >
                  <div>
                    <span className="font-bold block">{preset.label}</span>
                    <span className="text-[11px] opacity-75">{preset.desc}</span>
                  </div>
                  <span className="font-mono text-[10px] font-semibold bg-white/70 px-2 py-0.5 rounded shadow-2xs">
                    {preset.email}
                  </span>
                </button>
              ))}
            </div>
            <p className="text-[10px] text-center text-slate-400 mt-3 font-medium">Default password for demo: <code className="font-mono font-bold text-slate-600">Demo@123</code></p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center text-sm text-slate-500 font-medium">Preparing secure gateway...</div>}>
      <LoginForm />
    </Suspense>
  );
}
