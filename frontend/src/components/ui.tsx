import type { ReactNode } from "react";

export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <div className={`rounded-xl border border-slate-200 bg-white p-5 shadow-sm ${className}`}>
      {children}
    </div>
  );
}

export function Stat({ label, value }: { label: string; value: ReactNode }) {
  return (
    <Card className="text-center">
      <div className="text-3xl font-semibold text-brand">{value}</div>
      <div className="mt-1 text-sm text-slate-500">{label}</div>
    </Card>
  );
}

export function Spinner({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="flex items-center gap-2 text-slate-500" role="status">
      <span className="h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-brand" />
      {label}
    </div>
  );
}

export function Banner({ kind, children }: { kind: "error" | "info" | "warn"; children: ReactNode }) {
  const styles: Record<string, string> = {
    error: "border-red-200 bg-red-50 text-red-700",
    info: "border-sky-200 bg-sky-50 text-sky-700",
    warn: "border-amber-200 bg-amber-50 text-amber-800",
  };
  return <div className={`rounded-lg border px-4 py-3 text-sm ${styles[kind]}`}>{children}</div>;
}

export function Disclaimer() {
  return (
    <p className="mt-4 text-xs text-slate-400">
      AI-generated research communication — not medical advice. Summaries may contain errors; verify
      against the source document.
    </p>
  );
}
