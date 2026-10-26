"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import { useParams } from "next/navigation";
import AppShell from "@/components/AppShell";
import { RoleGuard } from "@/components/RoleGuard";
import { getStudent, issueRecord } from "@/lib/api/institution";

type Student = { apaar_id: string; student_ref: string; name: string; programme_name: string; academic_year: string; status: string };
type RecordData = { verify_url: string; qr_png_base64: string; payload: Record<string, unknown> };

function CertificateContent() {
  const params = useParams<{apaarId: string}>(); const apaarId = params.apaarId;
  const [student, setStudent] = useState<Student>(); const [record, setRecord] = useState<RecordData>(); const [error, setError] = useState("");
  useEffect(() => { getStudent(apaarId).then((response) => { const latest = response.items[0] as unknown as Student | undefined; if (!latest) throw new Error("Student not found"); setStudent(latest); return issueRecord(apaarId, latest.academic_year); }).then((response) => setRecord(response)).catch((caught: Error) => setError(caught.message)); }, [apaarId]);
  if (error) return <p className="rounded border border-red-200 bg-red-50 p-4 text-red-800">{error}</p>;
  if (!student || !record) return <p>Preparing certificate...</p>;
  return <article className="certificate mx-auto max-w-3xl rounded-xl border-2 border-[#1e3a8a] bg-white p-8 shadow-sm"><p className="mb-6 text-center font-semibold tracking-wide text-amber-700">SYNTHETIC DATA — DEMO ONLY</p><h1 className="text-center text-3xl font-bold text-[#1e3a8a]">Provisional Enrolment Certificate</h1><p className="mt-1 text-center text-slate-600">APAAR-Setu Prototype</p><div className="mt-8 grid gap-5 sm:grid-cols-[1fr_auto]"><div className="space-y-3"><p>This certifies the provisional enrolment of <strong>{student.name}</strong>.</p><dl className="grid grid-cols-2 gap-3"><dt className="text-slate-500">Programme</dt><dd>{student.programme_name}</dd><dt className="text-slate-500">Academic year</dt><dd>{student.academic_year}</dd><dt className="text-slate-500">Student ID</dt><dd>{student.student_ref}</dd><dt className="text-slate-500">APAAR ID</dt><dd>{student.apaar_id}</dd><dt className="text-slate-500">Status</dt><dd>{student.status}</dd></dl></div><Image className="h-40 w-40" alt="Verification QR code" src={`data:image/png;base64,${record.qr_png_base64}`} width={160} height={160} unoptimized /></div><p className="mt-8 break-all text-xs text-slate-500">Verify: {record.verify_url}</p><button onClick={() => window.print()} className="mt-6 rounded bg-[#1e3a8a] px-4 py-2 text-white print:hidden">Print certificate</button></article>;
}
export default function CertificatePage() { return <RoleGuard roles={["institution_admin", "aicte_officer"]}><AppShell><CertificateContent /></AppShell></RoleGuard>; }
