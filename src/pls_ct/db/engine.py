"""Engine/session helpers. Default backend is SQLite at ``<processed_dir>/pls.db``."""

from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from pls_ct.config import Config
from pls_ct.db.models import Base


def database_url(override: str | None = None) -> str:
    if override:
        return override
    env = os.environ.get("PLS_DATABASE_URL")
    if env:
        return env
    cfg = Config.from_env()
    cfg.processed_dir.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{cfg.processed_dir / 'pls.db'}"


def get_engine(url: str | None = None) -> Engine:
    return create_engine(database_url(url), future=True)


def create_all(engine: Engine) -> None:
    """Create tables directly (dev/test convenience; production uses Alembic migrations)."""
    Base.metadata.create_all(engine)


@contextmanager
def session_scope(engine: Engine | None = None) -> Iterator[Session]:
    engine = engine or get_engine()
    factory = sessionmaker(bind=engine, future=True, expire_on_commit=False)
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
