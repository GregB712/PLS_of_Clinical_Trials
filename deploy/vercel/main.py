"""Vercel entrypoint for the FastAPI backend (read-only public demo).

Serves the database built at deploy time by build_demo_db.py (next to this file), opened
read-only. Vercel's filesystem is read-only apart from /tmp, so working directories point
there, and uploads/deletions are refused (PLS_READ_ONLY). Local transformer models are not
installed; the lead baselines and hosted providers (with a visitor-supplied key) work.
"""

import os
from pathlib import Path

# pls_ct itself is installed into the function from the repository root (see pyproject.toml).
DEMO_DB = Path(__file__).resolve().parent / "demo.db"
os.environ.setdefault("PLS_READ_ONLY", "1")
os.environ.setdefault("PLS_PROCESSED_DIR", "/tmp/pls")
os.environ.setdefault("PLS_INTERIM_DIR", "/tmp/pls/interim")
# immutable=1: no locking or journal files, which a read-only filesystem cannot hold.
os.environ.setdefault("PLS_DATABASE_URL", f"sqlite:///file:{DEMO_DB}?mode=ro&immutable=1&uri=true")

from pls_ct.app.main import app  # noqa: E402

__all__ = ["app"]
