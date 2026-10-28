"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { logout, useAuth } from "@/lib/auth";
import type { Role } from "@/lib/types";

const NAV: Record<Role, [string, string][]> = {
  institution_admin: [
    ["Institutional Overview", "/institution/dashboard"],
    ["Ingest & Validate", "/institution/upload"],
    ["Student Registry", "/institution/students"],
  ],
  aicte_officer: [
    ["National Overview", "/aicte/dashboard"],
    ["Anomaly Alerts", "/aicte/alerts"],
    ["Regulatory Reports", "/aicte/reports"],
    ["Audit Trail", "/aicte/audit"],
  ],
  verifier: [
    ["Credential Verification", "/verify"],
  ],
  sys_admin: [
    ["Security Audit", "/aicte/audit"],
  ],
};

const ROLE_LABELS: Record<Role, string> = {
  institution_admin: "Institution Admin",
  aicte_officer: "AICTE Regulatory Officer",
  verifier: "Credential Verifier",
  sys_admin: "System Administrator",
};

export default function AppShell({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const links = user ? NAV[user.role] : [];

  return (
    <div className="min-h-screen bg-slate-50/70 bg-grid-pattern text-slate-900 flex flex-col font-sans">
      {/* Top Banner indicating official statutory portal styling */}
      <div className="bg-[#0f172a] text-slate-300 px-6 py-1 text-[11px] font-medium tracking-wide flex justify-between items-center border-b border-slate-800">
        <div className="flex items-center gap-3">
          <span className="inline-block w-2 h-2 rounded-full bg-emerald-400"></span>
          <span>APAAR-Setu Academic Registry · Prototype (Not an official Government of India system)</span>
        </div>
        <div className="flex items-center gap-4 text-slate-400">
          <span>Smart India Hackathon 2026</span>
          <span className="bg-slate-800 text-amber-300 font-mono px-2 py-0.5 rounded text-[10px] font-semibold">SYNTHETIC REGISTRY</span>
        </div>
      </div>

      {/* Main Navigation Header */}
      <header className="sticky top-0 z-40 bg-white/95 backdrop-blur-md border-b border-slate-200/90 shadow-sm px-6 py-3.5 transition-all">
        <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-6">
            <Link href="/" className="flex items-center gap-2.5 group">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-[#1e3a8a] to-[#2563eb] text-white flex items-center justify-center font-black text-sm shadow-sm group-hover:scale-105 transition">
                AS
              </div>
              <div>
                <span className="font-extrabold text-lg text-slate-900 tracking-tight flex items-center gap-1.5">
                  APAAR-Setu
                  <span className="text-[10px] uppercase font-bold px-1.5 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200">
                    Statutory v1.0
                  </span>
                </span>
                <p className="text-[10px] text-slate-500 font-medium -mt-0.5">Automated Enrolment Integrity Platform</p>
              </div>
            </Link>

            <nav className="hidden md:flex items-center gap-1 pl-4 border-l border-slate-200">
              {links.map(([label, href]) => {
                const active = pathname === href;
                return (
                  <Link
                    key={href}
                    href={href}
                    className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                      active
                        ? "bg-slate-100 text-slate-900 font-bold border border-slate-200 shadow-2xs"
                        : "text-slate-600 hover:text-slate-900 hover:bg-slate-50"
                    }`}
                  >
                    {label}
                  </Link>
                );
              })}
            </nav>
          </div>

          <div className="flex items-center gap-3">
            <div className="text-right hidden sm:block">
              <p className="text-xs font-bold text-slate-800 leading-tight">{user?.name || "Official User"}</p>
              <p className="text-[11px] font-medium text-slate-500">
                {user ? ROLE_LABELS[user.role] : "Authenticated"}
              </p>
            </div>
            <div className="h-7 w-[1px] bg-slate-200 hidden sm:block"></div>
            <button
              onClick={() => { logout(); router.push("/login"); }}
              className="text-xs font-semibold text-slate-600 hover:text-red-700 hover:bg-red-50 border border-slate-200 rounded-lg px-2.5 py-1.5 transition"
            >
              Sign Out
            </button>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 mx-auto w-full min-w-0 max-w-7xl px-4 sm:px-6 py-6 animate-in fade-in duration-200">
        {children}
      </main>

      {/* Statutory Footer */}
      <footer className="mt-auto border-t border-slate-200 bg-white/70 py-4 text-center text-xs text-slate-500 font-medium">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row justify-between items-center gap-2">
          <span>APAAR-Setu Platform · AICTE Autonomous Verification Prototype</span>
          <span className="text-[11px] text-slate-400">All data generated deterministically for testing under SIH26263 contract specifications</span>
        </div>
      </footer>
    </div>
  );
}
