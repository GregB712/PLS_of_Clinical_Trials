"""Section extraction, refactored from the thesis ``parser.py``.

The detection logic is a **pure function over ``(text, is_bold)`` lines**, so it is
testable without a PDF. ``extract_sections_from_pdf`` is a thin pdfminer wrapper that
produces those lines. A line starts a new section when it is bold and matches a known
section heading; subsequent lines accumulate into the current section.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

from pls_ct.ingestion.sections import REPORT_SECTIONS, SUMMARY_VARIANTS

Line = tuple[str, bool]  # (text, is_bold)

_REPORT_PATTERNS = [(name, re.compile(name, re.IGNORECASE)) for name in REPORT_SECTIONS]
_PAGE_NUMBER = re.compile(r"Page \d+", re.IGNORECASE)
_SKIP_SUBSTRINGS = ("Clinical Trial Results Website",)


def _norm(s: str) -> str:
    return " ".join(s.split()).strip().lower()


# Precompute normalized summary-question lookups (strip trailing '?' for robust matching).
_SUMMARY_LOOKUP = {
    _norm(variant).rstrip("?").strip(): canonical
    for variant, canonical in SUMMARY_VARIANTS.items()
}


def detect_report_section(text: str, bold: bool) -> str | None:
    if not bold:
        return None
    for name, pattern in _REPORT_PATTERNS:
        if pattern.search(text):
            return name
    return None


def detect_summary_section(text: str, bold: bool) -> str | None:
    if not bold:
        return None
    key = _norm(text).rstrip("?").strip()
    return _SUMMARY_LOOKUP.get(key)


def extract_sections(lines: Iterable[Line], kind: str) -> dict[str, str]:
    """Group lines into {section_name: text}. ``kind`` is 'report' or 'summary'."""
    if kind == "report":
        detect = detect_report_section
    elif kind == "summary":
        detect = detect_summary_section
    else:
        raise ValueError(f"kind must be 'report' or 'summary', got {kind!r}")

    sections: dict[str, list[str]] = {}
    current: str | None = None

    for text, bold in lines:
        text = text.strip()
        if not text or _PAGE_NUMBER.search(text):
            continue
        if any(sub in text for sub in _SKIP_SUBSTRINGS):
            continue

        found = detect(text, bold)
        if found:
            current = found
            sections.setdefault(current, [])
            # The heading line itself is not part of the body.
            continue
        if current is not None:
            sections[current].append(text)

    return {name: " ".join(body).strip() for name, body in sections.items()}


def extract_sections_from_pdf(pdf_path: str, kind: str) -> dict[str, str]:
    """Extract sections from a real PDF using pdfminer (bold = font name contains 'bold')."""
    from pdfminer.high_level import extract_pages
    from pdfminer.layout import LTChar, LTTextBoxHorizontal

    def iter_lines() -> Iterable[Line]:
        for page_layout in extract_pages(pdf_path):
            for element in page_layout:
                if not isinstance(element, LTTextBoxHorizontal):
                    continue
                for text_line in element:
                    text = text_line.get_text().strip()
                    if not text:
                        continue
                    bold = any(
                        isinstance(ch, LTChar) and "bold" in ch.fontname.lower()
                        for ch in text_line
                    )
                    yield text, bold

    return extract_sections(iter_lines(), kind)
