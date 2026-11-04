import { useState } from "react";
import type React from "react";
import { api } from "../lib/api";
import { useAsync } from "../hooks/useAsync";
import { Banner, PageHeader, Spinner } from "../components/ui";
import { loadPrefs, savePrefs } from "../lib/prefs";

export function Settings() {
  const backends = useAsync(() => api.backends(), []);
  const [prefs, setPrefs] = useState(loadPrefs());
  const [saved, setSaved] = useState(false);

  function update<K extends keyof typeof prefs>(key: K, value: (typeof prefs)[K]) {
    const next = { ...prefs, [key]: value };
    setPrefs(next);
    savePrefs(next);
    setSaved(true);
  }

  const providers = backends.data?.backends.filter((b) => b.kind === "provider") ?? [];

  return (
    <div className="mx-auto max-w-2xl space-y-10">
      <PageHeader title="Settings">Model providers, defaults, and data handling.</PageHeader>

      <Group
        title="Hosted providers"
        footer="Keys are configured on the server through environment variables and are never sent to or stored in the browser. You can also supply a key per request in the live demo; it is used once and never stored."
      >
        {backends.loading && (
          <div className="px-5 py-3">
            <Spinner />
          </div>
        )}
        {backends.error && (
          <div className="p-3">
            <Banner kind="error">{backends.error}</Banner>
          </div>
        )}
        {providers.map((p) => (
          <div key={p.spec} className="flex items-center justify-between gap-4 px-5 py-3 text-sm">
            <span className="font-medium text-ink">{p.spec}</span>
            <span
              className={`flex items-center gap-1.5 text-[0.8125rem] ${
                p.available ? "text-accent" : "text-ink-3"
              }`}
            >
              <span
                aria-hidden="true"
                className={`h-1.5 w-1.5 rounded-full ${p.available ? "bg-accent" : "bg-ink-3"}`}
              />
              {p.available ? "Configured" : p.detail ?? "No key"}
            </span>
          </div>
        ))}
        {backends.data && providers.length === 0 && (
          <p className="px-5 py-3 text-sm text-ink-3">No hosted providers are registered.</p>
        )}
      </Group>

      <Group
        title="Summarization defaults"
        footer={saved ? "Saved to this browser." : "Stored locally in this browser only."}
      >
        <label className="flex items-center justify-between gap-4 px-5 py-3">
          <span className="text-sm font-medium text-ink">Default backend</span>
          <input
            className="input max-w-56 text-right"
            value={prefs.backend}
            onChange={(e) => update("backend", e.target.value)}
          />
        </label>
        <label className="block px-5 py-3.5">
          <span className="mb-2 flex justify-between text-sm font-medium text-ink">
            Default max new tokens
            <span className="tabular-nums text-ink-2">{prefs.maxTokens}</span>
          </span>
          <input
            type="range"
            min={64}
            max={1024}
            step={32}
            value={prefs.maxTokens}
            onChange={(e) => update("maxTokens", Number(e.target.value))}
          />
        </label>
      </Group>

      <Group title="Privacy and retention">
        <p className="px-5 py-4 text-sm leading-relaxed text-ink-2">
          Uploaded PDFs are processed into text for summarization and are not added to the public
          dataset. Provider API keys are never logged. For a public deployment, review the data
          provenance and retention notes in the repository before enabling uploads.
        </p>
      </Group>
    </div>
  );
}

function Group({
  title,
  footer,
  children,
}: {
  title: string;
  footer?: string;
  children: React.ReactNode;
}) {
  return (
    <section className="space-y-2">
      <h2 className="px-5 text-sm font-semibold text-ink-2">{title}</h2>
      <div className="card grouped overflow-hidden">{children}</div>
      {footer && <p className="footnote px-5 text-ink-3">{footer}</p>}
    </section>
  );
}
