"""OpenAI GPT provider (Chat Completions API)."""

from __future__ import annotations

from typing import Any

from pls_ct.models.base import GenConfig
from pls_ct.providers.base import BaseProvider


class OpenAIProvider(BaseProvider):
    provider_name = "openai"
    api_key_env = "OPENAI_API_KEY"

    def _make_client(self, api_key: str) -> Any:
        from openai import OpenAI  # lazy: SDK is an optional extra

        return OpenAI(api_key=api_key)

    def _generate(
        self, client: Any, prompt: str, cfg: GenConfig
    ) -> tuple[str, int | None, int | None]:
        resp = client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=cfg.max_new_tokens,
            temperature=cfg.temperature,
            top_p=cfg.top_p,
        )
        text = (resp.choices[0].message.content or "").strip()
        usage = getattr(resp, "usage", None)
        in_tok = getattr(usage, "prompt_tokens", None) if usage else None
        out_tok = getattr(usage, "completion_tokens", None) if usage else None
        return text, in_tok, out_tok
