"""Unified summarization interface shared by every backend.

This is the seam the later hosted-provider abstraction and the web API plug into.
Metrics that a backend cannot measure are returned as ``None`` — never fabricated.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class GenConfig:
    """Generation settings. Backends use what applies and ignore the rest."""

    max_new_tokens: int = 256
    temperature: float = 0.7
    top_p: float = 1.0
    seed: int | None = None


@dataclass
class SummaryResult:
    text: str
    model: str
    generation_config: GenConfig
    run_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    input_tokens: int | None = None
    output_tokens: int | None = None
    latency_s: float | None = None
    provenance: dict | None = None  # e.g. {"trial_name": ..., "question": ...}
    warnings: list[str] = field(default_factory=list)


@runtime_checkable
class SummarizerBackend(Protocol):
    """Any model that turns (context, question) into a plain-language answer."""

    name: str

    def summarize(self, context: str, question: str, cfg: GenConfig) -> SummaryResult: ...
