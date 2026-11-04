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

## Public read-only demo on Vercel

`vercel.json` deploys the app as one Vercel project with two services:

- **web** (`frontend/`): the Vite build, served statically, with a fallback to `index.html`
  so links such as `/paper` work.
- **api** (`deploy/vercel/`): the FastAPI app as a Python function. Its `pyproject.toml`
  installs this repository's package with the `api` and `providers` extras.

The demo is **read-only**. At build time, `deploy/vercel/build_demo_db.py` creates
`deploy/vercel/demo.db` from the committed synthetic sample only (trials, RAG index, a Lead-k
benchmark). `deploy/vercel/main.py` opens it read-only and sets `PLS_READ_ONLY=1`, so PDF uploads
and trial deletion return 403, and the Demo page hides the upload box.

What works: the lead baselines, the research assistant, the dataset explorer, model
comparison and the Paper page. Hosted providers work when the visitor pastes their own API key
in the Demo page; it is sent with that request only. What does not: the local transformer
backends (`torch`/`transformers` exceed the function size limit), and uploads.

**Do not set provider API keys on the Vercel project.** The demo has no authentication or rate
limiting, so a server-side key could be used by anyone.

Check the build locally (requires the Vercel CLI and `uv`):

```bash
vercel build          # after `vercel link` / `vercel pull`
```

## Configuration

| Variable | Purpose | Default |
|---|---|---|
| `PLS_DATABASE_URL` | SQLAlchemy URL | SQLite under the processed dir |
| `PLS_PROCESSED_DIR` | writable data dir (SQLite, uploads) | `data/processed` (`/data` in Docker) |
| `PLS_SEED_SAMPLE` | seed synthetic data on container start | `1` in Compose |
| `PLS_CORS_ORIGINS` | comma-separated allowed origins | `localhost:5173` |
| `PLS_READ_ONLY` | refuse uploads and deletions (public demo) | unset |
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
