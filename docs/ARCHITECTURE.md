# Architecture

**Date:** 2026-10-13
**Scope of this document:** the architecture committed to **now** is the reproducible research core (Milestones 1–2). The full platform (FastAPI/Postgres/Next.js/RAG) is described as a *later* target so the core is designed to grow into it without rework — but is **not** built yet, per the agreed priority.

## 1. Principles
- **Scientific honesty first.** Reproducible, seeded, no fabricated metrics, limitations stated.
- **CPU-first, GPU-automatic.** All model code selects device at runtime; nothing requires a GPU.
- **No non-redistributable data in git.** Synthetic sample is the only committed data.
- **Simplicity.** One lean Python package; config over hardcoded paths; no framework added without a concrete need. The original research code is preserved, not discarded.

## 2. Package layout (Milestone 2 target)

```
src/pls_ct/                     # installable package ("PLS of Clinical Trials")
  config.py                     # paths + settings from env, with sane defaults
  device.py                     # CPU-first / GPU-auto selection helper
  ingestion/
    parser.py                   # PDF→sections (refactor of legacy/Preprocess Dataset/parser.py)
    normalize.py                # section normalization (from fixXMl.ipynb)
    pair.py                     # report+summary → database.json (from xml2json.py)
  dataset/
    clean.py                    # boilerplate strip / cleanup (from finalDataset.ipynb)
    build.py                    # Q→section mapping → QA triples
    split.py                    # split-by-trial train/val/test, seeded
  models/
    base.py                     # SummarizerBackend protocol (unified interface)
    extractive_qa.py            # DistilBERT backend (preserved baseline)
    generative.py               # HF/GGUF generative backend (Mistral etc.)
  evaluation/
    metrics.py                  # consolidated EM/F1/BLEU/ROUGE (+ hooks for BERTScore/readability)
    harness.py                  # run model(s) over a split → machine-readable results
  cli.py                        # `pls` CLI: ingest | build | split | train | predict | evaluate

data/sample/                    # committed synthetic trials (labeled)
data/{raw,interim,processed}/   # gitignored, local-only
tests/                          # pytest
docs/                           # these planning docs
legacy/                         # ORIGINAL thesis code, preserved verbatim (archived)
```

The original scripts/notebooks are preserved **verbatim under `legacy/`** (moved there intact, git history kept; ruff is configured to skip it) as the thesis record. The new `pls_ct` package *re-implements the same logic* in importable, tested, path-parameterized form rather than editing the originals. See `legacy/README.md` for the old→new mapping.

## 3. Unified model interface

```python
class SummarizerBackend(Protocol):
    name: str
    def summarize(self, context: str, question: str, cfg: GenConfig) -> SummaryResult: ...
```

`SummaryResult` carries: text, model id, generation config, input/output token counts (when available), latency, warnings, run id, source provenance (`trial_name` + section). Unavailable metrics are returned as `None`, never fabricated. This is the seam the later hosted-provider abstraction (Claude/OpenAI/Gemini) and the web API plug into unchanged.

## 4. Device strategy
`device.py` resolves, in order: explicit env override → CUDA if `torch.cuda.is_available()` → MPS (Apple) if present → CPU. Generative GGUF backend sets `n_gpu_layers` from the resolved device. Everything has a working CPU path.

## 5. Configuration & secrets
- Settings via environment with defaults in `config.py` (data dirs, model ids, seed, device override). `.env.example` ships placeholders only; `.env` is gitignored.
- Hosted-provider API keys (later milestone): env / local secrets only, never committed, never logged, masked in any UI.

## 6. Growth path to the full platform (NOT built now)
The package is the domain/ML core. Later milestones wrap it:
- **Persistence:** `data/processed/*.json(l)` is the interim store; migrates to Postgres (+ pgvector) when the API lands. The canonical record schema (`DATASET_AND_PIPELINE.md §2`) is DB-ready.
- **API:** FastAPI imports `pls_ct` backends/harness; long jobs (ingest/train) become background jobs with persisted status.
- **RAG:** `ingestion` already chunks by section → embeddings + retrieval layer added later.
- **Frontend:** Next.js consumes the API; no business logic in the browser.

Deferring these keeps the core small and correct first (Karpathy simplicity), and avoids speculative infrastructure.
