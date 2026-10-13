import { useState } from "react";
import { api, ApiError } from "../lib/api";
import { useAsync } from "../hooks/useAsync";
import { Banner, Card, Disclaimer, Spinner } from "../components/ui";
import type { SummarizeResponse } from "../lib/types";

const STYLES: Record<string, string> = {
  "Plain language": "Summarize this clinical trial for a non-specialist in plain language.",
  "Key results only": "In plain language, what were the key results of this clinical trial?",
  "Safety focus": "In plain language, what adverse events and safety findings were reported?",
};

export function Demo() {
  const trials = useAsync(() => api.trials({ limit: 200 }), []);
  const backends = useAsync(() => api.backends(), []);

  const [trial, setTrial] = useState("");
  const [backend, setBackend] = useState("lead");
  const [style, setStyle] = useState("Plain language");
  const [maxTokens, setMaxTokens] = useState(256);
  const [apiKey, setApiKey] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string>();
  const [result, setResult] = useState<SummarizeResponse>();

  const isProvider = ["anthropic", "openai", "gemini"].some((p) => backend.startsWith(p));

  async function generate() {
    if (!trial) {
      setError("Pick a trial first.");
      return;
    }
    setBusy(true);
    setError(undefined);
    setResult(undefined);
    try {
      const res = await api.summarize({
        trial_name: trial,
        question: STYLES[style],
        backend,
        max_new_tokens: maxTokens,
        api_key: isProvider && apiKey ? apiKey : undefined,
      });
      setResult(res);
    } catch (err) {
      const msg = err instanceof ApiError ? (err.detail ?? err.message) : String(err);
      setError(msg);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Live summarization demo</h1>
        <p className="mt-1 text-slate-600">
          Pick a stored trial, choose a model backend, and generate a plain-language summary.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="space-y-4">
          <label className="block text-sm font-medium text-slate-700">
            Clinical trial
            <select
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
              value={trial}
              onChange={(e) => setTrial(e.target.value)}
            >
              <option value="">— select a trial —</option>
              {trials.data?.items.map((t) => (
                <option key={t.protocol_id} value={t.protocol_id}>
                  {t.protocol_id} ({t.source})
                </option>
              ))}
            </select>
          </label>
          {trials.loading && <Spinner label="Loading trials…" />}
          {trials.error && <Banner kind="error">{trials.error}</Banner>}

          <label className="block text-sm font-medium text-slate-700">
            Model backend
            <select
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
              value={backend}
              onChange={(e) => setBackend(e.target.value)}
            >
              {backends.data?.backends.map((b) => (
                <option key={b.spec} value={b.spec} disabled={!b.available}>
                  {b.spec} {b.available ? "" : `— ${b.detail ?? "unavailable"}`}
                </option>
              ))}
            </select>
          </label>

          <label className="block text-sm font-medium text-slate-700">
            Style
            <select
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
              value={style}
              onChange={(e) => setStyle(e.target.value)}
            >
              {Object.keys(STYLES).map((s) => (
                <option key={s}>{s}</option>
              ))}
            </select>
          </label>

          <label className="block text-sm font-medium text-slate-700">
            Max new tokens: {maxTokens}
            <input
              type="range"
              min={64}
              max={1024}
              step={32}
              value={maxTokens}
              onChange={(e) => setMaxTokens(Number(e.target.value))}
              className="mt-1 w-full"
            />
          </label>

          {isProvider && (
            <label className="block text-sm font-medium text-slate-700">
              Provider API key (used for this request only, never stored)
              <input
                type="password"
                className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
                value={apiKey}
                placeholder="sk-…"
                onChange={(e) => setApiKey(e.target.value)}
              />
            </label>
          )}

          <button
            onClick={generate}
            disabled={busy}
            className="rounded-lg bg-brand px-4 py-2 font-medium text-white hover:bg-brand-dark disabled:opacity-50"
          >
            {busy ? "Generating…" : "Generate summary"}
          </button>
        </Card>

        <Card className="space-y-3">
          <h2 className="font-semibold text-slate-900">Result</h2>
          {busy && <Spinner label="Running the model…" />}
          {error && <Banner kind="error">{error}</Banner>}
          {!busy && !error && !result && (
            <p className="text-sm text-slate-500">The generated summary will appear here.</p>
          )}
          {result && (
            <div className="space-y-3">
              <p className="whitespace-pre-wrap text-slate-800">{result.text}</p>
              {result.warnings.length > 0 && (
                <Banner kind="warn">{result.warnings.join(" · ")}</Banner>
              )}
              <dl className="grid grid-cols-2 gap-2 text-xs text-slate-500">
                <div>model: {result.model}</div>
                <div>latency: {result.latency_s?.toFixed(3) ?? "—"}s</div>
                <div>input tokens: {result.input_tokens ?? "—"}</div>
                <div>output tokens: {result.output_tokens ?? "—"}</div>
              </dl>
              <Disclaimer />
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
