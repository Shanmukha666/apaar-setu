"use client";

import { useEffect, useState } from "react";
import AppShell from "@/components/AppShell";
import { RoleGuard } from "@/components/RoleGuard";
import { uploadFile, uploads } from "@/lib/api/institution";
import type { UploadResult } from "@/lib/types";

type Upload = { id: number; filename: string; dry_run: boolean; total_rows: number; accepted: number; flagged: number; rejected: number };

function UploadPageContent() {
  const [file, setFile] = useState<File>(); const [result, setResult] = useState<UploadResult>(); const [past, setPast] = useState<Upload[]>([]); const [error, setError] = useState(""); const [busy, setBusy] = useState(false);
  const refresh = () => uploads().then((rows) => setPast(rows as Upload[])).catch((caught: Error) => setError(caught.message));
  useEffect(() => { void refresh(); }, []);
  async function submit(dryRun: boolean) { if (!file) { setError("Choose a CSV file first."); return; } setBusy(true); setError(""); try { setResult(await uploadFile(file, dryRun)); refresh(); } catch (caught) { setError(caught instanceof Error ? caught.message : "Upload failed"); } finally { setBusy(false); } }
  return <div className="space-y-6"><div><h1 className="text-2xl font-bold text-[#1e3a8a]">Upload student data</h1><p className="text-slate-600">Validate before saving. Only synthetic demo data is accepted.</p></div>
    <section className="rounded-xl border bg-white p-5 shadow-sm"><input accept=".csv,text/csv" type="file" onChange={(event) => setFile(event.target.files?.[0])}/><a className="ml-4 text-sm text-[#1e3a8a] underline" href="/sample_upload.csv" download>Download sample CSV</a><div className="mt-4 flex gap-3"><button disabled={busy} onClick={() => submit(true)} className="rounded border border-[#1e3a8a] px-4 py-2 text-[#1e3a8a]">Validate only</button><button disabled={busy} onClick={() => submit(false)} className="rounded bg-[#1e3a8a] px-4 py-2 text-white">Upload</button></div>{error && <p className="mt-3 text-red-700">{error}</p>}</section>
    {result && <section className="rounded-xl border bg-white p-5 shadow-sm"><h2 className="font-semibold">{result.dry_run ? "Validation result" : "Upload result"}</h2><div className="mt-3 grid gap-3 sm:grid-cols-3">{[["Accepted", result.accepted, "text-green-700"], ["Flagged", result.flagged, "text-amber-700"], ["Rejected", result.rejected, "text-red-700"]].map(([label, value, colour]) => <div key={String(label)} className="rounded border p-3"><p className="text-sm text-slate-500">{label}</p><p className={`text-2xl font-semibold ${colour}`}>{value}</p></div>)}</div>{result.rows.length > 0 && <div className="mt-4 overflow-x-auto"><table className="w-full text-left text-sm"><thead><tr className="border-b"><th className="p-2">Row</th><th>APAAR ID</th><th>Status</th><th>Issues</th></tr></thead><tbody>{result.rows.map((row) => <tr key={row.row_number} className="border-b"><td className="p-2">{row.row_number}</td><td>{row.apaar_id || "—"}</td><td>{row.status}</td><td>{row.issues.map((issue) => <p key={issue.code}><b>{issue.code}</b>: {issue.message}</p>)}</td></tr>)}</tbody></table></div>}</section>}
    <section className="rounded-xl border bg-white p-5 shadow-sm"><h2 className="mb-3 font-semibold">Past uploads</h2><div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead><tr className="border-b"><th className="p-2">File</th><th>Mode</th><th>Rows</th><th>Accepted</th><th>Flagged</th><th>Rejected</th></tr></thead><tbody>{past.map((item) => <tr key={item.id} className="border-b"><td className="p-2">{item.filename}</td><td>{item.dry_run ? "Dry run" : "Uploaded"}</td><td>{item.total_rows}</td><td>{item.accepted}</td><td>{item.flagged}</td><td>{item.rejected}</td></tr>)}</tbody></table></div></section>
  </div>;
}

export default function UploadPage() { return <RoleGuard roles={["institution_admin"]}><AppShell><UploadPageContent /></AppShell></RoleGuard>; }
