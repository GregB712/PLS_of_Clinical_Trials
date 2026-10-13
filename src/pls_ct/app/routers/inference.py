"""Summarization and RAG question-answering."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from pls_ct.app.deps import get_session, resolve_backend
from pls_ct.app.schemas import (
    AskRequest,
    AskResponse,
    CitationOut,
    SummarizeRequest,
    SummarizeResponse,
)
from pls_ct.db import repository
from pls_ct.models.base import GenConfig

router = APIRouter(tags=["inference"])


def _trial_report_text(session: Session, protocol_id: str) -> str:
    trial = repository.get_trial(session, protocol_id)
    if trial is None:
        raise HTTPException(status_code=404, detail=f"trial {protocol_id!r} not found")
    parts = [
        section.text
        for doc in trial.documents
        if doc.kind == "report"
        for section in doc.sections
        if section.text
    ]
    if not parts:
        raise HTTPException(status_code=422, detail=f"trial {protocol_id!r} has no report text")
    return "\n".join(parts)


@router.post("/summarize", response_model=SummarizeResponse)
def summarize(req: SummarizeRequest, session: Session = Depends(get_session)) -> SummarizeResponse:
    context = req.context or _trial_report_text(session, req.trial_name)
    backend = resolve_backend(req.backend, api_key=req.api_key)  # key is never logged/stored
    cfg = GenConfig(
        max_new_tokens=req.max_new_tokens, temperature=req.temperature, top_p=req.top_p
    )
    result = backend.summarize(context, req.question, cfg)
    return SummarizeResponse(
        text=result.text,
        model=result.model,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        latency_s=result.latency_s,
        warnings=result.warnings,
        run_id=result.run_id,
        provenance=result.provenance,
    )


@router.post("/rag/ask", response_model=AskResponse)
def ask(req: AskRequest, session: Session = Depends(get_session)) -> AskResponse:
    from pls_ct.rag.assistant import answer_query
    from pls_ct.rag.embeddings import make_embedder
    from pls_ct.rag.index import load_store

    db_chunks = repository.load_chunks(session)
    if not db_chunks:
        raise HTTPException(status_code=409, detail="no chunks indexed; run indexing first")

    spec = db_chunks[0].embedder if req.embedder == "auto" else req.embedder
    store = load_store(db_chunks, make_embedder(spec))
    backend = resolve_backend(req.backend)
    ans = answer_query(store, backend, req.query, k=req.k, trial_name=req.trial_name)
    return AskResponse(
        answer=ans.answer,
        sufficient=ans.sufficient,
        citations=[
            CitationOut(
                trial_name=c.trial_name,
                section=c.section,
                start=c.start,
                end=c.end,
                score=c.score,
            )
            for c in ans.citations
        ],
    )
