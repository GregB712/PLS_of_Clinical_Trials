import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { useAsync } from "../hooks/useAsync";
import { Banner, Card, Spinner, Stat } from "../components/ui";

export function Landing() {
  const stats = useAsync(() => api.stats(), []);

  return (
    <div className="space-y-10">
      <section className="space-y-4">
        <h1 className="text-3xl font-bold text-slate-900 sm:text-4xl">
          Plain-language summaries of clinical trials
        </h1>
        <p className="max-w-3xl text-slate-600">
          Clinical-trial result documents are dense and technical, which keeps findings out of reach
          for the people they affect. This project turns those documents into accurate, readable
          summaries — and keeps the science honest: every summary is traceable to its source, and
          models are compared on measured results, not reputation.
        </p>
        <div className="flex flex-wrap gap-3">
          <Link to="/demo" className="rounded-lg bg-brand px-4 py-2 font-medium text-white hover:bg-brand-dark">
            Try the live demo
          </Link>
          <Link to="/dashboard" className="rounded-lg border border-slate-300 px-4 py-2 font-medium text-slate-700 hover:bg-slate-100">
            Compare models
          </Link>
          <a
            href="https://github.com/GregB712/PLS_of_Clinical_Trials"
            className="rounded-lg border border-slate-300 px-4 py-2 font-medium text-slate-700 hover:bg-slate-100"
          >
            Repository
          </a>
        </div>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold text-slate-900">Dataset at a glance</h2>
        {stats.loading && <Spinner />}
        {stats.error && <Banner kind="error">Could not load stats — {stats.error}</Banner>}
        {stats.data && (
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
            <Stat label="Trials" value={stats.data.trials} />
            <Stat label="Documents" value={stats.data.documents} />
            <Stat label="Sections" value={stats.data.sections} />
            <Stat label="Indexed chunks" value={stats.data.chunks} />
            <Stat label="Benchmarks" value={stats.data.experiments} />
          </div>
        )}
        {stats.data && stats.data.trials === 0 && (
          <Banner kind="info">
            The database is empty. Import data with <code>pls db-load</code> (see the README).
          </Banner>
        )}
      </section>

      <section className="grid gap-4 sm:grid-cols-3">
        <Card>
          <h3 className="font-semibold text-slate-900">Ingest</h3>
          <p className="mt-1 text-sm text-slate-600">
            Clinical-trial PDFs become structured, searchable records and Markdown.
          </p>
        </Card>
        <Card>
          <h3 className="font-semibold text-slate-900">Summarize &amp; evaluate</h3>
          <p className="mt-1 text-sm text-slate-600">
            Multiple model backends generate summaries, scored with ROUGE, BERTScore-ready metrics,
            and readability.
          </p>
        </Card>
        <Card>
          <h3 className="font-semibold text-slate-900">Retrieve with citations</h3>
          <p className="mt-1 text-sm text-slate-600">
            Ask questions across trials and get answers grounded in cited source passages.
          </p>
        </Card>
      </section>
    </div>
  );
}
