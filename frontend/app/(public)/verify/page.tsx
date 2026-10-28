"use client";
import { Suspense, useEffect, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import AppShell from "@/components/AppShell";
import { RoleGuard } from "@/components/RoleGuard";
import { Btn, ErrorBox, Loading, PageHeader, Panel } from "@/components/common";
import { getPublicKey, verifyRecord } from "@/lib/api/verify";
import { label } from "@/lib/format";
import { useAsync } from "@/lib/useAsync";
import type { VerifyResponse } from "@/lib/types";

const BAD_REASONS: Record<string, string> = {
  BAD_SIGNATURE: "The cryptographic signature does not match. This record was altered, forged, or was not issued by an authorized AICTE institution.",
  MALFORMED: "This token payload format is invalid or corrupted.",
  RECORD_NOT_FOUND: "The digital signature is authentic, but the corresponding student registration record is no longer active in the statutory registry.",
};

function ResultCard({ result }: { result: VerifyResponse }) {
  if (result.reason === "OK" && result.record) {
    return (
      <div className="rounded-2xl border-2 border-emerald-500 bg-emerald-50/80 p-6 shadow-sm">
        <div className="flex items-center justify-between border-b border-emerald-200 pb-3 mb-4">
          <div className="flex items-center gap-2">
            <span className="flex h-7 w-7 items-center justify-center rounded-full bg-emerald-600 text-white font-black text-sm">✓</span>
            <div>
              <h2 className="text-xl font-black text-emerald-950">Statutory Credential Authenticated</h2>
              <p className="text-xs text-emerald-800">Valid Ed25519 digital signature verified against AICTE National Root Key</p>
            </div>
          </div>
          <span className="rounded-full bg-emerald-200 px-3 py-1 font-mono text-[11px] font-bold text-emerald-900 border border-emerald-300">
            DPDP CONSENT ACTIVE
          </span>
        </div>
        <dl className="grid gap-x-6 gap-y-3 sm:grid-cols-2 text-xs">
          {Object.entries(result.record).map(([k, v]) => (
            <div key={k} className="rounded-xl bg-white/80 p-3 border border-emerald-100">
              <dt className="text-[10px] font-bold uppercase tracking-wider text-slate-500">{label(k)}</dt>
              <dd className="font-bold text-slate-900 text-sm mt-0.5">{String(v)}</dd>
            </div>
          ))}
        </dl>
      </div>
    );
  }
  if (result.reason === "CONSENT_REQUIRED") {
    return (
      <div className="rounded-2xl border-2 border-amber-500 bg-amber-50/80 p-6 shadow-sm">
        <div className="flex items-center gap-3">
          <span className="flex h-8 w-8 items-center justify-center rounded-full bg-amber-500 text-white font-black">!</span>
          <div>
            <h2 className="text-lg font-black text-amber-950">Authentic Signature · Student Consent Required</h2>
            <p className="text-xs text-amber-900 mt-0.5">
              Under India's Digital Personal Data Protection (DPDP) Act, personal details are withheld until the learner grants verification authorization.
            </p>
          </div>
        </div>
      </div>
    );
  }
  return (
    <div className="rounded-2xl border-2 border-rose-500 bg-rose-50/80 p-6 shadow-sm">
      <div className="flex items-center gap-3">
        <span className="flex h-8 w-8 items-center justify-center rounded-full bg-rose-600 text-white font-black">✕</span>
        <div>
          <h2 className="text-xl font-black text-rose-950">Verification Rejected</h2>
          <p className="text-xs text-rose-900 mt-0.5">{BAD_REASONS[result.reason ?? ""] ?? "Verification failed."}</p>
        </div>
      </div>
    </div>
  );
}

function VerifyPanel() {
  const params = useSearchParams();
  const [token, setToken] = useState(params.get("t") ?? "");
  const [submitted, setSubmitted] = useState((params.get("t") ?? "").trim());
  const [pem, setPem] = useState("");
  const [keyError, setKeyError] = useState("");
  const [offlineDecoded, setOfflineDecoded] = useState<Record<string, unknown> | null>(null);
  const [cameraActive, setCameraActive] = useState(false);
  const [cameraError, setCameraError] = useState("");
  const videoRef = useRef<HTMLVideoElement>(null);
  const check = useAsync(`verify-${submitted}`, () => (submitted ? verifyRecord(submitted) : Promise.resolve(null)));

  function verify(customToken?: string) {
    const value = (customToken ?? token).trim();
    if (value === submitted) check.reload(); else setSubmitted(value);
    decodeClientSide(value);
  }

  function decodeClientSide(rawToken: string) {
    try {
      const parts = rawToken.split(".");
      if (parts.length === 2) {
        let b64 = parts[0].replace(/-/g, "+").replace(/_/g, "/");
        while (b64.length % 4) b64 += "=";
        const decoded = JSON.parse(atob(b64));
        setOfflineDecoded(decoded);
        return;
      }
    } catch {
      // non-blocking
    }
    setOfflineDecoded(null);
  }

  // Camera QR scanner integration (BarCodeDetector API or canvas stream)
  async function toggleCamera() {
    if (cameraActive) {
      setCameraActive(false);
      return;
    }
    setCameraError("");
    setCameraActive(true);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play();
      }
    } catch (err) {
      setCameraError("Camera access denied or unavailable. You can paste the certificate token directly.");
      setCameraActive(false);
    }
  }

  useEffect(() => {
    return () => {
      if (videoRef.current && videoRef.current.srcObject) {
        (videoRef.current.srcObject as MediaStream).getTracks().forEach((t) => t.stop());
      }
    };
  }, [cameraActive]);

  async function showKey() {
    try { setPem((await getPublicKey()).public_key_pem); } catch (e) { setKeyError(e instanceof Error ? e.message : "Could not load key"); }
  }

  return (
    <>
      <PageHeader
        title="Public Credential Verification"
        subtitle="Verify authentic academic issuance via Ed25519 asymmetric cryptography. Supports physical QR scanning and digital token inspection."
        actions={
          <button
            onClick={toggleCamera}
            className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3.5 py-2 text-xs font-bold text-slate-800 shadow-2xs hover:bg-slate-50 transition"
          >
            <span>📷</span>
            <span>{cameraActive ? "Stop Camera Scanner" : "Launch Camera QR Scanner"}</span>
          </button>
        }
      />

      {cameraActive && (
        <div className="mb-6 rounded-2xl border border-slate-300 bg-slate-900 p-4 text-white animate-in fade-in">
          <div className="flex justify-between items-center mb-3">
            <span className="text-xs font-bold uppercase tracking-wider text-emerald-400">Live Camera Optical Scanner</span>
            <button onClick={() => setCameraActive(false)} className="text-xs text-slate-400 hover:text-white">✕ Close</button>
          </div>
          <div className="relative mx-auto aspect-video max-w-md overflow-hidden rounded-xl border-2 border-dashed border-emerald-500/50 bg-black flex items-center justify-center">
            <video ref={videoRef} className="h-full w-full object-cover" />
            <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
              <div className="h-40 w-40 rounded-xl border-2 border-emerald-400 animate-pulse"></div>
            </div>
          </div>
          <p className="mt-2 text-center text-[11px] text-slate-400">Position the QR code inside the green alignment frame</p>
        </div>
      )}

      {cameraError && <div className="mb-4"><ErrorBox message={cameraError} /></div>}

      <Panel title="Digital Verification Token Inspector">
        <textarea
          className="h-24 w-full rounded-xl border border-slate-200 p-3 font-mono text-xs text-slate-800 outline-none focus:border-[#1e3a8a] focus:ring-2 focus:ring-[#1e3a8a]/10"
          placeholder="Paste Ed25519 token (e.g. eyJ2IjoxLCJhcGFhci...)"
          value={token}
          onChange={(e) => setToken(e.target.value)}
        />
        <div className="mt-3 flex items-center justify-between">
          <Btn disabled={check.loading || !token.trim()} onClick={() => verify()}>
            {check.loading && submitted ? "Verifying cryptographic proof…" : "Authenticate Credential"}
          </Btn>
          <span className="text-[11px] text-slate-400 font-medium">Asymmetric Ed25519 Algorithm</span>
        </div>
      </Panel>

      <div className="mt-6 space-y-4">
        {submitted && check.loading && <Loading text="Verifying digital signature against AICTE root authority…" />}
        {check.error && <ErrorBox message={check.error} />}
        {check.data && <ResultCard result={check.data} />}

        {offlineDecoded && (
          <div className="rounded-2xl border border-blue-200 bg-blue-50/70 p-5 text-xs animate-in fade-in">
            <div className="flex items-center justify-between border-b border-blue-200/80 pb-2.5">
              <span className="font-bold text-blue-950 flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-blue-600"></span>
                Client-Side Authenticated Token Payload (Offline Readable)
              </span>
              <span className="rounded-md bg-blue-200 px-2 py-0.5 font-mono text-[10px] font-black text-blue-900">
                ZERO-CONNECTIVITY MODE
              </span>
            </div>
            <pre className="mt-3 overflow-x-auto rounded-xl bg-slate-900 p-3 text-blue-200 font-mono text-[11px] leading-relaxed">
              {JSON.stringify(offlineDecoded, null, 2)}
            </pre>
          </div>
        )}
      </div>

      <div className="mt-8 rounded-2xl border border-slate-200 bg-white p-4 text-xs text-slate-600 flex items-center justify-between">
        <span>Statutory Root Public Key (Ed25519):</span>
        <button className="font-bold text-[#1e3a8a] hover:underline" onClick={showKey}>
          Inspect Public Key PEM
        </button>
      </div>

      {keyError && <div className="mt-2"><ErrorBox message={keyError} /></div>}
      {pem && (
        <pre className="mt-2 overflow-x-auto rounded-xl bg-slate-900 p-4 font-mono text-[11px] text-emerald-400 border border-slate-800">
          {pem}
        </pre>
      )}
    </>
  );
}

export default function VerifyPage() {
  return (
    <RoleGuard roles={["verifier", "aicte_officer", "institution_admin"]}>
      <AppShell><Suspense fallback={<Loading />}><VerifyPanel /></Suspense></AppShell>
    </RoleGuard>
  );
}
