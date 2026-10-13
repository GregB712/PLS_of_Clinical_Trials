# Implementation Plan

**Date:** 2026-10-13
**Agreed priority:** reproducible research core first (Milestones 1–2). Web platform deferred.

Each task lists a **verify** check (goal-driven: the task is done only when the check passes).

---

## Milestone 1 — Audit & planning ✅ (this commit)
- [x] Repository audit → `docs/PROJECT_AUDIT.md`
- [x] Architecture → `docs/ARCHITECTURE.md`
- [x] Dataset & pipeline → `docs/DATASET_AND_PIPELINE.md`
- [x] Research & models → `docs/RESEARCH_AND_MODELS.md`
- [x] This plan
- [x] `.gitignore` protecting the non-redistributable corpus
- **Verify:** docs exist, are grounded in real files, and reflect the three scope decisions. ✔

## Milestone 2 — Reproducible research core ✅ (done, verified)

Status: all tasks below implemented; `ruff check .` clean, `pytest` 32 passing,
`pls demo` runs the full flow on synthetic data (CPU-only, no ML deps). The one
deferred piece is transformer **fine-tuning** as a CLI command — the preserved
`Extra Code/train_model.py` remains the training path for now (kept out of an
easy-run command deliberately, per the "don't trigger expensive training" rule).

### 2.1 Project scaffolding
- `pyproject.toml` with pinned deps (torch, transformers, datasets, pdfminer.six, rouge-score, nltk, scikit-learn, pyspellchecker; dev: pytest, ruff). Installable `pls_ct` + `pls` CLI.
- `.env.example`, package skeleton per ARCHITECTURE §2.
- **Verify:** `pip install -e .` succeeds; `pls --help` runs.

### 2.2 Device helper
- `device.py` CPU-first / CUDA / MPS auto-select + env override.
- **Verify:** unit test forces each branch via monkeypatch; returns `"cpu"` with no GPU.

### 2.3 Metrics (consolidate + test)
- One `evaluation/metrics.py` merging the two duplicate copies; identical numeric behavior.
- **Verify:** tests pin EM/F1/BLEU/ROUGE on known pairs (incl. identical strings → F1=100, EM=1).

### 2.4 Synthetic sample
- `data/sample/` : invented trials (8-question schema), labeled `source: synthetic`.
- **Verify:** `build` + `split` produce non-empty train/val/test from the sample only.

### 2.5 Dataset build & split (refactor, no hardcoded paths)
- `dataset/clean.py`, `build.py`, `split.py` (split **by trial**, seeded). Q→section map as data.
- **Verify:** idempotent (rerun → identical output, no dupes); no trial in two splits; tests cover the leakage guard.

### 2.6 Ingestion (refactor `parser.py`)
- `ingestion/parser.py` + `normalize.py` + `pair.py`, path-parameterized; per-file status + error log; dry-run; dedup by ID+hash.
- **Verify:** runs on a tiny committed text/XML fixture (not a real PDF); emits status report; empty-section detection fires on a blank fixture.

### 2.7 Model backends
- `models/base.py` protocol; `extractive_qa.py` (DistilBERT, preserved + the `[CLS]` defect documented in-code); `generative.py` (HF seq2seq / GGUF, device-agnostic, lazy-loaded).
- **Verify:** backend tests use a tiny/stub model (no large download in CI); `SummaryResult` well-formed; unavailable metrics are `None`.

### 2.8 Evaluation harness
- `evaluation/harness.py`: run backend(s) over a split → per-example + aggregate JSON; handles failed generations.
- **Verify:** end-to-end on synthetic sample with a stub backend produces a results file + aggregate table.

### 2.9 Tests, lint, CI, docs
- `pytest` green; `ruff` clean; GitHub Actions (install, lint, test — no model downloads, no paid APIs).
- README: honest reproduction instructions (synthetic path that works for anyone; real-data path for the author).
- **Verify:** `ruff check . && pytest` pass locally; CI workflow present.

**Milestone 2 definition of done:** a clone with no real data can `pip install -e .`, run the full `ingest(stub)/build/split/evaluate(stub)` flow on the synthetic sample, and pass tests — CPU-only. The author can point config at the real `ClinicalTrials_Dataset/` and reproduce the thesis-style pipeline + metrics.

---

## Later milestones (deferred — not started)
- **M3** Document ingestion + persistent DB (Postgres/pgvector), MarkItDown-based PDF→Markdown, migrations.
- **M4** Unified summarization engine + hosted-provider abstraction (user-supplied keys).
- **M5** Benchmarking/experiment tracking + optional LoRA/QLoRA fine-tuning.
- **M6** RAG assistant (chunking, retrieval, citations, retrieval eval).
- **M7** Web app (landing, dataset explorer, live demo, comparison dashboard, RAG page).
- **M8** Integration, security, Docker, CI, docs.
- **M9** Portfolio polish.

Each later milestone starts only after the prior one is runnable and tested, per execution rules.

## Risks / open items
- Re-running ingestion needs the real PDFs locally (author-only); CI exercises the synthetic path.
- Exact thesis metric numbers are not in the repo; they will be **re-measured**, labeled as such, and never copied from the published thesis as if reproduced here.
- Generative inference on CPU is slow; harness runs a small slice by default with a documented way to scale up on GPU.
