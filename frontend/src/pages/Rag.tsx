import { useState } from "react";
import { api, ApiError } from "../lib/api";
import { Banner, Card, PageHeader, Spinner } from "../components/ui";
import type { AskResponse } from "../lib/types";

export function Rag() {
  const [query, setQuery] = useState("");
  const [trial, setTrial] = useState("");
  const [k, setK] = useState(5);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string>();
  const [result, setResult] = useState<AskResponse>();

  async function ask() {
    if (!query.trim()) return;
    setBusy(true);
    setError(undefined);
    setResult(undefined);
    try {
      setResult(await api.ask({ query, trial_name: trial || undefined, k }));
    } catch (err) {
      setError(err instanceof ApiError ? (err.detail ?? err.message) : String(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-10">
      <PageHeader title="Research assistant">
        Ask questions across the trial collection. Answers are grounded in retrieved passages with
        source citations, and the assistant says so when the evidence is insufficient.
      </PageHeader>

      <form
        className="card max-w-3xl space-y-4 p-3 sm:p-3"
        onSubmit={(e) => {
          e.preventDefault();
          void ask();
        }}
      >
        <textarea
          aria-label="Question"
          className="input min-h-24 border-transparent bg-transparent text-[1.0625rem] hover:border-transparent focus:border-transparent focus:shadow-none"
          rows={3}
          placeholder="e.g. What adverse events were reported across these trials?"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
              e.preventDefault();
              void ask();
            }
          }}
        />
        <div className="flex flex-wrap items-end gap-x-5 gap-y-3 border-t border-line px-2 pt-3">
          <label className="min-w-48 flex-1">
            <span className="field-label">Scope to trial</span>
            <input
              className="input"
              placeholder="Protocol id, or blank for all"
              value={trial}
              onChange={(e) => setTrial(e.target.value)}
            />
          </label>
          <label className="w-40">
            <span className="field-label flex justify-between">
              Passages
              <span className="tabular-nums text-ink">{k}</span>
            </span>
            <input
              type="range"
              min={1}
              max={10}
              value={k}
              onChange={(e) => setK(Number(e.target.value))}
              className="h-10"
            />
          </label>
          <button type="submit" disabled={busy || !query.trim()} className="btn btn-primary">
            {busy ? "Searching…" : "Ask"}
          </button>
        </div>
      </form>

      <div aria-live="polite" className="max-w-3xl space-y-4">
        {busy && <Spinner label="Retrieving and answering…" />}
        {error && <Banner kind="error">{error}</Banner>}

        {result && (
          <div className="arrive space-y-4">
            {!result.sufficient && (
              <Banner kind="warn">Insufficient evidence. The assistant declined to answer.</Banner>
            )}
            <Card className="sm:p-7">
              <h2 className="footnote mb-2 font-semibold text-accent">Answer</h2>
              <p className="prose-read whitespace-pre-wrap text-ink">{result.answer}</p>
            </Card>
            {result.citations.length > 0 && (
              <section className="card overflow-hidden">
                <h2 className="title-2 px-5 pb-2 pt-5 text-ink sm:px-6">Citations</h2>
                <ol className="grouped text-sm">
                  {result.citations.map((c, i) => (
                    <li
                      key={i}
                      className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1 px-5 py-3 sm:px-6"
                    >
                      <span className="flex items-baseline gap-3 text-ink">
                        <span className="tabular-nums text-ink-3">{i + 1}</span>
                        <span>
                          <span className="font-semibold">{c.trial_name}</span>
                          <span className="text-ink-2">, {c.section}</span>
                        </span>
                      </span>
                      <span className="footnote flex gap-3 tabular-nums text-ink-3">
                        <span>Score {c.score.toFixed(3)}</span>
                        <span>
                          Chars {c.start}–{c.end}
                        </span>
                      </span>
                    </li>
                  ))}
                </ol>
              </section>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
