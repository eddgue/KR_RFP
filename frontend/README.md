# frontend/ — the web console (stub, built last)

React + Next.js (App Router) + TypeScript, a **pure client** of the FastAPI backend (ADR-0002).
The enterprise console is **built last** — implementation begins at **Phase F**, once the store and
the outward-facing half are proven (ADR-0001). This directory currently ships only enough to:

1. **Hold the API seam** — `app/page.tsx` fetches the backend `/health` endpoint so the
   store ↔ view boundary is real and exercised from day one.
2. **Reserve the generated-types pipeline** — `lib/api/` is where the typed client generated from
   the backend's OpenAPI contract will land (Phase F). `gen:api` is a placeholder script today.

## This is a placeholder client

No design system, no auth/RBAC surface, no real routes this phase. Design and the design system start
early (RACI) but the implementation is Phase F. Everything here is intentionally minimal.

## Scripts

| Script | Does |
|---|---|
| `npm run dev` | `next dev` — local dev server |
| `npm run build` | `next build` (full build wired in CI at Phase F) |
| `npm run typecheck` | `tsc --noEmit` — the check CI runs in the `frontend-build` job this phase |
| `npm run gen:api` | placeholder — at Phase F, generate the typed client from the backend OpenAPI contract into `lib/api/` |

## Local run

```bash
cd frontend
cp .env.example .env.local       # NEXT_PUBLIC_API_BASE_URL (defaults to http://localhost:8000)
npm install
npm run dev                      # http://localhost:3000 ; the landing page probes the backend /health
```

Bring the backend up first (`docker compose up` in `infra/`), or the health panel shows "unreachable".

## How types are generated (Phase F)

The backend is contract-first (`/api/v1`, OpenAPI). At Phase F, `gen:api` runs the OpenAPI generator
(e.g. `openapi-typescript`) against the backend's published schema and writes the typed client into
`lib/api/`. CI's `frontend-build` job then asserts the types regenerate clean from the contract, so
the frontend can never drift from the API. Until then, `lib/api/` holds only `.gitkeep`.

## CI

The `frontend-build` job (`.github/workflows/ci.yml`) is **path-filtered** to `frontend/**` and runs
`npm install` + `npm run typecheck` only. It expands to `next build` + the generated-client check at
Phase F (DevOps `PLAN.md` §3 job 6).
