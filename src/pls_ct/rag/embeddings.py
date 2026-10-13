"""Embedding backends behind one interface.

Default is :class:`HashingEmbedder` — a deterministic, dependency-free hashing bag-of-words
embedding (signed hashing trick, L2-normalized). It is a real, classic technique that gives
working cosine retrieval with zero ML deps. :class:`SentenceTransformerEmbedder` provides
stronger dense embeddings via the optional ``[rag]`` extra.
"""

from __future__ import annotations

import hashlib
import math
import re
from typing import Protocol, runtime_checkable

_TOKEN = re.compile(r"[a-z0-9]+")


@runtime_checkable
class Embedder(Protocol):
    name: str
    dim: int

    def embed(self, texts: list[str]) -> list[list[float]]: ...


def _tokenize(text: str) -> list[str]:
    return _TOKEN.findall(text.lower())


def cosine(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):
        raise ValueError("vector dim mismatch")
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    # Vectors from these embedders are L2-normalized, so dot == cosine; clamp for safety.
    return max(-1.0, min(1.0, dot))


class HashingEmbedder:
    def __init__(self, dim: int = 512) -> None:
        self.dim = dim
        self.name = f"hashing-{dim}"

    def _embed_one(self, text: str) -> list[float]:
        vec = [0.0] * self.dim
        for tok in _tokenize(text):
            digest = hashlib.md5(tok.encode("utf-8")).digest()  # stable across runs
            idx = int.from_bytes(digest[:4], "big") % self.dim
            sign = 1.0 if digest[4] & 1 else -1.0
            vec[idx] += sign
        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0:
            vec = [v / norm for v in vec]
        return vec

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(t) for t in texts]


def make_embedder(spec: str) -> Embedder:
    """Resolve an embedder spec: 'hashing[-DIM]' | 'st:<model_id>'."""
    if spec == "hashing" or spec.startswith("hashing-"):
        dim = int(spec.split("-", 1)[1]) if "-" in spec else 512
        return HashingEmbedder(dim=dim)
    if spec.startswith("st:"):
        return SentenceTransformerEmbedder(spec[3:])
    raise ValueError(f"unknown embedder spec: {spec!r} (use hashing[-DIM] | st:<model_id>)")


class SentenceTransformerEmbedder:
    """Dense embeddings via sentence-transformers (optional ``[rag]`` extra)."""

    def __init__(self, model_id: str = "sentence-transformers/all-MiniLM-L6-v2") -> None:
        self.model_id = model_id
        self.name = f"st:{model_id}"
        self._model = None
        self.dim = 0

    def _load(self) -> None:
        if self._model is not None:
            return
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(
                "SentenceTransformerEmbedder needs the rag extra: pip install -e '.[rag]'"
            ) from exc
        self._model = SentenceTransformer(self.model_id)
        self.dim = self._model.get_sentence_embedding_dimension()

    def embed(self, texts: list[str]) -> list[list[float]]:
        self._load()
        vectors = self._model.encode(texts, normalize_embeddings=True)
        return [list(map(float, v)) for v in vectors]
