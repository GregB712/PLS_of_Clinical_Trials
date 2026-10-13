"""DistilBERT extractive-QA backend — the thesis's baseline, preserved.

IMPORTANT (see docs/PROJECT_AUDIT.md section 4.1): the thesis trained this model with
labels built via ``context.find(answer)``. Because the plain-language answer is a
*rewrite* of the report, it is almost never a verbatim substring of the context, so
``find`` returns -1 and the span labels collapse to the ``[CLS]`` token. Extractive
span-QA therefore cannot express an abstractive rewrite. This backend is kept to
reproduce that honest negative result, NOT because the framing is correct.

Lazily loaded; needs ``pip install -e '.[ml]'``.
"""

from __future__ import annotations

import time

from pls_ct.device import resolve_device
from pls_ct.models.base import GenConfig, SummaryResult


def _require_ml():
    try:
        import torch  # noqa: F401
        import transformers  # noqa: F401
    except ImportError as exc:  # pragma: no cover - exercised via test with stubbed import
        raise RuntimeError(
            "The extractive-QA backend needs the ML extra. Install it with:\n"
            "    pip install -e '.[ml]'"
        ) from exc


class DistilBertQABackend:
    def __init__(
        self, model_id: str = "distilbert-base-uncased", *, device: str | None = None
    ) -> None:
        self.name = f"extractive-qa:{model_id}"
        self.model_id = model_id
        self.device = resolve_device(device)
        self._tokenizer = None
        self._model = None

    def _load(self) -> None:
        if self._model is not None:
            return
        _require_ml()
        import torch
        from transformers import DistilBertForQuestionAnswering, DistilBertTokenizerFast

        self._tokenizer = DistilBertTokenizerFast.from_pretrained(self.model_id)
        self._model = DistilBertForQuestionAnswering.from_pretrained(self.model_id)
        if self.device != "cpu":
            self._model = self._model.to(self.device)
        self._torch = torch

    def summarize(self, context: str, question: str, cfg: GenConfig) -> SummaryResult:
        self._load()
        inputs = self._tokenizer(
            question, context, truncation=True, padding="max_length",
            max_length=384, return_tensors="pt",
        )
        if self.device != "cpu":
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

        start = time.perf_counter()
        with self._torch.no_grad():
            out = self._model(**inputs)
        latency = time.perf_counter() - start

        start_idx = int(self._torch.argmax(out.start_logits, dim=1).item())
        end_idx = int(self._torch.argmax(out.end_logits, dim=1).item())
        warnings = []
        if end_idx < start_idx:
            text = ""
            warnings.append("empty span (end < start)")
        else:
            span = inputs["input_ids"][0][start_idx : end_idx + 1]
            text = self._tokenizer.decode(span, skip_special_tokens=True).strip()
        if not text:
            warnings.append("extractive QA returned no span (expected for abstractive targets)")

        return SummaryResult(
            text=text,
            model=self.name,
            generation_config=cfg,
            latency_s=latency,
            provenance={"question": question, "device": self.device},
            warnings=warnings,
        )
