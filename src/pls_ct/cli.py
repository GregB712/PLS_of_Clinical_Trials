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

    from pls_ct.providers import PROVIDERS, make_provider

    if spec in PROVIDERS:
        return make_provider(spec)
    if ":" in spec:
        prefix, model = spec.split(":", 1)
        if prefix in PROVIDERS:
            return make_provider(prefix, model)

    raise SystemExit(
        f"unknown backend spec: {spec!r} "
        "(use lead[-K] | distilbert | hf:<model_id> | <provider>[:<model>])"
    )


def cmd_benchmark(args) -> int:
    from pls_ct.evaluation.benchmark import comparison_markdown, run_benchmark
    from pls_ct.evaluation.harness import write_results

    examples = _read_jsonl(args.examples)
    specs = [s.strip() for s in args.backends.split(",") if s.strip()]
    backends = [_make_backend(s, lead_k=args.lead_k) for s in specs]
    bench = run_benchmark(backends, examples)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    write_results(bench, out_dir / "benchmark.json")
    table = comparison_markdown(bench)
    (out_dir / "comparison.md").write_text(table + "\n", encoding="utf-8")
    print(table)

    if args.to_db:
        from pls_ct.db.engine import create_all, get_engine, session_scope
        from pls_ct.db.repository import save_experiment

        engine = get_engine(args.db_url)
        create_all(engine)
        with session_scope(engine) as session:
            experiment = save_experiment(session, bench)
            print(f"saved experiment id={experiment.id}")
    print(f"wrote {out_dir / 'benchmark.json'} and {out_dir / 'comparison.md'}")
    return 0


def cmd_experiments(args) -> int:
    from pls_ct.db.engine import get_engine, session_scope
    from pls_ct.db.repository import list_experiments

    engine = get_engine(args.db_url)
    with session_scope(engine) as session:
        experiments = list_experiments(session)
        print(f"{len(experiments)} experiment(s):")
        for exp in experiments:
            backends = ",".join(r.backend for r in exp.results)
            print(
                f"  #{exp.id} {exp.created_at:%Y-%m-%d %H:%M} fp={exp.split_fingerprint} "
                f"n={exp.n_examples} backends=[{backends}]"
            )
    return 0


def cmd_train(args) -> int:
    from pls_ct.training.finetune import FinetuneConfig, finetune_seq2seq

    splits_dir = Path(args.splits_dir)
    splits = {
        name: _read_jsonl(splits_dir / f"{name}.jsonl")
        for name in ("train", "val", "test")
        if (splits_dir / f"{name}.jsonl").exists()
    }
    if "train" not in splits:
        raise SystemExit(f"no train.jsonl in {splits_dir} (run `pls split` first)")
    cfg = FinetuneConfig(base_model=args.model, epochs=args.epochs, use_lora=args.lora)
    metadata = finetune_seq2seq(splits, output_dir=args.out_dir, cfg=cfg)
    print(f"fine-tuning done -> {args.out_dir}")
    print(json.dumps(metadata, indent=2))
    return 0


def cmd_providers(args) -> int:
    from pls_ct.providers import DEFAULT_MODELS, PROVIDERS, make_provider

    print("hosted providers (keys are read from the environment, never logged):")
    for name in sorted(PROVIDERS):
        provider = make_provider(name)
        status = "configured" if provider.has_key() else "NO KEY"
        print(
            f"  {name:10} env={provider.api_key_env:18} "
            f"default={DEFAULT_MODELS[name]:20} key={provider.masked_key()} [{status}]"
        )
    return 0


def cmd_ingest(args) -> int:
    from pls_ct.ingestion.pair import ingest_directory

    records, report = ingest_directory(args.raw_dir, dry_run=args.dry_run)
    print(f"ingest report: {report.summary()}")
    if not args.dry_run:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(records, fh, indent=2, ensure_ascii=False)
        print(f"wrote {len(records)} records -> {args.out}")
        if args.to_db:
            _load_records_to_db(records, args.db_url)
    return 0


def _load_records_to_db(records: list[dict], db_url: str | None) -> None:
    from pls_ct.db.engine import create_all, get_engine, session_scope
    from pls_ct.db.repository import load_records

    engine = get_engine(db_url)
    create_all(engine)  # dev convenience; production uses `alembic upgrade head`
    with session_scope(engine) as session:
        counts = load_records(session, records)
    print(f"db load: {counts}")


def cmd_db_load(args) -> int:
    from pls_ct.dataset.build import load_records as load_json

    records = load_json(args.records)
    _load_records_to_db(records, args.db_url)
    return 0


def cmd_trials(args) -> int:
    from pls_ct.db.engine import get_engine, session_scope
    from pls_ct.db.repository import list_trials

    engine = get_engine(args.db_url)
    with session_scope(engine) as session:
        trials = list_trials(session)
        print(f"{len(trials)} trial(s):")
        for trial in trials:
            kinds = ",".join(sorted(d.kind for d in trial.documents))
            print(f"  {trial.protocol_id}  source={trial.source}  documents=[{kinds}]")
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
    p_ingest.add_argument("--to-db", action="store_true", help="also persist records to the DB")
    p_ingest.add_argument("--db-url", default=None, help="SQLAlchemy URL (default: local sqlite)")
    p_ingest.set_defaults(func=cmd_ingest)

    p_db_load = sub.add_parser("db-load", help="load canonical records JSON into the DB")
    p_db_load.add_argument("--records", required=True, help="JSON list of trial records")
    p_db_load.add_argument("--db-url", default=None)
    p_db_load.set_defaults(func=cmd_db_load)

    p_trials = sub.add_parser("trials", help="list trials stored in the DB")
    p_trials.add_argument("--db-url", default=None)
    p_trials.set_defaults(func=cmd_trials)

    p_providers = sub.add_parser("providers", help="list hosted providers and key status")
    p_providers.set_defaults(func=cmd_providers)

    p_bench = sub.add_parser("benchmark", help="compare several backends on one example set")
    p_bench.add_argument("--examples", required=True)
    p_bench.add_argument("--backends", default="lead,lead-3", help="comma-separated backend specs")
    p_bench.add_argument("--lead-k", type=int, default=2)
    p_bench.add_argument("--out-dir", default="data/processed/benchmark")
    p_bench.add_argument("--to-db", action="store_true", help="persist the experiment to the DB")
    p_bench.add_argument("--db-url", default=None)
    p_bench.set_defaults(func=cmd_benchmark)

    p_exps = sub.add_parser("experiments", help="list benchmark experiments stored in the DB")
    p_exps.add_argument("--db-url", default=None)
    p_exps.set_defaults(func=cmd_experiments)

    p_train = sub.add_parser("train", help="fine-tune a seq2seq model (needs [ml]; GPU optional)")
    p_train.add_argument("--splits-dir", required=True, help="dir with train/val/test .jsonl")
    p_train.add_argument("--model", default="google/flan-t5-base")
    p_train.add_argument("--epochs", type=int, default=3)
    p_train.add_argument("--lora", action="store_true", help="use LoRA (needs [peft])")
    p_train.add_argument("--out-dir", default="artifacts/finetuned")
    p_train.set_defaults(func=cmd_train)

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
    p_eval.add_argument(
        "--backend",
        default="lead",
        help="lead[-K] | distilbert | hf:<model_id> | <provider>[:<model>]",
    )
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
