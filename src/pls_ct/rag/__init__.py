"""Retrieval-augmented generation over the clinical-trial collection.

Chunk trial sections -> embed -> store/retrieve by cosine similarity -> answer with
citations. The default embedder is dependency-free (hashing), so RAG runs on a fresh
CPU-only clone; sentence-transformers is available behind the optional ``[rag]`` extra.
Retrieved passages are treated strictly as reference data, never as instructions.
"""
