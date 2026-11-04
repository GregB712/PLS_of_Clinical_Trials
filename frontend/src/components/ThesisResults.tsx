import { useState } from "react";
import {
  Bar,
  CartesianGrid,
  ComposedChart,
  ErrorBar,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import results from "../content/thesis_results.json";
import { Card, Segmented } from "./ui";

// Generated from the thesis result tables by paper/web/build_results.py.

const METRICS = {
  "ROUGE-L": "rougeL",
  "ROUGE-1": "rouge1",
  "ROUGE-2": "rouge2",
  BLEU: "bleu",
  "Token F1": "token_f1",
  BERTScore: "bertscore_f1",
} as const;
type MetricLabel = keyof typeof METRICS;
const LABELS = Object.keys(METRICS) as MetricLabel[];

type System = (typeof results.systems)[number];
type MetricKey = keyof System["metrics"];

const value = (s: System, m: MetricKey) => s.metrics[m];

export function ThesisResults() {
  const [label, setLabel] = useState<MetricLabel>("ROUGE-L");
  const metric = METRICS[label];
  const lead3 = results.systems.find((s) => s.id === "lead-3")!;
  const best = Math.max(...results.systems.map((s) => value(s, metric).mean));

  const data = results.systems.map((s) => {
    const v = value(s, metric);
    const err = [v.mean - v.lo, v.hi - v.mean];
    return { model: s.model, family: s.family, mean: v.mean, lo: v.lo, hi: v.hi, err };
  });

  return (
    <section aria-labelledby="thesis-results" className="space-y-5">
      <div className="max-w-3xl space-y-1.5">
        <h2 id="thesis-results" className="title-2 text-ink">
          Full study: held-out test set
        </h2>
        <p className="text-[0.9375rem] leading-relaxed text-ink-2">
          {results.testSet.examples} examples from {results.testSet.trials} trials the models never
          saw, from the thesis run on the full Novartis corpus. Bars are means; whiskers are 95%
          confidence intervals from a bootstrap over trials. The dashed line marks Lead-3, the
          strongest simple baseline.
        </p>
      </div>

      <div className="max-w-2xl">
        <Segmented label="Metric" options={LABELS} value={label} onChange={setLabel} />
      </div>

      <Card className="space-y-6">
        <div
          className="chart text-accent"
          style={{ height: data.length * 34 + 48 }}
          role="img"
          aria-label={`${label} by system with 95% confidence intervals; the table below lists every value`}
        >
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={data} layout="vertical" margin={{ top: 4, right: 24, left: 8, bottom: 4 }}>
              <CartesianGrid horizontal={false} />
              <XAxis type="number" fontSize={12} tickLine={false} />
              <YAxis
                type="category"
                dataKey="model"
                width={250}
                fontSize={12}
                tickLine={false}
                axisLine={false}
                interval={0}
              />
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
                formatter={(_v, _n, item) => {
                  const p = item.payload as (typeof data)[number];
                  return [`${p.mean.toFixed(2)} [${p.lo.toFixed(2)}, ${p.hi.toFixed(2)}]`, label];
                }}
              />
              <ReferenceLine
                x={value(lead3, metric).mean}
                strokeDasharray="4 4"
                className="reference-line"
              />
              <Bar
                dataKey="mean"
                fill="currentColor"
                fillOpacity={0.4}
                barSize={14}
                radius={2}
                isAnimationActive={false}
              >
                <ErrorBar dataKey="err" direction="x" width={6} strokeWidth={1.5} />
              </Bar>
            </ComposedChart>
          </ResponsiveContainer>
        </div>

        <div className="-mx-5 overflow-x-auto sm:-mx-6">
          <table className="w-full text-left text-sm tabular-nums">
            <thead className="footnote text-ink-3">
              <tr className="border-b border-line">
                <th className="py-2 pl-5 pr-4 font-medium sm:pl-6">System</th>
                <th className="px-3 py-2 font-medium">Family</th>
                <th className="py-2 pl-3 pr-5 text-right font-medium sm:pr-6">
                  {label} [95% CI]
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {data.map((d) => (
                <tr key={d.model}>
                  <td className="py-2.5 pl-5 pr-4 font-medium text-ink sm:pl-6">{d.model}</td>
                  <td className="px-3 py-2.5 text-ink-2">{d.family}</td>
                  <td
                    className={`py-2.5 pl-3 pr-5 text-right sm:pr-6 ${
                      d.mean === best ? "font-semibold text-accent" : "text-ink"
                    }`}
                  >
                    {d.mean.toFixed(2)}{" "}
                    <span className="text-ink-3">
                      [{d.lo.toFixed(2)}, {d.hi.toFixed(2)}]
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {metric === "bertscore_f1" && (
          <p className="footnote text-ink-3">
            BERTScore is baseline-rescaled, so scores near zero mean “no better than unrelated
            text” and negative values are expected for weak systems.
          </p>
        )}
        <p className="footnote text-ink-3">
          Main protocol: greedy decoding with no repeated trigrams. Higher means closer to the human
          patient summary, which is not the same as more correct; see the Paper page for why.
        </p>
      </Card>
    </section>
  );
}
