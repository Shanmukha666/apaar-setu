"use client";

import { Bar, BarChart, CartesianGrid, Cell, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import AppShell from "@/components/AppShell";
import { RoleGuard } from "@/components/RoleGuard";
import { ErrorBox, Loading } from "@/components/common";
import { getSummary } from "@/lib/api/institution";
import { useAuth } from "@/lib/auth";
import { useAsync } from "@/lib/useAsync";

type Programme = { code: string; academic_year: string; approved_intake: number; enrolled_regular: number; enrolled_supernumerary: number; fill_pct: number; flagged: number };
type Alert = { id: number; rule_code: string; severity: string; message: string };
type Summary = { institution: { name: string }; quality_score: number; risk_score: number; programmes: Programme[]; category_mix: Record<string, number>; recent_uploads: { id: number; filename: string; total_rows: number; accepted: number; flagged: number; rejected: number }[]; open_alerts: Alert[] };

function severityClass(severity: string) { return severity === "CRITICAL" ? "bg-red-100 text-red-800" : severity === "WARNING" ? "bg-amber-100 text-amber-800" : "bg-blue-100 text-blue-800"; }

function Dashboard() {
  const { user, ready } = useAuth();
  const institutionId = user?.institution_id ?? 1;
  const { data, error, loading } = useAsync(
    `summary-${institutionId}`,
    () => getSummary(institutionId)
  );

  if (!ready || loading) return <Loading text="Loading dashboard..." />;
  if (error || !data) return <ErrorBox message={error ?? "Failed to load dashboard data."} />;

  const typedData = data as unknown as Summary;
  // One bar group per programme AND academic year; capacity is judged per year. Red = over approved intake.
  const chartData = typedData.programmes.map((programme) => ({ ...programme, label: `${programme.code.split("-")[1]} ${programme.academic_year ?? ""}`.trim() }));
  const total = typedData.programmes.reduce((sum, programme) => sum + programme.enrolled_regular + programme.enrolled_supernumerary, 0);
  const flagged = typedData.programmes.reduce((sum, programme) => sum + programme.flagged, 0);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-[#1e3a8a]">{typedData.institution.name}</h1>
        <p className="text-slate-600">Institution data quality and enrolment overview</p>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[["Data quality", typedData.quality_score], ["Risk score", typedData.risk_score], ["Total enrolled", total], ["Flagged records", flagged]].map(([label, value]) => (
          <section key={String(label)} className="rounded-xl border bg-white p-4 shadow-sm">
            <p className="text-sm text-slate-500">{label}</p>
            <p className="text-3xl font-semibold text-[#1e3a8a]">{value}</p>
          </section>
        ))}
      </div>
      <section className="rounded-xl border bg-white p-5 shadow-sm">
        <h2 className="mb-3 font-semibold">Approved intake and regular enrolment</h2>
        <div className="h-80">
          <ResponsiveContainer>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3"/>
              <XAxis dataKey="label" interval={0} tick={{ fontSize: 11 }}/>
              <YAxis/>
              <Tooltip/>
              <Legend/>
              <Bar dataKey="approved_intake" fill="#1e3a8a" name="Approved" isAnimationActive={false}/>
              <Bar dataKey="enrolled_regular" fill="#f59e0b" name="Regular enrolled" isAnimationActive={false}>
                {chartData.map((row) => <Cell key={row.label} fill={row.enrolled_regular > row.approved_intake ? "#dc2626" : "#f59e0b"}/>)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </section>
      <section className="rounded-xl border bg-white p-5 shadow-sm">
        <h2 className="mb-3 font-semibold">Open alerts</h2>
        {typedData.open_alerts.length ? (
          <ul className="space-y-2">
            {typedData.open_alerts.map((alert) => (
              <li key={alert.id} className="rounded border p-3">
                <span className={`mr-2 rounded px-2 py-1 text-xs font-medium ${severityClass(alert.severity)}`}>{alert.severity}</span>
                {alert.message}
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-slate-500">No open alerts.</p>
        )}
      </section>
      <section className="rounded-xl border bg-white p-5 shadow-sm">
        <h2 className="mb-3 font-semibold">Recent uploads</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b text-slate-500">
                <th className="p-2">File</th>
                <th>Rows</th>
                <th>Accepted</th>
                <th>Flagged</th>
                <th>Rejected</th>
              </tr>
            </thead>
            <tbody>
              {typedData.recent_uploads.map((upload) => (
                <tr key={upload.id} className="border-b">
                  <td className="p-2">{upload.filename}</td>
                  <td>{upload.total_rows}</td>
                  <td>{upload.accepted}</td>
                  <td>{upload.flagged}</td>
                  <td>{upload.rejected}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

export default function InstitutionDashboardPage() {
  return (
    <RoleGuard roles={["institution_admin"]}>
      <AppShell>
        <Dashboard />
      </AppShell>
    </RoleGuard>
  );
}
