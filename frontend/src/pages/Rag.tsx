import { useState } from "react";
import { api, ApiError } from "../lib/api";
import { Banner, Card, Spinner } from "../components/ui";
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
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Research assistant</h1>
        <p className="mt-1 text-slate-600">
          Ask questions across the trial collection. Answers are grounded in retrieved passages with
          source citations, and the assistant says when the evidence is insufficient.
        </p>
      </div>

      <Card className="space-y-3">
        <textarea
          className="w-full rounded-md border border-slate-300 px-3 py-2"
          rows={3}
          placeholder="e.g. What adverse events were reported across these trials?"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <div className="flex flex-wrap items-end gap-4">
          <label className="text-sm text-slate-700">
            Scope to trial (optional)
            <input
              className="mt-1 block rounded-md border border-slate-300 px-3 py-2"
              placeholder="protocol id, or blank for all"
              value={trial}
              onChange={(e) => setTrial(e.target.value)}
            />
          </label>
          <label className="text-sm text-slate-700">
            Passages (k): {k}
            <input
              type="range"
              min={1}
              max={10}
              value={k}
              onChange={(e) => setK(Number(e.target.value))}
              className="mt-1 block w-40"
            />
          </label>
          <button
            onClick={ask}
            disabled={busy || !query.trim()}
            className="rounded-lg bg-brand px-4 py-2 font-medium text-white hover:bg-brand-dark disabled:opacity-50"
          >
            {busy ? "Searching…" : "Ask"}
          </button>
        </div>
      </Card>

      {busy && <Spinner label="Retrieving and answering…" />}
      {error && <Banner kind="error">{error}</Banner>}

      {result && (
        <div className="space-y-4">
          {!result.sufficient && (
            <Banner kind="warn">Insufficient evidence — the assistant declined to answer.</Banner>
          )}
          <Card>
            <h2 className="mb-2 font-semibold text-slate-900">Answer</h2>
            <p className="whitespace-pre-wrap text-slate-800">{result.answer}</p>
          </Card>
          {result.citations.length > 0 && (
            <Card>
              <h2 className="mb-2 font-semibold text-slate-900">Citations</h2>
              <ol className="space-y-1 text-sm">
                {result.citations.map((c, i) => (
                  <li key={i} className="flex items-center justify-between gap-3">
                    <span className="text-slate-700">
                      <span className="font-medium">{c.trial_name}</span> — {c.section}
                    </span>
                    <span className="text-xs text-slate-400">
                      score {c.score.toFixed(3)} · chars {c.start}-{c.end}
                    </span>
                  </li>
                ))}
              </ol>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}
