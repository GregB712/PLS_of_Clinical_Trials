"""Provider tests — fully mocked: no SDKs installed, no API keys, no network, no cost."""

from types import SimpleNamespace

import pytest

from pls_ct.models.base import GenConfig, SummarizerBackend
from pls_ct.providers import (
    ProviderAuthError,
    ProviderConfigError,
    ProviderRateLimitError,
    ProviderResponseError,
    make_provider,
    mask_key,
)

CFG = GenConfig(max_new_tokens=64, temperature=0.2)


# --- key safety -----------------------------------------------------------
def test_mask_key_never_reveals_full_key():
    assert mask_key("sk-ant-1234567890abcdef") == "sk-a…cdef"
    assert mask_key("short") == "*****"
    assert mask_key(None) == "<none>"
    assert mask_key("") == "<none>"


def test_unknown_provider_raises_config_error():
    with pytest.raises(ProviderConfigError, match="unknown provider"):
        make_provider("bedrock")


def test_missing_key_raises_config_error_without_network(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    provider = make_provider("anthropic")
    assert provider.has_key() is False
    with pytest.raises(ProviderConfigError, match="ANTHROPIC_API_KEY"):
        provider.validate()


def test_explicit_key_overrides_env_and_is_masked(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    provider = make_provider("openai", api_key="sk-explicit-abcdefgh")
    assert provider.has_key() is True
    provider.validate()  # no raise
    assert "explicit" not in provider.masked_key()


# --- successful generation via injected fake clients ----------------------
class _FakeAnthropic:
    class messages:  # noqa: N801 - mimic SDK attribute path client.messages.create
        @staticmethod
        def create(model, max_tokens, temperature, messages):
            assert "CONTEXT" in messages[0]["content"]  # prompt was built
            return SimpleNamespace(
                content=[SimpleNamespace(type="text", text="plain answer")],
                usage=SimpleNamespace(input_tokens=11, output_tokens=5),
            )


def test_anthropic_backend_returns_summary_with_usage():
    provider = make_provider("anthropic", "claude-sonnet-5-5", client=_FakeAnthropic())
    assert isinstance(provider, SummarizerBackend)
    res = provider.summarize("some context", "Why?", CFG)
    assert res.text == "plain answer"
    assert res.model == "anthropic:claude-sonnet-5-5"
    assert res.input_tokens == 11 and res.output_tokens == 5
    assert res.latency_s is not None
    # No pricing registered -> cost unknown, surfaced as a warning (never fabricated).
    assert res.provenance["estimated_cost_usd"] is None
    assert any("cost" in w for w in res.warnings)


class _FakeOpenAI:
    class chat:  # noqa: N801
        class completions:  # noqa: N801
            @staticmethod
            def create(model, messages, max_tokens, temperature, top_p):
                return SimpleNamespace(
                    choices=[SimpleNamespace(message=SimpleNamespace(content="oa answer"))],
                    usage=SimpleNamespace(prompt_tokens=7, completion_tokens=3),
                )


def test_openai_backend_returns_summary():
    provider = make_provider("openai", client=_FakeOpenAI())
    res = provider.summarize("ctx", "Who?", CFG)
    assert res.text == "oa answer"
    assert res.input_tokens == 7 and res.output_tokens == 3


class _FakeGemini:
    class models:  # noqa: N801
        @staticmethod
        def generate_content(model, contents, config):
            return SimpleNamespace(
                text="gem answer",
                usage_metadata=SimpleNamespace(prompt_token_count=9, candidates_token_count=4),
            )


def test_gemini_backend_returns_summary():
    provider = make_provider("gemini", client=_FakeGemini())
    res = provider.summarize("ctx", "What?", CFG)
    assert res.text == "gem answer"
    assert res.input_tokens == 9 and res.output_tokens == 4


# --- error normalization --------------------------------------------------
class _RaisingClient:
    def __init__(self, exc):
        self._exc = exc

    class messages:  # placeholder; replaced per-instance below
        pass


def _anthropic_raising(exc):
    client = _FakeAnthropic()

    def boom(**kwargs):
        raise exc

    client.messages = SimpleNamespace(create=boom)
    return make_provider("anthropic", client=client)


def test_auth_error_classified():
    exc = type("AuthenticationError", (Exception,), {})("bad key")
    with pytest.raises(ProviderAuthError):
        _anthropic_raising(exc).summarize("c", "q", CFG)


def test_rate_limit_classified_by_status_code():
    exc = Exception("too many")
    exc.status_code = 429
    with pytest.raises(ProviderRateLimitError):
        _anthropic_raising(exc).summarize("c", "q", CFG)


def test_other_errors_become_response_error():
    with pytest.raises(ProviderResponseError):
        _anthropic_raising(RuntimeError("network down")).summarize("c", "q", CFG)
