"""Pair Clinical Trial Results reports with their plain-language Patient Summaries.

Replaces ``xml2json.py``. Files are classified by name (summary vs report) and grouped
by protocol-ID prefix. Ingestion is idempotent (dedup by content hash), supports a
dry-run, validates that extracted sections are non-empty, and emits a per-file status
report instead of silently producing blanks.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from pls_ct.ingestion.parser import extract_sections_from_pdf

_SUMMARY_MARKER = re.compile(r"patientsummary", re.IGNORECASE)  # covers PediatricPatientSummary too


def classify_filename(name: str) -> tuple[str, str]:
    """Return ``(protocol_id, kind)`` where kind is 'summary' or 'report'.

    Protocol ID is the leading token before the first ``_`` or whitespace, e.g.
    ``CAIN457A2325_PatientSummary_...pdf`` and ``CAIN457A2325.pdf`` both map to
    ``CAIN457A2325``.
    """
    stem = Path(name).stem
    protocol_id = re.split(r"[_\s]", stem, maxsplit=1)[0]
    kind = "summary" if _SUMMARY_MARKER.search(name.replace("_", "")) else "report"
    return protocol_id, kind


def plan_pairs(filenames: list[str]) -> dict[str, dict[str, str]]:
    """Group filenames into ``{protocol_id: {"report": name, "summary": name}}``.

    If several files map to the same slot, the first encountered wins (sorted order).
    """
    plan: dict[str, dict[str, str]] = {}
    for name in sorted(filenames):
        protocol_id, kind = classify_filename(name)
        plan.setdefault(protocol_id, {})
        plan[protocol_id].setdefault(kind, name)
    return plan


def file_hash(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


@dataclass
class IngestReport:
    paired: list[str] = field(default_factory=list)
    unpaired: list[str] = field(default_factory=list)  # protocol ids missing a report or summary
    empty_sections: list[str] = field(default_factory=list)
    duplicates: list[str] = field(default_factory=list)
    errors: list[tuple[str, str]] = field(default_factory=list)  # (protocol_id, message)

    def summary(self) -> dict[str, int]:
        return {
            "paired": len(self.paired),
            "unpaired": len(self.unpaired),
            "empty_sections": len(self.empty_sections),
            "duplicates": len(self.duplicates),
            "errors": len(self.errors),
        }


def ingest_directory(
    raw_dir: str | Path,
    *,
    dry_run: bool = False,
    extractor: Callable[[str, str], dict[str, str]] = extract_sections_from_pdf,
    pattern: str = "*.pdf",
) -> tuple[list[dict], IngestReport]:
    """Build trial records from a directory of paired PDFs.

    ``extractor(path, kind)`` is injectable so tests can avoid real PDFs. On a dry run,
    files are classified and paired but not extracted (records come back empty).
    """
    raw_dir = Path(raw_dir)
    filenames = [p.name for p in sorted(raw_dir.glob(pattern))]
    plan = plan_pairs(filenames)

    records: list[dict] = []
    report = IngestReport()
    seen_hashes: set[str] = set()

    for protocol_id, slots in plan.items():
        if "report" not in slots or "summary" not in slots:
            report.unpaired.append(protocol_id)
            continue

        report_path = raw_dir / slots["report"]
        summary_path = raw_dir / slots["summary"]

        if dry_run:
            report.paired.append(protocol_id)
            continue

        # Idempotency: skip if we've already ingested this exact (report, summary) content.
        try:
            key = file_hash(report_path) + file_hash(summary_path)
        except OSError as exc:
            report.errors.append((protocol_id, f"hash failed: {exc}"))
            continue
        if key in seen_hashes:
            report.duplicates.append(protocol_id)
            continue
        seen_hashes.add(key)

        try:
            report_sections = extractor(str(report_path), "report")
            summary_sections = extractor(str(summary_path), "summary")
        except Exception as exc:  # noqa: BLE001 - record and continue, don't abort the batch
            report.errors.append((protocol_id, f"extraction failed: {exc}"))
            continue

        if not report_sections or not summary_sections:
            report.empty_sections.append(protocol_id)
            continue

        records.append(
            {
                "trial_name": protocol_id,
                "source": "novartis",
                "report_path": str(report_path),
                "summary_path": str(summary_path),
                "report_sections": report_sections,
                "summary_sections": summary_sections,
                "ingested_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        report.paired.append(protocol_id)

    return records, report
