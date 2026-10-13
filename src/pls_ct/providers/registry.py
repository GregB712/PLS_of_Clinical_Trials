"""Provider registry + factory. Add a provider by registering one class here."""

from __future__ import annotations

from typing import Any

from pls_ct.providers.anthropic import AnthropicProvider
from pls_ct.providers.base import BaseProvider, ProviderConfigError
from pls_ct.providers.gemini import GeminiProvider
from pls_ct.providers.openai import OpenAIProvider

PROVIDERS: dict[str, type[BaseProvider]] = {
    "anthropic": AnthropicProvider,
    "openai": OpenAIProvider,
    "gemini": GeminiProvider,
}

# Convenience defaults (updateable; not a claim of "best"). Explicit models override these.
DEFAULT_MODELS: dict[str, str] = {
    "anthropic": "claude-sonnet-5-5",
    "openai": "gpt-4o-mini",
    "gemini": "gemini-2.5-flash",
}


def make_provider(
    name: str,
    model: str | None = None,
    *,
    api_key: str | None = None,
    client: Any = None,
) -> BaseProvider:
    cls = PROVIDERS.get(name)
    if cls is None:
        raise ProviderConfigError(
            f"unknown provider {name!r}; known: {sorted(PROVIDERS)}"
        )
    return cls(model=model or DEFAULT_MODELS[name], api_key=api_key, client=client)
