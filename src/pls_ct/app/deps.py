"""Shared dependencies: DB session + backend resolution."""

from __future__ import annotations

from collections.abc import Iterator

from fastapi import Request
from sqlalchemy.orm import Session, sessionmaker

from pls_ct.models.base import SummarizerBackend


def get_session(request: Request) -> Iterator[Session]:
    """Yield a session bound to the app's engine (set at startup / overridden in tests)."""
    engine = request.app.state.engine
    factory = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def resolve_backend(spec: str, *, api_key: str | None = None) -> SummarizerBackend:
    """Resolve a backend spec for the API, allowing a user-supplied provider key.

    The key is passed straight to the provider and never logged or persisted.
    """
    if spec == "lead" or spec.startswith("lead-"):
        from pls_ct.models.baseline import LeadSentencesBackend

        k = int(spec.split("-", 1)[1]) if "-" in spec else 2
        return LeadSentencesBackend(k=k)
    if spec == "distilbert":
        from pls_ct.models.extractive_qa import DistilBertQABackend

        return DistilBertQABackend()
    if spec.startswith("hf:"):
        from pls_ct.models.generative import HFGenerativeBackend

        return HFGenerativeBackend(spec[3:])

    from pls_ct.providers import PROVIDERS, make_provider

    name, _, model = spec.partition(":")
    if name in PROVIDERS:
        return make_provider(name, model or None, api_key=api_key)

    raise ValueError(f"unknown backend spec: {spec!r}")
