import type { ReactNode } from "react";
import { PageHeader } from "../components/ui";

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="space-y-3 border-t border-line pt-8">
      <h2 className="title-2 text-ink">{title}</h2>
      <p className="prose-read text-ink-2 [&_strong]:font-semibold [&_strong]:text-ink">{children}</p>
    </section>
  );
}

export function Research() {
  return (
    <article className="mx-auto max-w-3xl space-y-10">
      <PageHeader title="Research and methodology">
        How the project works, and what to trust about it.
      </PageHeader>

      <div className="space-y-8">
        <Section title="Original thesis">
          A Master&apos;s thesis (Aristotle University of Thessaloniki, 2024) on plain-language
          summarization of clinical-trial result documents. It paired dense result reports with their
          plain-language patient summaries and compared a fine-tuned <strong>DistilBERT</strong>{" "}
          (extractive QA) against zero-shot <strong>Mistral-7B-Instruct</strong>. The original code
          is preserved verbatim in the repository; this platform rebuilds it as a reproducible,
          testable system.
        </Section>

        <Section title="Dataset">
          Clinical-trial reports paired with plain-language summaries by protocol id, split into
          eight canonical patient questions (purpose, who took part, treatments, results, adverse
          events, and so on). The source corpus is treated as non-redistributable, so the public
          build ships a clearly labeled <em>synthetic</em> sample and everything runs with zero real
          data. Splits are made <strong>by trial</strong> to prevent leakage across questions.
        </Section>

        <Section title="A key, honest finding">
          The thesis built extractive-QA labels with <code>context.find(answer)</code>. Because a
          plain-language answer is a <em>rewrite</em>, it is almost never a verbatim substring of the
          report, so the labels collapse to the <code>[CLS]</code> token. Extractive span-QA cannot
          express an abstractive rewrite; the generative approach is the one that fits. This
          negative result is preserved rather than hidden.
        </Section>

        <Section title="Evaluation">
          Summaries are scored with ROUGE-1/2/L, token-F1, BLEU and exact match. These n-gram metrics
          understate faithful paraphrases, so they are reported as complementary signals, never as
          proof of quality. Benchmarks record software versions, a seed, and a fingerprint of the
          exact examples for reproducibility, and are kept separate from the interactive demo.
        </Section>

        <Section title="Limitations and responsible use">
          Generated summaries are AI-generated research communication, <strong>not medical
          advice</strong>, and may contain errors, so verify them against the source. The default
          retrieval embedder is dependency-free and deliberately weak; stronger embeddings are
          optional. Numbers shown on synthetic data are illustrative, not real results.
        </Section>
      </div>
    </article>
  );
}
