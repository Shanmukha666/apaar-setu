"use client";

import { useEffect, useState } from "react";
import AppShell from "@/components/AppShell";
import { RoleGuard } from "@/components/RoleGuard";
import { alerts } from "@/lib/api/aicte";

type Alert = { id: number; institution_id: number; rule_code: string; severity: string; message: string; evidence?: Record<string, unknown> };

function AlertsPageContent() {
  const [items, setItems] = useState<Alert[]>([]); const [severity, setSeverity] = useState(""); const [error, setError] = useState("");
  useEffect(() => { alerts().then((rows) => setItems(rows as unknown as Alert[])).catch((caught: Error) => setError(caught.message)); }, []);
  const visible = severity ? items.filter((item) => item.severity === severity) : items;
  return <div><h1 className="text-2xl font-bold text-[#1e3a8a]">Alerts</h1><select className="my-4 rounded border p-2" value={severity} onChange={(event) => setSeverity(event.target.value)}><option value="">All severities</option><option>CRITICAL</option><option>WARNING</option><option>INFO</option></select>{error && <p className="text-red-700">{error}</p>}<div className="space-y-3">{visible.map((item) => <details key={item.id} className="rounded-xl border bg-white p-4"><summary className="cursor-pointer"><span className="mr-2 font-medium">{item.severity}</span>{item.rule_code}: {item.message}</summary><pre className="mt-3 overflow-auto rounded bg-slate-50 p-3 text-xs">{JSON.stringify(item.evidence ?? {}, null, 2)}</pre></details>)}</div></div>;
}
export default function AlertsPage() { return <RoleGuard roles={["aicte_officer"]}><AppShell><AlertsPageContent /></AppShell></RoleGuard>; }
