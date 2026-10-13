"""Generative backend using Hugging Face Transformers (seq2seq or causal LM).

Device-aware (CPU-first, GPU-automatic) and lazily loaded, so importing this module
never requires torch. Install the extra with ``pip install -e '.[ml]'`` to use it.
The instruction prompt mirrors the thesis (``Extra Code/pretrained.py``).
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

    def __init__(self, model_id: str, *, task: str = "auto", device: str | None = None) -> None:
        self.name = model_id
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
        prompt = build_prompt(context, question)
        inputs = self._tokenizer(prompt, return_tensors="pt", truncation=True)
        if self.device != "cpu":
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
        input_len = int(inputs["input_ids"].shape[-1])

        start = time.perf_counter()
        with self._torch.no_grad():
            output = self._model.generate(
                **inputs,
                max_new_tokens=cfg.max_new_tokens,
                do_sample=cfg.temperature > 0,
                temperature=max(cfg.temperature, 1e-5),
                top_p=cfg.top_p,
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
