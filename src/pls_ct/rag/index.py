"""Bridge between chunks/embeddings and persisted rows (keeps store.py DB-free)."""

from __future__ import annotations

from typing import Any

from pls_ct.rag.chunk import Chunk
from pls_ct.rag.embeddings import Embedder
from pls_ct.rag.store import VectorStore


def build_rows(chunks: list[Chunk], embedder: Embedder) -> list[dict]:
    """Embed chunks and produce row dicts for ``repository.replace_chunks``."""
    vectors = embedder.embed([c.text for c in chunks])
    rows = []
    for chunk, vec in zip(chunks, vectors, strict=True):
        rows.append(
            {
                "chunk_id": chunk.chunk_id,
                "trial_name": chunk.trial_name,
                "section": chunk.section,
                "text": chunk.text,
                "start": chunk.start,
                "end": chunk.end,
                "idx": chunk.index,
                "embedder": embedder.name,
                "dim": embedder.dim,
                "embedding": vec,
            }
        )
    return rows


def load_store(db_chunks: list[Any], embedder: Embedder) -> VectorStore:
    """Reconstruct a VectorStore from persisted chunk rows (duck-typed; no DB import)."""
    store = VectorStore(embedder)
    pairs = [
        (
            Chunk(row.trial_name, row.section, row.text, row.start, row.end, row.idx),
            list(row.embedding),
        )
        for row in db_chunks
    ]
    store.add_precomputed(pairs)
    return store
