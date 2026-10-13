"""`pls` command-line entry point.

Subcommands: ingest | build | split | evaluate | demo. Kept import-light (no torch at
import time) so `pls --help` runs on a bare install; ML backends are imported lazily
only when actually selected.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from pls_ct import __version__
from pls_ct.config import Config


def _read_jsonl(path: str | Path) -> list[dict]:
    with open(path, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def _make_backend(spec: str, *, lead_k: int = 2):
    """Resolve a backend spec: 'lead[-K]' | 'distilbert' | 'hf:<model_id>'."""
    if spec == "lead" or spec.startswith("lead-"):
        from pls_ct.models.baseline import LeadSentencesBackend

        k = int(spec.split("-", 1)[1]) if "-" in spec else lead_k
        return LeadSentencesBackend(k=k)
    if spec == "distilbert":
        from pls_ct.models.extractive_qa import DistilBertQABackend

        return DistilBertQABackend()
    if spec.startswith("hf:"):
        from pls_ct.models.generative import HFGenerativeBackend

        return HFGenerativeBackend(spec[3:])
    raise SystemExit(f"unknown backend spec: {spec!r} (use lead[-K] | distilbert | hf:<model_id>)")


def cmd_ingest(args) -> int:
    from pls_ct.ingestion.pair import ingest_directory

    records, report = ingest_directory(args.raw_dir, dry_run=args.dry_run)
    print(f"ingest report: {report.summary()}")
    if not args.dry_run:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(records, fh, indent=2, ensure_ascii=False)
        print(f"wrote {len(records)} records -> {args.out}")
    return 0


def cmd_build(args) -> int:
    from pls_ct.dataset.build import build_examples, load_records, write_jsonl

    records = load_records(args.db)
    examples, report = build_examples(records)
    write_jsonl(examples, args.out)
    print(f"build report: {report}")
    print(f"wrote {len(examples)} examples -> {args.out}")
    return 0


def cmd_split(args) -> int:
    from pls_ct.dataset.build import write_jsonl
    from pls_ct.dataset.split import split_by_trial

    examples = _read_jsonl(args.examples)
    splits = split_by_trial(examples, seed=args.seed)
    out_dir = Path(args.out_dir)
    for name, rows in splits.items():
        write_jsonl(rows, out_dir / f"{name}.jsonl")
    print({name: len(rows) for name, rows in splits.items()})
    return 0


def cmd_evaluate(args) -> int:
    from pls_ct.evaluation.harness import evaluate_backend, write_results

    examples = _read_jsonl(args.examples)
    backend = _make_backend(args.backend, lead_k=args.lead_k)
    results = evaluate_backend(backend, examples)
    write_results(results, args.out)
    print(f"backend={results['backend']} scored={results['n_scored']} errors={results['n_errors']}")
    for metric, value in results["aggregate"].items():
        print(f"  {metric}: {value:.2f}" if isinstance(value, float) else f"  {metric}: {value}")
    print(f"wrote results -> {args.out}")
    return 0


def cmd_demo(args) -> int:
    """End-to-end on the synthetic sample with the Lead baseline (no ML deps, CPU-only)."""
    from pls_ct.dataset.build import build_examples, load_records
    from pls_ct.dataset.split import split_by_trial
    from pls_ct.evaluation.harness import evaluate_backend, write_results

    cfg = Config.from_env()
    sample = cfg.raw_dir / "trials.json"
    print(f"[demo] using synthetic sample: {sample}")
    records = load_records(sample)
    examples, report = build_examples(records)
    print(f"[demo] built {report.n_examples} examples from {report.n_trials} trials")
    splits = split_by_trial(examples, seed=cfg.seed)
    print("[demo] split (by trial): " + str({k: len(v) for k, v in splits.items()}))

    backend = _make_backend(args.backend, lead_k=args.lead_k)
    results = evaluate_backend(backend, splits["test"] or examples)
    out = Path(args.out)
    write_results(results, out)
    print(f"[demo] backend={results['backend']} scored={results['n_scored']}")
    for metric, value in results["aggregate"].items():
        print(f"  {metric}: {value:.2f}" if isinstance(value, float) else f"  {metric}: {value}")
    print(f"[demo] wrote results -> {out}")
    print("[demo] NOTE: synthetic data — these numbers are illustrative, not real results.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pls", description="PLS of Clinical Trials — research CLI"
    )
    parser.add_argument("--version", action="version", version=f"pls-ct {__version__}")
    sub = parser.add_subparsers(dest="command")

    p_ingest = sub.add_parser("ingest", help="PDF directory -> trial records JSON")
    p_ingest.add_argument("--raw-dir", required=True)
    p_ingest.add_argument("--out", default="data/processed/database.json")
    p_ingest.add_argument("--dry-run", action="store_true")
    p_ingest.set_defaults(func=cmd_ingest)

    p_build = sub.add_parser("build", help="trial records -> QA examples (jsonl)")
    p_build.add_argument("--db", required=True)
    p_build.add_argument("--out", default="data/processed/examples.jsonl")
    p_build.set_defaults(func=cmd_build)

    p_split = sub.add_parser("split", help="QA examples -> train/val/test (by trial)")
    p_split.add_argument("--examples", required=True)
    p_split.add_argument("--out-dir", default="data/processed/splits")
    p_split.add_argument("--seed", type=int, default=42)
    p_split.set_defaults(func=cmd_split)

    p_eval = sub.add_parser("evaluate", help="run a backend over examples -> results JSON")
    p_eval.add_argument("--examples", required=True)
    p_eval.add_argument("--backend", default="lead", help="lead[-K] | distilbert | hf:<model_id>")
    p_eval.add_argument("--lead-k", type=int, default=2)
    p_eval.add_argument("--out", default="data/processed/results.json")
    p_eval.set_defaults(func=cmd_evaluate)

    p_demo = sub.add_parser("demo", help="end-to-end on the synthetic sample (CPU, no ML deps)")
    p_demo.add_argument("--backend", default="lead")
    p_demo.add_argument("--lead-k", type=int, default=2)
    p_demo.add_argument("--out", default="data/processed/demo_results.json")
    p_demo.set_defaults(func=cmd_demo)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
