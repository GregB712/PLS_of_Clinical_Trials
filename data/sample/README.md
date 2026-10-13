# Synthetic sample data

**Everything in this directory is fictional.** No real patients, drugs, trials, or
results. It exists so the pipeline, tests, and CI run with **zero** real data, since
the real Novartis corpus is non-redistributable (see `../../docs/DATASET_AND_PIPELINE.md`).

`trials.json` is a JSON list of trial records in the canonical schema
(`trial_name`, `report_sections`, `summary_sections`, `source: "synthetic"`).
Never present metrics computed on this sample as real results.
