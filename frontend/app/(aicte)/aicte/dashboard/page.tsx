"use client";

import { useEffect, useState } from "react";

import AppShell from "@/components/AppShell";
import { RoleGuard } from "@/components/RoleGuard";
import { alerts, duplicates, nationalDashboard } from "@/lib/api/aicte";
import type { Alert, Duplicate, NationalDashboard, NationalRiskRow } from "@/lib/types";

type DashboardView = NationalDashboard & { risk_ranking: NationalRiskRow[]; alerts: Alert[]; duplicates: Duplicate[] };

export default function AicteDashboardPage() {
  const [data, setData] = useState<DashboardView>();
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([nationalDashboard(), alerts(), duplicates()])
      .then(([dashboard, alertRows, duplicateRows]) => setData({ ...dashboard, alerts: alertRows, duplicates: duplicateRows }))
      .catch((err: Error) => setError(err.message));
  }, []);

  return <RoleGuard roles={["aicte_officer"]}><AppShell>
    {error ? <p className="text-red-700">{error}</p> : !data ? <p>Loading dashboard…</p> : <>
      <h1 className="text-2xl font-bold text-[#1e3a8a]">National dashboard</h1>
      <div className="my-4 grid grid-cols-2 gap-3 md:grid-cols-3">
        {Object.entries(data.cards as Record<string, number>).map(([key, value]) => <div key={key} className="rounded border p-3"><p className="text-sm">{key.replaceAll("_", " ")}</p><strong className="text-2xl">{value}</strong></div>)}
      </div>
      <h2 className="font-semibold">Risk ranking</h2>
      <table className="w-full text-left"><tbody>{data.risk_ranking.map((row) => <tr key={row.institution_id} className="border-b"><td>{row.name}</td><td><span className="inline-block h-2 bg-red-600" style={{ width: `${row.risk_score}px` }} /> {row.risk_score}</td><td>Quality {row.quality_score}</td></tr>)}</tbody></table>
      <h2 className="mt-5 font-semibold">Cross-institution duplicates</h2>
      {data.duplicates.map((duplicate) => <p key={duplicate.apaar_id}>••••{duplicate.apaar_id.slice(-4)} · {duplicate.academic_year} · {duplicate.institutions.map((institution) => institution.name).join(", ")}</p>)}
    </>}
  </AppShell></RoleGuard>;
}
