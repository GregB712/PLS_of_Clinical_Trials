"""Exception handlers mapping domain errors to clean HTTP responses (no stack traces)."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from pls_ct.providers import (
    ProviderAuthError,
    ProviderConfigError,
    ProviderError,
    ProviderRateLimitError,
)


def _json(status: int, error: str, detail: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": error, "detail": detail})


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ProviderConfigError)
    async def _config(_: Request, exc: ProviderConfigError):
        return _json(400, "provider_config", str(exc))

    @app.exception_handler(ProviderAuthError)
    async def _auth(_: Request, exc: ProviderAuthError):
        return _json(401, "provider_auth", str(exc))

    @app.exception_handler(ProviderRateLimitError)
    async def _rate(_: Request, exc: ProviderRateLimitError):
        return _json(429, "provider_rate_limit", str(exc))

    @app.exception_handler(ProviderError)
    async def _provider(_: Request, exc: ProviderError):
        return _json(502, "provider_error", str(exc))

    @app.exception_handler(ValueError)
    async def _value(_: Request, exc: ValueError):
        return _json(400, "bad_request", str(exc))
