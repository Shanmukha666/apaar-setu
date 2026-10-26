"use client";

import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import AppShell from "@/components/AppShell";
import { RoleGuard } from "@/components/RoleGuard";
import { getSummary } from "@/lib/api/institution";
import { getUser } from "@/lib/auth";

type Programme = { code: string; approved_intake: number; enrolled_regular: number; enrolled_supernumerary: number; fill_pct: number; flagged: number };
type Alert = { id: number; rule_code: string; severity: string; message: string };
type Summary = { institution: { name: string }; quality_score: number; risk_score: number; programmes: Programme[]; category_mix: Record<string, number>; recent_uploads: { id: number; filename: string; total_rows: number; accepted: number; flagged: number; rejected: number }[]; open_alerts: Alert[] };

function severityClass(severity: string) { return severity === "CRITICAL" ? "bg-red-100 text-red-800" : severity === "WARNING" ? "bg-amber-100 text-amber-800" : "bg-blue-100 text-blue-800"; }

function Dashboard() {
  const [data, setData] = useState<Summary>(); const [error, setError] = useState("");
  useEffect(() => { const user = getUser(); if (user?.institution_id) getSummary(user.institution_id).then((response) => setData(response as unknown as Summary)).catch((caught: Error) => setError(caught.message)); }, []);
  if (error) return <p className="rounded border border-red-200 bg-red-50 p-4 text-red-800">{error}</p>;
  if (!data) return <p>Loading dashboard...</p>;
  const total = data.programmes.reduce((sum, programme) => sum + programme.enrolled_regular + programme.enrolled_supernumerary, 0);
  const flagged = data.programmes.reduce((sum, programme) => sum + programme.flagged, 0);
  return <div className="space-y-6"><div><h1 className="text-2xl font-bold text-[#1e3a8a]">{data.institution.name}</h1><p className="text-slate-600">Institution data quality and enrolment overview</p></div>
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">{[["Data quality", data.quality_score], ["Risk score", data.risk_score], ["Total enrolled", total], ["Flagged records", flagged]].map(([label, value]) => <section key={String(label)} className="rounded-xl border bg-white p-4 shadow-sm"><p className="text-sm text-slate-500">{label}</p><p className="text-3xl font-semibold text-[#1e3a8a]">{value}</p></section>)}</div>
    <section className="rounded-xl border bg-white p-5 shadow-sm"><h2 className="mb-3 font-semibold">Approved intake and regular enrolment</h2><div className="h-80"><ResponsiveContainer><BarChart data={data.programmes}><CartesianGrid strokeDasharray="3 3"/><XAxis dataKey="code"/><YAxis/><Tooltip/><Legend/><Bar dataKey="approved_intake" fill="#1e3a8a" name="Approved"/><Bar dataKey="enrolled_regular" fill="#f59e0b" name="Regular enrolled"/></BarChart></ResponsiveContainer></div></section>
    <section className="rounded-xl border bg-white p-5 shadow-sm"><h2 className="mb-3 font-semibold">Open alerts</h2>{data.open_alerts.length ? <ul className="space-y-2">{data.open_alerts.map((alert) => <li key={alert.id} className="rounded border p-3"><span className={`mr-2 rounded px-2 py-1 text-xs font-medium ${severityClass(alert.severity)}`}>{alert.severity}</span>{alert.message}</li>)}</ul> : <p className="text-slate-500">No open alerts.</p>}</section>
    <section className="rounded-xl border bg-white p-5 shadow-sm"><h2 className="mb-3 font-semibold">Recent uploads</h2><div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead><tr className="border-b text-slate-500"><th className="p-2">File</th><th>Rows</th><th>Accepted</th><th>Flagged</th><th>Rejected</th></tr></thead><tbody>{data.recent_uploads.map((upload) => <tr key={upload.id} className="border-b"><td className="p-2">{upload.filename}</td><td>{upload.total_rows}</td><td>{upload.accepted}</td><td>{upload.flagged}</td><td>{upload.rejected}</td></tr>)}</tbody></table></div></section>
  </div>;
}

export default function InstitutionDashboardPage() { return <RoleGuard roles={["institution_admin"]}><AppShell><Dashboard /></AppShell></RoleGuard>; }
