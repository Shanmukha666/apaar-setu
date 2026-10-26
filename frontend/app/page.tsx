import Link from "next/link";

export default function Home() {
  return <main className="mx-auto flex min-h-screen max-w-5xl items-center px-6 py-16">
    <section className="grid gap-10 md:grid-cols-[1.4fr_1fr] md:items-center">
      <div><p className="mb-3 font-semibold tracking-wide text-amber-600">AICTE · SMART INDIA HACKATHON 2026</p><h1 className="text-4xl font-bold tracking-tight text-[#1e3a8a] sm:text-5xl">APAAR-Setu</h1><p className="mt-5 max-w-2xl text-lg leading-8 text-slate-700">A prototype for APAAR ID-based student-data validation, transparent enrolment monitoring, and signed record verification for AICTE-approved institutions.</p><p className="mt-3 text-sm text-slate-500">Prototype — synthetic data only. APAAR integration is mocked.</p><Link href="/login" className="mt-7 inline-block rounded-lg bg-[#1e3a8a] px-5 py-3 font-medium text-white shadow-sm">Open demo portal</Link></div>
      <aside className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"><h2 className="text-lg font-semibold text-[#1e3a8a]">What the prototype demonstrates</h2><ul className="mt-4 space-y-3 text-sm leading-6 text-slate-700"><li>APAAR-format and registry validation before records are stored.</li><li>Capacity, duplicate, data-quality, and anomaly monitoring.</li><li>Consent-aware signed certificates verified with Ed25519.</li><li>Tamper-evident audit records for every key action.</li></ul></aside>
    </section>
  </main>;
}
