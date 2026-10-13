# Research and Models

**Date:** 2026-10-13

This documents the baseline from the thesis, the candidate models for the upgrade, and the evaluation methodology. It separates **what the thesis did** from **proposed additions**. No performance number is asserted here unless it is actually measured in this repo — the thesis's own numbers live only in the published document (http://ikee.lib.auth.gr/record/359574) and **must be re-measured, not copied as fact**.

## 1. Baseline models (from the thesis — preserve)

### 1.1 DistilBERT (extractive QA) — the honest negative baseline
- **Identifier:** `distilbert-base-uncased` fine-tuned via `DistilBertForQuestionAnswering`.
- **Params:** ~66M. **License:** Apache-2.0. **Runs on:** CPU (slow) or any GPU.
- **Framing:** extractive span prediction over (question, report-section-context).
- **Known defect:** targets built with `context.find(answer)`; plain-language answers are rewrites → labels collapse to `[CLS]` (audit §4.1). Keep as a documented baseline that demonstrates *why extractive QA is the wrong tool* for abstractive PLS.
- **Fine-tuning:** feasible on CPU for the small dataset; trivial on GPU. Device-agnostic.

### 1.2 Mistral-7B-Instruct (zero-shot generation) — the task-appropriate baseline
- **Identifier (thesis):** `mistralai/Mistral-7B-Instruct-v0.1`, run as `mistral-7b-instruct-v0.1.Q5_K_M.gguf` via `llama.cpp` / LangChain `LlamaCpp`.
- **Params:** 7.2B. **License:** Apache-2.0.
- **Hardware:** Q5_K_M GGUF ≈ 5 GB; runs CPU-only (slow, minutes/trial) or offloaded to GPU. Fits the **CPU-first, GPU-if-available** constraint.
- **Framing:** instruction prompt (CONTEXT + QUESTION → plain-language answer). This matches the abstractive task.

## 2. Candidate additions (research, not yet chosen)

Treated as **experiments to run**, not predetermined winners. Each needs a pilot on the synthetic sample / a small real slice before any full run, and a resource estimate (Claude_Prompt.md execution rule 7).

| Candidate | Why consider | License | CPU-first fit |
|---|---|---|---|
| **Flan-T5 / LongT5 (base/large)** | encoder-decoder actually built for abstractive summarization; fine-tunable on small data | Apache-2.0 | base runs on CPU; large wants GPU |
| **BART / `facebook/bart-large-cnn`** | strong summarization prior | MIT | CPU-OK for inference |
| **BioBART / Clinical-T5 / SciFive** | biomedical-domain pretraining | mixed (check per-model) | base CPU-OK |
| **Qwen2.5-Instruct / Llama-3.x-Instruct (GGUF)** | stronger modern instruct LLMs, quantized for CPU | Apache-2.0 / Llama community | GGUF CPU-OK, GPU faster |
| **Hosted: Claude / GPT / Gemini** | ceiling reference; user-supplied keys only | commercial API | N/A (API) |

PEFT: **LoRA/QLoRA** for any ≥7B local fine-tune (keeps VRAM/CPU-RAM tractable). Full fine-tune only for the small encoder-decoders.

## 3. Evaluation methodology

### 3.1 Baseline metrics (keep — already implemented)
Exact-Match, SQuAD-style token-F1, BLEU (smoothing method4), ROUGE-1/2/L. Consolidate the duplicated implementations (`common_functions.py`, `evaluate.py`) into one tested module.

### 3.2 Proposed additions (after literature review)
- **BERTScore** — semantic overlap, better for abstractive rewrites than n-gram metrics.
- **Readability** — Flesch-Kincaid / Flesch Reading Ease (the whole point is *plain* language; readability should be measured, not assumed).
- **Length / compression ratio.**
- **Factual-consistency signal** — NLI-based or QA-based faithfulness check (report-grounded), flagged as a research signal, not ground truth.
- **Human eval rubric** — accuracy, completeness, readability, usefulness (defined, even if not run at scale).

### 3.3 Harness requirements
Reproducible splits (by trial), fixed seeds, recorded model+generation+software versions, per-example + aggregate machine-readable results, graceful handling of failed generations, comparison of multiple models on identical examples. Benchmark results kept separate from interactive/demo outputs.

## 4. Caveats on comparison
- n-gram metrics (BLEU/ROUGE/EM) systematically **understate** abstractive quality — a faithful paraphrase scores low. Report them, but lead with BERTScore + readability + human rubric.
- Reference summaries are **not** absolute ground truth for every factual claim; don't treat them as such.
- Any cross-model comparison must use the identical evaluation set, stated explicitly.
