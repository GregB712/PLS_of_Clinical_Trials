# Legacy — original thesis code (archived, unmaintained)

This directory preserves the **original Master's-thesis code verbatim**, kept for the
scientific/historical record. It is **not used at runtime** and is **not maintained** — the
platform re-implements all of this logic in the installable `pls_ct` package (`src/pls_ct/`),
with configuration instead of hardcoded paths, tests, and a CLI.

| Legacy file | Re-implemented in |
|---|---|
| `Preprocess Dataset/parser.py` (PDF→XML sections) | `pls_ct.ingestion.parser` + `pls_ct.ingestion.sections` |
| `Preprocess Dataset/xml2json.py` (pair report+summary) | `pls_ct.ingestion.pair` |
| `Preprocess Dataset/finalDataset.ipynb` / `fixXMl.ipynb` | `pls_ct.dataset.clean` / `build` / `split` |
| `Extra Code/common_functions.py`, `evaluate.py` (metrics) | `pls_ct.evaluation.metrics` |
| `Extra Code/train_model.py`, `predict_and_evaluate.py` (DistilBERT QA) | `pls_ct.models.extractive_qa` + `pls_ct.training` |
| `Extra Code/pretrained.py` (Mistral via llama.cpp) | `pls_ct.models.generative` |
| `model.ipynb` (main train/eval notebook) | the `pls` CLI (`build`/`split`/`train`/`evaluate`) |

See `docs/PROJECT_AUDIT.md` for the full audit of this code, including the key finding that
the extractive-QA labels (`context.find(answer)`) collapse to `[CLS]` for abstractive targets.
