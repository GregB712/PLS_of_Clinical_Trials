import { Card } from "../components/ui";

export function Research() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Research &amp; methodology</h1>
        <p className="mt-1 text-slate-600">
          How the project works and what to trust about it.
        </p>
      </div>

      <Card className="space-y-2">
        <h2 className="font-semibold text-slate-900">Original thesis</h2>
        <p className="text-sm text-slate-700">
          A Master's thesis (Aristotle University of Thessaloniki, 2024) on plain-language
          summarization of clinical-trial result documents. It paired dense result reports with their
          plain-language patient summaries and compared a fine-tuned{" "}
          <strong>DistilBERT</strong> (extractive QA) against zero-shot{" "}
          <strong>Mistral-7B-Instruct</strong>. The original code is preserved verbatim in the
          repository; this platform rebuilds it as a reproducible, testable system.
        </p>
      </Card>

      <Card className="space-y-2">
        <h2 className="font-semibold text-slate-900">Dataset</h2>
        <p className="text-sm text-slate-700">
          Clinical-trial reports paired with plain-language summaries by protocol id, split into
          eight canonical patient questions (purpose, who took part, treatments, results, adverse
          events, …). The source corpus is treated as non-redistributable; the public build ships a
          clearly-labeled <em>synthetic</em> sample so everything runs with zero real data. Splits
          are made <strong>by trial</strong> to prevent leakage across questions.
        </p>
      </Card>

      <Card className="space-y-2">
        <h2 className="font-semibold text-slate-900">A key, honest finding</h2>
        <p className="text-sm text-slate-700">
          The thesis built extractive-QA labels with <code>context.find(answer)</code>. Because a
          plain-language answer is a <em>rewrite</em>, it is almost never a verbatim substring of the
          report, so the labels collapse to the <code>[CLS]</code> token. Extractive span-QA cannot
          express an abstractive rewrite — the generative approach is the one that fits. This
          negative result is preserved rather than hidden.
        </p>
      </Card>

      <Card className="space-y-2">
        <h2 className="font-semibold text-slate-900">Evaluation</h2>
        <p className="text-sm text-slate-700">
          Summaries are scored with ROUGE-1/2/L, token-F1, BLEU and exact match. These n-gram metrics
          understate faithful paraphrases, so they are reported as complementary signals — never as
          proof of quality. Benchmarks record software versions, a seed, and a fingerprint of the
          exact examples for reproducibility, and are kept separate from the interactive demo.
        </p>
      </Card>

      <Card className="space-y-2">
        <h2 className="font-semibold text-slate-900">Limitations &amp; responsible use</h2>
        <p className="text-sm text-slate-700">
          Generated summaries are AI-generated research communication, <strong>not medical
          advice</strong>, and may contain errors — verify against the source. The default retrieval
          embedder is dependency-free and deliberately weak; stronger embeddings are optional.
          Numbers shown on synthetic data are illustrative, not real results.
        </p>
      </Card>
    </div>
  );
}
