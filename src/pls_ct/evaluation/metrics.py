"""Summarization/QA metrics — single consolidated implementation.

Merges the two identical copies from the thesis (``legacy/Extra Code/common_functions.py``
and ``legacy/Extra Code/evaluate.py``) into one tested module. Numeric behavior is preserved:
SQuAD-style normalization, token-F1, exact match, smoothed sentence-BLEU (method4),
and ROUGE-1/2/L f-measures with stemming.

These n-gram/overlap metrics systematically understate abstractive-rewrite quality
(a faithful paraphrase scores low); see docs/RESEARCH_AND_MODELS.md. They are the
preserved baseline, not the final word on summary quality.
"""

from __future__ import annotations

import re
import string
from collections import Counter

from nltk.translate.bleu_score import SmoothingFunction, sentence_bleu
from rouge_score import rouge_scorer

_PUNCT = set(string.punctuation)
_ARTICLES = re.compile(r"\b(a|an|the)\b")
# One scorer instance; RougeScorer is stateless across .score() calls.
_ROUGE = rouge_scorer.RougeScorer(["rouge1", "rouge2", "rougeL"], use_stemmer=True)


def normalize_answer(s: str) -> str:
    """Lower-case, strip punctuation/articles, and collapse whitespace (SQuAD style)."""
    s = s.lower()
    s = "".join(ch for ch in s if ch not in _PUNCT)
    s = _ARTICLES.sub(" ", s)
    return " ".join(s.split())


def f1_score(prediction: str, ground_truth: str) -> float:
    pred_tokens = normalize_answer(prediction).split()
    truth_tokens = normalize_answer(ground_truth).split()
    common = Counter(pred_tokens) & Counter(truth_tokens)
    num_same = sum(common.values())
    if num_same == 0 or not pred_tokens or not truth_tokens:
        return 0.0
    precision = num_same / len(pred_tokens)
    recall = num_same / len(truth_tokens)
    return (2 * precision * recall) / (precision + recall)


def exact_match_score(prediction: str, ground_truth: str) -> bool:
    return normalize_answer(prediction) == normalize_answer(ground_truth)


def bleu_score(prediction: str, references: list[str]) -> float:
    reference_tokens = [normalize_answer(ref).split() for ref in references]
    prediction_tokens = normalize_answer(prediction).split()
    if not prediction_tokens:
        return 0.0
    smoothing = SmoothingFunction().method4
    return sentence_bleu(reference_tokens, prediction_tokens, smoothing_function=smoothing)


def rouge_scores(prediction: str, reference: str) -> dict:
    return _ROUGE.score(normalize_answer(reference), normalize_answer(prediction))


def calculate_metrics(predictions: list[str], references: list[str]) -> dict[str, float]:
    """Aggregate metrics over paired lists. Percentages (0–100), plus the count."""
    if len(predictions) != len(references):
        raise ValueError(
            f"predictions ({len(predictions)}) and references ({len(references)}) must align"
        )
    n = len(references)
    if n == 0:
        raise ValueError("cannot compute metrics over zero examples")

    totals = {"em": 0.0, "f1": 0.0, "bleu": 0.0, "r1": 0.0, "r2": 0.0, "rL": 0.0}
    for pred, ref in zip(predictions, references, strict=True):
        totals["em"] += exact_match_score(pred, ref)
        totals["f1"] += f1_score(pred, ref)
        totals["bleu"] += bleu_score(pred, [ref])
        r = rouge_scores(pred, ref)
        totals["r1"] += r["rouge1"].fmeasure
        totals["r2"] += r["rouge2"].fmeasure
        totals["rL"] += r["rougeL"].fmeasure

    return {
        "Exact Match": 100.0 * totals["em"] / n,
        "F1 Score": 100.0 * totals["f1"] / n,
        "BLEU Score": 100.0 * totals["bleu"] / n,
        "ROUGE-1": 100.0 * totals["r1"] / n,
        "ROUGE-2": 100.0 * totals["r2"] / n,
        "ROUGE-L": 100.0 * totals["rL"] / n,
        "Number of observations": n,
    }
