import { useState } from "react";
import { api, ApiError } from "../lib/api";
import { useAsync } from "../hooks/useAsync";
import { Banner, Card, Disclaimer, Spinner } from "../components/ui";
import { loadPrefs } from "../lib/prefs";
import type { SummarizeResponse } from "../lib/types";

const STYLES: Record<string, string> = {
  "Plain language": "Summarize this clinical trial for a non-specialist in plain language.",
  "Key results only": "In plain language, what were the key results of this clinical trial?",
  "Safety focus": "In plain language, what adverse events and safety findings were reported?",
};

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));
const isProvider = (spec: string) =>
  ["anthropic", "openai", "gemini"].some((p) => spec.startsWith(p));

interface Outcome {
  backend: string;
  data?: SummarizeResponse;
  error?: string;
}

export function Demo() {
  const prefs = loadPrefs();
  const trials = useAsync(() => api.trials({ limit: 200 }), []);
  const backends = useAsync(() => api.backends(), []);

  const [trial, setTrial] = useState("");
  const [primary, setPrimary] = useState(prefs.backend);
  const [compare, setCompare] = useState(false);
  const [selected, setSelected] = useState<string[]>([]);
  const [style, setStyle] = useState("Plain language");
  const [maxTokens, setMaxTokens] = useState(prefs.maxTokens);
  const [apiKey, setApiKey] = useState("");

  const [uploadText, setUploadText] = useState<string>();
  const [uploadMsg, setUploadMsg] = useState<string>();
  const [uploading, setUploading] = useState(false);

  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string>();
  const [results, setResults] = useState<Outcome[]>([]);

  const available = (backends.data?.backends ?? []).filter((b) => b.available);

  async function handleUpload(file: File) {
    setUploading(true);
    setUploadMsg(undefined);
    setUploadText(undefined);
    try {
      const { job_id } = await api.uploadPdf(file);
      for (let i = 0; i < 30; i++) {
        const job = await api.job(job_id);
        if (job.status === "succeeded") {
          const text = job.result?.preview ?? "";
          setUploadText(text);
          setTrial("");
          setUploadMsg(`Extracted ${job.result?.n_chars ?? 0} chars (preview used as context).`);
          return;
        }
        if (job.status === "failed") {
          setUploadMsg(`Preprocessing failed: ${job.error ?? "unknown error"}`);
          return;
        }
        await sleep(1000);
      }
      setUploadMsg("Preprocessing timed out.");
    } catch (err) {
      setUploadMsg(err instanceof ApiError ? (err.detail ?? err.message) : String(err));
    } finally {
      setUploading(false);
    }
  }

  async function generate() {
    const specs = compare ? selected : [primary];
    if (specs.length === 0) {
      setError("Pick at least one backend.");
      return;
    }
    if (!uploadText && !trial) {
      setError("Pick a trial or upload a PDF first.");
      return;
    }
    setBusy(true);
    setError(undefined);
    setResults([]);
    const outcomes: Outcome[] = [];
    for (const spec of specs) {
      try {
        const data = await api.summarize({
          trial_name: uploadText ? undefined : trial,
          context: uploadText,
          question: STYLES[style],
          backend: spec,
          max_new_tokens: maxTokens,
          api_key: isProvider(spec) && apiKey ? apiKey : undefined,
        });
        outcomes.push({ backend: spec, data });
      } catch (err) {
        outcomes.push({
          backend: spec,
          error: err instanceof ApiError ? (err.detail ?? err.message) : String(err),
        });
      }
      setResults([...outcomes]);
    }
    setBusy(false);
  }

  function exportResults() {
    const blob = new Blob([JSON.stringify(results, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "pls-summaries.json";
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Live summarization demo</h1>
        <p className="mt-1 text-slate-600">
          Pick a stored trial or upload a PDF, choose one or more backends, and generate a
          plain-language summary.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="space-y-4">
          <label className="block text-sm font-medium text-slate-700">
            Clinical trial
            <select
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
              value={trial}
              onChange={(e) => {
                setTrial(e.target.value);
                if (e.target.value) {
                  setUploadText(undefined);
                  setUploadMsg(undefined);
                }
              }}
            >
              <option value="">— select a trial —</option>
              {trials.data?.items.map((t) => (
                <option key={t.protocol_id} value={t.protocol_id}>
                  {t.protocol_id} ({t.source})
                </option>
              ))}
            </select>
          </label>
          {trials.error && <Banner kind="error">{trials.error}</Banner>}

          <div className="rounded-md border border-dashed border-slate-300 p-3">
            <label className="block text-sm font-medium text-slate-700">
              …or upload a PDF
              <input
                type="file"
                accept="application/pdf"
                className="mt-1 block w-full text-sm"
                onChange={(e) => {
                  const f = e.target.files?.[0];
                  if (f) void handleUpload(f);
                }}
              />
            </label>
            {uploading && <Spinner label="Preprocessing PDF…" />}
            {uploadMsg && <p className="mt-1 text-xs text-slate-500">{uploadMsg}</p>}
          </div>

          <div className="space-y-2">
            <label className="flex items-center gap-2 text-sm font-medium text-slate-700">
              <input
                type="checkbox"
                checked={compare}
                onChange={(e) => setCompare(e.target.checked)}
              />
              Compare multiple models
            </label>
            {!compare ? (
              <select
                className="w-full rounded-md border border-slate-300 px-3 py-2"
                value={primary}
                onChange={(e) => setPrimary(e.target.value)}
              >
                {backends.data?.backends.map((b) => (
                  <option key={b.spec} value={b.spec} disabled={!b.available}>
                    {b.spec} {b.available ? "" : `— ${b.detail ?? "unavailable"}`}
                  </option>
                ))}
              </select>
            ) : (
              <div className="grid grid-cols-2 gap-1 text-sm">
                {available.map((b) => (
                  <label key={b.spec} className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={selected.includes(b.spec)}
                      onChange={(e) =>
                        setSelected((prev) =>
                          e.target.checked
                            ? [...prev, b.spec]
                            : prev.filter((s) => s !== b.spec),
                        )
                      }
                    />
                    {b.spec}
                  </label>
                ))}
              </div>
            )}
          </div>

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

          <label className="block text-sm font-medium text-slate-700">
            Provider API key (used for this request only, never stored)
            <input
              type="password"
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
              value={apiKey}
              placeholder="only needed for hosted providers"
              onChange={(e) => setApiKey(e.target.value)}
            />
          </label>

          <button
            onClick={generate}
            disabled={busy}
            className="rounded-lg bg-brand px-4 py-2 font-medium text-white hover:bg-brand-dark disabled:opacity-50"
          >
            {busy ? "Generating…" : "Generate"}
          </button>
        </Card>

        <Card className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold text-slate-900">Result{results.length > 1 ? "s" : ""}</h2>
            {results.some((r) => r.data) && (
              <button
                onClick={exportResults}
                className="rounded border border-slate-300 px-2 py-1 text-xs hover:bg-slate-100"
              >
                Export JSON
              </button>
            )}
          </div>
          {busy && results.length === 0 && <Spinner label="Running the model…" />}
          {error && <Banner kind="error">{error}</Banner>}
          {!busy && !error && results.length === 0 && (
            <p className="text-sm text-slate-500">The generated summary will appear here.</p>
          )}
          <div className="space-y-4">
            {results.map((r) => (
              <div key={r.backend} className="rounded-lg border border-slate-200 p-3">
                <div className="mb-1 text-xs font-medium text-slate-500">{r.backend}</div>
                {r.error ? (
                  <Banner kind="error">{r.error}</Banner>
                ) : (
                  <>
                    <p className="whitespace-pre-wrap text-sm text-slate-800">{r.data!.text}</p>
                    {r.data!.warnings.length > 0 && (
                      <p className="mt-1 text-xs text-amber-700">{r.data!.warnings.join(" · ")}</p>
                    )}
                    <div className="mt-1 text-xs text-slate-400">
                      {r.data!.latency_s?.toFixed(3) ?? "—"}s · in {r.data!.input_tokens ?? "—"} /
                      out {r.data!.output_tokens ?? "—"} tokens
                    </div>
                  </>
                )}
              </div>
            ))}
          </div>
          {results.some((r) => r.data) && <Disclaimer />}
        </Card>
      </div>
    </div>
  );
}
