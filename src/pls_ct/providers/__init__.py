"""Hosted-LLM provider abstraction (Anthropic, OpenAI, Gemini).

All providers implement the same :class:`~pls_ct.models.base.SummarizerBackend` interface,
so the summarization pipeline and web API treat them like any local backend. Keys come
from the environment or are passed explicitly (for user-supplied keys); they are never
hardcoded and never logged (only masked). Adding a provider = one subclass + a registry entry.
"""

from pls_ct.providers.base import (
    ProviderAuthError,
    ProviderConfigError,
    ProviderError,
    ProviderRateLimitError,
    ProviderResponseError,
    mask_key,
)
from pls_ct.providers.registry import DEFAULT_MODELS, PROVIDERS, make_provider

__all__ = [
    "ProviderError",
    "ProviderConfigError",
    "ProviderAuthError",
    "ProviderRateLimitError",
    "ProviderResponseError",
    "mask_key",
    "make_provider",
    "PROVIDERS",
    "DEFAULT_MODELS",
]
