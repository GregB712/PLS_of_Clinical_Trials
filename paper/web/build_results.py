#!/usr/bin/env python3
"""Extract the full-dataset numbers shown on the web app's Landing and Model comparison pages.

Reads the thesis result tables (the CSVs that Tables/make_tables.py also reads) and writes
frontend/src/content/thesis_results.json. Nothing is typed by hand except the corpus funnel,
which has no CSV; those counts are checked against the committed thesis text (Chapter 3),
so the build fails if the paper and the web page ever disagree.

Run from the repository root:
  python paper/web/build_results.py [--tables paper_results/tables]
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "frontend" / "src" / "content" / "thesis_results.json"
CHAPTER3 = ROOT / "paper" / "Chapters" / "Chapter3.tex"

# Corpus funnel (Chapter 3, Section "Corpus"); verified against the LaTeX text below.
FUNNEL = {"pdfs": 561, "protocolIds": 273, "pairs": 256, "usableTrials": 212}

METRICS = ["rouge1", "rouge2", "rougeL", "bleu", "token_f1", "bertscore_f1"]


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def check_funnel() -> None:
    text = re.sub(r"\s+", " ", CHAPTER3.read_text(encoding="utf-8"))
    for phrase in (
        f"{FUNNEL['pdfs']} PDF documents",
        f"cover {FUNNEL['protocolIds']} protocol IDs",
        f"{FUNNEL['pairs']} IDs have both a report and a patient summary",
        f"{FUNNEL['usableTrials']} usable trials",
    ):
        if phrase not in text:
            raise SystemExit(f"error: corpus count not found in {CHAPTER3.name}: {phrase!r}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--tables", type=Path, default=ROOT / "paper_results" / "tables")
    t = ap.parse_args().tables
    check_funnel()

    coverage = rows(t / "dataset_question_coverage.csv")
    examples = sum(int(r["usable"]) for r in coverage)
    splits = {
        r[""]: {"trials": int(r["trials"]), "examples": int(r["examples"])}
        for r in rows(t / "dataset_splits.csv")
    }
    if sum(s["examples"] for s in splits.values()) != examples:
        raise SystemExit("error: split sizes do not add up to the example count")
    stats = {
        r[""]: {"mean": float(r["mean"]), "median": float(r["50%"])}
        for r in rows(t / "dataset_text_statistics.csv")
    }

    systems = []
    for r in rows(t / "main_results.csv"):
        if r["main"] != "True":
            continue
        systems.append(
            {
                "id": r["run"],
                "model": r["model"],
                "family": r["family"],
                "decoding": r["decoding"],
                "n": int(r["n"]),
                "metrics": {
                    m: {
                        "mean": round(float(r[m]), 2),
                        "lo": round(float(r[f"{m}_lo"]), 2),
                        "hi": round(float(r[f"{m}_hi"]), 2),
                    }
                    for m in METRICS
                },
            }
        )
    seeds = {r[""]: r for r in rows(t / "seed_variance_ft_small.csv")}
    lead3 = next(s for s in systems if s["id"] == "lead-3")

    out = {
        "source": "Barmpas, Plain Language Summarization of Clinical Trials (MSc thesis, 2026)",
        "corpus": {
            **FUNNEL,
            "examples": examples,
            "questions": len(coverage),
            "questionsWithExamples": sum(1 for r in coverage if int(r["usable"]) > 0),
        },
        "splits": splits,
        "text": {
            "contextWordsMedian": stats["context_words"]["median"],
            "referenceWordsMedian": stats["reference_words"]["median"],
            "contextFkglMedian": stats["context_fkgl"]["median"],
            "referenceFkglMedian": stats["reference_fkgl"]["median"],
            "referenceNovelBigramsMean": stats["novel_bigrams"]["mean"],
        },
        "headline": {
            "model": "Flan-T5-small, fine-tuned (3 seeds)",
            "rougeLMean": round(float(seeds["mean"]["rougeL"]), 2),
            "rougeLStd": round(float(seeds["std"]["rougeL"]), 2),
            "lead3RougeL": lead3["metrics"]["rougeL"]["mean"],
        },
        "testSet": {"examples": splits["test"]["examples"], "trials": splits["test"]["trials"]},
        "systems": systems,
    }
    OUT.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}: {examples} examples, {len(systems)} systems")
    return 0


if __name__ == "__main__":
    sys.exit(main())
