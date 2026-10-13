# Deployment

## Local, one command (Docker Compose)

```bash
docker compose up --build
```

- **Web UI**: http://localhost:8080
- **API + docs**: http://localhost:8000/docs

The `api` service runs migrations on start and (by default) seeds the **synthetic** sample
plus a RAG index, so the UI has data immediately. The database is SQLite in the named
volume `pls-data` and persists across restarts. Set `PLS_SEED_SAMPLE=0` for an empty DB.

The frontend is built and served by nginx, which proxies `/api` to the backend — so the
browser talks to a single origin and no CORS configuration is needed.

```bash
docker compose down          # stop
docker compose down -v       # stop and wipe the data volume
```

> **Note:** the Docker images are defined and syntax-checked but were not built in the
> development environment (no Docker available there). Build locally before relying on them.

## Without Docker (dev)

```bash
make install     # backend (dev+api) + frontend deps
make seed        # migrate + load the synthetic sample + build the RAG index
make api         # terminal 1: uvicorn on :8000
make web         # terminal 2: vite on :5173 (proxies /api -> :8000)
```

## Configuration

| Variable | Purpose | Default |
|---|---|---|
| `PLS_DATABASE_URL` | SQLAlchemy URL | SQLite under the processed dir |
| `PLS_PROCESSED_DIR` | writable data dir (SQLite, uploads) | `data/processed` (`/data` in Docker) |
| `PLS_SEED_SAMPLE` | seed synthetic data on container start | `1` in Compose |
| `PLS_CORS_ORIGINS` | comma-separated allowed origins | `localhost:5173` |
| `PLS_DEVICE` | `auto`\|`cpu`\|`cuda`\|`mps` | `auto` |
| `ANTHROPIC_/OPENAI_/GOOGLE_API_KEY` | hosted-provider keys (optional) | unset |

Copy `.env.example` → `.env` for local overrides (gitignored; placeholders only).

## Scaling to PostgreSQL (+ pgvector)

The default SQLite backend is fine for a single-node demo. For scale:

1. Run a Postgres service and add `psycopg[binary]` to the backend image.
2. Set `PLS_DATABASE_URL=postgresql+psycopg://user:pass@db:5432/pls`.
3. `alembic upgrade head` creates the schema. Vector search currently ranks in Python
   (research-scale); move embeddings to **pgvector** when the corpus grows (the `chunks`
   schema already stores vectors + embedder metadata for a mechanical migration).

## Before a public deployment

See [`SECURITY.md`](SECURITY.md) — most importantly, add authentication/authorization
(the app ships without auth for a local single-user demo) and review data provenance and
retention for any real uploaded documents.
