import { useState } from "react";
import { api } from "../lib/api";
import { useAsync } from "../hooks/useAsync";
import { Banner, PageHeader, Spinner } from "../components/ui";
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
    <div className="space-y-10">
      <PageHeader title="Dataset explorer">
        Browse the stored clinical trials and read each report next to its plain-language summary.
      </PageHeader>

      <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,20rem)_minmax(0,1fr)]">
        <div className="card space-y-3 p-3 lg:sticky lg:top-20">
          <input
            type="search"
            aria-label="Filter trials"
            placeholder="Filter by protocol id…"
            className="input"
            value={q}
            onChange={(e) => {
              setOffset(0);
              setQ(e.target.value);
            }}
          />
          {list.loading && (
            <div className="px-2">
              <Spinner />
            </div>
          )}
          {list.error && <Banner kind="error">{list.error}</Banner>}
          {list.data && list.data.items.length === 0 && (
            <Banner kind="info">
              No trials match. Import data with <code>pls db-load</code>.
            </Banner>
          )}
          <ul className="space-y-0.5">
            {list.data?.items.map((t) => {
              const active = selected === t.protocol_id;
              return (
                <li key={t.protocol_id}>
                  <button
                    onClick={() => setSelected(t.protocol_id)}
                    aria-current={active ? "true" : undefined}
                    className={`flex w-full items-center justify-between gap-3 rounded-lg px-3 py-2 text-left text-sm transition-colors duration-150 ${
                      active ? "bg-accent text-white dark:text-[#06201b]" : "text-ink hover:bg-sunken"
                    }`}
                  >
                    <span className="font-medium tabular-nums">{t.protocol_id}</span>
                    <span className={`text-xs ${active ? "opacity-80" : "text-ink-3"}`}>
                      {t.document_kinds.join(", ")}
                    </span>
                  </button>
                </li>
              );
            })}
          </ul>
          {total > PAGE && (
            <div className="flex items-center justify-between border-t border-line px-1 pt-3 text-sm">
              <button
                disabled={offset === 0}
                onClick={() => setOffset(Math.max(0, offset - PAGE))}
                className="btn btn-secondary btn-small"
              >
                Previous
              </button>
              <span className="footnote tabular-nums text-ink-3">
                {offset + 1}–{Math.min(offset + PAGE, total)} of {total}
              </span>
              <button
                disabled={offset + PAGE >= total}
                onClick={() => setOffset(offset + PAGE)}
                className="btn btn-secondary btn-small"
              >
                Next
              </button>
            </div>
          )}
        </div>

        <div className="min-w-0">
          {!selected && (
            <div className="rounded-[1.125rem] border border-dashed border-line px-6 py-16 text-center">
              <p className="font-serif text-lg text-ink-2">Select a trial to read it.</p>
            </div>
          )}
          {selected && detail.loading && <Spinner />}
          {detail.error && <Banner kind="error">{detail.error}</Banner>}
          {detail.data && <TrialView key={detail.data.protocol_id} trial={detail.data} />}
        </div>
      </div>
    </div>
  );
}

function TrialView({ trial }: { trial: TrialDetail }) {
  return (
    <article className="arrive space-y-8">
      <header className="space-y-1">
        <h2 className="title-1 tabular-nums text-ink">{trial.protocol_id}</h2>
        <p className="footnote flex flex-wrap gap-x-4 text-ink-3">
          <span>Source: {trial.source}</span>
          {trial.documents.map((d) => (
            <span key={d.kind}>
              {d.kind}, {d.n_sections} sections
            </span>
          ))}
        </p>
      </header>
      <Sections title="Plain-language summary" sections={trial.summary_sections} plain />
      <Sections title="Report sections" sections={trial.report_sections} />
    </article>
  );
}

function Sections({
  title,
  sections,
  plain = false,
}: {
  title: string;
  sections: Record<string, string>;
  plain?: boolean;
}) {
  const entries = Object.entries(sections);
  if (entries.length === 0) return null;
  return (
    <section className="card overflow-hidden">
      <h3 className={`title-2 px-5 pb-2 pt-5 sm:px-6 ${plain ? "text-accent" : "text-ink"}`}>
        {title}
      </h3>
      <dl className="grouped">
        {entries.map(([name, text]) => (
          <div key={name} className="px-5 py-4 sm:px-6">
            <dt className="text-sm font-semibold text-ink">{name}</dt>
            <dd
              className={
                plain
                  ? "prose-read mt-1 text-ink"
                  : "mt-1 max-w-[72ch] text-[0.9375rem] leading-relaxed text-ink-2"
              }
            >
              {text}
            </dd>
          </div>
        ))}
      </dl>
    </section>
  );
}
