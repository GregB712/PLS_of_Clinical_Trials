"""Trial listing, detail, and deletion (retention)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from pls_ct.app.deps import get_session
from pls_ct.app.schemas import DocumentOut, TrialDetail, TrialPage, TrialSummary
from pls_ct.db import repository
from pls_ct.db.models import Trial

router = APIRouter(prefix="/trials", tags=["trials"])


@router.get("", response_model=TrialPage)
def list_trials(
    session: Session = Depends(get_session),
    q: str | None = Query(None, description="case-insensitive protocol-id substring"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> TrialPage:
    stmt = select(Trial)
    if q:
        stmt = stmt.where(Trial.protocol_id.ilike(f"%{q}%"))
    total = session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = session.scalars(
        stmt.order_by(Trial.protocol_id).limit(limit).offset(offset)
    ).all()
    items = [
        TrialSummary(
            protocol_id=t.protocol_id,
            source=t.source,
            document_kinds=sorted(d.kind for d in t.documents),
        )
        for t in rows
    ]
    return TrialPage(items=items, total=total, limit=limit, offset=offset)


@router.get("/{protocol_id}", response_model=TrialDetail)
def get_trial(protocol_id: str, session: Session = Depends(get_session)) -> TrialDetail:
    trial = repository.get_trial(session, protocol_id)
    if trial is None:
        raise HTTPException(status_code=404, detail=f"trial {protocol_id!r} not found")

    documents, report_sections, summary_sections = [], {}, {}
    for doc in trial.documents:
        documents.append(
            DocumentOut(kind=doc.kind, fmt=doc.fmt, status=doc.status, n_sections=len(doc.sections))
        )
        target = report_sections if doc.kind == "report" else summary_sections
        for section in doc.sections:
            target[section.name] = section.text

    return TrialDetail(
        protocol_id=trial.protocol_id,
        source=trial.source,
        documents=documents,
        report_sections=report_sections,
        summary_sections=summary_sections,
    )


@router.delete("/{protocol_id}", status_code=204)
def delete_trial(protocol_id: str, session: Session = Depends(get_session)) -> None:
    trial = repository.get_trial(session, protocol_id)
    if trial is None:
        raise HTTPException(status_code=404, detail=f"trial {protocol_id!r} not found")
    session.delete(trial)  # cascades to documents + sections
