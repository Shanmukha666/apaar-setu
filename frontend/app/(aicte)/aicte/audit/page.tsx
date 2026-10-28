"use client";
import { useState } from "react";
import AppShell from "@/components/AppShell";
import { RoleGuard } from "@/components/RoleGuard";
import { Btn, ErrorBox, Loading, PageHeader, Panel, TableWrap, td, th } from "@/components/common";
import { getAudit, restoreTamper, simulateTamper, verifyAuditChain } from "@/lib/api/aicte";
import { formatTime } from "@/lib/format";
import { useAsync } from "@/lib/useAsync";
import type { AuditVerification } from "@/lib/types";

const ACTIONS = ["LOGIN", "UPLOAD", "UPLOAD_DRY_RUN", "CONSENT_CHANGED", "RECORD_ISSUED", "VERIFY_ATTEMPT"];
const PAGE_SIZE = 15;

function AuditPageContent() {
  const [action, setAction] = useState("");
  const [page, setPage] = useState(1);
  const [chain, setChain] = useState<AuditVerification | null>(null);
  const [chainError, setChainError] = useState("");
  const [checking, setChecking] = useState(false);
  const [tampering, setTampering] = useState(false);
  const { data, error, loading, reload } = useAsync(`audit-${action}-${page}`, () => getAudit(action, page, PAGE_SIZE));
  const pages = data ? Math.max(1, Math.ceil(data.total / PAGE_SIZE)) : 1;

  async function checkChain() {
    setChecking(true); setChainError(""); setChain(null);
    try { setChain(await verifyAuditChain()); }
    catch (e) { setChainError(e instanceof Error ? e.message : "Check failed"); }
    finally { setChecking(false); }
  }

  async function handleTamper() {
    setTampering(true);
    try {
      await simulateTamper();
      await checkChain();
      reload();
    } catch (e) {
      setChainError(e instanceof Error ? e.message : "Simulation failed");
    } finally {
      setTampering(false);
    }
  }

  async function handleRestore() {
    setTampering(true);
    try {
      await restoreTamper();
      await checkChain();
      reload();
    } catch (e) {
      setChainError(e instanceof Error ? e.message : "Restore failed");
    } finally {
      setTampering(false);
    }
  }

  return (
    <>
        <PageHeader title="Audit trail" subtitle="Every login, upload, consent change, record issue and verification is logged in a tamper-evident hash chain."
          actions={
            <div className="flex flex-wrap items-center gap-2">
              <Btn onClick={checkChain} disabled={checking || tampering}>{checking ? "Checking…" : "Verify audit chain"}</Btn>
              <button onClick={handleTamper} disabled={checking || tampering} className="rounded-lg border border-red-500 bg-red-50 px-3 py-1.5 text-xs font-semibold text-red-700 hover:bg-red-100 transition shadow-sm">
                ⚡ Simulate DB Tamper
              </button>
              <button onClick={handleRestore} disabled={checking || tampering} className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition shadow-sm">
                ↺ Restore Chain
              </button>
            </div>
          } />
        {chainError && <ErrorBox message={chainError} />}
        {chain && (chain.valid
          ? <p className="mb-4 rounded-lg border border-green-400 bg-green-50 p-3 font-medium text-green-800" role="status">Chain intact · {chain.checked} entries verified</p>
          : <p className="mb-4 rounded-lg border border-red-400 bg-red-50 p-3 font-medium text-red-800" role="alert">Tampering detected at entry #{chain.broken_at}</p>)}
        <Panel>
          <select className="mb-3 rounded-lg border border-slate-300 p-2 text-sm" value={action} onChange={(e) => { setAction(e.target.value); setPage(1); }}>
            <option value="">All actions</option>{ACTIONS.map((a) => <option key={a}>{a}</option>)}
          </select>
          {loading ? <Loading /> : error || !data ? <ErrorBox message={error ?? "No data"} /> : (
            <>
              <TableWrap>
                <thead><tr><th className={th}>#</th><th className={th}>Time</th><th className={th}>Actor</th><th className={th}>Action</th><th className={th}>Entity</th><th className={th}>Hash</th></tr></thead>
                <tbody>
                  {data.items.map((a) => (
                    <tr key={a.id}>
                      <td className={td}>{a.id}</td><td className={td}>{formatTime(a.ts)}</td>
                      <td className={td}>{a.actor_email} <span className="text-xs text-slate-500">({a.actor_role})</span></td>
                      <td className={`${td} font-mono text-xs`}>{a.action}</td><td className={td}>{a.entity_type} {a.entity_id}</td>
                      <td className={`${td} font-mono text-xs`}>{a.hash.slice(0, 10)}…</td>
                    </tr>
                  ))}
                </tbody>
              </TableWrap>
              <div className="mt-3 flex items-center justify-between text-sm">
                <span className="text-slate-600">{data.total} entries · page {page} of {pages}</span>
                <span className="flex gap-2">
                  <Btn variant="secondary" disabled={page <= 1} onClick={() => setPage(page - 1)}>Newer</Btn>
                  <Btn variant="secondary" disabled={page >= pages} onClick={() => setPage(page + 1)}>Older</Btn>
                </span>
              </div>
            </>
          )}
        </Panel>
    </>
  );
}

/** Data hooks live in the Content component so nothing is fetched until the role guard has approved the session. */
export default function AuditPage() {
  return (
    <RoleGuard roles={["aicte_officer", "sys_admin"]}>
      <AppShell><AuditPageContent /></AppShell>
    </RoleGuard>
  );
}
