"""Tests for ingestion: section extraction (pure), filename classification, pairing."""

from pls_ct.ingestion.pair import (
    classify_filename,
    ingest_directory,
    plan_pairs,
)
from pls_ct.ingestion.parser import extract_sections


def test_extract_report_sections_from_lines():
    lines = [
        ("Objectives", True),
        ("To test the drug.", False),
        ("More detail.", False),
        ("Conclusion", True),
        ("It worked.", False),
    ]
    out = extract_sections(lines, "report")
    assert out == {"Objectives": "To test the drug. More detail.", "Conclusion": "It worked."}


def test_extract_ignores_non_bold_headings_and_pagenumbers():
    lines = [
        ("Objectives", False),  # not bold -> not a heading
        ("Page 3", True),  # page number -> skipped
        ("Conclusion", True),
        ("Done.", False),
    ]
    out = extract_sections(lines, "report")
    # "Objectives" line is dropped (no current section yet), only Conclusion captured.
    assert out == {"Conclusion": "Done."}


def test_extract_summary_maps_variant_to_canonical():
    lines = [
        ("What were the main results of this trial?", True),  # variant
        ("People improved.", False),
    ]
    out = extract_sections(lines, "summary")
    assert out == {"What were the results of the trial?": "People improved."}


def test_classify_filename():
    assert classify_filename("CAIN457A2325.pdf") == ("CAIN457A2325", "report")
    assert classify_filename("CAIN457A2325_PatientSummary_English-US_19Jul2021.pdf") == (
        "CAIN457A2325",
        "summary",
    )
    assert classify_filename("CQVM149B2303_PediatricPatientSummary_English-US_17Aug2021.pdf") == (
        "CQVM149B2303",
        "summary",
    )


def test_plan_pairs_groups_by_protocol():
    plan = plan_pairs(
        [
            "CAIN457A2325.pdf",
            "CAIN457A2325_PatientSummary_x.pdf",
            "SOLO001.pdf",  # report with no summary
        ]
    )
    assert plan["CAIN457A2325"] == {
        "report": "CAIN457A2325.pdf",
        "summary": "CAIN457A2325_PatientSummary_x.pdf",
    }
    assert plan["SOLO001"] == {"report": "SOLO001.pdf"}


def test_ingest_directory_dry_run_pairs_without_extraction(tmp_path):
    (tmp_path / "T1.pdf").write_bytes(b"%PDF-1.4 report")
    (tmp_path / "T1_PatientSummary_x.pdf").write_bytes(b"%PDF-1.4 summary")
    (tmp_path / "T2.pdf").write_bytes(b"%PDF-1.4 lonely report")

    records, report = ingest_directory(tmp_path, dry_run=True)
    assert records == []
    assert report.paired == ["T1"]
    assert report.unpaired == ["T2"]


def test_ingest_directory_with_stub_extractor(tmp_path):
    (tmp_path / "T1.pdf").write_bytes(b"report-bytes")
    (tmp_path / "T1_PatientSummary_x.pdf").write_bytes(b"summary-bytes")

    def stub(path: str, kind: str) -> dict:
        if kind == "report":
            return {"Objectives": "ctx"}
        return {"Why was the research needed?": "ans"}

    records, report = ingest_directory(tmp_path, extractor=stub)
    assert report.summary()["paired"] == 1
    assert len(records) == 1
    rec = records[0]
    assert rec["trial_name"] == "T1"
    assert rec["source"] == "novartis"
    assert rec["report_sections"] == {"Objectives": "ctx"}
    assert "ingested_at" in rec


def test_ingest_directory_flags_empty_sections(tmp_path):
    (tmp_path / "T1.pdf").write_bytes(b"x")
    (tmp_path / "T1_PatientSummary_x.pdf").write_bytes(b"y")

    records, report = ingest_directory(tmp_path, extractor=lambda path, kind: {})
    assert records == []
    assert report.empty_sections == ["T1"]
