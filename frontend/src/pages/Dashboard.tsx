import { useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "../lib/api";
import { useAsync } from "../hooks/useAsync";
import { Banner, Card, PageHeader, Segmented, Spinner } from "../components/ui";

const METRICS = ["F1 Score", "ROUGE-1", "ROUGE-2", "ROUGE-L", "BLEU Score"] as const;
type Metric = (typeof METRICS)[number];

const fmt = (v: number | null | undefined) => (v != null ? v.toFixed(2) : "n/a");

export function Dashboard() {
  const experiments = useAsync(() => api.experiments(), []);
  const [metric, setMetric] = useState<Metric>("F1 Score");

  return (
    <div className="space-y-10">
      <PageHeader title="Model comparison">
        Backends scored on the same examples. These are benchmark results, kept separate from the
        live demo.
      </PageHeader>

      {experiments.loading && <Spinner />}
      {experiments.error && <Banner kind="error">{experiments.error}</Banner>}
      {experiments.data && experiments.data.length === 0 && (
        <Banner kind="info">
          No benchmarks recorded yet. Run <code>pls benchmark --to-db</code> to populate this page.
        </Banner>
      )}

      {experiments.data && experiments.data.length > 0 && (
        <div className="max-w-xl">
          <Segmented label="Metric" options={METRICS} value={metric} onChange={setMetric} />
        </div>
      )}

      {experiments.data?.map((exp) => {
        const chartData = exp.results.map((r) => ({
          backend: r.backend,
          value: Number((r.aggregate[metric] ?? 0).toFixed(2)),
        }));
        const best = Math.max(...exp.results.map((r) => r.aggregate[metric] ?? -Infinity));
        return (
          <Card key={exp.id} className="space-y-6">
            <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
              <h2 className="title-2 text-ink">Experiment {exp.id}</h2>
              <p className="footnote flex flex-wrap gap-x-4 tabular-nums text-ink-3">
                <span>{exp.n_examples} examples</span>
                <span>Split {exp.split_fingerprint}</span>
              </p>
            </div>

            <div className="chart h-64 w-full text-accent" role="img" aria-label={`${metric} by backend`}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 8, right: 8, left: -12, bottom: 0 }}>
                  <CartesianGrid vertical={false} />
                  <XAxis dataKey="backend" fontSize={12} tickLine={false} />
                  <YAxis fontSize={12} tickLine={false} axisLine={false} />
                  <Tooltip
                    cursor={{ className: "recharts-tooltip-cursor" }}
                    contentStyle={{
                      background: "var(--color-surface)",
                      border: "1px solid var(--color-line)",
                      borderRadius: 12,
                      fontSize: 13,
                      color: "var(--color-ink)",
                    }}
                    labelStyle={{ fontWeight: 600, color: "var(--color-ink)" }}
                  />
                  <Bar
                    dataKey="value"
                    name={metric}
                    fill="currentColor"
                    radius={[6, 6, 0, 0]}
                    maxBarSize={56}
                    isAnimationActive={false}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="-mx-5 overflow-x-auto sm:-mx-6">
              <table className="w-full text-left text-sm tabular-nums">
                <thead className="footnote text-ink-3">
                  <tr className="border-b border-line">
                    <th className="py-2 pl-5 pr-4 font-medium sm:pl-6">Backend</th>
                    {METRICS.map((m) => (
                      <th
                        key={m}
                        className={`px-3 py-2 text-right font-medium ${m === metric ? "text-ink" : ""}`}
                      >
                        {m}
                      </th>
                    ))}
                    <th className="px-3 py-2 text-right font-medium">Scored</th>
                    <th className="py-2 pl-3 pr-5 text-right font-medium sm:pr-6">Errors</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-line">
                  {exp.results.map((r) => (
                    <tr key={r.backend}>
                      <td className="py-2.5 pl-5 pr-4 font-medium text-ink sm:pl-6">{r.backend}</td>
                      {METRICS.map((m) => {
                        const v = r.aggregate[m];
                        const isBest = m === metric && v != null && v === best;
                        return (
                          <td
                            key={m}
                            className={`px-3 py-2.5 text-right ${
                              isBest
                                ? "font-semibold text-accent"
                                : m === metric
                                  ? "text-ink"
                                  : "text-ink-2"
                            }`}
                          >
                            {fmt(v)}
                          </td>
                        );
                      })}
                      <td className="px-3 py-2.5 text-right text-ink-2">{r.n_scored}</td>
                      <td className="py-2.5 pl-3 pr-5 text-right text-ink-2 sm:pr-6">{r.n_errors}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        );
      })}
    </div>
  );
}
