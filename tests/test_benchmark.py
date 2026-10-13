"""Tests for the multi-backend benchmark + experiment persistence."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from pls_ct.config import REPO_ROOT
from pls_ct.dataset.build import build_examples, load_records
from pls_ct.db import repository
from pls_ct.db.engine import create_all
from pls_ct.evaluation.benchmark import (
    comparison_markdown,
    examples_fingerprint,
    run_benchmark,
    software_versions,
)
from pls_ct.models.baseline import LeadSentencesBackend

SAMPLE = REPO_ROOT / "data" / "sample" / "trials.json"


@pytest.fixture
def examples():
    return build_examples(load_records(SAMPLE))[0]


def test_fingerprint_is_order_independent(examples):
    fp1 = examples_fingerprint(examples)
    fp2 = examples_fingerprint(list(reversed(examples)))
    assert fp1 == fp2 and len(fp1) == 16


def test_software_versions_capture():
    v = software_versions()
    assert v["pls_ct"] and v["python"]
    assert "torch" in v  # present as a key even when torch isn't installed (None)


def test_run_benchmark_multi_backend(examples):
    bench = run_benchmark([LeadSentencesBackend(2), LeadSentencesBackend(3)], examples)
    assert bench["n_examples"] == len(examples)
    assert [r["backend"] for r in bench["results"]] == ["lead-2", "lead-3"]
    assert all("aggregate" in r for r in bench["results"])
    assert bench["split_fingerprint"]


def test_comparison_markdown_has_rows(examples):
    bench = run_benchmark([LeadSentencesBackend(2)], examples)
    table = comparison_markdown(bench)
    assert "| Backend |" in table
    assert "lead-2" in table
    assert "F1 Score" in table


def test_save_and_list_experiment(examples):
    engine = create_engine("sqlite://", future=True)
    create_all(engine)
    bench = run_benchmark([LeadSentencesBackend(2), LeadSentencesBackend(3)], examples)
    with Session(engine, future=True) as session:
        exp = repository.save_experiment(session, bench)
        session.commit()
        assert exp.id is not None
        assert len(exp.results) == 2

        listed = repository.list_experiments(session)
        assert len(listed) == 1
        assert listed[0].n_examples == len(examples)
        assert {r.backend for r in listed[0].results} == {"lead-2", "lead-3"}
