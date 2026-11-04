import type { ReactNode } from "react";

export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <div className={`card p-5 sm:p-6 ${className}`}>{children}</div>;
}

export function PageHeader({ title, children }: { title: string; children?: ReactNode }) {
  return (
    <header className="max-w-3xl space-y-2">
      <h1 className="title-1 text-ink">{title}</h1>
      {children && <p className="text-[1.0625rem] leading-relaxed text-ink-2">{children}</p>}
    </header>
  );
}

export function Stat({
  label,
  value,
  small = false,
}: {
  label: string;
  value: ReactNode;
  small?: boolean;
}) {
  const size = small ? "text-xl" : "text-[1.75rem]";
  return (
    <div className="flex flex-col-reverse">
      <dt className="footnote text-ink-2">{label}</dt>
      <dd className={`${size} font-semibold tabular-nums tracking-[-0.02em] text-ink`}>
        {value}
      </dd>
    </div>
  );
}

export function Spinner({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="flex items-center gap-2.5 text-sm text-ink-2" role="status">
      <span className="h-4 w-4 animate-spin rounded-full border-2 border-line border-t-accent" />
      {label}
    </div>
  );
}

export function Banner({ kind, children }: { kind: "error" | "info" | "warn"; children: ReactNode }) {
  const styles: Record<string, string> = {
    error:
      "border-red-200 bg-red-50 text-red-800 dark:border-red-900/60 dark:bg-red-950/40 dark:text-red-200",
    info: "border-line bg-sunken text-ink-2",
    warn:
      "border-amber-200 bg-amber-50 text-amber-900 dark:border-amber-900/60 dark:bg-amber-950/40 dark:text-amber-100",
  };
  return (
    <div
      role={kind === "error" ? "alert" : undefined}
      className={`rounded-xl border px-4 py-3 text-sm ${styles[kind]}`}
    >
      {children}
    </div>
  );
}

export function Segmented<T extends string>({
  label,
  options,
  value,
  onChange,
}: {
  label: string;
  options: readonly T[];
  value: T;
  onChange: (v: T) => void;
}) {
  return (
    <div role="radiogroup" aria-label={label} className="segmented">
      {options.map((o) => (
        <button
          key={o}
          type="button"
          role="radio"
          aria-checked={o === value}
          onClick={() => onChange(o)}
        >
          {o}
        </button>
      ))}
    </div>
  );
}

export function Switch({
  checked,
  onChange,
  children,
}: {
  checked: boolean;
  onChange: (v: boolean) => void;
  children: ReactNode;
}) {
  return (
    <label className="flex cursor-pointer items-center justify-between gap-4 text-sm font-medium text-ink">
      {children}
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        onClick={() => onChange(!checked)}
        className="switch"
      />
    </label>
  );
}

export function Disclaimer() {
  return (
    <p className="footnote mt-4 text-ink-3">
      AI-generated research communication, not medical advice. Summaries may contain errors, so
      verify them against the source document.
    </p>
  );
}
