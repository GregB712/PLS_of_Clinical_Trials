"""In-memory vector store (cosine top-k, optional trial scoping).

Research-scale: a few hundred trials' chunks ranked in pure Python. The documented
production path for scale is Postgres + pgvector (see docs/ARCHITECTURE.md) — the chunk
schema and embedder metadata are stored so that migration is mechanical.
"""

from __future__ import annotations

from dataclasses import dataclass

from pls_ct.rag.chunk import Chunk
from pls_ct.rag.embeddings import Embedder, cosine


@dataclass
class ScoredChunk:
    chunk: Chunk
    score: float


class VectorStore:
    def __init__(self, embedder: Embedder) -> None:
        self.embedder = embedder
        self._items: list[tuple[Chunk, list[float]]] = []

    def __len__(self) -> int:
        return len(self._items)

    def add(self, chunks: list[Chunk]) -> None:
        vectors = self.embedder.embed([c.text for c in chunks])
        self._items.extend(zip(chunks, vectors, strict=True))

    def add_precomputed(self, pairs: list[tuple[Chunk, list[float]]]) -> None:
        self._items.extend(pairs)

    def search(
        self, query: str, k: int = 5, *, trial_name: str | None = None
    ) -> list[ScoredChunk]:
        qv = self.embedder.embed([query])[0]
        scored = [
            ScoredChunk(chunk, cosine(qv, vec))
            for chunk, vec in self._items
            if trial_name is None or chunk.trial_name == trial_name
        ]
        scored.sort(key=lambda s: s.score, reverse=True)
        return scored[:k]
