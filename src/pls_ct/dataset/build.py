"""Build (question, context, answer) examples from cleaned trial records.

Mirrors the thesis's "Database Mapping" step: for each trial and each of the 8
canonical questions, the context is the concatenation of the mapped report
section(s) and the answer is the matching plain-language summary section.

Examples with an empty context or empty answer are dropped and counted (the
original silently produced blanks). Output is a list of dicts — JSONL-friendly.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from pls_ct.dataset.clean import clean_record
from pls_ct.dataset.mapping import QUESTION_TO_SECTIONS


@dataclass
class BuildReport:
    n_trials: int
    n_examples: int
    n_skipped_empty_context: int
    n_skipped_empty_answer: int


def load_records(path: str | Path) -> list[dict]:
    """Load a JSON list of trial records (e.g. processed/database.json or the sample)."""
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, list):
        raise ValueError(f"{path}: expected a JSON list of trial records")
    return data


def build_examples(
    records: list[dict], *, clean: bool = True
) -> tuple[list[dict], BuildReport]:
    """Turn trial records into QA examples. Returns (examples, report)."""
    examples: list[dict] = []
    skipped_ctx = 0
    skipped_ans = 0

    for record in records:
        if clean:
            record = clean_record(record)
        trial_name = record.get("trial_name", "")
        report_sections = record.get("report_sections") or {}
        summary_sections = record.get("summary_sections") or {}

        for question, sections in QUESTION_TO_SECTIONS.items():
            context = "\n".join(
                report_sections[s] for s in sections if report_sections.get(s)
            ).strip()
            answer = (summary_sections.get(question) or "").strip()

            if not context:
                skipped_ctx += 1
                continue
            if not answer:
                skipped_ans += 1
                continue

            examples.append(
                {
                    "trial_name": trial_name,
                    "question": question,
                    "context": context,
                    "answer": answer,
                }
            )

    report = BuildReport(
        n_trials=len(records),
        n_examples=len(examples),
        n_skipped_empty_context=skipped_ctx,
        n_skipped_empty_answer=skipped_ans,
    )
    return examples, report


def write_jsonl(examples: list[dict], path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        for ex in examples:
            fh.write(json.dumps(ex, ensure_ascii=False) + "\n")
