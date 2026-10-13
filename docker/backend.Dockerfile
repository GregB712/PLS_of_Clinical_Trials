# FastAPI backend image. Build context = repo root.
FROM python:3.12-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PLS_PROCESSED_DIR=/data \
    PLS_DATABASE_URL=sqlite:////data/pls.db

# Install the package (API extra) first for better layer caching.
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install -e ".[api]"

# Runtime files: migrations, alembic config, and the synthetic sample.
COPY migrations ./migrations
COPY alembic.ini ./
COPY data/sample ./data/sample
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["/entrypoint.sh"]
