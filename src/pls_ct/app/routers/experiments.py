"""Benchmark experiment results (model comparison dashboard data)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from pls_ct.app.deps import get_session
from pls_ct.app.schemas import ExperimentOut, ExperimentResultOut
from pls_ct.db import repository

router = APIRouter(prefix="/experiments", tags=["experiments"])


def _to_out(exp) -> ExperimentOut:
    return ExperimentOut(
        id=exp.id,
        created_at=exp.created_at,
        split_fingerprint=exp.split_fingerprint,
        n_examples=exp.n_examples,
        results=[
            ExperimentResultOut(
                backend=r.backend,
                n_scored=r.n_scored,
                n_errors=r.n_errors,
                aggregate=r.aggregate,
            )
            for r in exp.results
        ],
    )


@router.get("", response_model=list[ExperimentOut])
def list_experiments(session: Session = Depends(get_session)) -> list[ExperimentOut]:
    return [_to_out(e) for e in repository.list_experiments(session)]


@router.get("/{experiment_id}", response_model=ExperimentOut)
def get_experiment(experiment_id: int, session: Session = Depends(get_session)) -> ExperimentOut:
    for exp in repository.list_experiments(session):
        if exp.id == experiment_id:
            return _to_out(exp)
    raise HTTPException(status_code=404, detail=f"experiment {experiment_id} not found")
