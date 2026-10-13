"""Tests for dataset cleaning, building QA triples, and split-by-trial."""

from pathlib import Path

from pls_ct.config import REPO_ROOT
from pls_ct.dataset.build import build_examples, load_records, write_jsonl
from pls_ct.dataset.clean import clean_text
from pls_ct.dataset.mapping import QUESTION_TO_SECTIONS
from pls_ct.dataset.split import split_by_trial

SAMPLE = REPO_ROOT / "data" / "sample" / "trials.json"


def test_clean_strips_boilerplate_and_id_and_normalizes():
    raw = "Result.  www.novartisclinicaltrials.com  SYN001A2101 | Trial Results Summary | 3  done"
    out = clean_text(raw, trial_name="SYN001A2101")
    assert "novartisclinicaltrials" not in out
    assert "SYN001A2101" not in out
    assert "Trial Results Summary" not in out
    assert out == "Result. done"


def test_clean_handles_empty():
    assert clean_text("") == ""
    assert clean_text(None or "") == ""


def test_build_examples_from_sample():
    records = load_records(SAMPLE)
    examples, report = build_examples(records)
    # 6 synthetic trials x 8 questions, all sections populated -> 48 examples.
    assert report.n_trials == 6
    assert report.n_examples == 6 * len(QUESTION_TO_SECTIONS)
    assert report.n_skipped_empty_context == 0
    assert report.n_skipped_empty_answer == 0
    ex = examples[0]
    assert set(ex) == {"trial_name", "question", "context", "answer"}
    assert ex["context"] and ex["answer"]


def test_build_skips_empty_context_and_answer():
    records = [
        {
            "trial_name": "T1",
            "report_sections": {},  # no context for any question
            "summary_sections": {q: "ans" for q in QUESTION_TO_SECTIONS},
        },
        {
            "trial_name": "T2",
            "report_sections": {"Objectives": "ctx"},  # only "Why was the research needed?"
            "summary_sections": {},  # no answers
        },
    ]
    examples, report = build_examples(records)
    assert examples == []
    assert report.n_skipped_empty_context > 0
    assert report.n_skipped_empty_answer > 0


def test_split_by_trial_no_leakage():
    records = load_records(SAMPLE)
    examples, _ = build_examples(records)
    splits = split_by_trial(examples, seed=42)

    def trials(key):
        return {e["trial_name"] for e in splits[key]}

    assert trials("train") & trials("val") == set()
    assert trials("train") & trials("test") == set()
    assert trials("val") & trials("test") == set()
    # All examples accounted for.
    assert sum(len(v) for v in splits.values()) == len(examples)
    # With 6 trials and 0.7/0.15/0.15, all three splits are non-empty.
    assert all(len(v) > 0 for v in splits.values())


def test_split_is_deterministic():
    records = load_records(SAMPLE)
    examples, _ = build_examples(records)
    a = split_by_trial(examples, seed=7)
    b = split_by_trial(examples, seed=7)
    assert [e["trial_name"] for e in a["test"]] == [e["trial_name"] for e in b["test"]]


def test_write_jsonl_roundtrip(tmp_path: Path):
    examples = [{"trial_name": "T1", "question": "q", "context": "c", "answer": "a"}]
    out = tmp_path / "ex.jsonl"
    write_jsonl(examples, out)
    lines = out.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
