import { Banner } from "../components/ui";

export function Explorer() {
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-slate-900">Dataset explorer</h1>
      <Banner kind="info">
        Coming in the next iteration: a searchable, filterable trial catalogue with per-trial detail
        (metadata, Markdown source, sections, summaries). The backend already serves it at{" "}
        <code>/api/trials</code>.
      </Banner>
    </div>
  );
}
