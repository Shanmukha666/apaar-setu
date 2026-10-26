"use client";

import { useEffect, useState } from "react";
import AppShell from "@/components/AppShell";
import { RoleGuard } from "@/components/RoleGuard";
import { audit, verifyAuditChain } from "@/lib/api/aicte";

type Entry = { id: number; ts: string; actor_email: string; actor_role: string; action: string; entity_type: string; hash: string };

function AuditContent() {
  const [items, setItems] = useState<Entry[]>([]); const [chain, setChain] = useState(""); const [error, setError] = useState("");
  useEffect(() => { audit().then((response) => setItems(response.items as Entry[])).catch((caught: Error) => setError(caught.message)); }, []);
  async function check() { try { const result = await verifyAuditChain(); setChain(result.valid ? `Chain intact - ${result.checked} entries verified` : `Tampering detected at entry #${result.broken_at}`); } catch (caught) { setError(caught instanceof Error ? caught.message : "Audit check failed"); } }
  return <div><h1 className="text-2xl font-bold text-[#1e3a8a]">Audit trail</h1><button onClick={check} className="my-4 rounded bg-[#1e3a8a] px-4 py-2 text-white">Verify audit chain</button>{chain && <p className="mb-3 rounded border border-green-200 bg-green-50 p-3 text-green-800">{chain}</p>}{error && <p className="text-red-700">{error}</p>}<div className="overflow-x-auto rounded-xl border bg-white"><table className="w-full text-left text-sm"><thead><tr className="border-b"><th className="p-3">Time</th><th>Actor</th><th>Role</th><th>Action</th><th>Entity</th><th>Hash</th></tr></thead><tbody>{items.map((item) => <tr key={item.id} className="border-b"><td className="p-3">{item.ts}</td><td>{item.actor_email}</td><td>{item.actor_role}</td><td>{item.action}</td><td>{item.entity_type}</td><td>{item.hash.slice(0, 12)}</td></tr>)}</tbody></table></div></div>;
}
export default function AuditPage() { return <RoleGuard roles={["aicte_officer"]}><AppShell><AuditContent /></AppShell></RoleGuard>; }
