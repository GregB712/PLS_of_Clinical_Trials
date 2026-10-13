"""Chunk trial sections into retrievable passages, preserving provenance.

Each chunk keeps its ``trial_name``, ``section`` name, and character offsets within the
section, so a citation can point back to the exact source span. Chunking happens *within*
sections (they are already semantic units); long sections are split on sentence
boundaries into overlapping windows.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


@dataclass
class Chunk:
    trial_name: str
    section: str
    text: str
    start: int  # char offset within the section
    end: int
    index: int  # chunk ordinal within the (trial, section)

    @property
    def chunk_id(self) -> str:
        return f"{self.trial_name}::{self.section}::{self.index}"


def _split_section(text: str, max_chars: int, overlap: int) -> list[tuple[str, int, int]]:
    """Return (text, start, end) windows covering the section, split on sentences."""
    text = text.strip()
    if not text:
        return []
    if len(text) <= max_chars:
        return [(text, 0, len(text))]

    sentences = _SENTENCE_SPLIT.split(text)
    windows: list[tuple[str, int, int]] = []
    cur: list[str] = []
    cur_len = 0
    cursor = 0  # char offset of the start of the current window
    for sent in sentences:
        if cur and cur_len + len(sent) + 1 > max_chars:
            chunk_text = " ".join(cur)
            windows.append((chunk_text, cursor, cursor + len(chunk_text)))
            # Start next window with an overlap tail of the previous chunk.
            tail = chunk_text[-overlap:] if overlap else ""
            cursor = cursor + len(chunk_text) - len(tail)
            cur = [tail] if tail else []
            cur_len = len(tail)
        cur.append(sent)
        cur_len += len(sent) + 1
    if cur:
        chunk_text = " ".join(cur).strip()
        if chunk_text:
            windows.append((chunk_text, cursor, cursor + len(chunk_text)))
    return windows


def chunk_record(
    record: dict,
    *,
    which: str = "report_sections",
    max_chars: int = 800,
    overlap: int = 100,
) -> list[Chunk]:
    """Chunk one trial record's sections (``report_sections`` by default)."""
    trial_name = record.get("trial_name", "")
    sections = record.get(which) or {}
    chunks: list[Chunk] = []
    for section, text in sections.items():
        for i, (ctext, start, end) in enumerate(_split_section(text or "", max_chars, overlap)):
            chunks.append(Chunk(trial_name, section, ctext, start, end, i))
    return chunks


def chunk_records(records: list[dict], **kwargs) -> list[Chunk]:
    out: list[Chunk] = []
    for record in records:
        out.extend(chunk_record(record, **kwargs))
    return out
