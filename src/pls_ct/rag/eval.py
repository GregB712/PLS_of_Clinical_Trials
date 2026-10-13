"""Retrieval evaluation — measured separately from answer quality.

Relevance is derived from the dataset itself: for a patient question about a trial, the
relevant chunks are those drawn from the report section(s) that question maps to
(``QUESTION_TO_SECTIONS``). Metrics: recall@k, precision@k, and MRR.
"""

from __future__ import annotations

from pls_ct.dataset.mapping import QUESTION_TO_SECTIONS
from pls_ct.rag.chunk import Chunk
from pls_ct.rag.store import VectorStore


def recall_at_k(retrieved_ids: list[str], relevant_ids: set[str], k: int) -> float:
    if not relevant_ids:
        return 0.0
    hit = len(set(retrieved_ids[:k]) & relevant_ids)
    return hit / len(relevant_ids)


def precision_at_k(retrieved_ids: list[str], relevant_ids: set[str], k: int) -> float:
    if k <= 0:
        return 0.0
    hit = len(set(retrieved_ids[:k]) & relevant_ids)
    return hit / k


def reciprocal_rank(retrieved_ids: list[str], relevant_ids: set[str]) -> float:
    for rank, cid in enumerate(retrieved_ids, 1):
        if cid in relevant_ids:
            return 1.0 / rank
    return 0.0


def relevant_chunk_ids(question: str, trial_name: str, chunks: list[Chunk]) -> set[str]:
    """Chunk ids for this trial whose section is one the question maps to."""
    sections = set(QUESTION_TO_SECTIONS.get(question, []))
    return {
        c.chunk_id for c in chunks if c.trial_name == trial_name and c.section in sections
    }


def evaluate_retrieval(
    store: VectorStore,
    chunks: list[Chunk],
    examples: list[dict],
    *,
    k: int = 5,
    scope_to_trial: bool = True,
) -> dict[str, float]:
    """Mean recall@k / precision@k / MRR over examples that have known relevant chunks."""
    recalls, precisions, rrs = [], [], []
    for ex in examples:
        question, trial = ex["question"], ex["trial_name"]
        relevant = relevant_chunk_ids(question, trial, chunks)
        if not relevant:
            continue
        hits = store.search(question, k=k, trial_name=trial if scope_to_trial else None)
        retrieved_ids = [h.chunk.chunk_id for h in hits]
        recalls.append(recall_at_k(retrieved_ids, relevant, k))
        precisions.append(precision_at_k(retrieved_ids, relevant, k))
        rrs.append(reciprocal_rank(retrieved_ids, relevant))

    n = len(recalls)
    if n == 0:
        return {"recall@k": 0.0, "precision@k": 0.0, "mrr": 0.0, "k": k, "n_queries": 0}
    return {
        "recall@k": sum(recalls) / n,
        "precision@k": sum(precisions) / n,
        "mrr": sum(rrs) / n,
        "k": k,
        "n_queries": n,
    }
