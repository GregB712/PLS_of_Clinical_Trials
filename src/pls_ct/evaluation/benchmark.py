"""Benchmark several backends on the *same* examples, reproducibly.

Captures the reproducibility context (software versions, seed, generation config, and a
fingerprint of the exact examples) so a run can be audited and compared later. Produces
machine-readable results plus a Markdown comparison table. Reuses ``evaluate_backend``,
so per-example failures are handled the same way (recorded, excluded from aggregates).
"""

from __future__ import annotations

import hashlib
import json
import platform
import sys
from datetime import datetime, timezone

from pls_ct import __version__
from pls_ct.evaluation.harness import evaluate_backend
from pls_ct.models.base import GenConfig, SummarizerBackend

# Metrics shown in the comparison table, in order.
_TABLE_METRICS = ["F1 Score", "ROUGE-1", "ROUGE-2", "ROUGE-L", "BLEU Score", "Exact Match"]


def software_versions() -> dict[str, str | None]:
    versions: dict[str, str | None] = {
        "python": sys.version.split()[0],
        "pls_ct": __version__,
        "platform": platform.platform(),
    }
    for mod in ("torch", "transformers", "peft"):
        try:
            versions[mod] = __import__(mod).__version__
        except Exception:  # noqa: BLE001 - optional deps; absence is informative
            versions[mod] = None
    return versions


def examples_fingerprint(examples: list[dict]) -> str:
    """Stable 16-hex fingerprint of the evaluation set (order-independent)."""
    h = hashlib.sha256()
    keyed = sorted(
        json.dumps(
            [ex.get("trial_name"), ex.get("question"), ex.get("answer")],
            sort_keys=True,
            ensure_ascii=False,
        )
        for ex in examples
    )
    for item in keyed:
        h.update(item.encode("utf-8"))
    return h.hexdigest()[:16]


def run_benchmark(
    backends: list[SummarizerBackend],
    examples: list[dict],
    cfg: GenConfig | None = None,
) -> dict:
    cfg = cfg or GenConfig()
    results = [evaluate_backend(backend, examples, cfg) for backend in backends]
    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "n_examples": len(examples),
        "split_fingerprint": examples_fingerprint(examples),
        "generation_config": vars(cfg),
        "versions": software_versions(),
        "results": results,
    }


def comparison_markdown(benchmark: dict) -> str:
    """Render the per-backend aggregates as a Markdown table (measured results only)."""
    header = "| Backend | " + " | ".join(_TABLE_METRICS) + " | scored | errors |"
    sep = "|" + "---|" * (len(_TABLE_METRICS) + 3)
    lines = [header, sep]
    for res in benchmark["results"]:
        agg = res.get("aggregate", {})
        cells = [f"{agg[m]:.2f}" if m in agg else "—" for m in _TABLE_METRICS]
        lines.append(
            f"| {res['backend']} | "
            + " | ".join(cells)
            + f" | {res['n_scored']} | {res['n_errors']} |"
        )
    return "\n".join(lines)
