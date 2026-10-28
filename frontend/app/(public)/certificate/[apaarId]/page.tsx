"use client";
import { Suspense } from "react";
import { useParams, useSearchParams } from "next/navigation";
import AppShell from "@/components/AppShell";
import { RoleGuard } from "@/components/RoleGuard";
import { Btn, ErrorBox, Loading } from "@/components/common";
import { getStudentRecords } from "@/lib/api/institution";
import { issueRecord } from "@/lib/api/verify";
import { useAsync } from "@/lib/useAsync";
import type { IssuedRecord, StudentItem } from "@/lib/types";

async function load(apaarId: string, year: string | null): Promise<{ student: StudentItem; issued: IssuedRecord }> {
  const detail = await getStudentRecords(apaarId);
  // The API lists the newest academic year first; use the requested year when given.
  const student = detail.records.find((r) => r.academic_year === year) ?? detail.records[0];
  const issued = await issueRecord(apaarId, student.academic_year);
  return { student, issued };
}

function Certificate() {
  const { apaarId } = useParams<{ apaarId: string }>();
  const year = useSearchParams().get("year");
  const { data, error, loading } = useAsync(`cert-${apaarId}-${year}`, () => load(apaarId, year));
  if (loading) return <Loading text="Issuing signed record…" />;
  if (error || !data) return <ErrorBox message={error ?? "No data"} />;
  const { student, issued } = data;

  return (
    <>
      <div className="no-print mb-4 flex justify-end"><Btn variant="accent" onClick={() => window.print()}>Print certificate</Btn></div>
      <article className="relative mx-auto max-w-3xl rounded-lg border-4 border-double border-[#1e3a8a] bg-white p-8">
        <p className="mb-4 rounded bg-amber-100 p-1 text-center text-xs font-semibold text-amber-900">Synthetic data · demo only</p>
        <h1 className="text-center text-2xl font-bold text-[#1e3a8a]">Provisional Enrolment Certificate (Prototype)</h1>
        <p className="mt-6 text-center text-lg">This is to certify that</p>
        <p className="my-2 text-center text-3xl font-bold">{student.name}</p>
        <p className="text-center text-lg">
          is enrolled in <strong>{student.programme_code}</strong> at <strong>{student.institution_name}</strong>{" "}
          for the academic year <strong>{student.academic_year}</strong>.
        </p>
        <div className="mt-8 grid grid-cols-2 gap-4 rounded-lg bg-slate-50 p-4 text-center">
          <div><p className="text-xs uppercase text-slate-500">Student ID</p><p className="font-mono text-xl font-bold">{student.student_ref}</p></div>
          <div><p className="text-xs uppercase text-slate-500">APAAR ID</p><p className="font-mono text-xl font-bold">{student.apaar_id}</p></div>
        </div>
        <div className="mt-8 flex flex-col items-center">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img alt="QR code to verify this record" className="h-44 w-44" src={`data:image/png;base64,${issued.qr_png_base64}`} />
          <p className="mt-2 text-sm font-medium">Scan to verify</p>
          <p className="mt-1 max-w-full break-all text-center text-[10px] text-slate-500">{issued.verify_url}</p>
        </div>
      </article>
    </>
  );
}

export default function CertificatePage() {
  return (
    <RoleGuard roles={["institution_admin", "aicte_officer"]}>
      <AppShell><Suspense fallback={<Loading />}><Certificate /></Suspense></AppShell>
    </RoleGuard>
  );
}
