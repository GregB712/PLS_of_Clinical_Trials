"""Tests for the MarkItDown PDF->Markdown path (no markitdown install required)."""

import builtins

import pytest

from pls_ct.ingestion.markdown import MarkdownConversionError, pdf_to_markdown


def test_missing_file_raises(tmp_path):
    with pytest.raises(MarkdownConversionError, match="file not found"):
        pdf_to_markdown(tmp_path / "nope.pdf")


def test_missing_extra_raises_helpful_error(tmp_path, monkeypatch):
    pdf = tmp_path / "x.pdf"
    pdf.write_bytes(b"%PDF-1.4")

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "markitdown" or name.startswith("markitdown."):
            raise ImportError("no markitdown")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    with pytest.raises(MarkdownConversionError, match=r"\[pdf\]"):
        pdf_to_markdown(pdf)


def test_short_output_is_flagged(tmp_path, monkeypatch):
    pdf = tmp_path / "x.pdf"
    pdf.write_bytes(b"%PDF-1.4")

    # Inject a fake markitdown module so no real dependency/PDF is needed.
    import sys
    import types

    fake = types.ModuleType("markitdown")

    class _Result:
        text_content = "tiny"

    class MarkItDown:
        def convert(self, _path):
            return _Result()

    fake.MarkItDown = MarkItDown
    monkeypatch.setitem(sys.modules, "markitdown", fake)

    markdown, warnings = pdf_to_markdown(pdf)
    assert markdown == "tiny"
    assert any("suspiciously short" in w for w in warnings)
