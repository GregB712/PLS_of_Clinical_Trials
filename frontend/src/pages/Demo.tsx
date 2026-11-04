import { useState } from "react";
import { api, ApiError } from "../lib/api";
import { useAsync } from "../hooks/useAsync";
import { Banner, Card, Disclaimer, PageHeader, Segmented, Spinner, Switch } from "../components/ui";
import { loadPrefs } from "../lib/prefs";
import type { BackendInfo, SummarizeResponse, TrialDetail } from "../lib/types";

const STYLES = {
  Overview: "Summarize this clinical trial for a non-specialist in plain language.",
  "Key results": "In plain language, what were the key results of this clinical trial?",
  Safety: "In plain language, what adverse events and safety findings were reported?",
} as const;
type Style = keyof typeof STYLES;

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
  const original = useAsync<TrialDetail | null>(
    () => (trial ? api.trial(trial) : Promise.resolve(null)),
    [trial],
  );
  const allSynthetic =
    !!trials.data?.items.length && trials.data.items.every((t) => t.source === "synthetic");
  const [primary, setPrimary] = useState(prefs.backend);
  const [compare, setCompare] = useState(false);
  const [selected, setSelected] = useState<string[]>([]);
  const [style, setStyle] = useState<Style>("Overview");
  const [maxTokens, setMaxTokens] = useState(prefs.maxTokens);
  const [apiKey, setApiKey] = useState("");

  const [uploadText, setUploadText] = useState<string>();
  const [uploadMsg, setUploadMsg] = useState<string>();
  const [uploading, setUploading] = useState(false);

  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string>();
  const [results, setResults] = useState<Outcome[]>([]);

  // Hosted providers are usable without a server key: the visitor can paste their own.
  const usable = (b: BackendInfo) => b.available || b.kind === "provider";
  const available = (backends.data?.backends ?? []).filter(usable);
  const uploadsEnabled = backends.data?.uploads_enabled ?? true;

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
      setError(uploadsEnabled ? "Pick a trial or upload a PDF first." : "Pick a trial first.");
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


  const source = uploadText ? "upload" : trial ? "trial" : null;

  return (
    <div className="space-y-10">
      <PageHeader title="Live summarization demo">
        Pick a stored trial{uploadsEnabled ? " or upload a PDF" : ""}, choose one or more backends,
        and generate a plain-language summary.
      </PageHeader>

      <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,22rem)_minmax(0,1fr)]">
        <Card className="space-y-6 lg:sticky lg:top-20">
          <fieldset className="space-y-3">
            <legend className="field-label">Source</legend>
            <select
              aria-label="Clinical trial"
              className="input"
              value={trial}
              onChange={(e) => {
                setTrial(e.target.value);
                if (e.target.value) {
                  setUploadText(undefined);
                  setUploadMsg(undefined);
                }
              }}
            >
              <option value="">Select a trial</option>
              {trials.data?.items.map((t) => (
                <option key={t.protocol_id} value={t.protocol_id}>
                  {t.protocol_id} ({t.source})
                </option>
              ))}
            </select>
            {trials.error && <Banner kind="error">{trials.error}</Banner>}
            {allSynthetic && (
              <p className="footnote text-ink-3">
                These trials are synthetic samples made for this showcase. The study used real
                Novartis trials, which can&apos;t be shared.
              </p>
            )}

            {uploadsEnabled ? (
              <label
                className={`block cursor-pointer rounded-xl border border-dashed px-4 py-3 text-sm transition-colors ${
                  source === "upload"
                    ? "border-accent bg-accent-soft"
                    : "border-line hover:border-ink-3 hover:bg-sunken"
                }`}
              >
                <span className="font-medium text-ink">Or upload a PDF</span>
                <span className="block text-xs text-ink-3">Text is extracted and used as context.</span>
                <input
                  type="file"
                  accept="application/pdf"
                  className="sr-only"
                  onChange={(e) => {
                    const f = e.target.files?.[0];
                    if (f) void handleUpload(f);
                  }}
                />
              </label>
            ) : (
              <p className="footnote text-ink-3">PDF upload is turned off in this public demo.</p>
            )}
            {uploading && <Spinner label="Preprocessing PDF…" />}
            {uploadMsg && <p className="footnote text-ink-2">{uploadMsg}</p>}
          </fieldset>

          <fieldset className="space-y-3">
            <legend className="field-label">Model</legend>
            <Switch checked={compare} onChange={setCompare}>
              Compare multiple models
            </Switch>
            {!compare ? (
              <select
                aria-label="Backend"
                className="input"
                value={primary}
                onChange={(e) => setPrimary(e.target.value)}
              >
                {backends.data?.backends.map((b) => (
                  <option key={b.spec} value={b.spec} disabled={!usable(b)}>
                    {b.spec}
                    {b.available
                      ? ""
                      : b.kind === "provider"
                        ? " (needs your API key)"
                        : ` (${b.detail ?? "unavailable"})`}
                  </option>
                ))}
              </select>
            ) : (
              <div className="grouped overflow-hidden rounded-xl border border-line text-sm">
                {available.map((b) => (
                  <label
                    key={b.spec}
                    className="flex cursor-pointer items-center gap-3 px-3 py-2.5 hover:bg-sunken"
                  >
                    <input
                      type="checkbox"
                      className="h-4 w-4"
                      checked={selected.includes(b.spec)}
                      onChange={(e) =>
                        setSelected((prev) =>
                          e.target.checked
                            ? [...prev, b.spec]
                            : prev.filter((s) => s !== b.spec),
                        )
                      }
                    />
                    <span className="text-ink">{b.spec}</span>
                  </label>
                ))}
              </div>
            )}
          </fieldset>

          <div>
            <span className="field-label">Style</span>
            <Segmented
              label="Style"
              options={Object.keys(STYLES) as Style[]}
              value={style}
              onChange={setStyle}
            />
          </div>

          <label className="block">
            <span className="field-label flex justify-between">
              Max new tokens
              <span className="tabular-nums text-ink">{maxTokens}</span>
            </span>
            <input
              type="range"
              min={64}
              max={1024}
              step={32}
              value={maxTokens}
              onChange={(e) => setMaxTokens(Number(e.target.value))}
            />
          </label>

          <label className="block">
            <span className="field-label">Provider API key</span>
            <input
              type="password"
              className="input"
              value={apiKey}
              placeholder="Only for hosted providers"
              onChange={(e) => setApiKey(e.target.value)}
            />
            <span className="footnote mt-1.5 block text-ink-3">
              Used for this request only. Never stored.
            </span>
          </label>

          <button onClick={generate} disabled={busy} className="btn btn-primary w-full">
            {busy ? "Generating…" : "Generate summary"}
          </button>
        </Card>

        <section aria-live="polite" className="min-w-0 space-y-4">
          <div className="flex min-h-8 items-center justify-between">
            <h2 className="title-2 text-ink">Result{results.length > 1 ? "s" : ""}</h2>
            {results.some((r) => r.data) && (
              <button onClick={exportResults} className="btn btn-secondary btn-small">
                Export JSON
              </button>
            )}
          </div>
          {busy && results.length === 0 && <Spinner label="Running the model…" />}
          {error && <Banner kind="error">{error}</Banner>}
          {!busy && !error && results.length === 0 && !trial && (
            <div className="rounded-[1.125rem] border border-dashed border-line px-6 py-16 text-center">
              <p className="font-serif text-lg text-ink-2">The summary will appear here.</p>
              <p className="footnote mt-1 text-ink-3">
                {uploadsEnabled
                  ? "Choose a trial or upload a PDF, then generate."
                  : "Choose a trial, then generate."}
              </p>
            </div>
          )}
          {results.map((r) => (
            <article key={r.backend} className="card arrive p-5 sm:p-7">
              <div className="footnote mb-3 font-semibold text-accent">{r.backend}</div>
              {r.error ? (
                <Banner kind="error">{r.error}</Banner>
              ) : (
                <>
                  <p className="prose-read whitespace-pre-wrap text-ink">{r.data!.text}</p>
                  {r.data!.warnings.length > 0 && (
                    <ul className="footnote mt-3 space-y-0.5 text-amber-700 dark:text-amber-300">
                      {r.data!.warnings.map((w) => (
                        <li key={w}>{w}</li>
                      ))}
                    </ul>
                  )}
                  <div className="footnote mt-4 flex flex-wrap gap-x-4 gap-y-1 border-t border-line pt-3 tabular-nums text-ink-3">
                    <span>{r.data!.latency_s?.toFixed(2) ?? "n/a"} s</span>
                    <span>{r.data!.input_tokens ?? "n/a"} tokens in</span>
                    <span>{r.data!.output_tokens ?? "n/a"} tokens out</span>
                  </div>
                </>
              )}
            </article>
          ))}
          {results.some((r) => r.data) && <Disclaimer />}
          {!busy && !error && results.length === 0 && trial && (
            <p className="footnote text-ink-3">
              Press Generate summary to write one. The original document is below.
            </p>
          )}
          {trial && original.loading && <Spinner label="Loading the original document…" />}
          {original.error && <Banner kind="error">{original.error}</Banner>}
          {original.data && <OriginalDocument key={original.data.protocol_id} trial={original.data} />}
        </section>
      </div>
    </div>
  );
}

const VIEWS = ["Technical report", "Patient summary"] as const;

/** The selected trial as stored: its technical report and its human-written patient summary. */
function OriginalDocument({ trial }: { trial: TrialDetail }) {
  const [view, setView] = useState<(typeof VIEWS)[number]>("Technical report");
  const sections = view === "Technical report" ? trial.report_sections : trial.summary_sections;
  const entries = Object.entries(sections);
  return (
    <article className="card arrive overflow-hidden" aria-labelledby="original-title">
      <header className="space-y-3 border-b border-line px-5 pb-4 pt-5 sm:px-6">
        <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
          <h2 id="original-title" className="title-2 text-ink">
            Original: <span className="tabular-nums">{trial.protocol_id}</span>
          </h2>
          <span className="footnote text-ink-3">Source: {trial.source}</span>
        </div>
        {trial.source === "synthetic" && (
          <Banner kind="info">
            Synthetic sample for showcasing. The drug, condition and results are invented; nothing
            here describes a real trial.
          </Banner>
        )}
        <div className="max-w-sm">
          <Segmented label="Document" options={VIEWS} value={view} onChange={setView} />
        </div>
        <p className="footnote text-ink-3">
          {view === "Technical report"
            ? "What the model reads: the sponsor's results report."
            : "What a person wrote for patients. Compare the generated summary with this."}
        </p>
      </header>
      {entries.length === 0 ? (
        <p className="px-5 py-4 text-sm text-ink-3 sm:px-6">This document has no sections.</p>
      ) : (
        <dl className="grouped max-h-[32rem] overflow-y-auto">
          {entries.map(([name, text]) => (
            <div key={name} className="px-5 py-4 sm:px-6">
              <dt className="text-sm font-semibold text-ink">{name}</dt>
              <dd
                className={
                  view === "Patient summary"
                    ? "prose-read mt-1 text-ink"
                    : "mt-1 text-[0.9375rem] leading-relaxed text-ink-2"
                }
              >
                {text}
              </dd>
            </div>
          ))}
        </dl>
      )}
    </article>
  );
}
