"""Lead-sentences baseline — a standard, dependency-free summarization baseline.

Returns the first ``k`` sentences of the context. "Lead-N" is a well-known, hard-to-beat
baseline in summarization research; including it keeps the whole pipeline runnable on a
fresh CPU-only clone (no torch) and gives every learned model an honest reference point.
It is a real baseline, not a stand-in for a model.
"""

from __future__ import annotations

import re
import time

from pls_ct.models.base import GenConfig, SummaryResult

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


class LeadSentencesBackend:
    def __init__(self, k: int = 2) -> None:
        self.k = k
        self.name = f"lead-{k}"

    def summarize(self, context: str, question: str, cfg: GenConfig) -> SummaryResult:
        start = time.perf_counter()
        sentences = [s for s in _SENTENCE_SPLIT.split(context.strip()) if s]
        text = " ".join(sentences[: self.k]).strip()
        return SummaryResult(
            text=text,
            model=self.name,
            generation_config=cfg,
            input_tokens=len(context.split()),
            output_tokens=len(text.split()),
            latency_s=time.perf_counter() - start,
            provenance={"question": question},
        )
