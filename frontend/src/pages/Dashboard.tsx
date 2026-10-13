import { useState } from "react";
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "../lib/api";
import { useAsync } from "../hooks/useAsync";
import { Banner, Card, Spinner } from "../components/ui";

const METRICS = ["F1 Score", "ROUGE-1", "ROUGE-2", "ROUGE-L", "BLEU Score"];

export function Dashboard() {
  const experiments = useAsync(() => api.experiments(), []);
  const [metric, setMetric] = useState("F1 Score");

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Model comparison</h1>
        <p className="mt-1 text-slate-600">
          Backends scored on the same examples. Benchmark results only — distinct from the live demo.
        </p>
      </div>

      {experiments.loading && <Spinner />}
      {experiments.error && <Banner kind="error">{experiments.error}</Banner>}
      {experiments.data && experiments.data.length === 0 && (
        <Banner kind="info">
          No benchmarks recorded yet. Run <code>pls benchmark --to-db</code> to populate this page.
        </Banner>
      )}

      {experiments.data?.map((exp) => {
        const chartData = exp.results.map((r) => ({
          backend: r.backend,
          value: Number((r.aggregate[metric] ?? 0).toFixed(2)),
        }));
        return (
          <Card key={exp.id} className="space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h2 className="font-semibold text-slate-900">
                Experiment #{exp.id} · {exp.n_examples} examples · {exp.split_fingerprint}
              </h2>
              <label className="text-sm text-slate-600">
                Metric{" "}
                <select
                  className="rounded-md border border-slate-300 px-2 py-1"
                  value={metric}
                  onChange={(e) => setMetric(e.target.value)}
                >
                  {METRICS.map((m) => (
                    <option key={m}>{m}</option>
                  ))}
                </select>
              </label>
            </div>

            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="backend" fontSize={12} />
                  <YAxis fontSize={12} />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="value" name={metric} fill="#0f766e" />
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="border-b border-slate-200 text-slate-500">
                  <tr>
                    <th className="py-2 pr-4">Backend</th>
                    {METRICS.map((m) => (
                      <th key={m} className="py-2 pr-4">{m}</th>
                    ))}
                    <th className="py-2 pr-4">scored</th>
                    <th className="py-2">errors</th>
                  </tr>
                </thead>
                <tbody>
                  {exp.results.map((r) => (
                    <tr key={r.backend} className="border-b border-slate-100">
                      <td className="py-2 pr-4 font-medium">{r.backend}</td>
                      {METRICS.map((m) => (
                        <td key={m} className="py-2 pr-4">
                          {r.aggregate[m] != null ? r.aggregate[m].toFixed(2) : "—"}
                        </td>
                      ))}
                      <td className="py-2 pr-4">{r.n_scored}</td>
                      <td className="py-2">{r.n_errors}</td>
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
