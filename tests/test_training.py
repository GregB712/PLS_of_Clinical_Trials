"""Tests for training data-prep (pure) and the ML-gated trainer guard."""

import builtins

import pytest

from pls_ct.training.dataprep import (
    assert_no_leakage,
    dataset_stats,
    find_leakage,
    to_training_pairs,
)
from pls_ct.training.finetune import FinetuneConfig, finetune_seq2seq

EXAMPLES = [
    {"trial_name": "T1", "question": "Why?", "context": "ctx one", "answer": "plain one"},
    {"trial_name": "T1", "question": "Who?", "context": "ctx two", "answer": "plain two"},
    {"trial_name": "T2", "question": "Why?", "context": "ctx three", "answer": ""},  # empty answer
]


def test_to_training_pairs_builds_prompt_and_skips_empty():
    pairs = to_training_pairs(EXAMPLES)
    assert len(pairs) == 2  # the empty-answer example is dropped
    assert "CONTEXT" in pairs[0]["input_text"] and "QUESTION" in pairs[0]["input_text"]
    assert pairs[0]["target_text"] == "plain one"


def test_find_leakage_clean_and_dirty():
    clean = {"train": [EXAMPLES[0]], "test": [{"trial_name": "T9"}]}
    assert find_leakage(clean) == {}

    dirty = {"train": [{"trial_name": "T1"}], "test": [{"trial_name": "T1"}]}
    overlaps = find_leakage(dirty)
    assert overlaps and "T1" in next(iter(overlaps.values()))


def test_assert_no_leakage_raises():
    with pytest.raises(ValueError, match="leakage"):
        assert_no_leakage({"train": [{"trial_name": "X"}], "test": [{"trial_name": "X"}]})


def test_dataset_stats():
    stats = dataset_stats(EXAMPLES)
    assert stats == {"n_examples": 3, "n_trials": 2, "n_questions": 2}


def test_finetune_requires_ml_extra(monkeypatch, tmp_path):
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name in {"torch", "transformers"}:
            raise ImportError("no ml")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    splits = {"train": EXAMPLES[:2], "val": [], "test": []}
    with pytest.raises(RuntimeError, match=r"\[ml\]"):
        finetune_seq2seq(splits, output_dir=tmp_path, cfg=FinetuneConfig(epochs=1))
