"""Persistence: SQLAlchemy models, engine/session, and the data-access layer.

Default backend is SQLite (file-based, zero-infra, survives restarts). Set
``PLS_DATABASE_URL`` to a Postgres URL to switch backends without code changes.
All DB access goes through :mod:`pls_ct.db.repository` — no raw queries elsewhere.
"""
