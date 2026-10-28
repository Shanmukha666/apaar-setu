"use client";
import { Fragment, useState } from "react";
import AppShell from "@/components/AppShell";
import { RoleGuard } from "@/components/RoleGuard";
import { ErrorBox, Loading, PageHeader, Panel, SeverityBadge, TableWrap, td, th } from "@/components/common";
import { getAlerts, getInstitutions } from "@/lib/api/aicte";
import { formatTime } from "@/lib/format";
import { useAsync } from "@/lib/useAsync";
import type { Alert } from "@/lib/types";

function ShowCauseModal({ alert, onClose }: { alert: Alert | null; onClose: () => void }) {
  if (!alert) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-sm animate-in fade-in">
      <div className="w-full max-w-2xl rounded-2xl bg-white p-6 shadow-2xl border border-slate-200">
        <div className="border-b border-slate-200 pb-3 flex justify-between items-start">
          <div>
            <div className="flex items-center gap-2">
              <span className="rounded bg-rose-100 text-rose-800 text-[10px] font-black uppercase px-2 py-0.5">
                Statutory Notice Draft
              </span>
              <span className="text-xs text-slate-400 font-mono">REF: AICTE/REG/2026/{alert.id}</span>
            </div>
            <h2 className="text-lg font-black text-slate-900 mt-1">Form 4-B: Show-Cause Compliance Requisition</h2>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-700">✕</button>
        </div>

        <div className="mt-4 space-y-3 text-xs text-slate-700 leading-relaxed font-serif">
          <p>
            <strong>TO THE PRINCIPAL / DIRECTOR:</strong><br />
            {alert.institution_name}
          </p>

          <p>
            <strong>SUBJECT:</strong> Notice of Regulatory Anomaly Detection under Rule <code className="font-mono font-bold text-slate-900">{alert.rule_code}</code>.
          </p>

          <p className="border-l-2 border-slate-300 pl-3 italic text-slate-600">
            &ldquo;{alert.message}&rdquo;
          </p>

          <div>
            <p className="font-bold mb-1">Empirical Evidence Collected by Automated Registry:</p>
            <div className="rounded-xl bg-slate-50 p-3 font-mono text-[11px] text-slate-800 border border-slate-200">
              {JSON.stringify(alert.evidence, null, 2)}
            </div>
          </div>

          <p>
            Pursuant to AICTE Approval Process Handbook Regulations, you are hereby requested to present formal clarification or reconcile your APAAR-linked enrolments within <strong>7 working days</strong>. Failure to respond may trigger formal hearing or adjustment of approved intake quotas.
          </p>
        </div>

        <div className="mt-6 flex justify-between items-center pt-3 border-t border-slate-100 text-xs">
          <span className="text-slate-400 font-sans">Issued by AICTE Regulatory Enforcement Cell</span>
          <div className="flex gap-2 font-sans">
            <button onClick={() => window.print()} className="rounded-xl border border-slate-200 bg-white px-3 py-1.5 font-bold text-slate-700 hover:bg-slate-50">
              🖨 Print / Export PDF
            </button>
            <button onClick={onClose} className="rounded-xl bg-[#1e3a8a] px-4 py-1.5 font-bold text-white hover:bg-blue-900">
              Dismiss Notice
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function AlertsPageContent() {
  const [severity, setSeverity] = useState("");
  const [institution, setInstitution] = useState("");
  const [open, setOpen] = useState<number | null>(null);
  const [noticeAlert, setNoticeAlert] = useState<Alert | null>(null);
  const institutions = useAsync("institutions", getInstitutions);
  const { data, error, loading } = useAsync(`alerts-${severity}-${institution}`, () => getAlerts(institution, severity));

  return (
    <>
        <ShowCauseModal alert={noticeAlert} onClose={() => setNoticeAlert(null)} />
        <PageHeader title="Statutory Anomaly & Enforcement Feed" subtitle="Rule-based, tamper-evident regulatory alerts with actionable forensic evidence." />
        <Panel>
          <div className="mb-4 flex flex-wrap gap-3">
            <select className="rounded-xl border border-slate-200 p-2 text-xs font-semibold text-slate-700 outline-none" value={severity} onChange={(e) => setSeverity(e.target.value)}>
              <option value="">All Severities</option>
              <option value="CRITICAL">Critical Only</option>
              <option value="WARNING">Warnings</option>
              <option value="INFO">Informational</option>
            </select>
            <select className="rounded-xl border border-slate-200 p-2 text-xs font-semibold text-slate-700 outline-none" value={institution} onChange={(e) => setInstitution(e.target.value)}>
              <option value="">All Institutions</option>
              {(institutions.data ?? []).map((i) => <option key={i.id} value={i.id}>{i.name}</option>)}
            </select>
          </div>
          {loading ? <Loading /> : error || !data ? <ErrorBox message={error ?? "No data"} /> : (
            <>
              <TableWrap>
                <thead>
                  <tr>
                    <th className={th}>Severity</th>
                    <th className={th}>Institution</th>
                    <th className={th}>Rule Code</th>
                    <th className={th}>Violation Summary</th>
                    <th className={th}>Timestamp</th>
                    <th className={th}>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {data.map((a) => (
                    <Fragment key={a.id}>
                      <tr className="cursor-pointer hover:bg-slate-50 transition" onClick={() => setOpen(open === a.id ? null : a.id)}>
                        <td className={td}><SeverityBadge severity={a.severity} /></td>
                        <td className={`${td} font-bold text-slate-900`}>{a.institution_name}</td>
                        <td className={`${td} font-mono text-[11px] font-semibold text-slate-700`}>{a.rule_code}</td>
                        <td className={td}>{a.message}</td>
                        <td className={td}>{formatTime(a.created_at)}</td>
                        <td className={td} onClick={(e) => e.stopPropagation()}>
                          {a.severity === "CRITICAL" && (
                            <button
                              onClick={() => setNoticeAlert(a)}
                              className="rounded-lg border border-rose-300 bg-rose-50 px-2 py-1 text-[10px] font-bold text-rose-800 hover:bg-rose-100 transition shadow-2xs"
                            >
                              Generate Notice ⚖
                            </button>
                          )}
                        </td>
                      </tr>
                      {open === a.id && (
                        <tr>
                          <td colSpan={6} className="bg-slate-50 p-4 border-t border-b border-slate-200">
                            <p className="mb-2 text-[10px] font-black uppercase tracking-wider text-slate-500">Forensic Evidence Metadata</p>
                            <dl className="grid grid-cols-2 gap-x-6 gap-y-2 text-xs sm:grid-cols-4">
                              {Object.entries(a.evidence).map(([k, v]) => (
                                <div key={k} className="rounded-lg bg-white p-2 border border-slate-200">
                                  <dt className="text-[10px] font-semibold uppercase text-slate-400">{k.replaceAll("_", " ")}</dt>
                                  <dd className="font-mono font-bold text-slate-800 text-xs mt-0.5">{String(v)}</dd>
                                </div>
                              ))}
                            </dl>
                          </td>
                        </tr>
                      )}
                    </Fragment>
                  ))}
                </tbody>
              </TableWrap>
              {data.length === 0 && <p className="py-8 text-center text-xs text-slate-500">No anomaly alerts match the current regulatory filter.</p>}
            </>
          )}
        </Panel>
    </>
  );
}

export default function AlertsPage() {
  return (
    <RoleGuard roles={["aicte_officer"]}>
      <AppShell><AlertsPageContent /></AppShell>
    </RoleGuard>
  );
}
