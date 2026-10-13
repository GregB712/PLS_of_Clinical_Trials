"""Google Gemini provider (google-genai SDK: `from google import genai`)."""

from __future__ import annotations

from typing import Any

from pls_ct.models.base import GenConfig
from pls_ct.providers.base import BaseProvider


class GeminiProvider(BaseProvider):
    provider_name = "gemini"
    api_key_env = "GOOGLE_API_KEY"

    def _make_client(self, api_key: str) -> Any:
        from google import genai  # lazy: SDK is an optional extra

        return genai.Client(api_key=api_key)

    def _generate(
        self, client: Any, prompt: str, cfg: GenConfig
    ) -> tuple[str, int | None, int | None]:
        resp = client.models.generate_content(
            model=self.model,
            contents=prompt,
            config={
                "temperature": cfg.temperature,
                "max_output_tokens": cfg.max_new_tokens,
                "top_p": cfg.top_p,
            },
        )
        text = (getattr(resp, "text", None) or "").strip()
        usage = getattr(resp, "usage_metadata", None)
        in_tok = getattr(usage, "prompt_token_count", None) if usage else None
        out_tok = getattr(usage, "candidates_token_count", None) if usage else None
        return text, in_tok, out_tok
