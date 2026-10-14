# Reproduce: full pipeline + model training

End-to-end steps to run the whole pipeline on the raw PDF corpus
(`ClinicalTrials_Dataset/`): preprocess → build → split → index → baseline
benchmark → fine-tune a model → evaluate → load everything into the DB so it
shows up in the API/UI.

Run from the project root with the venv active.

> **Note on Python version.** The project targets **Python 3.10**. These steps
> were last run on **Python 3.14**, which is newer than much of the ML stack
> supports, so steps 5–6 pin specific versions and patch one line of code to
> work around it. On a 3.10/3.11 interpreter, `pip install -e ".[ml]"` works
> as-is and steps 5–6 are unnecessary.

## 0. Setup

```bash
cd /path/to/PLS_of_Clinical_Trials
source .venv/bin/activate
# first time only:
# python3 -m venv .venv && source .venv/bin/activate && pip install -e ".[dev,api]"
```

## 1. Clean the database (optional — start fresh)

```bash
alembic downgrade base
alembic upgrade head
```

## 2. Preprocess the PDFs → DB

```bash
# optional: preview how PDFs pair into trials
pls ingest --raw-dir ClinicalTrials_Dataset --dry-run

# real ingest: writes a records JSON and loads into the DB
pls ingest --raw-dir ClinicalTrials_Dataset --out data/processed/trials_full.json --to-db
```

## 3. Build examples → split → RAG index

```bash
pls build --db data/processed/trials_full.json --out data/processed/examples_full.jsonl
pls split --examples data/processed/examples_full.jsonl --out-dir data/processed/splits_full
pls index --records data/processed/trials_full.json
```

## 4. Baseline benchmark (fast, no ML deps) → DB

```bash
pls benchmark --examples data/processed/examples_full.jsonl \
  --backends "lead-1,lead-2,lead-3" \
  --out-dir data/processed/benchmark_full --to-db
```

## 5. Install the ML stack (with Python 3.14 workarounds)

```bash
pip install -e ".[ml]"                 # torch, transformers, datasets
pip install "accelerate>=1.1.0"        # the HF Trainer needs it; not pinned by the project

# 3.14 only: datasets<4 / dill 0.3.x crash in datasets.map() on Python 3.14.
# Pin the 3.14-compatible versions:
pip install -U "transformers>=5" "datasets>=5" "huggingface-hub>=2" \
  "dill>=0.4.1" "multiprocess>=0.70.18"
```

Sanity check that `datasets.map()` works:

```bash
python -c "import datasets; datasets.Dataset.from_dict({'a':['x']}).map(lambda b:{'n':[1]}, batched=True); print('ok')"
```

## 6. Code patch for transformers 5 (one line)

transformers 5 renamed the `Seq2SeqTrainer` `tokenizer` argument to
`processing_class`. In `src/pls_ct/training/finetune.py`, inside the
`Seq2SeqTrainer(...)` call:

```diff
-        tokenizer=tokenizer,
+        processing_class=tokenizer,   # transformers>=5 renamed this arg
```

(Not needed on transformers 4.x / Python 3.10.)

## 7. Train (flan-t5-small, 1 epoch, CPU)

```bash
pls train --splits-dir data/processed/splits_full \
  --model google/flan-t5-small --epochs 1 \
  --out-dir artifacts/ft_flan_t5_small
```

The fine-tuned model is written to `artifacts/ft_flan_t5_small/`.

Scale knobs: `--epochs N`; `--model google/flan-t5-base --lora`
(LoRA needs `pip install -e ".[peft]"`). CPU-only training is slow — base + LoRA
can take hours; Mistral-7B fine-tuning is not feasible on CPU.

## 8. Evaluate the fine-tuned model vs baseline → DB

```bash
pls benchmark --examples data/processed/splits_full/test.jsonl \
  --backends "hf:artifacts/ft_flan_t5_small,lead-2" \
  --out-dir data/processed/benchmark_ft --to-db
```

`hf:<path>` loads a local fine-tuned model directory as a backend.

## 9. Verify it landed in the DB / UI

```bash
pls experiments
curl -s localhost:8000/api/stats
```

## Gotchas

- **The API runs with `--reload`.** Editing anything under `src/` (e.g. step 6)
  restarts it, and it can be killed under training memory pressure. Either stop
  the API before training, or make the edit *before* starting the API. Restart
  with `uvicorn pls_ct.app.main:app --reload`.
- **Root cause of the dependency pain is Python 3.14.** On a 3.10/3.11 venv,
  skip the pins in step 5 and the patch in step 6.
- **CPU only on this machine** (no GPU): keep models small for a real run.
