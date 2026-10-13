"""FastAPI application factory.

``create_app`` builds the app with a DB engine on ``app.state`` (overridable in tests).
The module-level ``app`` is what uvicorn serves: ``uvicorn pls_ct.app.main:app``.
"""

from __future__ import annotations

import os

from fastapi import FastAPI
from sqlalchemy import Engine
from starlette.middleware.cors import CORSMiddleware

from pls_ct import __version__
from pls_ct.app.errors import register_error_handlers
from pls_ct.app.routers import core, experiments, inference, jobs, trials
from pls_ct.db.engine import get_engine

_DEFAULT_ORIGINS = "http://localhost:5173,http://127.0.0.1:5173"


def _cors_origins() -> list[str]:
    raw = os.environ.get("PLS_CORS_ORIGINS", _DEFAULT_ORIGINS)
    return [o.strip() for o in raw.split(",") if o.strip()]


def create_app(engine: Engine | None = None) -> FastAPI:
    app = FastAPI(
        title="PLS of Clinical Trials API",
        version=__version__,
        description="Plain-language summarization of clinical trials — research platform API.",
    )
    app.state.engine = engine or get_engine()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins(),
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_error_handlers(app)
    for module in (core, trials, inference, experiments, jobs):
        app.include_router(module.router, prefix="/api")
    return app


app = create_app()
