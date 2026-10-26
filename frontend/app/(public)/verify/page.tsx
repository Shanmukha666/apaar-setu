"use client";
import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import AppShell from "@/components/AppShell";
import { RoleGuard } from "@/components/RoleGuard";
import { verifyRecord } from "@/lib/api/verify";
import type { VerifyResponse } from "@/lib/types";

function VerifyForm() {
  const params = useSearchParams();
  const initialToken = params.get("t") || "";
  const [token, setToken] = useState(initialToken);
  const [result, setResult] = useState<VerifyResponse>();
  const [error, setError] = useState("");
  const verify = () => verifyRecord(token).then(setResult).catch((err) => setError(err.message));
  useEffect(() => {
    if (initialToken) verifyRecord(initialToken).then(setResult).catch((err: Error) => setError(err.message));
  }, [initialToken]);
  return <><h1>Verify record</h1><textarea className="w-full border p-2" value={token} onChange={(event) => setToken(event.target.value)} /><button className="mt-2 rounded bg-[#1e3a8a] px-3 py-2 text-white" onClick={verify}>Verify</button>{error && <p className="text-red-700">{error}</p>}{result && <section className={result.valid ? "mt-4 rounded border border-green-500 p-4" : "mt-4 rounded border border-red-500 p-4"}><h2>{result.reason === "OK" ? "VERIFIED" : result.reason === "CONSENT_REQUIRED" ? "Signature valid - student consent required, details hidden" : "NOT VERIFIED"}</h2>{result.record && <pre>{JSON.stringify(result.record, null, 2)}</pre>}<p>Signature checked with Ed25519 public key</p></section>}</>;
}

export default function Verify() {
  return <RoleGuard roles={["verifier", "aicte_officer", "institution_admin"]}><AppShell><Suspense fallback={<p>Loading verification…</p>}><VerifyForm /></Suspense></AppShell></RoleGuard>;
}
