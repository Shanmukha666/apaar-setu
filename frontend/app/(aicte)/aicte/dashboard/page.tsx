"use client";
import { Fragment, useState } from "react";
import AppShell from "@/components/AppShell";
import { RoleGuard } from "@/components/RoleGuard";
import { ErrorBox, EvidenceChips, Loading, PageHeader, Panel, SeverityBadge, Stat, TableWrap, td, th } from "@/components/common";
import IntakeChart from "@/components/aicte/IntakeChart";
import { getAlerts, getDuplicates, nationalDashboard } from "@/lib/api/aicte";
import { getSummary } from "@/lib/api/institution";
import { maskApaar } from "@/lib/format";
import { useAsync } from "@/lib/useAsync";

interface RiskModalProps {
  institution: { id: number; name: string; risk_score: number; quality_score: number; alerts: number } | null;
  onClose: () => void;
}

function RiskExplainerModal({ institution, onClose }: RiskModalProps) {
  if (!institution) return null;
  const qualityDeduction = Math.floor((100 - institution.quality_score) / 2);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-sm animate-in fade-in duration-150">
      <div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl border border-slate-100">
        <div className="flex items-center justify-between border-b pb-3">
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Risk Assessment Heuristic</span>
            <h3 className="text-lg font-bold text-slate-900">{institution.name}</h3>
          </div>
          <button onClick={onClose} className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700">✕</button>
        </div>

        <div className="mt-4 space-y-3 text-sm">
          <div className="rounded-xl bg-slate-50 p-3 font-mono text-xs text-slate-700 border border-slate-200">
            Formula: min(100, 30×over_intake + 10×anomalies + 5×cross_dups + ⌊(100-quality)/2⌋)
          </div>

          <div className="space-y-2 divide-y divide-slate-100 text-xs sm:text-sm">
            <div className="flex justify-between py-1.5">
              <span className="text-slate-600">Active Alert Count</span>
              <span className="font-semibold text-slate-900">{institution.alerts} alert(s)</span>
            </div>
            <div className="flex justify-between py-1.5">
              <span className="text-slate-600">Data Quality Score</span>
              <span className="font-semibold text-slate-900">{institution.quality_score}% (Penalty: +{qualityDeduction})</span>
            </div>
            <div className="flex justify-between py-1.5">
              <span className="text-slate-600">Risk Tier Classification</span>
              <span className={`font-bold ${institution.risk_score >= 40 ? "text-red-700" : institution.risk_score >= 15 ? "text-amber-600" : "text-green-700"}`}>
                {institution.risk_score >= 40 ? "HIGH RISK (Immediate AICTE Action)" : institution.risk_score >= 15 ? "MODERATE (Watchlist)" : "LOW RISK (Compliant)"}
              </span>
            </div>
          </div>

          <div className="mt-4 flex items-center justify-between rounded-xl bg-slate-900 p-4 text-white">
            <span className="font-medium text-slate-300">Total Calculated Risk Score</span>
            <span className="text-2xl font-black text-amber-400">{institution.risk_score} <span className="text-xs text-slate-400">/ 100</span></span>
          </div>
        </div>

        <div className="mt-5 flex justify-end">
          <button onClick={onClose} className="rounded-lg bg-slate-100 px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-200">
            Dismiss
          </button>
        </div>
      </div>
    </div>
  );
}

function ProgrammeFill({ institutionId }: { institutionId: number }) {
  const { data, error, loading } = useAsync(`inst-${institutionId}`, () => getSummary(institutionId));
  if (loading) return <Loading />;
  if (error || !data) return <ErrorBox message={error ?? "No data"} />;
  return (
    <ul className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
      {data.programmes.map((p) => (
        <li key={`${p.programme_id}-${p.academic_year}`} className="rounded-lg border border-slate-200 bg-white p-2 text-sm">
          <div className="flex justify-between"><span className="font-medium">{p.code} <span className="text-slate-500">{p.academic_year}</span></span>
            <span className={p.fill_pct > 100 ? "font-bold text-red-700" : ""}>{p.fill_pct}%</span></div>
          <div className="mt-1 h-2 rounded bg-slate-100"><div className={`h-2 rounded ${p.fill_pct > 100 ? "bg-red-600" : "bg-[#1e3a8a]"}`} style={{ width: `${Math.min(p.fill_pct, 100)}%` }} /></div>
          <p className="mt-1 text-xs text-slate-500">{p.enrolled_regular} of {p.approved_intake} regular seats</p>
        </li>
      ))}
    </ul>
  );
}

function AicteDashboardPageContent() {
  const national = useAsync("national", nationalDashboard);
  const alerts = useAsync("alerts-feed", () => getAlerts());
  const dups = useAsync("duplicates", getDuplicates);
  const [open, setOpen] = useState<number | null>(null);
  const [inspectRisk, setInspectRisk] = useState<{ id: number; name: string; risk_score: number; quality_score: number; alerts: number } | null>(null);
  const c = national.data?.cards;

  return (
    <>
        <RiskExplainerModal institution={inspectRisk} onClose={() => setInspectRisk(null)} />
        <PageHeader title="National dashboard" subtitle="Admissions, data quality and risk across AICTE-approved institutions (synthetic data)." />
        {national.loading ? <Loading text="Loading dashboard…" /> : national.error || !national.data || !c ? <ErrorBox message={national.error ?? "No data"} /> : (
          <>
            <div className="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-6">
              <Stat label="Institutions" value={c.institutions} />
              <Stat label="Students" value={c.students} />
              <Stat label="Flagged records" value={c.flagged} tone={c.flagged ? "warn" : "good"} />
              <Stat label="Rejected rows" value={c.rejected_rows} />
              <Stat label="Critical alerts" value={c.open_critical_alerts} tone={c.open_critical_alerts ? "bad" : "good"} />
              <Stat label="Cross-institution duplicates" value={c.cross_duplicates} tone={c.cross_duplicates ? "bad" : "good"} />
            </div>

            <div className="mt-5 grid gap-5 lg:grid-cols-2">
              <Panel title="Intake vs enrolment by institution">
                <IntakeChart data={national.data.intake_vs_enrolment.map((d) => ({ name: d.institution.split(" ")[0], intake: d.intake, enrolled: d.enrolled }))} />
              </Panel>
              <Panel title="By state"><IntakeChart data={national.data.by_state.map((s) => ({ name: s.state, intake: s.intake, enrolled: s.enrolled }))} /></Panel>
            </div>

            <Panel title="Institution risk ranking (click a row for programme fill)" className="mt-5">
              <TableWrap>
                <thead><tr><th className={th}>Institution</th><th className={th}>Risk score</th><th className={th}>Quality</th><th className={th}>Alerts</th></tr></thead>
                <tbody>
                  {national.data.risk_ranking.map((r) => (
                    <Fragment key={r.institution_id}>
                      <tr className="cursor-pointer hover:bg-slate-50" onClick={() => setOpen(open === r.institution_id ? null : r.institution_id)}>
                        <td className={`${td} font-medium`}>{r.name}</td>
                        <td className={td}>
                          <div className="flex items-center gap-2">
                            <div className="h-2.5 w-32 rounded bg-slate-100"><div className={`h-2.5 rounded ${r.risk_score >= 40 ? "bg-red-600" : r.risk_score >= 15 ? "bg-amber-500" : "bg-green-600"}`} style={{ width: `${Math.min(r.risk_score, 100)}%` }} /></div>
                            <button
                              onClick={(e) => { e.stopPropagation(); setInspectRisk({ id: r.institution_id, name: r.name, risk_score: r.risk_score, quality_score: r.quality_score, alerts: r.alerts }); }}
                              className="rounded border border-slate-200 bg-white px-1.5 py-0.5 text-xs font-bold text-slate-700 hover:border-slate-400 hover:bg-slate-100 transition"
                              title="Click to view explainable risk formula">
                              {r.risk_score} ℹ
                            </button>
                          </div>
                        </td>
                        <td className={td}>{r.quality_score}</td><td className={td}>{r.alerts}</td>
                      </tr>
                      {open === r.institution_id && <tr><td colSpan={4} className="bg-slate-50 p-3"><ProgrammeFill institutionId={r.institution_id} /></td></tr>}
                    </Fragment>
                  ))}
                </tbody>
              </TableWrap>
            </Panel>
          </>
        )}

        <div className="mt-5 grid gap-5 lg:grid-cols-2">
          <Panel title="Latest alerts">
            {alerts.loading ? <Loading /> : alerts.error ? <ErrorBox message={alerts.error} /> : (
              <ul className="space-y-3">
                {(alerts.data ?? []).slice(0, 8).map((a) => (
                  <li key={a.id} className="rounded-lg border border-slate-200 p-3">
                    <div className="flex flex-wrap items-center gap-2"><SeverityBadge severity={a.severity} /><span className="text-sm font-medium">{a.institution_name}</span></div>
                    <p className="mt-1 text-sm">{a.message}</p>
                    <EvidenceChips evidence={a.evidence} />
                  </li>
                ))}
              </ul>
            )}
          </Panel>
          <Panel title="Possible duplicate enrolment across institutions">
            {dups.loading ? <Loading /> : dups.error ? <ErrorBox message={dups.error} /> : (
              <TableWrap>
                <thead><tr><th className={th}>APAAR ID</th><th className={th}>Year</th><th className={th}>Institutions</th></tr></thead>
                <tbody>
                  {(dups.data ?? []).map((d) => (
                    <tr key={`${d.apaar_id}-${d.academic_year}`}>
                      <td className={`${td} font-mono`}>{maskApaar(d.apaar_id)}</td><td className={td}>{d.academic_year}</td>
                      <td className={td}>{d.institutions.map((i) => i.name).join(" & ")}</td>
                    </tr>
                  ))}
                </tbody>
              </TableWrap>
            )}
          </Panel>
        </div>
    </>
  );
}

/** Data hooks live in the Content component so nothing is fetched until the role guard has approved the session. */
export default function AicteDashboardPage() {
  return (
    <RoleGuard roles={["aicte_officer"]}>
      <AppShell><AicteDashboardPageContent /></AppShell>
    </RoleGuard>
  );
}
