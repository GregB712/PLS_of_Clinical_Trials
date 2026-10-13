"""PDF -> Markdown conversion via Microsoft MarkItDown (verified against v0.1.6).

Complements the section-based ``parser.py`` path: MarkItDown preserves more document
structure (headings, tables) as Markdown, which is better for RAG chunking later.
Lazily imported so the package works without the optional ``[pdf]`` extra; install with
``pip install -e '.[pdf]'``.
"""

from __future__ import annotations

from pathlib import Path

# Documents shorter than this after conversion are likely scanned/image PDFs with no
# selectable text (MarkItDown has no OCR by default). We flag rather than silently accept.
_SUSPICIOUSLY_SHORT = 50


class MarkdownConversionError(RuntimeError):
    pass


def _require_pdf_extra():
    try:
        from markitdown import MarkItDown  # noqa: F401
    except ImportError as exc:  # pragma: no cover - exercised via stubbed-import test
        raise MarkdownConversionError(
            "PDF->Markdown needs the pdf extra. Install it with:\n    pip install -e '.[pdf]'"
        ) from exc


def pdf_to_markdown(pdf_path: str | Path) -> tuple[str, list[str]]:
    """Convert a PDF to Markdown. Returns ``(markdown, warnings)``.

    Raises :class:`MarkdownConversionError` if the pdf extra is missing or conversion fails.
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise MarkdownConversionError(f"file not found: {pdf_path}")

    _require_pdf_extra()
    from markitdown import MarkItDown

    try:
        result = MarkItDown().convert(str(pdf_path))
    except Exception as exc:  # noqa: BLE001 - normalize to our error type
        raise MarkdownConversionError(f"MarkItDown failed on {pdf_path.name}: {exc}") from exc

    markdown = (result.text_content or "").strip()
    warnings: list[str] = []
    if not markdown:
        warnings.append("empty conversion (likely a scanned/image PDF; OCR not enabled)")
    elif len(markdown) < _SUSPICIOUSLY_SHORT:
        warnings.append(
            f"suspiciously short output ({len(markdown)} chars); check for a scanned PDF"
        )
    return markdown, warnings
