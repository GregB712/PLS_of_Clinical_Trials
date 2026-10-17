"""Generative backend using Hugging Face Transformers (seq2seq or causal LM).

Device-aware (CPU-first, GPU-automatic) and lazily loaded, so importing this module
never requires torch. Install the extra with ``pip install -e '.[ml]'`` to use it.
The instruction prompt mirrors the thesis (``legacy/Extra Code/pretrained.py``).
"""

from __future__ import annotations

import time

from pls_ct.device import resolve_device
from pls_ct.models.base import GenConfig, SummaryResult

_PROMPT = (
    "CONTEXT:\n{context}\n\n"
    "QUESTION:\n{question}\n\n"
    "INSTRUCTIONS:\nAnswer the QUESTION using only the CONTEXT above. "
    "Keep the answer grounded in the facts of the CONTEXT and written in plain language."
)


def build_prompt(context: str, question: str) -> str:
    """Build the instruction prompt (pure; testable without a model)."""
    return _PROMPT.format(context=context, question=question)


def fit_context(tokenizer, context: str, question: str, max_tokens: int) -> str:
    """Shorten ``context`` so the whole prompt fits in ``max_tokens``.

    The prompt puts the QUESTION after the CONTEXT, so truncating the tokenized prompt from the
    right would silently drop the question on long inputs. Cutting the context instead keeps the
    question and instructions intact.
    """
    overhead = len(tokenizer(build_prompt("", question)).input_ids)
    ids = tokenizer(context, add_special_tokens=False).input_ids
    budget = max(max_tokens - overhead, 0)
    if len(ids) <= budget:
        return context
    return tokenizer.decode(ids[:budget], skip_special_tokens=True)


def _require_ml():
    try:
        import torch  # noqa: F401
        import transformers  # noqa: F401
    except ImportError as exc:  # pragma: no cover - exercised via test with stubbed import
        raise RuntimeError(
            "The generative backend needs the ML extra. Install it with:\n"
            "    pip install -e '.[ml]'"
        ) from exc


class HFGenerativeBackend:
    """Lazily loads a seq2seq (T5/BART) or causal (Mistral/Llama) model."""

    def __init__(
        self,
        model_id: str,
        *,
        task: str = "auto",
        device: str | None = None,
        max_input_tokens: int = 1024,
    ) -> None:
        self.name = model_id
        self.max_input_tokens = max_input_tokens  # matches FinetuneConfig.max_input_len
        self.model_id = model_id
        self.task = task
        self.device = resolve_device(device)
        self._tokenizer = None
        self._model = None

    def _load(self) -> None:
        if self._model is not None:
            return
        _require_ml()
        import torch
        from transformers import AutoModelForCausalLM, AutoModelForSeq2SeqLM, AutoTokenizer

        self._tokenizer = AutoTokenizer.from_pretrained(self.model_id)
        task = self.task
        if task == "auto":
            try:
                self._model = AutoModelForSeq2SeqLM.from_pretrained(self.model_id)
                task = "seq2seq"
            except (ValueError, OSError):
                self._model = AutoModelForCausalLM.from_pretrained(self.model_id)
                task = "causal"
        elif task == "seq2seq":
            self._model = AutoModelForSeq2SeqLM.from_pretrained(self.model_id)
        else:
            self._model = AutoModelForCausalLM.from_pretrained(self.model_id)
        self._resolved_task = task
        if self.device != "cpu":
            self._model = self._model.to(self.device)
        self._torch = torch

    def summarize(self, context: str, question: str, cfg: GenConfig) -> SummaryResult:
        self._load()
        context = fit_context(self._tokenizer, context, question, self.max_input_tokens)
        prompt = build_prompt(context, question)
        inputs = self._tokenizer(
            prompt, return_tensors="pt", truncation=True, max_length=self.max_input_tokens
        )
        if self.device != "cpu":
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
        input_len = int(inputs["input_ids"].shape[-1])

        start = time.perf_counter()
        sampling = {"do_sample": False}
        if cfg.temperature > 0:
            sampling = {"do_sample": True, "temperature": cfg.temperature, "top_p": cfg.top_p}
        with self._torch.no_grad():
            output = self._model.generate(
                **inputs, max_new_tokens=cfg.max_new_tokens, **sampling
            )
        latency = time.perf_counter() - start

        new_tokens = output[0]
        if self._resolved_task == "causal":
            new_tokens = new_tokens[input_len:]  # strip the echoed prompt
        text = self._tokenizer.decode(new_tokens, skip_special_tokens=True).strip()

        return SummaryResult(
            text=text,
            model=self.model_id,
            generation_config=cfg,
            input_tokens=input_len,
            output_tokens=int(new_tokens.shape[-1]),
            latency_s=latency,
            provenance={"question": question, "device": self.device},
        )
