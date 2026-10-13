# Master's Thesis: Plain Language Summarization of Clinical Trials

📘 **Thesis Title:** Plain Language Summarization of Clinical Trials  
🎓 **Institution:** Aristotle University of Thessaloniki  
📅 **Submission Date:** September, 2024
📄 **Published Version:** [ikee.lib.auth.gr link](http://ikee.lib.auth.gr/record/359574)

---

## 🧠 Overview

This repository contains the code and documentation related to my Master's Thesis submitted to the [School of Informatics](https://www.csd.auth.gr/en/) at the Aristotle University of Thessaloniki, as part of the MSc in Data and Web Science program.

The work focuses on:

> This thesis explores the challenge of making clinical trial findings accessible to the general public by translating them into plain language. It introduces a custom dataset of 286 clinical trials and their simplified summaries, and evaluates the performance of two NLP models—fine-tuned DistilBERT and Mistral-7B-Instruct—in generating readable, accurate translations. The work highlights both the potential and limitations of large language models in improving health communication.


For full details, please refer to the [ikee.lib.auth.gr link](http://ikee.lib.auth.gr/record/359574) hosted by the university library.

---

## 📂 Repository Structure

├── Extra Code/ # Additional scripts used for automation and testing 

├── Preprocess Dataset/ # Code for preprocessing the clinical trial dataset 

├── model.ipynb # Jupyter notebook for model training and evaluation

└── README.md # Project overview and documentation. You’re here!


---

## 🚀 Technologies Used

This thesis leverages modern machine learning and natural language processing (NLP) tools to build and evaluate models for plain language summarization of clinical trial documents. Key technologies and tools include:

- **Python 3.10** – Primary programming language for all experimentation and scripting.
- **Hugging Face Transformers** – Used for model loading, fine-tuning, and inference, especially with:
  - `DistilBERT`: a lightweight version of BERT fine-tuned on the custom clinical trial dataset.
- **LangChain** – For orchestrating interactions with large language models and managing prompt templates.
- **Mistral-7B-Instruct** – A powerful open-source large language model tested without fine-tuning for zero-shot summarization.
- **PyTorch** – Backend framework for training and fine-tuning transformer models.
- **Datasets Library (Hugging Face)** – Used to manage and manipulate text datasets efficiently.
- **scikit-learn & pandas** – For data preprocessing and analysis.
- **Matplotlib & Seaborn** – For generating visualizations of results and evaluation metrics.
- **Evaluation Metrics**:
  - **ROUGE**, **BLEU**, and **F1 Score** – Used to assess the performance of generated summaries.

Additional techniques applied include:
- **Gradient Checkpointing** and **Mixed Precision Training** – To optimize memory and computation during training.
- **Custom Prompt Engineering** – Designed to tailor responses from the Mistral model to clinical summarization tasks.

---

## 🔁 Reproducible research core

> This section documents an in-progress upgrade that makes the thesis pipeline
> reproducible. The original thesis code is preserved **verbatim** in `Extra Code/`,
> `Preprocess Dataset/`, and `model.ipynb`. Planning and findings live in [`docs/`](docs/)
> — start with [`docs/PROJECT_AUDIT.md`](docs/PROJECT_AUDIT.md).

**Data note:** the raw Novartis clinical-trial PDFs are treated as **non-redistributable**
and are gitignored. A small, clearly-labeled **synthetic** sample (`data/sample/`) ships so
the pipeline, tests, and CI run with zero real data. Synthetic numbers are illustrative, never real results.

### Install (CPU-only, no GPU required)

```bash
uv venv .venv && uv pip install --python .venv -e ".[dev]"   # or: python -m venv .venv && pip install -e ".[dev]"
```

The transformer baselines (DistilBERT, Mistral/T5, …) are an optional extra — install with
`pip install -e ".[ml]"` only when you want to run them. Device selection is **CPU-first and
uses a GPU automatically** when one is present (override with `PLS_DEVICE`).

### Run the pipeline end-to-end on the synthetic sample

```bash
pls demo                     # build → split (by trial) → evaluate (Lead baseline) → metrics
```

Or step by step (also works against the real corpus by pointing `--raw-dir`/`PLS_RAW_DIR` at it):

```bash
pls ingest  --raw-dir data/sample --out data/processed/database.json   # PDFs → records (real corpus)
pls build   --db data/sample/trials.json --out data/processed/examples.jsonl
pls split   --examples data/processed/examples.jsonl --out-dir data/processed/splits
pls evaluate --examples data/processed/splits/test.jsonl --backend lead --out data/processed/results.json
# transformer backends (need the [ml] extra): --backend distilbert  |  --backend hf:google/flan-t5-base
```

### Persist to a database (optional)

Trials are stored via SQLAlchemy — **SQLite by default** (no setup), or any backend via
`PLS_DATABASE_URL` (e.g. Postgres). Schema is managed with Alembic migrations.

```bash
alembic upgrade head                                   # create/upgrade schema (production path)
pls db-load --records data/sample/trials.json          # load canonical records (idempotent)
pls trials                                             # list stored trials
pls ingest --raw-dir data/sample --to-db               # ingest real PDFs straight into the DB
```

PDF → Markdown conversion (MarkItDown) is available with the `[pdf]` extra
(`pip install -e ".[pdf]"`); it preserves more structure than the section parser and feeds
the future RAG layer.

### Hosted LLM providers (optional, bring your own key)

Anthropic, OpenAI, and Gemini are available as drop-in summarization backends with the
`[providers]` extra (`pip install -e ".[providers]"`). Keys are read from the environment
(`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GOOGLE_API_KEY`) — never hardcoded, never logged,
masked in output. No developer key is ever consumed silently.

```bash
pls providers                                              # show providers + masked key status
export ANTHROPIC_API_KEY=sk-...                            # your key
pls evaluate --examples <split>.jsonl --backend anthropic:claude-sonnet-5-5 --out out.json
```

### Benchmark models against each other

Evaluate several backends on the *same* examples and get a reproducible comparison
(versions, seed, and a fingerprint of the exact examples are recorded):

```bash
pls benchmark --examples <split>.jsonl --backends "lead-1,lead-2,lead-3" --out-dir out/ --to-db
pls experiments                      # list stored benchmark runs
```

Writes `benchmark.json` + a Markdown `comparison.md`; `--to-db` persists an experiment.

### Fine-tuning (optional, GPU-gated)

A reproducible seq2seq fine-tune (early stopping, optional LoRA) lives in
`pls_ct.training`. It needs the `[ml]` extra (`[peft]` for LoRA), runs on CPU but is slow,
and uses a GPU automatically when present. It is **not** run in CI.

```bash
pip install -e ".[ml]" ".[peft]"
pls train --splits-dir data/processed/splits --model google/flan-t5-base --lora --out-dir artifacts/ft
```

### RAG research assistant

Index the trials, then ask questions and get answers **with citations** back to the source
trial/section. The default embedder is dependency-free (hashing); install `[rag]`
(`pip install -e ".[rag]"`) for stronger sentence-transformer retrieval.

```bash
alembic upgrade head
pls index --records data/sample/trials.json              # chunk + embed into the vector store
pls ask --query "What adverse events were reported?" --trial SYN001A2101 --k 3
pls rag-eval --examples data/processed/examples.jsonl --k 5   # recall@k / precision@k / MRR
```

The assistant states when the evidence is insufficient rather than guessing, treats
retrieved text as reference-only data, and (by construction) cannot execute tools.

### Develop

```bash
ruff check .      # lint (new code only; original thesis files are excluded)
pytest -q         # test suite (no model downloads, no paid APIs)
```

See [`docs/IMPLEMENTATION_PLAN.md`](docs/IMPLEMENTATION_PLAN.md) for milestone status and what's next.

## 📝 Citation

If you find this work useful, please consider citing:

@mastersthesis{Barmpas2025thesis, title = {Plain Language Summarization of Clinical Trials}, author = {Grigorios Barmpas}, school = {Aristotle University of Thessaloniki}, year = {2024}, url = {https://ikee.lib.auth.gr/record/359574} }

## 📬 Contact

For questions, collaborations, or discussions:

- GitHub: [GregB712](https://github.com/GregB712)
- Email: [gregorybarbas@gmail.com]

---

## 📌 Notes

> This repository is maintained as a public reference for academic and personal portfolio purposes.
