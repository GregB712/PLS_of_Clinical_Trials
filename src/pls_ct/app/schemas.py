"""Pydantic request/response schemas for the API (OpenAPI-documented)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class Health(BaseModel):
    status: str = "ok"


class Readiness(BaseModel):
    status: str
    database: bool


class Stats(BaseModel):
    trials: int
    documents: int
    sections: int
    chunks: int
    experiments: int


class BackendInfo(BaseModel):
    spec: str
    kind: str  # baseline | local-ml | provider
    available: bool
    detail: str | None = None


class BackendsResponse(BaseModel):
    backends: list[BackendInfo]


class TrialSummary(BaseModel):
    protocol_id: str
    source: str
    document_kinds: list[str]


class TrialPage(BaseModel):
    items: list[TrialSummary]
    total: int
    limit: int
    offset: int


class DocumentOut(BaseModel):
    kind: str
    fmt: str
    status: str
    n_sections: int


class TrialDetail(BaseModel):
    protocol_id: str
    source: str
    documents: list[DocumentOut]
    report_sections: dict[str, str]
    summary_sections: dict[str, str]


class SummarizeRequest(BaseModel):
    trial_name: str | None = Field(None, description="Summarize this stored trial's report")
    context: str | None = Field(None, description="Or summarize this raw text")
    question: str = "Summarize this clinical trial for a non-specialist in plain language."
    backend: str = Field("lead", description="lead[-K] | distilbert | hf:<id> | provider[:model]")
    max_new_tokens: int = Field(256, ge=1, le=4096)
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    top_p: float = Field(1.0, ge=0.0, le=1.0)
    api_key: str | None = Field(None, description="User-supplied provider key; never logged")

    @model_validator(mode="after")
    def _need_source(self) -> SummarizeRequest:
        if not self.trial_name and not self.context:
            raise ValueError("provide either trial_name or context")
        return self


class SummarizeResponse(BaseModel):
    text: str
    model: str
    input_tokens: int | None
    output_tokens: int | None
    latency_s: float | None
    warnings: list[str]
    run_id: str
    provenance: dict | None


class AskRequest(BaseModel):
    query: str = Field(..., min_length=1)
    trial_name: str | None = None
    k: int = Field(5, ge=1, le=50)
    backend: str = "lead"
    embedder: str = "auto"


class CitationOut(BaseModel):
    trial_name: str
    section: str
    start: int
    end: int
    score: float


class AskResponse(BaseModel):
    answer: str
    sufficient: bool
    citations: list[CitationOut]


class ExperimentResultOut(BaseModel):
    backend: str
    n_scored: int
    n_errors: int
    aggregate: dict


class ExperimentOut(BaseModel):
    id: int
    created_at: datetime
    split_fingerprint: str
    n_examples: int
    results: list[ExperimentResultOut]


class JobOut(BaseModel):
    id: int
    kind: str
    status: str
    result: dict | None = None
    error: str | None = None


class UploadResponse(BaseModel):
    job_id: int
    status: str


class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None
