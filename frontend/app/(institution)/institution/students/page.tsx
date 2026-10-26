"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import AppShell from "@/components/AppShell";
import { RoleGuard } from "@/components/RoleGuard";
import { students } from "@/lib/api/institution";

type Student = { apaar_id: string; student_ref: string; name: string; programme_code: string; academic_year: string; status: string };
type StudentResponse = { items: Student[]; total: number; page: number; page_size: number };

function StudentsContent() {
  const [data, setData] = useState<StudentResponse>(); const [query, setQuery] = useState(""); const [status, setStatus] = useState(""); const [page, setPage] = useState(1); const [error, setError] = useState("");
  useEffect(() => { const params = new URLSearchParams({ page: String(page), page_size: "20" }); if (query) params.set("q", query); if (status) params.set("status", status); students(params.toString()).then((response) => setData(response as StudentResponse)).catch((caught: Error) => setError(caught.message)); }, [query, status, page]);
  return <div className="space-y-5"><div><h1 className="text-2xl font-bold text-[#1e3a8a]">Students</h1><p className="text-slate-600">Search the approved institutional enrolment records.</p></div><div className="flex flex-wrap gap-3"><input className="rounded border p-2" placeholder="Search name, APAAR ID, reference" value={query} onChange={(event) => { setPage(1); setQuery(event.target.value); }}/><select className="rounded border p-2" value={status} onChange={(event) => { setPage(1); setStatus(event.target.value); }}><option value="">All statuses</option><option>ACCEPTED</option><option>FLAGGED</option></select></div>{error && <p className="text-red-700">{error}</p>}{!data ? <p>Loading students...</p> : <section className="overflow-x-auto rounded-xl border bg-white shadow-sm"><table className="w-full text-left text-sm"><thead><tr className="border-b text-slate-500"><th className="p-3">Name</th><th>APAAR ID</th><th>Programme</th><th>Year</th><th>Status</th><th></th></tr></thead><tbody>{data.items.map((student) => <tr key={`${student.apaar_id}-${student.academic_year}`} className="border-b"><td className="p-3">{student.name}</td><td>{student.apaar_id}</td><td>{student.programme_code}</td><td>{student.academic_year}</td><td><span className={student.status === "FLAGGED" ? "rounded bg-amber-100 px-2 py-1 text-amber-800" : "rounded bg-green-100 px-2 py-1 text-green-800"}>{student.status}</span></td><td><Link className="text-[#1e3a8a] underline" href={`/certificate/${student.apaar_id}`}>Certificate</Link></td></tr>)}</tbody></table><div className="flex items-center justify-between p-3"><span className="text-sm text-slate-500">{data.total} records</span><div className="space-x-2"><button disabled={page === 1} onClick={() => setPage(page - 1)} className="rounded border px-2 py-1">Previous</button><button disabled={page * data.page_size >= data.total} onClick={() => setPage(page + 1)} className="rounded border px-2 py-1">Next</button></div></div></section>}</div>;
}

export default function StudentsPage() { return <RoleGuard roles={["institution_admin"]}><AppShell><StudentsContent /></AppShell></RoleGuard>; }
