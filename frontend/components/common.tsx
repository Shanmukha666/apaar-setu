import type { ReactNode } from "react";
import type { RowStatus, Severity } from "@/lib/types";

export function PageHeader({ title, subtitle, actions }: { title: string; subtitle?: string; actions?: ReactNode }) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-4 border-b border-slate-200/60 pb-4">
      <div>
        <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-900">{title}</h1>
        {subtitle && <p className="mt-1 text-sm font-medium text-slate-500 max-w-3xl">{subtitle}</p>}
      </div>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </div>
  );
}

export function Panel({ title, children, className = "" }: { title?: string; children: ReactNode; className?: string }) {
  return (
    <section className={`min-w-0 rounded-2xl border border-slate-200/90 bg-white p-5 sm:p-6 shadow-sm hover:shadow transition-shadow duration-200 ${className}`}>
      {title && (
        <div className="mb-4 flex items-center justify-between border-b border-slate-100 pb-3">
          <h2 className="font-bold text-slate-800 text-sm sm:text-base tracking-tight">{title}</h2>
        </div>
      )}
      {children}
    </section>
  );
}

const TONES = {
  neutral: "text-slate-900",
  good: "text-emerald-700",
  warn: "text-amber-600",
  bad: "text-rose-700",
} as const;

export function Stat({ label, value, tone = "neutral", hint }: { label: string; value: string | number; tone?: keyof typeof TONES; hint?: string }) {
  return (
    <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm transition hover:border-slate-300">
      <p className="text-[11px] font-bold uppercase tracking-wider text-slate-500">{label}</p>
      <p className={`mt-1.5 text-3xl font-black tracking-tight ${TONES[tone]}`}>{value}</p>
      {hint && <p className="mt-1.5 text-[11px] text-slate-400 font-medium">{hint}</p>}
    </div>
  );
}

const SEVERITY: Record<Severity, string> = {
  CRITICAL: "bg-rose-50 text-rose-800 border-rose-200 font-bold",
  WARNING: "bg-amber-50 text-amber-800 border-amber-200 font-semibold",
  INFO: "bg-blue-50 text-blue-800 border-blue-200 font-medium",
};
export function SeverityBadge({ severity }: { severity: Severity }) {
  return <span className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-[11px] ${SEVERITY[severity]}`}>{severity}</span>;
}

const STATUS: Record<RowStatus, string> = {
  ACCEPTED: "bg-emerald-50 text-emerald-800 border-emerald-200 font-bold",
  FLAGGED: "bg-amber-50 text-amber-800 border-amber-200 font-bold",
  REJECTED: "bg-rose-50 text-rose-800 border-rose-200 font-bold",
};
export function StatusBadge({ status }: { status: RowStatus }) {
  return <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-[11px] tracking-wide ${STATUS[status]}`}>{status}</span>;
}

export function Loading({ text = "Loading…" }: { text?: string }) {
  return (
    <div className="py-12 flex flex-col items-center justify-center gap-3">
      <div className="w-6 h-6 border-2 border-slate-200 border-t-[#1e3a8a] rounded-full animate-spin"></div>
      <p className="text-xs font-semibold text-slate-500">{text}</p>
    </div>
  );
}

export function ErrorBox({ message }: { message: string }) {
  return (
    <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-xs font-semibold text-rose-800 flex items-center gap-2" role="alert">
      <span>⚠</span>
      <span>{message}</span>
    </div>
  );
}

export function EvidenceChips({ evidence }: { evidence: Record<string, string | number | boolean | null> }) {
  return (
    <div className="mt-2.5 flex flex-wrap gap-1.5">
      {Object.entries(evidence).map(([key, value]) => (
        <span key={key} className="rounded-lg border border-slate-200 bg-slate-50/80 px-2 py-0.5 text-[11px] text-slate-600 font-medium">
          {key.replaceAll("_", " ")}: <strong className="text-slate-800 font-mono">{String(value)}</strong>
        </span>
      ))}
    </div>
  );
}

export function Btn({ variant = "primary", className = "", ...props }: React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary" | "secondary" | "accent" }) {
  const styles = {
    primary: "bg-gradient-to-r from-[#1e3a8a] to-[#2563eb] text-white hover:opacity-95 shadow-sm active:scale-[0.98]",
    secondary: "border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 hover:border-slate-300 shadow-2xs active:scale-[0.98]",
    accent: "bg-amber-500 text-slate-950 font-bold hover:bg-amber-400 shadow-sm",
  };
  return (
    <button
      {...props}
      className={`rounded-xl px-4 py-2 text-xs font-bold transition disabled:opacity-40 disabled:pointer-events-none ${styles[variant]} ${className}`}
    />
  );
}

export function TableWrap({ children }: { children: ReactNode }) {
  return (
    <div className="overflow-x-auto rounded-xl border border-slate-200">
      <table className="min-w-full divide-y divide-slate-200 text-left text-xs">{children}</table>
    </div>
  );
}

export const th = "bg-slate-50/80 px-3.5 py-2.5 font-bold uppercase tracking-wider text-slate-600 text-[10px]";
export const td = "px-3.5 py-2.5 text-slate-700 whitespace-nowrap";
