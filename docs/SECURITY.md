# Security & privacy

This documents the posture of the platform and what must change before a public, multi-user
deployment. It is a research/portfolio project, **not** a clinically validated system.

## What's implemented

- **Secrets**: provider API keys come from the environment or per-request; never hardcoded,
  never logged, and masked in any output. `.env` is gitignored; `.env.example` holds
  placeholders only.
- **Uploads**: PDF-only validation, a 20 MB size cap enforced while streaming, and
  **server-generated filenames** (UUIDs) so a malicious filename can't cause path traversal.
  nginx also caps proxied bodies at 25 MB.
- **Error handling**: domain errors map to clean status codes; a catch-all handler returns a
  generic 500 with no stack trace or internals leaked to the client.
- **CORS**: closed by default to an allow-list (`PLS_CORS_ORIGINS`); in the Docker stack the
  SPA is same-origin via the nginx proxy, so cross-origin access isn't needed at all.
- **RAG safety**: retrieved passages are passed as labeled reference data with an injection
  guard, and the answer backends are plain text-in/text-out (no tools), so retrieved content
  cannot trigger actions.
- **Data**: the source Novartis PDFs are treated as non-redistributable and are gitignored;
  only a clearly-labeled synthetic sample is committed.

## What must change before public / multi-user deployment

- **Authentication & authorization** — the app ships with **no auth** (local single-user
  demo). Add user auth and per-user isolation of uploads, summaries, API keys, and RAG scope.
- **Secret storage** — move provider keys from env/local to a proper secrets manager; if
  users supply keys, store them per-user server-side, encrypted, never in the browser.
- **Rate limiting & quotas** on summarize/RAG/upload to bound cost and abuse.
- **Upload retention** — implement explicit retention/deletion for uploaded documents and
  derived artifacts; the delete endpoint exists for stored trials but an upload lifecycle
  policy should be defined.
- **Transport** — terminate TLS at the proxy/load balancer.
- **Dependency & container scanning** — add `pip-audit`/`npm audit` and image scanning to CI.

## Responsible use

Generated summaries are AI-generated research communication, not medical advice, and may
contain errors — always verify against the source document.
