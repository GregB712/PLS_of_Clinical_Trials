"""Tests for the model interface, the Lead baseline, and the evaluation harness."""

import builtins

import pytest

from pls_ct.evaluation.harness import evaluate_backend
from pls_ct.models.base import GenConfig, SummarizerBackend, SummaryResult
from pls_ct.models.baseline import LeadSentencesBackend
from pls_ct.models.generative import build_prompt


def test_lead_backend_returns_first_k_sentences():
    backend = LeadSentencesBackend(k=2)
    ctx = "First sentence. Second sentence. Third sentence."
    res = backend.summarize(ctx, "Why?", GenConfig())
    assert res.text == "First sentence. Second sentence."
    assert res.model == "lead-2"
    assert res.output_tokens is not None
    assert isinstance(res, SummaryResult)


def test_lead_backend_satisfies_protocol():
    assert isinstance(LeadSentencesBackend(), SummarizerBackend)


def test_build_prompt_contains_context_and_question():
    p = build_prompt("the context", "the question")
    assert "the context" in p
    assert "the question" in p
    assert "plain language" in p


def test_harness_scores_and_handles_errors():
    examples = [
        {
            "trial_name": "T1",
            "question": "Why?",
            "context": "A b c. D e f.",
            "answer": "A b c. D e f.",
        },
        {"trial_name": "T2", "question": "Who?", "context": "X y z.", "answer": "X y z."},
    ]
    results = evaluate_backend(LeadSentencesBackend(k=5), examples)
    assert results["n_examples"] == 2
    assert results["n_scored"] == 2
    assert results["n_errors"] == 0
    # Lead-5 returns the whole (short) context, which equals the reference here.
    assert results["aggregate"]["Exact Match"] == 100.0


def test_harness_records_backend_exceptions_without_aborting():
    class Boom:
        name = "boom"

        def summarize(self, context, question, cfg):
            raise RuntimeError("kaboom")

    examples = [{"trial_name": "T1", "question": "Why?", "context": "c", "answer": "a"}]
    results = evaluate_backend(Boom(), examples)
    assert results["n_scored"] == 0
    assert results["n_errors"] == 1
    assert results["aggregate"] == {}
    assert "kaboom" in results["per_example"][0]["error"]


def test_ml_backend_raises_helpful_error_without_torch(monkeypatch):
    # Simulate torch missing; the lazy loader must raise a clear install hint.
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name in {"torch", "transformers"}:
            raise ImportError("no ml")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    from pls_ct.models.extractive_qa import DistilBertQABackend

    backend = DistilBertQABackend()
    with pytest.raises(RuntimeError, match=r"\[ml\]"):
        backend.summarize("ctx", "q", GenConfig())


class _WordTokenizer:
    """Whitespace stand-in for a HF tokenizer: one token per word."""

    def __call__(self, text, add_special_tokens=True):
        class Enc:
            input_ids = text.split()

        return Enc()

    def decode(self, ids, skip_special_tokens=True):
        return " ".join(ids)


def test_fit_context_keeps_question_when_context_is_long():
    from pls_ct.models.generative import fit_context

    tok = _WordTokenizer()
    question = "Why was the research needed?"
    overhead = len(tok(build_prompt("", question)).input_ids)
    ctx = " ".join(f"w{i}" for i in range(500))
    fitted = fit_context(tok, ctx, question, max_tokens=overhead + 50)
    prompt = build_prompt(fitted, question)
    assert len(tok(prompt).input_ids) <= overhead + 50
    assert question in prompt  # the question survives; the context is what gets cut
    assert fitted.split() == [f"w{i}" for i in range(50)]


def test_fit_context_leaves_short_context_unchanged():
    from pls_ct.models.generative import fit_context

    assert fit_context(_WordTokenizer(), "short context", "Q?", max_tokens=1024) == "short context"


def test_default_generation_is_deterministic_and_long_enough():
    cfg = GenConfig()
    assert cfg.temperature == 0.0  # greedy by default: benchmark numbers are reproducible
    assert cfg.max_new_tokens >= 512  # median test reference is ~280 Flan-T5 tokens
