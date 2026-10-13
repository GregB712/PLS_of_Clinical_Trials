"""Base class + errors shared by all hosted providers.

Handles the cross-cutting concerns once: key resolution (env or explicit, never
hardcoded), masking, prompt building, latency, normalized error classification, and
cost estimation. Subclasses implement just ``_make_client`` and ``_generate``.
"""

from __future__ import annotations

import os
import time
from abc import ABC, abstractmethod
from typing import Any, ClassVar

from pls_ct.models.base import GenConfig, SummaryResult
from pls_ct.models.generative import build_prompt
from pls_ct.providers.pricing import estimate_cost


class ProviderError(RuntimeError):
    """Base for all provider failures."""


class ProviderConfigError(ProviderError):
    """Missing/invalid key, unknown provider, or unsupported model (no request made)."""


class ProviderAuthError(ProviderError):
    """Authentication/authorization rejected by the provider."""


class ProviderRateLimitError(ProviderError):
    """Provider rate limit / quota exceeded."""


class ProviderResponseError(ProviderError):
    """Any other failed request (network, server, bad response)."""


def mask_key(key: str | None) -> str:
    """Render an API key for display without revealing it."""
    if not key:
        return "<none>"
    if len(key) <= 8:
        return "*" * len(key)
    return f"{key[:4]}…{key[-4:]}"


class BaseProvider(ABC):
    provider_name: ClassVar[str]
    api_key_env: ClassVar[str]

    def __init__(
        self,
        model: str,
        *,
        api_key: str | None = None,
        client: Any = None,
    ) -> None:
        self.model = model
        self.name = f"{self.provider_name}:{model}"
        self._api_key = api_key
        self._client = client  # injectable (tests / preconfigured clients)

    # --- key handling -----------------------------------------------------
    def resolve_key(self) -> str:
        key = self._api_key or os.environ.get(self.api_key_env)
        if not key:
            raise ProviderConfigError(
                f"{self.provider_name}: no API key. Set ${self.api_key_env} or pass api_key."
            )
        return key

    def has_key(self) -> bool:
        return bool(self._api_key or os.environ.get(self.api_key_env))

    def masked_key(self) -> str:
        return mask_key(self._api_key or os.environ.get(self.api_key_env))

    def validate(self) -> None:
        """Check configuration (key presence) without making a network call."""
        self.resolve_key()

    # --- generation -------------------------------------------------------
    def _ensure_client(self) -> Any:
        if self._client is None:
            self._client = self._make_client(self.resolve_key())
        return self._client

    def summarize(self, context: str, question: str, cfg: GenConfig) -> SummaryResult:
        prompt = build_prompt(context, question)
        client = self._ensure_client()
        start = time.perf_counter()
        try:
            text, in_tok, out_tok = self._generate(client, prompt, cfg)
        except ProviderError:
            raise
        except Exception as exc:  # noqa: BLE001 - normalize SDK errors to our taxonomy
            raise self._classify_error(exc) from exc
        latency = time.perf_counter() - start

        cost = estimate_cost(self.model, in_tok, out_tok)
        warnings: list[str] = []
        if cost is None:
            warnings.append("estimated cost unavailable (model not in pricing registry)")

        return SummaryResult(
            text=text,
            model=self.name,
            generation_config=cfg,
            input_tokens=in_tok,
            output_tokens=out_tok,
            latency_s=latency,
            provenance={
                "provider": self.provider_name,
                "question": question,
                "estimated_cost_usd": cost,
            },
            warnings=warnings,
        )

    def _classify_error(self, exc: Exception) -> ProviderError:
        status = getattr(exc, "status_code", None)
        if status is None:
            status = getattr(getattr(exc, "response", None), "status_code", None)
        name = type(exc).__name__.lower()
        msg = f"{self.provider_name} request failed: {exc}"
        if status in (401, 403) or "authentication" in name or "permission" in name:
            return ProviderAuthError(msg)
        if status == 429 or "ratelimit" in name or "rate_limit" in name:
            return ProviderRateLimitError(msg)
        return ProviderResponseError(msg)

    @abstractmethod
    def _make_client(self, api_key: str) -> Any: ...

    @abstractmethod
    def _generate(
        self, client: Any, prompt: str, cfg: GenConfig
    ) -> tuple[str, int | None, int | None]:
        """Return (text, input_tokens, output_tokens). Tokens may be None if unavailable."""
