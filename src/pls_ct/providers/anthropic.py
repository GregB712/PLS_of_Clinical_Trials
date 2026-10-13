"""Anthropic Claude provider (verified against the anthropic Python SDK)."""

from __future__ import annotations

from typing import Any

from pls_ct.models.base import GenConfig
from pls_ct.providers.base import BaseProvider


class AnthropicProvider(BaseProvider):
    provider_name = "anthropic"
    api_key_env = "ANTHROPIC_API_KEY"

    def _make_client(self, api_key: str) -> Any:
        from anthropic import Anthropic  # lazy: SDK is an optional extra

        return Anthropic(api_key=api_key)

    def _generate(
        self, client: Any, prompt: str, cfg: GenConfig
    ) -> tuple[str, int | None, int | None]:
        message = client.messages.create(
            model=self.model,
            max_tokens=cfg.max_new_tokens,
            temperature=cfg.temperature,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(
            block.text for block in message.content if getattr(block, "type", None) == "text"
        ).strip()
        usage = getattr(message, "usage", None)
        in_tok = getattr(usage, "input_tokens", None) if usage else None
        out_tok = getattr(usage, "output_tokens", None) if usage else None
        return text, in_tok, out_tok
