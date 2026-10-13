# Dataset and Pipeline

**Date:** 2026-10-13

## 1. Provenance & licensing

The raw corpus in `ClinicalTrials_Dataset/` is **561 Novartis clinical-trial PDFs** (`novartisclinicaltrials.com` / `novctrd.com` Trial Results Summaries), in two paired kinds:

- **Clinical Trial Results report** — the dense source document (`<ProtocolID>.pdf`).
- **Patient Summary** — the plain-language target (`<ProtocolID>_PatientSummary_English-US_<date>.pdf`, also `PediatricPatientSummary`).

They pair by **protocol-ID prefix** (e.g. `CAIN457A2325`). ~270 unique prefixes; ~282 summary PDFs; ~281 report PDFs. The thesis reports **286 usable trials** after pairing/cleaning.

**Licensing decision (2026-10-13): non-redistributable.** Rationale: Novartis-sourced documents whose redistribution terms are not established. Therefore:

- `ClinicalTrials_Dataset/` and all derived artifacts are **gitignored** (`.gitignore` already added).
- The public repo ships a **small, clearly-labeled synthetic sample** (`data/sample/`, invented trials in the same schema) so tests, CI, and a demo run work with **zero** real data.
- Ingestion runs locally against the real PDFs on the author's machine; nothing derived from them is committed.

## 2. Canonical data model (target schema)

One record per trial, produced by ingestion:

```jsonc
{
  "trial_name": "CXXX999X9999",            // protocol ID (provenance key)
  "report_path": "…/CXXX999X9999.pdf",      // local only
  "summary_path": "…/CXXX999X9999_PatientSummary_…pdf",
  "report_sections":  { "Objectives": "…", "Conclusion": "…", … },
  "summary_sections": { "Why was the research needed?": "…", … },
  "source": "novartis",
  "ingested_at": "2026-10-13T…Z"
}
```

Section vocabularies are fixed (from `parser.py`): ~22 report sections, 18 canonical patient-summary questions (after mapping the ~60 observed phrasings down to 8–18 canonical ones).

## 3. Pipeline stages (reproducible redesign)

Each stage is a pure function with explicit input/output paths (config-driven, no hardcoded `FinalDataset/…`). Stages are **idempotent**: rerunning does not duplicate records.

| Stage | Input | Output | From original |
|---|---|---|---|
| `ingest` | raw PDFs dir | `data/interim/<id>.xml` | `parser.py` |
| `normalize` | interim XML | normalized XML | `fixXMl.ipynb` |
| `pair` | report+summary XML | `data/processed/database.json` | `xml2json.py` |
| `clean` | `database.json` | `database_clean.json` | `finalDataset.ipynb` (boilerplate strip, spellcheck) |
| `build` | clean DB | `data/processed/qa/<question>.jsonl` | `finalDataset.ipynb` (Q→section mapping → triples) |
| `split` | per-question QA | `train/val/test` per question | `finalDataset.ipynb` (was 85/15; add val) |

**Split policy:** split **by trial**, not by row, so the same trial never appears in both train and test (prevents leakage across the 8 questions). The original did an 85/15 per-question shuffle; the leakage risk is documented in `RESEARCH_AND_MODELS.md` and fixed here. Fixed `random_state` for reproducibility.

## 4. Known data-quality hazards (carry forward from audit)
- Section detection depends on PDF bold-font tagging → scanned/flattened PDFs yield empty sections. Ingestion will **validate** non-empty section coverage and record a per-file status instead of silently emitting blanks.
- Table structure is lost by the original parser (single-column cells). Tables are out of scope for the research core; noted for later.
- Plain-language answers are rewrites, not extracts → extractive-span labels are mostly degenerate (see audit §4.1). The dataset is fundamentally an **abstractive** (report-section → plain-language) pairing.

## 5. Synthetic sample (`data/sample/`)
A handful of fully-invented trials in the exact schema above, each covering the 8 canonical questions, clearly marked `"source": "synthetic"`. Purpose: make `build`/`split`/train/eval runnable and testable without the real corpus. **Never presented as real results.**

## 6. Import/migration requirements (per Claude_Prompt.md §3, honored at research-core scope)
- Batch processing over a directory; dry-run mode; resumable; per-file status + error log; duplicate detection by protocol ID + file hash; preserve source filenames. These become the `ingest` CLI's flags in Milestone 2.
