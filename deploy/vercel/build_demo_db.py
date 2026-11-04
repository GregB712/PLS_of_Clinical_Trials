"""Build the read-only demo database bundled with the Vercel deployment.

Creates deploy/vercel/demo.db from the committed synthetic sample only: schema via the
Alembic migrations, the six synthetic trials, the RAG index (hashing embedder), and a
Lead-k benchmark so the Model comparison page has data. No real trial data is involved.

Run:  python deploy/vercel/build_demo_db.py   (works from any directory)
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "deploy" / "vercel" / "demo.db"
SAMPLE = ROOT / "data" / "sample" / "trials.json"


def run(*args: str, env: dict[str, str]) -> None:
    print("+", " ".join(args), flush=True)
    subprocess.run([sys.executable, *args], cwd=ROOT, env=env, check=True)


def main() -> int:
    DB.unlink(missing_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        env = {
            **os.environ,
            "PYTHONPATH": str(ROOT / "src"),
            "PLS_DATABASE_URL": f"sqlite:///{DB}",
            "PLS_PROCESSED_DIR": tmp,
            "PLS_INTERIM_DIR": tmp,
        }
        examples = str(Path(tmp) / "examples.jsonl")
        cli = ("-m", "pls_ct.cli")
        run("-m", "alembic", "upgrade", "head", env=env)
        run(*cli, "db-load", "--records", str(SAMPLE), env=env)
        run(*cli, "index", "--records", str(SAMPLE), env=env)
        run(*cli, "build", "--db", str(SAMPLE), "--out", examples, env=env)
        run(
            *cli,
            "benchmark",
            "--examples",
            examples,
            "--backends",
            "lead-1,lead-2,lead-3",
            "--out-dir",
            str(Path(tmp) / "bench"),
            "--to-db",
            env=env,
        )
    print(f"wrote {DB.relative_to(ROOT)} ({DB.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
