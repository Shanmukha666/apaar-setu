"use client";
import Link from "next/link";
import { useState } from "react";
import AppShell from "@/components/AppShell";
import { RoleGuard } from "@/components/RoleGuard";
import { Btn, ErrorBox, Loading, PageHeader, Panel, StatusBadge, TableWrap, td, th } from "@/components/common";
import { getConsent, getStudents, updateConsent } from "@/lib/api/institution";
import { useAsync } from "@/lib/useAsync";

const PAGE_SIZE = 15;

function ConsentSimulatorModal({ apaarId, onClose }: { apaarId: string | null; onClose: () => void }) {
  const [granted, setGranted] = useState<boolean | null>(null);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState("");
  const consentAsync = useAsync(`consent-${apaarId}`, async () => {
    if (!apaarId) return null;
    const res = await getConsent(apaarId);
    setGranted(res.granted);
    return res;
  });

  if (!apaarId) return null;

  async function handleToggle() {
    if (granted === null) return;
    setSaving(true);
    setMsg("");
    try {
      const res = await updateConsent(apaarId!, !granted);
      setGranted(res.granted);
      setMsg(`Consent updated: ${res.granted ? "GRANTED (Full access on /verify)" : "REVOKED (Masked on /verify)"}`);
    } catch {
      setMsg("Failed to update consent");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-sm animate-in fade-in">
      <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl border border-slate-200">
        <div className="flex justify-between items-start border-b border-slate-100 pb-3 mb-4">
          <div>
            <span className="rounded bg-indigo-50 text-indigo-700 text-[10px] font-bold uppercase px-2 py-0.5">
              DPDP Compliance Engine
            </span>
            <h2 className="text-base font-bold text-slate-900 mt-1">Learner Consent Preferences</h2>
            <p className="text-xs font-mono text-slate-500">APAAR ID: {apaarId}</p>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-700">✕</button>
        </div>

        {consentAsync.loading ? (
          <Loading text="Loading consent status..." />
        ) : (
          <div className="space-y-4 text-xs">
            <div className={`p-4 rounded-xl border ${granted ? "border-emerald-200 bg-emerald-50 text-emerald-900" : "border-amber-200 bg-amber-50 text-amber-900"}`}>
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-bold text-sm">{granted ? "Verification Consent Granted" : "Verification Consent Withheld"}</p>
                  <p className="text-[11px] opacity-80 mt-0.5">
                    {granted ? "Employers & verifiers can see name and academic records." : "Personal details are hidden during public Ed25519 QR scans."}
                  </p>
                </div>
                <button
                  disabled={saving}
                  onClick={handleToggle}
                  className={`rounded-xl px-3 py-1.5 font-bold shadow-sm transition ${
                    granted ? "bg-amber-600 text-white hover:bg-amber-700" : "bg-emerald-600 text-white hover:bg-emerald-700"
                  }`}
                >
                  {saving ? "Updating..." : granted ? "Revoke Consent" : "Grant Consent"}
                </button>
              </div>
            </div>

            {msg && <p className="text-xs font-semibold text-indigo-700 text-center">{msg}</p>}

            <div className="rounded-xl bg-slate-50 p-3 text-[11px] text-slate-500 border border-slate-200">
              <strong>Statutory Note:</strong> Changes are immediately committed to the immutable audit log (`CONSENT_CHANGED`) and reflected across the verification engine.
            </div>
          </div>
        )}

        <div className="mt-5 flex justify-end">
          <button onClick={onClose} className="rounded-xl bg-slate-100 px-4 py-2 text-xs font-bold text-slate-700 hover:bg-slate-200">
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

function StudentsPageContent() {
  const [q, setQ] = useState("");
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);
  const [simulatingConsent, setSimulatingConsent] = useState<string | null>(null);
  const { data, error, loading } = useAsync(`students-${q}-${status}-${page}`, () => getStudents({ q, status, page, page_size: PAGE_SIZE }));
  const pages = data ? Math.max(1, Math.ceil(data.total / PAGE_SIZE)) : 1;

  return (
    <>
        <ConsentSimulatorModal apaarId={simulatingConsent} onClose={() => setSimulatingConsent(null)} />
        <PageHeader title="Student Registry & Verification" subtitle="Search and inspect institutional students, issue certificates, and simulate DPDP consent." />
        <Panel>
          <div className="mb-4 flex flex-wrap gap-3">
            <input className="min-w-64 flex-1 rounded-xl border border-slate-200 px-3.5 py-2 text-xs font-medium text-slate-800 outline-none focus:border-[#1e3a8a] focus:ring-2 focus:ring-[#1e3a8a]/10" placeholder="Search by name, student ID or 12-digit APAAR ID…" value={q}
              onChange={(e) => { setQ(e.target.value); setPage(1); }} />
            <select className="rounded-xl border border-slate-200 px-3 py-2 text-xs font-semibold text-slate-700 outline-none" value={status} onChange={(e) => { setStatus(e.target.value); setPage(1); }}>
              <option value="">All Statuses</option>
              <option value="ACCEPTED">Accepted Only</option>
              <option value="FLAGGED">Flagged with Issues</option>
            </select>
          </div>
          {loading ? <Loading /> : error || !data ? <ErrorBox message={error ?? "No data"} /> : (
            <>
              <TableWrap>
                <thead>
                  <tr>
                    <th className={th}>APAAR ID</th>
                    <th className={th}>Student Ref</th>
                    <th className={th}>Name</th>
                    <th className={th}>Programme</th>
                    <th className={th}>Year</th>
                    <th className={th}>Validation Status</th>
                    <th className={th}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((s) => (
                    <tr key={s.id} className="hover:bg-slate-50/80 transition">
                      <td className={`${td} font-mono font-bold text-slate-800`}>{s.apaar_id}</td>
                      <td className={td}>{s.student_ref}</td>
                      <td className={`${td} font-bold text-slate-900`}>{s.name}</td>
                      <td className={td}><span className="rounded bg-slate-100 px-1.5 py-0.5 font-mono text-[11px] text-slate-700">{s.programme_code}</span></td>
                      <td className={td}>{s.academic_year}</td>
                      <td className={td}>
                        <StatusBadge status={s.status} />
                        {s.issue_codes.length > 0 && <p className="mt-1 font-mono text-[10px] text-amber-700">{s.issue_codes.join(", ")}</p>}
                      </td>
                      <td className={td}>
                        <div className="flex items-center gap-2">
                          <Link className="rounded-lg bg-blue-50 px-2.5 py-1 text-[11px] font-bold text-[#1e3a8a] border border-blue-200 hover:bg-blue-100 transition shadow-2xs" href={`/certificate/${s.apaar_id}?year=${s.academic_year}`}>
                            Certificate 📜
                          </Link>
                          <button
                            onClick={() => setSimulatingConsent(s.apaar_id)}
                            className="rounded-lg bg-slate-50 px-2 py-1 text-[11px] font-semibold text-slate-600 border border-slate-200 hover:bg-slate-100 transition"
                            title="Manage DPDP consent permissions"
                          >
                            Consent 🔒
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </TableWrap>
              {data.items.length === 0 && <p className="py-8 text-center text-xs text-slate-500">No student records match the active search filter.</p>}
              <div className="mt-4 flex items-center justify-between text-xs">
                <span className="text-slate-500 font-medium">{data.total} registered records · Page {page} of {pages}</span>
                <span className="flex gap-2">
                  <Btn variant="secondary" disabled={page <= 1} onClick={() => setPage(page - 1)}>Previous</Btn>
                  <Btn variant="secondary" disabled={page >= pages} onClick={() => setPage(page + 1)}>Next</Btn>
                </span>
              </div>
            </>
          )}
        </Panel>
    </>
  );
}

export default function StudentsPage() {
  return (
    <RoleGuard roles={["institution_admin"]}>
      <AppShell><StudentsPageContent /></AppShell>
    </RoleGuard>
  );
}
