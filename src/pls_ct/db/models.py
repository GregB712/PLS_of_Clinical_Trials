"""SQLAlchemy ORM models for the trial document lifecycle.

Trial 1--* Document (kind = report|summary) 1--* Section. A Document carries a content
hash for idempotent re-ingestion and a processing status. Kept intentionally small for
the research core; extends toward the full schema in docs/DATASET_AND_PIPELINE.md.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Trial(Base):
    __tablename__ = "trials"

    id: Mapped[int] = mapped_column(primary_key=True)
    protocol_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    source: Mapped[str] = mapped_column(String(32), default="unknown")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    documents: Mapped[list[Document]] = relationship(
        back_populates="trial", cascade="all, delete-orphan"
    )


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (UniqueConstraint("trial_id", "kind", name="uq_document_trial_kind"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    trial_id: Mapped[int] = mapped_column(ForeignKey("trials.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(16))  # "report" | "summary"
    path: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_sha256: Mapped[str] = mapped_column(String(64), index=True)
    fmt: Mapped[str] = mapped_column(String(16), default="sections")  # sections | markdown
    status: Mapped[str] = mapped_column(String(16), default="ingested")
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    trial: Mapped[Trial] = relationship(back_populates="documents")
    sections: Mapped[list[Section]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )


class Section(Base):
    __tablename__ = "sections"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(128))
    text: Mapped[str] = mapped_column(Text, default="")

    document: Mapped[Document] = relationship(back_populates="sections")


class Experiment(Base):
    """One benchmark run: a set of backends evaluated on the same examples."""

    __tablename__ = "experiments"

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    split_fingerprint: Mapped[str] = mapped_column(String(32), index=True)
    n_examples: Mapped[int] = mapped_column(Integer)
    seed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    generation_config: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    versions: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    results: Mapped[list[ExperimentResult]] = relationship(
        back_populates="experiment", cascade="all, delete-orphan"
    )


class ExperimentResult(Base):
    """One backend's aggregate metrics within an experiment."""

    __tablename__ = "experiment_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    experiment_id: Mapped[int] = mapped_column(
        ForeignKey("experiments.id", ondelete="CASCADE"), index=True
    )
    backend: Mapped[str] = mapped_column(String(128))
    n_scored: Mapped[int] = mapped_column(Integer, default=0)
    n_errors: Mapped[int] = mapped_column(Integer, default=0)
    aggregate: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    experiment: Mapped[Experiment] = relationship(back_populates="results")
