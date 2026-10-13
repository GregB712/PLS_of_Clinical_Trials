"""Central configuration — paths and settings from the environment with sane defaults.

Replaces the hardcoded paths scattered through the original thesis code
(``FinalDataset/...``, the ``.gguf`` path, etc.). Everything is overridable via
environment variables so the same code runs against the synthetic sample (default)
or the author's local Novartis corpus.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

# Repo root = two levels up from this file (src/pls_ct/config.py -> repo root).
REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = REPO_ROOT / "data"


def _env_path(var: str, default: Path) -> Path:
    raw = os.environ.get(var)
    return Path(raw).expanduser().resolve() if raw else default


@dataclass(frozen=True)
class Config:
    """Resolved runtime configuration. Construct with :meth:`from_env`."""

    # Where raw Novartis PDFs live (local-only, gitignored). Default is the synthetic
    # sample so a fresh clone works with zero real data.
    raw_dir: Path = DATA_ROOT / "sample"
    interim_dir: Path = DATA_ROOT / "interim"
    processed_dir: Path = DATA_ROOT / "processed"

    seed: int = 42

    # Device override: "auto" (default), "cpu", "cuda", "mps".
    device: str = "auto"

    # Default model identifiers (overridable).
    extractive_model: str = "distilbert-base-uncased"
    generative_model: str = "mistralai/Mistral-7B-Instruct-v0.1"

    @classmethod
    def from_env(cls) -> Config:
        """Build a config, applying ``PLS_*`` environment overrides."""
        return cls(
            raw_dir=_env_path("PLS_RAW_DIR", DATA_ROOT / "sample"),
            interim_dir=_env_path("PLS_INTERIM_DIR", DATA_ROOT / "interim"),
            processed_dir=_env_path("PLS_PROCESSED_DIR", DATA_ROOT / "processed"),
            seed=int(os.environ.get("PLS_SEED", "42")),
            device=os.environ.get("PLS_DEVICE", "auto"),
            extractive_model=os.environ.get("PLS_EXTRACTIVE_MODEL", "distilbert-base-uncased"),
            generative_model=os.environ.get(
                "PLS_GENERATIVE_MODEL", "mistralai/Mistral-7B-Instruct-v0.1"
            ),
        )

    def ensure_dirs(self) -> None:
        """Create the writable interim/processed dirs (never the read-only raw dir)."""
        self.interim_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
