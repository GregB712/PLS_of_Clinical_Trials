# Frontend — PLS of Clinical Trials

Vite + React + TypeScript + Tailwind SPA for the platform. It consumes the FastAPI
backend (`src/pls_ct/app`) over the typed client in `src/lib/api.ts`.

## Develop

```bash
npm install
npm run dev          # http://localhost:5173  (proxies /api -> http://127.0.0.1:8000)
```

Run the backend alongside it:

```bash
# from the repo root, in the Python venv
uvicorn pls_ct.app.main:app --reload
```

Point the SPA at a different API with `VITE_API_TARGET` (dev proxy) or `VITE_API_BASE`
(build-time base URL, default `/api`).

## Scripts

| command | what it does |
|---|---|
| `npm run build` | `tsc --noEmit` type-check, then production bundle in `dist/` |
| `npm run typecheck` | type-check only |
| `npm test` | Vitest (API client + page tests, mocked fetch) |

## Pages (first iteration)

- **Landing** — real dataset stats from `/api/stats`.
- **Live demo** — pick a trial, pick a backend, generate a summary with metadata.
- **Model comparison** — `/api/experiments` → table + Recharts bar chart.
- **Dataset explorer** / **Research assistant** — stubs; backend endpoints already exist
  (`/api/trials`, `/api/rag/ask`) and these are the next iteration.
