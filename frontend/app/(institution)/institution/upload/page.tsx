"use client";
import { useRef, useState } from "react";
import AppShell from "@/components/AppShell";
import { RoleGuard } from "@/components/RoleGuard";
import { Btn, ErrorBox, Loading, PageHeader, Panel, Stat, StatusBadge, TableWrap, td, th } from "@/components/common";
import { downloadIssuesCsv, getUploads, uploadFile } from "@/lib/api/institution";
import { saveBlob } from "@/lib/api/client";
import { formatTime } from "@/lib/format";
import { useAsync } from "@/lib/useAsync";
import type { RowStatus, UploadResult } from "@/lib/types";

type Filter = "ALL" | RowStatus;
const DEMO_FILES = [
  ["demo_clean.csv", "20 valid rows"], ["demo_messy.csv", "30 rows, one of every error type"], ["demo_overflow.csv", "95 rows into a programme of 90"],
];

function UploadPageContent() {
  const fileInput = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [previewRows, setPreviewRows] = useState<string[][]>([]);
  const [headerValid, setHeaderValid] = useState<boolean | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<UploadResult | null>(null);
  const [filter, setFilter] = useState<Filter>("ALL");
  const history = useAsync("uploads", getUploads);

  const EXPECTED_HEADER = ["apaar_id","student_ref","name","dob","gender","category","programme_code","academic_year","admission_date","admission_type","nri","oci","fn"];

  async function handleFileSelect(selectedFile: File | null) {
    setFile(selectedFile);
    setResult(null);
    setError("");
    setPreviewRows([]);
    setHeaderValid(null);

    if (!selectedFile) return;

    try {
      const text = await selectedFile.slice(0, 4096).text();
      const lines = text.split(/\r?\n/).filter((l) => l.trim().length > 0);
      if (lines.length > 0) {
        const header = lines[0].split(",").map((c) => c.trim().replace(/^"|"$/g, ""));
        const matches = header.length === EXPECTED_HEADER.length && header.every((h, i) => h === EXPECTED_HEADER[i]);
        setHeaderValid(matches);

        const sample = lines.slice(1, 4).map((l) => l.split(",").map((c) => c.trim().replace(/^"|"$/g, "")));
        setPreviewRows(sample);
      }
    } catch {
      // Non-blocking preview fail
    }
  }

  async function run(dryRun: boolean) {
    if (!file) { setError("Choose a CSV file first."); return; }
    setBusy(true); setError(""); setResult(null); setFilter("ALL");
    try {
      setResult(await uploadFile(file, dryRun));
      if (!dryRun) history.reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setBusy(false);
    }
  }

  async function downloadReport(id: number) {
    try { saveBlob(await downloadIssuesCsv(id), `upload_${id}_issues.csv`); }
    catch (e) { setError(e instanceof Error ? e.message : "Download failed"); }
  }

  const rows = result?.rows.filter((r) => filter === "ALL" || r.status === filter) ?? [];
  return (
    <>
        <PageHeader title="Upload student data" subtitle="CSV with the APAAR ID as the key. Use “Validate only” to test a file without saving anything." />
        <Panel>
          <div className="flex flex-wrap items-center gap-3">
            <input ref={fileInput} type="file" accept=".csv,text/csv" className="text-sm"
              onChange={(e) => handleFileSelect(e.target.files?.[0] ?? null)} />
            <Btn variant="secondary" disabled={busy || !file} onClick={() => run(true)}>Validate only (dry run)</Btn>
            <Btn disabled={busy || !file} onClick={() => run(false)}>Upload</Btn>
          </div>

          {file && headerValid !== null && (
            <div className={`mt-3 rounded-lg border p-3 text-xs ${headerValid ? "border-green-300 bg-green-50 text-green-800" : "border-amber-300 bg-amber-50 text-amber-800"}`}>
              <div className="flex items-center gap-2 font-semibold">
                <span>{headerValid ? "✔ CSV Header Format Verified (13 contract columns matched)" : "⚠ CSV Header Warning: columns might not match standard contract"}</span>
              </div>
              {previewRows.length > 0 && (
                <div className="mt-2 overflow-x-auto">
                  <p className="font-semibold text-slate-600 mb-1">Pre-flight preview (first {previewRows.length} rows):</p>
                  <table className="min-w-full divide-y divide-slate-200 border border-slate-200 bg-white">
                    <tbody>
                      {previewRows.map((row, idx) => (
                        <tr key={idx} className="divide-x divide-slate-100">
                          {row.slice(0, 7).map((val, cIdx) => (
                            <td key={cIdx} className="px-2 py-1 font-mono text-[11px] text-slate-700">{val}</td>
                          ))}
                          {row.length > 7 && <td className="px-2 py-1 text-[11px] text-slate-400">+{row.length - 7} more</td>}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
          <p className="mt-3 text-sm text-slate-600">
            Need a file? <a className="text-[#1e3a8a] underline" href="/sample_upload.csv" download>Download the sample CSV</a>, or try a demo file:
          </p>
          <ul className="mt-1 flex flex-wrap gap-x-5 gap-y-1 text-sm">
            {DEMO_FILES.map(([name, note]) => (
              <li key={name}><a className="text-[#1e3a8a] underline" href={`/demo/${name}`} download>{name}</a> <span className="text-slate-500">({note})</span></li>
            ))}
          </ul>
        </Panel>

        {busy && <Loading text="Validating…" />}
        {error && <div className="mt-4"><ErrorBox message={error} /></div>}

        {result && (
          <Panel className="mt-5" title={result.dry_run ? "Dry run result (nothing was saved)" : `Upload #${result.upload_id} saved`}>
            <div className="grid grid-cols-3 gap-3">
              <Stat label="Accepted" value={result.accepted} tone="good" />
              <Stat label="Flagged" value={result.flagged} tone="warn" />
              <Stat label="Rejected" value={result.rejected} tone="bad" />
            </div>
            <div className="mt-4 flex flex-wrap items-center gap-2">
              {(["ALL", "REJECTED", "FLAGGED", "ACCEPTED"] as Filter[]).map((f) => (
                <button key={f} onClick={() => setFilter(f)}
                  className={`rounded-full border px-3 py-1 text-xs ${filter === f ? "border-[#1e3a8a] bg-[#1e3a8a] text-white" : "border-slate-300"}`}>{f}</button>
              ))}
              {result.upload_id !== null && (
                <Btn variant="secondary" className="ml-auto" onClick={() => downloadReport(result.upload_id as number)}>Download error report</Btn>
              )}
            </div>
            <div className="mt-3">
              <TableWrap>
                <thead><tr><th className={th}>Row</th><th className={th}>APAAR ID</th><th className={th}>Status</th><th className={th}>Issues</th></tr></thead>
                <tbody>
                  {rows.map((r) => (
                    <tr key={r.row_number}>
                      <td className={td}>{r.row_number}</td>
                      <td className={`${td} font-mono`}>{r.apaar_id || "—"}</td>
                      <td className={td}><StatusBadge status={r.status} /></td>
                      <td className={td}>
                        {r.issues.length === 0 ? <span className="text-slate-400">none</span> : r.issues.map((i) => (
                          <p key={i.code}><code className="text-xs font-semibold">{i.code}</code> <span className="text-slate-600">{i.message}</span></p>
                        ))}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </TableWrap>
              {rows.length === 0 && <p className="py-4 text-center text-sm text-slate-500">No rows in this filter.</p>}
            </div>
          </Panel>
        )}

        <Panel className="mt-5" title="Past uploads">
          {history.loading ? <Loading /> : history.error ? <ErrorBox message={history.error} /> : (
            <TableWrap>
              <thead><tr><th className={th}>#</th><th className={th}>File</th><th className={th}>Type</th><th className={th}>Rows</th><th className={th}>OK</th><th className={th}>Flag</th><th className={th}>Rej</th><th className={th}>When</th><th className={th}></th></tr></thead>
              <tbody>
                {(history.data ?? []).map((u) => (
                  <tr key={u.id}>
                    <td className={td}>{u.id}</td><td className={td}>{u.filename}</td>
                    <td className={td}>{u.dry_run ? <span className="text-slate-500">dry run</span> : "saved"}</td>
                    <td className={td}>{u.total_rows}</td><td className={td}>{u.accepted}</td><td className={td}>{u.flagged}</td><td className={td}>{u.rejected}</td>
                    <td className={td}>{formatTime(u.created_at)}</td>
                    <td className={td}>{u.flagged + u.rejected > 0 && <button className="text-[#1e3a8a] underline" onClick={() => downloadReport(u.id)}>error report</button>}</td>
                  </tr>
                ))}
              </tbody>
            </TableWrap>
          )}
        </Panel>
    </>
  );
}

/** Data hooks live in the Content component so nothing is fetched until the role guard has approved the session. */
export default function UploadPage() {
  return (
    <RoleGuard roles={["institution_admin"]}>
      <AppShell><UploadPageContent /></AppShell>
    </RoleGuard>
  );
}
