import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { useAsync } from "../hooks/useAsync";
import { Banner, Spinner, Stat } from "../components/ui";
import results from "../content/thesis_results.json";

const FUNNEL = [
  { label: "Clinical-trial PDFs", value: results.corpus.pdfs },
  { label: "Protocol IDs", value: results.corpus.protocolIds },
  { label: "Report and summary pairs", value: results.corpus.pairs },
  { label: "Usable trials", value: results.corpus.usableTrials },
  { label: "Question-level examples", value: results.corpus.examples },
];
const sp = results.splits;
const tx = results.text;
const hl = results.headline;

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

      <section className="space-y-6" aria-labelledby="study">
        <div className="max-w-3xl space-y-1.5">
          <h2 id="study" className="title-2 text-ink">
            The study dataset
          </h2>
          <p className="text-[0.9375rem] leading-relaxed text-ink-2">
            Built from Novartis clinical-trial documents for the thesis. The documents themselves
            can&apos;t be redistributed, so this site runs on a small synthetic sample instead.
          </p>
        </div>

        <ol className="card grid gap-px overflow-hidden bg-line p-0 sm:grid-cols-5">
          {FUNNEL.map((step) => (
            <li key={step.label} className="bg-surface px-5 py-5">
              <div className="text-[1.75rem] font-semibold tabular-nums tracking-[-0.02em] text-ink">
                {step.value.toLocaleString("en-US")}
              </div>
              <div className="footnote text-ink-2">{step.label}</div>
            </li>
          ))}
        </ol>

        <dl className="grid gap-6 sm:grid-cols-3">
          <div className="border-t border-line pt-4">
            <dt className="footnote text-ink-2">Split by trial (train / validation / test)</dt>
            <dd className="mt-1 text-lg font-semibold tabular-nums text-ink">
              {sp.train.examples} / {sp.val.examples} / {sp.test.examples}
              <span className="block text-sm font-normal text-ink-3">
                examples from {sp.train.trials} / {sp.val.trials} / {sp.test.trials} trials
              </span>
            </dd>
          </div>
          <div className="border-t border-line pt-4">
            <dt className="footnote text-ink-2">Median reading grade, report to patient summary</dt>
            <dd className="mt-1 text-lg font-semibold tabular-nums text-ink">
              {tx.contextFkglMedian.toFixed(1)} → {tx.referenceFkglMedian.toFixed(1)}
              <span className="block text-sm font-normal text-ink-3">Flesch–Kincaid</span>
            </dd>
          </div>
          <div className="border-t border-line pt-4">
            <dt className="footnote text-ink-2">Best model on the test set (ROUGE-L)</dt>
            <dd className="mt-1 text-lg font-semibold tabular-nums text-ink">
              {hl.rougeLMean.toFixed(2)} ± {hl.rougeLStd.toFixed(2)}
              <span className="block text-sm font-normal text-ink-3">
                vs {hl.lead3RougeL.toFixed(2)} for Lead-3
              </span>
            </dd>
          </div>
        </dl>
        <p className="footnote text-ink-3">
          {results.corpus.questionsWithExamples} of {results.corpus.questions} patient questions
          yield examples. Best model: {hl.model}.{" "}
          <Link to="/dashboard" className="text-accent hover:underline">
            Compare all systems
          </Link>
        </p>
      </section>

      <section className="space-y-3" aria-labelledby="glance">
        <h2 id="glance" className="text-sm font-semibold text-ink-2">
          Loaded in this deployment
        </h2>
        {stats.loading && <Spinner />}
        {stats.error && <Banner kind="error">Could not load stats: {stats.error}</Banner>}
        {stats.data && (
          <dl className="flex flex-wrap gap-x-8 gap-y-3">
            <Stat label="Trials" value={stats.data.trials} small />
            <Stat label="Documents" value={stats.data.documents} small />
            <Stat label="Sections" value={stats.data.sections} small />
            <Stat label="Indexed chunks" value={stats.data.chunks} small />
            <Stat label="Benchmarks" value={stats.data.experiments} small />
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
