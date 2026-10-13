"""Benchmarking harness: run a backend over examples -> per-example + aggregate results.

Per-example generation failures are caught and recorded (not fatal); they are excluded
from the aggregate metrics. Empty predictions are kept and scored (they count against
the model). Output is JSON-serializable and reproducible given a fixed GenConfig.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from pls_ct.evaluation.metrics import calculate_metrics
from pls_ct.models.base import GenConfig, SummarizerBackend


def evaluate_backend(
    backend: SummarizerBackend,
    examples: list[dict],
    cfg: GenConfig | None = None,
) -> dict:
    cfg = cfg or GenConfig()
    per_example: list[dict] = []
    preds: list[str] = []
    refs: list[str] = []

    for ex in examples:
        row = {
            "trial_name": ex.get("trial_name"),
            "question": ex.get("question"),
            "reference": ex.get("answer", ""),
        }
        try:
            result = backend.summarize(ex["context"], ex["question"], cfg)
            row["prediction"] = result.text
            row["latency_s"] = result.latency_s
            row["warnings"] = result.warnings
            row["error"] = None
            preds.append(result.text)
            refs.append(ex.get("answer", ""))
        except Exception as exc:  # noqa: BLE001 - record and continue
            row["prediction"] = ""
            row["error"] = f"{type(exc).__name__}: {exc}"
        per_example.append(row)

    aggregate = calculate_metrics(preds, refs) if preds else {}
    return {
        "backend": backend.name,
        "generation_config": vars(cfg),
        "run_at": datetime.now(timezone.utc).isoformat(),
        "n_examples": len(examples),
        "n_scored": len(preds),
        "n_errors": len(examples) - len(preds),
        "aggregate": aggregate,
        "per_example": per_example,
    }


def write_results(results: dict, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2, ensure_ascii=False)
