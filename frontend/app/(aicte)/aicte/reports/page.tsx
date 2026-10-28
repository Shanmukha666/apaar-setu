"use client";
import { useState } from "react";
import AppShell from "@/components/AppShell";
import { RoleGuard } from "@/components/RoleGuard";
import { Btn, ErrorBox, Loading, PageHeader, Panel } from "@/components/common";
import { downloadEnrolmentCsv, getInstitutions } from "@/lib/api/aicte";
import { saveBlob } from "@/lib/api/client";
import { useAsync } from "@/lib/useAsync";

export default function ReportsPage() {
  const [instId, setInstId] = useState<number>(1);
  const [year, setYear] = useState<string>("2026-27");
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState("");
  const institutions = useAsync("reports-institutions", getInstitutions);

  async function handleDownload() {
    setDownloading(true);
    setError("");
    try {
      const blob = await downloadEnrolmentCsv(instId, year);
      saveBlob(blob, `AICTE_Enrolment_${instId}_${year}.csv`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to download report");
    } finally {
      setDownloading(false);
    }
  }

  return (
    <RoleGuard roles={["aicte_officer"]}>
      <AppShell>
        <PageHeader
          title="Statutory Regulatory Reports"
          subtitle="Generate and export official AICTE institutional compliance and student-level enrolment reports in CSV format."
        />

        <div className="grid gap-6 lg:grid-cols-3">
          <Panel title="Export Enrolment Register" className="lg:col-span-2">
            <p className="text-xs text-slate-500 mb-4">
              Exports the complete student-level admission register for any approved institution and academic year, including APAAR IDs, admission categories, and flag diagnostics.
            </p>

            {institutions.loading ? (
              <Loading text="Loading institutions..." />
            ) : institutions.error ? (
              <ErrorBox message={institutions.error} />
            ) : (
              <div className="space-y-4">
                <div className="grid gap-3 sm:grid-cols-2">
                  <div>
                    <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-600 mb-1">
                      Institution
                    </label>
                    <select
                      className="w-full rounded-xl border border-slate-200 p-2.5 text-xs font-semibold text-slate-800 outline-none"
                      value={instId}
                      onChange={(e) => setInstId(Number(e.target.value))}
                    >
                      {(institutions.data ?? []).map((i) => (
                        <option key={i.id} value={i.id}>
                          {i.code} — {i.name} ({i.state})
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-600 mb-1">
                      Academic Year
                    </label>
                    <select
                      className="w-full rounded-xl border border-slate-200 p-2.5 text-xs font-semibold text-slate-800 outline-none"
                      value={year}
                      onChange={(e) => setYear(e.target.value)}
                    >
                      <option value="2026-27">2026-27 (Current)</option>
                      <option value="2027-28">2027-28</option>
                      <option value="2025-26">2025-26</option>
                    </select>
                  </div>
                </div>

                {error && <ErrorBox message={error} />}

                <div className="pt-2">
                  <Btn disabled={downloading} onClick={handleDownload}>
                    {downloading ? "Generating CSV Report..." : "📥 Download Official Enrolment CSV"}
                  </Btn>
                </div>
              </div>
            )}
          </Panel>

          <Panel title="Statutory Assurance">
            <div className="space-y-3 text-xs text-slate-600">
              <div className="rounded-xl border border-emerald-200 bg-emerald-50/70 p-3 text-emerald-950">
                <p className="font-bold">Formula Injection Guarded</p>
                <p className="text-[11px] mt-0.5 opacity-80">
                  All exported cells with leading arithmetic symbols are escaped with apostrophes (`_safe()`) to eliminate spreadsheet execution vulnerabilities.
                </p>
              </div>

              <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 text-slate-700">
                <p className="font-bold">DPDP & AICTE Compliance</p>
                <p className="text-[11px] mt-0.5 opacity-80">
                  Includes validation issue codes (`issue_codes`) to immediately cross-verify students flagged for duplicate enrollment or excess intake.
                </p>
              </div>
            </div>
          </Panel>
        </div>
      </AppShell>
    </RoleGuard>
  );
}
