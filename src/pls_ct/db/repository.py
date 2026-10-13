"""Data-access layer. The only place that issues DB queries for trials/documents.

``upsert_trial`` is idempotent: re-ingesting identical content is a no-op ("unchanged"),
changed content updates in place ("updated"), new content inserts ("created").
"""

from __future__ import annotations

import hashlib
import json

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from pls_ct.db.models import Chunk, Document, Experiment, ExperimentResult, Section, Trial


def content_hash(sections: dict[str, str]) -> str:
    """Deterministic hash of a sections mapping (order-independent)."""
    canonical = json.dumps(sections, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _upsert_document(
    session: Session,
    trial: Trial,
    kind: str,
    sections: dict[str, str],
    *,
    path: str | None,
    fmt: str,
) -> str:
    sha = content_hash(sections)
    existing = next((d for d in trial.documents if d.kind == kind), None)

    if existing is not None:
        if existing.content_sha256 == sha:
            return "unchanged"
        # Content changed: replace sections and metadata.
        existing.content_sha256 = sha
        existing.path = path
        existing.fmt = fmt
        existing.sections.clear()
        session.flush()
        existing.sections.extend(
            Section(name=name, text=text) for name, text in sections.items()
        )
        return "updated"

    doc = Document(kind=kind, path=path, content_sha256=sha, fmt=fmt)
    doc.sections = [Section(name=name, text=text) for name, text in sections.items()]
    trial.documents.append(doc)
    return "created"


def upsert_trial(session: Session, record: dict) -> dict[str, str]:
    """Insert/update a trial + its report/summary documents from a canonical record.

    Returns ``{"report": <status>, "summary": <status>}`` where each status is
    created | updated | unchanged | absent.
    """
    protocol_id = record["trial_name"]
    trial = session.scalar(select(Trial).where(Trial.protocol_id == protocol_id))
    if trial is None:
        trial = Trial(protocol_id=protocol_id, source=record.get("source", "unknown"))
        session.add(trial)
        session.flush()

    outcome: dict[str, str] = {}
    pairs = (
        ("report", record.get("report_sections"), record.get("report_path")),
        ("summary", record.get("summary_sections"), record.get("summary_path")),
    )
    for kind, sections, path in pairs:
        if not sections:
            outcome[kind] = "absent"
            continue
        outcome[kind] = _upsert_document(
            session, trial, kind, sections, path=path, fmt=record.get("fmt", "sections")
        )
    return outcome


def load_records(session: Session, records: list[dict]) -> dict[str, int]:
    """Upsert many records; return aggregate counts."""
    counts = {"created": 0, "updated": 0, "unchanged": 0, "absent": 0}
    for record in records:
        for status in upsert_trial(session, record).values():
            counts[status] += 1
    return counts


def count_trials(session: Session) -> int:
    return session.scalar(select(func.count()).select_from(Trial)) or 0


def list_trials(session: Session) -> list[Trial]:
    return list(session.scalars(select(Trial).order_by(Trial.protocol_id)))


def get_trial(session: Session, protocol_id: str) -> Trial | None:
    return session.scalar(select(Trial).where(Trial.protocol_id == protocol_id))


def save_experiment(session: Session, benchmark: dict) -> Experiment:
    """Persist a benchmark dict (from run_benchmark) as an Experiment + its results."""
    experiment = Experiment(
        split_fingerprint=benchmark["split_fingerprint"],
        n_examples=benchmark["n_examples"],
        seed=benchmark.get("generation_config", {}).get("seed"),
        generation_config=benchmark.get("generation_config", {}),
        versions=benchmark.get("versions", {}),
    )
    for res in benchmark.get("results", []):
        experiment.results.append(
            ExperimentResult(
                backend=res["backend"],
                n_scored=res.get("n_scored", 0),
                n_errors=res.get("n_errors", 0),
                aggregate=res.get("aggregate", {}),
            )
        )
    session.add(experiment)
    session.flush()
    return experiment


def list_experiments(session: Session) -> list[Experiment]:
    return list(session.scalars(select(Experiment).order_by(Experiment.created_at.desc())))


def replace_chunks(session: Session, rows: list[dict]) -> int:
    """Full re-index: delete all stored chunks, then insert the given rows. Idempotent."""
    session.query(Chunk).delete()
    session.flush()
    for row in rows:
        session.add(Chunk(**row))
    session.flush()
    return len(rows)


def load_chunks(session: Session) -> list[Chunk]:
    return list(session.scalars(select(Chunk).order_by(Chunk.id)))


def count_chunks(session: Session) -> int:
    return session.scalar(select(func.count()).select_from(Chunk)) or 0
