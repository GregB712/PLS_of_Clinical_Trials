import { useState } from "react";
import { api } from "../lib/api";
import { useAsync } from "../hooks/useAsync";
import { Banner, Card, Spinner } from "../components/ui";
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
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Settings</h1>
        <p className="mt-1 text-slate-600">Model providers, defaults, and data handling.</p>
      </div>

      <Card className="space-y-3">
        <h2 className="font-semibold text-slate-900">Hosted providers</h2>
        <p className="text-sm text-slate-600">
          Keys are configured on the server via environment variables and are never sent to or stored
          in the browser. You can also supply a key per-request in the live demo (used once, never
          stored). This page only reports configuration status.
        </p>
        {backends.loading && <Spinner />}
        {backends.error && <Banner kind="error">{backends.error}</Banner>}
        <ul className="divide-y divide-slate-100 text-sm">
          {providers.map((p) => (
            <li key={p.spec} className="flex items-center justify-between py-2">
              <span className="text-slate-700">{p.spec}</span>
              <span
                className={`rounded-full px-2 py-0.5 text-xs ${
                  p.available ? "bg-emerald-100 text-emerald-700" : "bg-slate-100 text-slate-500"
                }`}
              >
                {p.available ? "configured" : p.detail ?? "no key"}
              </span>
            </li>
          ))}
        </ul>
      </Card>

      <Card className="space-y-3">
        <h2 className="font-semibold text-slate-900">Default summarization settings</h2>
        <p className="text-sm text-slate-600">Stored locally in your browser only.</p>
        <label className="block text-sm text-slate-700">
          Default backend
          <input
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
            value={prefs.backend}
            onChange={(e) => update("backend", e.target.value)}
          />
        </label>
        <label className="block text-sm text-slate-700">
          Default max new tokens: {prefs.maxTokens}
          <input
            type="range"
            min={64}
            max={1024}
            step={32}
            value={prefs.maxTokens}
            onChange={(e) => update("maxTokens", Number(e.target.value))}
            className="mt-1 w-full"
          />
        </label>
        {saved && <p className="text-xs text-emerald-600">Saved to this browser.</p>}
      </Card>

      <Card className="space-y-2">
        <h2 className="font-semibold text-slate-900">Privacy &amp; retention</h2>
        <p className="text-sm text-slate-600">
          Uploaded PDFs are processed into text for summarization and are not added to the public
          dataset. Provider API keys are never logged. For a public deployment, review the data
          provenance and retention notes in the repository before enabling uploads.
        </p>
      </Card>
    </div>
  );
}
