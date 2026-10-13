"""Health, readiness, dataset stats, and available backends."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from pls_ct.app.deps import get_session
from pls_ct.app.schemas import BackendInfo, BackendsResponse, Health, Readiness, Stats
from pls_ct.db import repository

router = APIRouter(tags=["core"])


@router.get("/health", response_model=Health)
def health() -> Health:
    return Health()


@router.get("/ready", response_model=Readiness)
def ready(session: Session = Depends(get_session)) -> Readiness:
    try:
        session.execute(text("SELECT 1"))
        db_ok = True
    except Exception:  # noqa: BLE001 - readiness probe must not raise
        db_ok = False
    return Readiness(status="ok" if db_ok else "degraded", database=db_ok)


@router.get("/stats", response_model=Stats)
def stats(session: Session = Depends(get_session)) -> Stats:
    return Stats(**repository.stats(session))


@router.get("/backends", response_model=BackendsResponse)
def backends() -> BackendsResponse:
    from pls_ct.providers import DEFAULT_MODELS, PROVIDERS, make_provider

    infos = [
        BackendInfo(spec="lead", kind="baseline", available=True, detail="lead-N sentences"),
        BackendInfo(
            spec="distilbert",
            kind="local-ml",
            available=_ml_available(),
            detail="needs the [ml] extra",
        ),
        BackendInfo(
            spec="hf:<model_id>",
            kind="local-ml",
            available=_ml_available(),
            detail="HF seq2seq/causal; needs [ml]",
        ),
    ]
    for name in sorted(PROVIDERS):
        provider = make_provider(name)
        infos.append(
            BackendInfo(
                spec=f"{name}:{DEFAULT_MODELS[name]}",
                kind="provider",
                available=provider.has_key(),
                detail="configured" if provider.has_key() else f"set ${provider.api_key_env}",
            )
        )
    return BackendsResponse(backends=infos)


def _ml_available() -> bool:
    try:
        import torch  # noqa: F401
        import transformers  # noqa: F401

        return True
    except ImportError:
        return False
