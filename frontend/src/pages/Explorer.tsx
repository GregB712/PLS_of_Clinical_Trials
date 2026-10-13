import { useState } from "react";
import { api } from "../lib/api";
import { useAsync } from "../hooks/useAsync";
import { Banner, Card, Spinner } from "../components/ui";
import type { TrialDetail } from "../lib/types";

const PAGE = 20;

export function Explorer() {
  const [q, setQ] = useState("");
  const [offset, setOffset] = useState(0);
  const [selected, setSelected] = useState<string | null>(null);

  const list = useAsync(() => api.trials({ q: q || undefined, limit: PAGE, offset }), [q, offset]);
  const detail = useAsync<TrialDetail | null>(
    () => (selected ? api.trial(selected) : Promise.resolve(null)),
    [selected],
  );

  const total = list.data?.total ?? 0;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Dataset explorer</h1>
        <p className="mt-1 text-slate-600">Browse the stored clinical trials and inspect sources.</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1fr_1.4fr]">
        <Card className="space-y-3">
          <input
            type="search"
            placeholder="Filter by protocol id…"
            className="w-full rounded-md border border-slate-300 px-3 py-2"
            value={q}
            onChange={(e) => {
              setOffset(0);
              setQ(e.target.value);
            }}
          />
          {list.loading && <Spinner />}
          {list.error && <Banner kind="error">{list.error}</Banner>}
          {list.data && list.data.items.length === 0 && (
            <Banner kind="info">No trials match. Import data with <code>pls db-load</code>.</Banner>
          )}
          <ul className="divide-y divide-slate-100">
            {list.data?.items.map((t) => (
              <li key={t.protocol_id}>
                <button
                  onClick={() => setSelected(t.protocol_id)}
                  className={`flex w-full items-center justify-between px-1 py-2 text-left text-sm hover:bg-slate-50 ${
                    selected === t.protocol_id ? "font-semibold text-brand" : "text-slate-700"
                  }`}
                >
                  <span>{t.protocol_id}</span>
                  <span className="text-xs text-slate-400">{t.document_kinds.join(", ")}</span>
                </button>
              </li>
            ))}
          </ul>
          {total > PAGE && (
            <div className="flex items-center justify-between text-sm">
              <button
                disabled={offset === 0}
                onClick={() => setOffset(Math.max(0, offset - PAGE))}
                className="rounded border border-slate-300 px-2 py-1 disabled:opacity-40"
              >
                ← Prev
              </button>
              <span className="text-slate-500">
                {offset + 1}–{Math.min(offset + PAGE, total)} of {total}
              </span>
              <button
                disabled={offset + PAGE >= total}
                onClick={() => setOffset(offset + PAGE)}
                className="rounded border border-slate-300 px-2 py-1 disabled:opacity-40"
              >
                Next →
              </button>
            </div>
          )}
        </Card>

        <Card>
          {!selected && <p className="text-sm text-slate-500">Select a trial to see its details.</p>}
          {selected && detail.loading && <Spinner />}
          {detail.error && <Banner kind="error">{detail.error}</Banner>}
          {detail.data && <TrialView trial={detail.data} />}
        </Card>
      </div>
    </div>
  );
}

function TrialView({ trial }: { trial: TrialDetail }) {
  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold text-slate-900">{trial.protocol_id}</h2>
        <p className="text-xs text-slate-400">
          source: {trial.source} · {trial.documents.map((d) => `${d.kind} (${d.n_sections})`).join(", ")}
        </p>
      </div>
      <Sections title="Report sections" sections={trial.report_sections} />
      <Sections title="Plain-language summary" sections={trial.summary_sections} />
    </div>
  );
}

function Sections({ title, sections }: { title: string; sections: Record<string, string> }) {
  const entries = Object.entries(sections);
  if (entries.length === 0) return null;
  return (
    <div>
      <h3 className="mb-1 text-sm font-semibold text-slate-700">{title}</h3>
      <dl className="space-y-2">
        {entries.map(([name, text]) => (
          <div key={name} className="rounded-md bg-slate-50 p-3">
            <dt className="text-xs font-medium text-slate-500">{name}</dt>
            <dd className="mt-0.5 text-sm text-slate-700">{text}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}
