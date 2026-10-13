# Project Audit

**Date:** 2026-10-13
**Auditor:** Senior engineering pass over the original thesis repository, before any implementation.
**Source of truth:** the actual files in this repo (not the README prose, not the published thesis).

---

## 1. What this project is

A Master's thesis (Aristotle University of Thessaloniki, School of Informatics, MSc Data & Web Science, submitted Sept 2024) on **Plain Language Summarization (PLS) of clinical trials**: turning dense clinical-trial result documents into summaries a non-specialist can read.

Published thesis: http://ikee.lib.auth.gr/record/359574

The abstract claims a custom dataset of **286 clinical trials** with simplified summaries, evaluated with **two models**: a fine-tuned **DistilBERT** and **Mistral-7B-Instruct**.

## 2. Repository inventory (as committed)

> Note: this inventory reflects the repo **at audit time**. The thesis code below
> (`Extra Code/`, `Preprocess Dataset/`, `model.ipynb`) has since been moved intact to
> `legacy/` and re-implemented in `src/pls_ct/`; see `legacy/README.md`.

| Path | Tracked in git? | Role |
|---|---|---|
| `README.md` | yes | Thesis overview + tech list |
| `model.ipynb` | yes | Main notebook: DistilBERT QA train + eval |
| `Preprocess Dataset/parser.py` | yes | PDF → XML section extraction (`pdfminer`) |
| `Preprocess Dataset/xml2json.py` | yes | Pair trial+summary XML → `database.json` |
| `Preprocess Dataset/finalDataset.ipynb` | yes | Clean DB, map Q→sections, build triples, split |
| `Preprocess Dataset/fixXMl.ipynb` | yes | Normalize/rename XML sections |
| `Extra Code/train_model.py` | yes | DistilBERT extractive-QA fine-tuning |
| `Extra Code/predict_and_evaluate.py` | yes | DistilBERT inference + metrics |
| `Extra Code/common_functions.py` | yes | `prepare_data` + metrics (EM/F1/BLEU/ROUGE) |
| `Extra Code/evaluate.py` | yes | Metrics over saved LLM-answer JSON (dup of metrics) |
| `Extra Code/pretrained.py` | yes | Mistral-7B-Instruct zero-shot via llama.cpp |
| `Extra Code/gpt4all.ipynb` | yes | GPT4All experiment |
| `Extra Code/advanced_rag.ipynb` | yes | Early RAG experiment |
| `ClinicalTrials_Dataset/` (561 PDFs, ~368 MB) | **NO** (untracked) | Raw Novartis PDFs |
| `database.json`, `FinalDataset/`, checkpoints | **absent** | Generated locally during thesis; not in repo |

**Key fact:** the entire git repo is ~33 KB. The data, the processed dataset, and all model checkpoints exist (or existed) only on the author's local machine. Nothing large was ever committed.

## 3. The actual pipeline (verified from code)

```
Novartis PDFs (report + paired patient-summary, matched by protocol ID)
   │  parser.py  (pdfminer: detect bold section headers via regex → XML)
   ▼
per-PDF XML (sections)
   │  fixXMl.ipynb  (normalize/rename sections, map question variants)
   ▼
normalized XML
   │  xml2json.py  (match report+summary by ID prefix)
   ▼
database.json  { trial_name, trial:{sections}, summary:{questions} }
   │  finalDataset.ipynb  (strip Novartis boilerplate/URLs/phones, spellcheck,
   │                       map 8 canonical questions → report sections,
   │                       build (question, context, answer) triples, 85/15 split)
   ▼
FinalDataset/{train,test}_<question>.json
   │
   ├── train_model.py → DistilBERT (extractive QA, span prediction)
   └── pretrained.py  → Mistral-7B-Instruct (zero-shot generation, llama.cpp GGUF)
   ▼
predict_and_evaluate.py / evaluate.py → EM, F1, BLEU, ROUGE-1/2/L
```

The 8 canonical questions and their report-section mapping (from `finalDataset.ipynb`):

| Patient question | Report section(s) used as context |
|---|---|
| Why was the research needed? | Objectives |
| How long was the trial? | Study Start/End Dates, Reason for Termination |
| Who was in this clinical trial? | Study Population: Key Inclusion/Exclusion Criteria |
| What treatments did the participants take? | Statistical Methods, Trial Analysis |
| What happened during the trial? | Study Design/Methodology |
| What were the results of the trial? | Trial Analysis, Conclusion |
| What adverse events did participants report? | Trial Analysis |
| How has this trial helped? | Conclusion |

## 4. Findings

### 4.1 Critical — the DistilBERT framing is scientifically mismatched
`train_model.py:24` and `common_functions.py:25` build labels with
`answer_start = context.find(answer)`. The "answer" is the **rewritten plain-language** summary; it is almost never a verbatim substring of the clinical report "context", so `.find()` returns `-1` for the overwhelming majority of examples. The preprocessing then sends those to the "answer not in span" branch and sets `start_positions = end_positions = 0` (the `[CLS]` token).

**Consequence:** DistilBERT was largely trained to point at `[CLS]` ("no answer"). Extractive span-QA cannot express an abstractive rewrite. This is the central limitation of the thesis and **must be preserved and stated honestly**, not hidden. The generative path (Mistral) is the approach that actually matches the task.

### 4.2 High — not reproducible as-is
- No `requirements.txt` / `pyproject.toml` / environment pin anywhere. README lists libraries prose-only ("Python 3.10", Transformers, LangChain, PyTorch, …) with no versions.
- Hardcoded paths everywhere: `FinalDataset/...`, `FinalDataset/FullDataset2/FullDataset2/`, the GGUF path `Mistral-7B-Instruct-v0.1.gguf/mistral-7b-instruct-v0.1.Q5_K_M.gguf`.
- The intermediate artifacts needed to rerun (`database.json`, `FinalDataset/`, cleaned DBs `database_clean2.json`, `tables.md`) are **not in the repo** and are produced by notebook cells in an order that isn't documented.
- Notebooks mix commented-out training cells with live cells; execution order is implicit.

### 4.3 Medium — duplication & dead paths
- Metrics code is duplicated verbatim in `common_functions.py` and `evaluate.py`.
- `prepare_data` exists in both `common_functions.py` (with `trial_name`) and `model.ipynb` (without).
- `advanced_rag.ipynb` / `gpt4all.ipynb` are exploratory and not wired into the reported results.

### 4.4 Medium — data & licensing risk
- `ClinicalTrials_Dataset/` holds 561 Novartis PDFs (patient summaries + result reports). `finalDataset.ipynb` strips Novartis URLs/phone numbers, confirming provenance.
- **Decision (2026-10-13):** treat as **non-redistributable**. They stay gitignored; the public project ships a labeled synthetic sample. See `DATASET_AND_PIPELINE.md`.

### 4.5 Low — correctness nits worth noting (not fixing blindly)
- `parser.py` table handling flattens every table cell into a single-column `<row><cell>` — table structure is effectively lost.
- Section detection relies on the PDF font being tagged `bold`; scanned/flattened PDFs will silently yield empty sections (no OCR fallback, no validation).
- `predict_and_evaluate.py:48` returns `""` when `end < start` but doesn't handle the no-answer (`[CLS]`) case, inflating empty predictions.

## 5. What must be preserved (the scientific contribution)
1. The **paired dataset construction** (report ↔ plain-language summary, matched by protocol ID, 8-question schema). This is the real asset.
2. The **two-model comparison** framing (small fine-tuned encoder vs. instruction-tuned generative LLM) and its honest negative result for extractive QA.
3. The **evaluation metric suite** (EM, F1, BLEU, ROUGE) as the baseline, extended later (BERTScore, readability, factuality) per `RESEARCH_AND_MODELS.md`.

## 6. Reusable components
- `parser.py` section schemas and the question→section mapping — reusable, need parametrized paths + validation.
- Metrics functions — consolidate the two copies into one tested module.
- The question canonicalization map in `parser.py` / `fixXMl.ipynb` — reusable as data.

## 7. Immediate roadmap (see IMPLEMENTATION_PLAN.md)
Milestone 1 (this audit + 4 companion docs) → Milestone 2: make the pipeline reproducible (packaged, config-driven, tested, CPU-first/GPU-auto, synthetic demo data) before any web platform work.
