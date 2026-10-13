#!/bin/sh
# Apply migrations, optionally seed the synthetic sample, then serve the API.
set -e

echo "[entrypoint] applying database migrations…"
alembic upgrade head

if [ "${PLS_SEED_SAMPLE:-0}" = "1" ]; then
  echo "[entrypoint] seeding synthetic sample (trials + RAG index)…"
  pls db-load --records data/sample/trials.json || echo "[entrypoint] db-load skipped/failed"
  pls index --records data/sample/trials.json || echo "[entrypoint] index skipped/failed"
fi

echo "[entrypoint] starting API on :8000"
exec uvicorn pls_ct.app.main:app --host 0.0.0.0 --port 8000
