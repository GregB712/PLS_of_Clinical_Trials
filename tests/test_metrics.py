"""Tests pinning the consolidated metrics behavior."""

import math

import pytest

from pls_ct.evaluation import metrics


def test_normalize_answer_strips_punct_articles_case():
    assert metrics.normalize_answer("The  Quick, Brown FOX!") == "quick brown fox"


def test_identical_strings_score_perfect():
    pred = ["the patients recovered fully"]
    ref = ["the patients recovered fully"]
    out = metrics.calculate_metrics(pred, ref)
    assert out["Exact Match"] == 100.0
    assert out["F1 Score"] == 100.0
    assert out["ROUGE-1"] == 100.0
    assert out["ROUGE-L"] == 100.0
    assert out["Number of observations"] == 1


def test_disjoint_strings_score_zero_overlap():
    assert metrics.f1_score("alpha beta", "gamma delta") == 0.0
    assert metrics.exact_match_score("alpha", "beta") is False


def test_f1_partial_overlap():
    # pred tokens: {cat, sat}; truth tokens: {cat, ran}; 1 common.
    # precision = 1/2, recall = 1/2 -> f1 = 0.5
    assert math.isclose(metrics.f1_score("the cat sat", "the cat ran"), 0.5, rel_tol=1e-9)


def test_empty_prediction_is_zero_not_crash():
    assert metrics.f1_score("", "something") == 0.0
    assert metrics.bleu_score("", ["something"]) == 0.0


def test_mismatched_lengths_raise():
    with pytest.raises(ValueError):
        metrics.calculate_metrics(["a"], ["a", "b"])


def test_zero_examples_raise():
    with pytest.raises(ValueError):
        metrics.calculate_metrics([], [])
