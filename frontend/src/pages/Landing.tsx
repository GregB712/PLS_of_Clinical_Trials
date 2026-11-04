import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { useAsync } from "../hooks/useAsync";
import { Banner, Spinner, Stat } from "../components/ui";

// A real pair from the bundled synthetic sample (data/sample/trials.json, SYN001A2101).
const REPORT =
  "At week 24, fictozumab lowered the pain score by 3.1 points versus 1.2 for placebo, a statistically significant difference. The most common side effect was mild injection-site redness.";
const PLAIN = "People taking fictozumab had noticeably less joint pain than those on placebo.";

const PIPELINE = [
  {
    title: "Ingest",
    body: "Clinical-trial PDFs become structured, searchable records and Markdown.",
  },
  {
    title: "Summarize and evaluate",
    body: "Several model backends write summaries, scored with ROUGE, token-F1, BLEU and readability.",
  },
  {
    title: "Retrieve with citations",
    body: "Ask questions across trials and get answers grounded in cited source passages.",
  },
];

export function Landing() {
  const stats = useAsync(() => api.stats(), []);

  return (
    <div className="space-y-20 sm:space-y-24">
      <section className="grid items-center gap-12 lg:grid-cols-[1.05fr_1fr] lg:gap-16">
        <div className="space-y-6">
          <h1 className="display text-ink">Plain-language summaries of clinical trials</h1>
          <p className="max-w-xl text-[1.0625rem] leading-relaxed text-ink-2">
            Trial result documents are dense and technical, which keeps findings out of reach for
            the people they affect. This project rewrites them as accurate, readable summaries. Every
            summary traces back to its source, and models are compared on measured results.
          </p>
          <div className="flex flex-wrap gap-3 pt-1">
            <Link to="/demo" className="btn btn-primary">
              Try the live demo
            </Link>
            <Link to="/paper" className="btn btn-secondary">
              Read the paper
            </Link>
            <Link to="/dashboard" className="btn btn-secondary">
              Compare models
            </Link>
            <a href="https://github.com/GregB712/PLS_of_Clinical_Trials" className="btn btn-secondary">
              View on GitHub
            </a>
          </div>
        </div>

        <figure className="relative">
          <div className="card p-5 sm:p-6">
            <div className="footnote mb-2 font-semibold text-ink-3">Trial report, results section</div>
            <p className="text-[0.875rem] leading-[1.55] text-ink-2">{REPORT}</p>
          </div>
          <div aria-hidden="true" className="ml-8 h-8 w-px bg-line" />
          <div className="card border-accent/30 p-5 sm:p-7">
            <div className="footnote mb-2 font-semibold text-accent">Plain-language summary</div>
            <p className="font-serif text-[1.5rem] leading-[1.35] tracking-[-0.01em] text-ink sm:text-[1.75rem]">
              <span className="mark mark-sweep">{PLAIN}</span>
            </p>
          </div>
          <figcaption className="footnote mt-3 text-ink-3">
            Reference pair from the bundled synthetic sample. The drug and condition are invented.
          </figcaption>
        </figure>
      </section>

      <section className="space-y-5" aria-labelledby="glance">
        <h2 id="glance" className="title-2 text-ink">
          Dataset at a glance
        </h2>
        {stats.loading && <Spinner />}
        {stats.error && <Banner kind="error">Could not load stats: {stats.error}</Banner>}
        {stats.data && (
          <dl className="card grid grid-cols-2 gap-x-6 gap-y-6 p-6 sm:grid-cols-3 lg:grid-cols-5 lg:divide-x lg:divide-line lg:[&>*]:pl-6 lg:[&>*:first-child]:pl-0">
            <Stat label="Trials" value={stats.data.trials} />
            <Stat label="Documents" value={stats.data.documents} />
            <Stat label="Sections" value={stats.data.sections} />
            <Stat label="Indexed chunks" value={stats.data.chunks} />
            <Stat label="Benchmarks" value={stats.data.experiments} />
          </dl>
        )}
        {stats.data && stats.data.trials === 0 && (
          <Banner kind="info">
            The database is empty. Import data with <code>pls db-load</code> (see the README).
          </Banner>
        )}
      </section>

      <section aria-labelledby="how" className="space-y-6">
        <h2 id="how" className="title-2 text-ink">
          How it works
        </h2>
        <ol className="grid gap-8 sm:grid-cols-3 sm:gap-6">
          {PIPELINE.map((step, i) => (
            <li key={step.title} className="border-t border-line pt-4">
              <div className="flex items-baseline gap-2.5">
                <span className="text-sm font-semibold tabular-nums text-accent">{i + 1}</span>
                <h3 className="font-semibold tracking-[-0.01em] text-ink">{step.title}</h3>
              </div>
              <p className="mt-1.5 text-[0.9375rem] leading-relaxed text-ink-2">{step.body}</p>
            </li>
          ))}
        </ol>
      </section>
    </div>
  );
}
