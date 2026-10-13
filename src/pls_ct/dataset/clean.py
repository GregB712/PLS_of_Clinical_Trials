"""Text cleaning for trial/summary sections (from ``finalDataset.ipynb`` "Clean up Database").

Strips Novartis contact boilerplate, repeated page footers, and the trial's own
protocol ID, then normalizes unicode and whitespace. Deliberately conservative:
it removes extraction artifacts, not clinically meaningful content.
"""

from __future__ import annotations

from unicodedata import normalize as _unormalize

from pls_ct.dataset.mapping import NOVARTIS_BOILERPLATE, footer_boilerplate

_FOOTERS = footer_boilerplate()


def clean_text(text: str, trial_name: str | None = None) -> str:
    """Remove boilerplate + the trial id, normalize unicode/whitespace."""
    if not text:
        return ""
    # Strip longest footers first, then contact boilerplate, then the protocol id.
    for term in _FOOTERS:
        text = text.replace(term, " ")
    for term in NOVARTIS_BOILERPLATE:
        text = text.replace(term, " ")
    if trial_name:
        text = text.replace(trial_name, " ")
    # NFKD-normalize and drop non-ASCII extraction artifacts (matches thesis behavior).
    text = _unormalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return " ".join(text.split())


def clean_record(record: dict) -> dict:
    """Return a copy of a trial record with cleaned report/summary section text."""
    trial_name = record.get("trial_name")
    cleaned = dict(record)
    for key in ("report_sections", "summary_sections"):
        sections = record.get(key) or {}
        cleaned[key] = {
            name: clean_text(value, trial_name) for name, value in sections.items()
        }
    return cleaned
