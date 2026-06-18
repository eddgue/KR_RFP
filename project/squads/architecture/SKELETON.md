---
doc: Phase 0/A Repository Skeleton Spec
id: ARCH-002
version: 0.1
status: Draft (Phase 0)
created: 2026-06-18
owner: Solution Architect (`architect` agent)
depends_on: ARCH-001 (PLAN.md), ADR-0001, ADR-0003
---

# Repository Skeleton — Phase 0/A Scaffold

The exact monorepo layout and the starter files for the Phase 0/A scaffold (ADR-0003: plan-then-scaffold, backend-first). Precise enough to create verbatim. This realizes the architecture in `PLAN.md` and obeys the clean-room boundary (ADR-0001): `backend/` never imports `reference/`; the as-built schema is re-expressed under `db/baseline/`, never imported as code.

Conventions: Python 3.12, FastAPI, SQLAlchemy 2.x, Alembic, PostgreSQL 15+. Eight logical layers (`ref norm cyc bid eng awd perf audit`) are real PG schemas and 1:1 domain packages. The engine is a pure library behind a stable interface, stubbed until the D2 spike resolves. No full file bodies appear here — this is paths + purpose + must-have starter files.

---

## 0. Top-level layout

```
KR_RFP/
├── backend/            # the FastAPI/SQLAlchemy/Alembic system of record (the only writer)
├── frontend/           # Next.js/TypeScript web app — minimal stub now, built last (ADR-0002)
├── db/                 # database artifacts not owned by the app runtime
│   └── baseline/       # the re-expressed-clean as-built schema = migration baseline (ADR-0001)
├── infra/              # local + deploy infrastructure (docker-compose, env templates)
├── reference/          # QUARANTINE — input-only; never imported by backend/ (ADR-0001)
├── docs/               # already present: docs/adr/ (ADR-0001..0003 ratified)
├── project/            # already present: charter, RACI, roadmap, squads/
├── audit/ specs/       # already present: the audit + the two spec packages
├── .github/workflows/  # CI
├── .gitignore
├── .editorconfig
└── README.md           # already present
```

| Top-level dir | One-line purpose | Must-have starter files |
|---|---|---|
| `backend/` | The governed store + API + domain services + engine library | `pyproject.toml`, `Dockerfile`, `app/`, `alembic/`, `tests/`, `README.md` |
| `frontend/` | The enterprise web app; a pure API client, built last | `package.json`, `app/page.tsx`, `README.md` (stub only this phase) |
| `db/baseline/` | The as-built schema re-expressed as clean PostgreSQL = the Alembic baseline | `schema.sql`, `NAMING_MAP.md`, `README.md` |
| `infra/` | Local dev + deploy infra | `docker-compose.yml`, `.env.example`, `postgres/init/` |
| `reference/` | Isolated read-only quarantine for as-built extracts + sample files | `README.md`, `.gitkeep` (subdirs created on intake) |
| `.github/workflows/` | CI: lint, types, tests, migration round-trip, clean-room import check | `ci.yml` |

---

## 1. `backend/` — the system of record

Purpose: the only writer to the store. Hosts domain services (one package per layer), the engine library (pure), the four core cross-cutting concerns, the API, and Alembic. **Services `add`+`flush`, never `commit`** (PLAN §7).

```
backend/
├── pyproject.toml          # deps + tool config (ruff, mypy, pytest); package name; py3.12
├── Dockerfile              # python:3.12-slim build of the API/worker image
├── README.md               # how to run, migrate, test locally
├── alembic.ini             # Alembic config pointing at app config for the URL
├── .env.example            # backend env contract (DB URL, tenant defaults, engine impl flag)
├── app/
│   ├── __init__.py
│   ├── main.py             # FastAPI app factory: mounts routers, middleware, exception handlers
│   ├── core/               # cross-cutting concerns (PLAN §4)
│   │   ├── config/
│   │   │   ├── __init__.py
│   │   │   └── settings.py     # typed pydantic-settings; DB URL, env, ENGINE_IMPL, tenant defaults
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── base.py         # SQLAlchemy DeclarativeBase + naming convention (schema-qualified)
│   │   │   ├── session.py      # engine + sessionmaker; request-scoped unit-of-work; owns commit
│   │   │   └── types.py        # shared column types (UUID pk, Numeric(18,6) money, etc.)
│   │   ├── security/
│   │   │   ├── __init__.py
│   │   │   ├── principal.py    # verified principal (subject, tenant_id, roles) from the edge
│   │   │   ├── tenant.py       # request-scoped tenant context; never from request body
│   │   │   ├── rbac.py         # role/permission model + route-guard dependencies
│   │   │   └── deps.py         # FastAPI dependencies: get_principal, require_permission, get_tenant
│   │   ├── audit/
│   │   │   ├── __init__.py
│   │   │   ├── events.py       # domain-event types emitted by services
│   │   │   ├── writer.py       # single subscriber → hash-chained event_log row, same txn
│   │   │   └── guards.py       # immutability guard listeners (sealed runs, frozen awards)
│   │   └── errors/
│   │       ├── __init__.py
│   │       ├── taxonomy.py     # machine codes + problem-shaped error envelope (PLAN §5, ADR-0007)
│   │       └── handlers.py     # FastAPI exception handlers → uniform envelope
│   ├── domain/             # one package per logical layer = per PG schema (PLAN §2)
│   │   ├── __init__.py
│   │   ├── ref/            # client/tenant, commodity, dc, supplier, item, aliases, zip_centroid, quarantine
│   │   │   ├── __init__.py
│   │   │   ├── models.py       # SQLAlchemy mapped classes (schema="ref")
│   │   │   ├── schemas.py      # pydantic request/response models
│   │   │   ├── repository.py   # tenant-scoped queries
│   │   │   └── service.py      # add+flush services (incl. tenancy upsert, alias resolve)
│   │   ├── norm/          # lot, attribute_def, lot_attribute, item_lot_map (sticky)
│   │   │   └── (models, schemas, repository, service).py
│   │   ├── cyc/           # cycle keystone + satellites (objective, pricing+safety, terms, rail, narrative)
│   │   │   └── (models, schemas, repository, service).py
│   │   ├── bid/          # bid_submission, bid, bid_price, eligibility, capacity, landed_cost
│   │   │   └── (models, schemas, repository, service).py
│   │   ├── eng/          # analysis_run, bid_score, scenario, scenario_award (split) + runner
│   │   │   ├── (models, schemas, repository).py
│   │   │   └── runner.py       # seals run, freezes inputs, hashes manifests, calls engine library
│   │   ├── awd/          # award, award_layer, signoff, generated_document (mostly net-new)
│   │   │   └── (models, schemas, repository, service).py
│   │   ├── perf/         # itrade_receipt, kcms_movement, supplier_scorecard, commercial pricing, VSP
│   │   │   └── (models, schemas, repository, service).py
│   │   └── audit/        # event_log, decision_note (read models; writes via core/audit)
│   │       └── (models, schemas, repository).py
│   ├── engine/            # the pure decision-support library — NO db/http/clock (PLAN §3)
│   │   ├── __init__.py
│   │   ├── interface.py       # frozen run(inputs)->result contract + dataclass/pydantic IO types
│   │   ├── stub.py            # deterministic stub impl behind the interface (until D2 resolves)
│   │   └── README.md          # the D2-independent boundary; links SPIKE_D2_engine.md
│   └── api/               # the HTTP surface (contract-first, /api/v1) (PLAN §5)
│       ├── __init__.py
│       ├── router.py         # mounts versioned sub-routers
│       ├── deps.py           # shared route dependencies (db session, principal, tenant)
│       └── v1/
│           ├── __init__.py
│           ├── health.py     # /health, /ready (liveness/readiness)
│           ├── cycles.py     # /cycles, timeframes, rounds, full cycle view ("open last cycle")
│           ├── bids.py       # bid import + list at one grain
│           ├── runs.py       # POST run -> run_id; GET scenarios/scores
│           ├── awards.py     # select (promote), signoff, approve (freeze)
│           ├── documents.py  # generate booking guide / deck / letters
│           └── ingest.py     # itrade/import, kcms/import, normalize/propose+confirm
├── alembic/
│   ├── env.py               # wires Alembic to app metadata + config DB URL; schema-aware
│   ├── script.py.mako
│   └── versions/
│       └── 0001_baseline.py # apply db/baseline/schema.sql (the re-expressed as-built) as rev 0001
└── tests/
    ├── conftest.py          # real-Postgres fixtures (testcontainers/compose); tenant fixtures
    ├── test_health.py       # smoke: app boots, /health green
    ├── test_migrations_roundtrip.py  # up→down→up clean (kills SQLite-ism risk R8)
    ├── test_cleanroom_import.py      # asserts backend/ never imports reference/ (ADR-0001)
    ├── test_tenant_isolation.py      # cross-tenant read returns nothing (S7)
    └── engine/
        └── test_engine_stub.py       # engine library is pure + deterministic via interface
```

Must-have starter files (the minimum that makes Phase 0/A real): `pyproject.toml`, `Dockerfile`, `app/main.py`, `app/core/config/settings.py`, `app/core/db/{base,session}.py`, `app/core/security/{principal,tenant,rbac,deps}.py`, `app/core/audit/{events,writer,guards}.py`, `app/core/errors/{taxonomy,handlers}.py`, `app/engine/{interface,stub}.py`, `app/api/v1/health.py`, `alembic/env.py` + `versions/0001_baseline.py`, and the five `tests/` guards above. Domain packages start with `ref` (tenancy + reference) wired end-to-end; the other seven ship as empty-but-present packages with `models.py` stubs so the layer map is visible from day one.

---

## 2. `frontend/` — the web app (stub only this phase)

Purpose: the enterprise web app (React/Next.js App Router + TypeScript, ADR-0002), a pure client of the API, **built last** (Phase F). This phase ships only enough to hold the seam and the generated-types pipeline.

```
frontend/
├── package.json            # Next.js + TypeScript; scripts incl. openapi type generation
├── tsconfig.json
├── next.config.mjs
├── .env.example            # API base URL
├── README.md               # "built last; this is a placeholder client" + how types are generated
├── app/
│   ├── layout.tsx
│   └── page.tsx            # landing stub that calls /health to prove the API seam
└── lib/
    └── api/
        └── .gitkeep        # generated OpenAPI client/types land here (Phase F)
```

Must-have: `package.json`, `tsconfig.json`, `next.config.mjs`, `app/page.tsx`, `README.md`. No design system, no real routes this phase — the design starts early (RACI) but implementation is Phase F.

---

## 3. `db/baseline/` — the migration baseline

Purpose: the as-built 63-table schema **re-expressed as clean PostgreSQL** — our own artifact, not an import (ADR-0001). It is what Alembic rev `0001` applies; SQLite-isms and the no-op CHECK removed; flat names canonicalized to schema-qualified names.

```
db/baseline/
├── schema.sql              # clean PG DDL: 8 schemas + the re-expressed as-built tables (KEEP set)
├── NAMING_MAP.md           # as-built-flat -> target schema-qualified mapping (rfp_cycle->cyc.cycle, scenario_a_*->eng.*) (ADR-0008)
└── README.md               # provenance: derived from specs/original-engine/BUILD_03_schema.sql + reference/as-built-db/, NOT imported as code
```

Must-have: `schema.sql`, `NAMING_MAP.md`, `README.md`. (The full reconciled DDL is the Platform & Data squad's first deliverable; this phase lands the directory, the provenance note, and the naming map so the baseline has a home.)

---

## 4. `infra/` — local + deploy infrastructure

Purpose: stand up Postgres + the backend locally; hold env templates and DB init. IaC/cloud is DevOps' later deliverable; this phase ships local dev.

```
infra/
├── docker-compose.yml      # services: db (postgres:15), backend (build ../backend); volumes; healthchecks
├── .env.example            # compose-level env (POSTGRES_*, backend DATABASE_URL)
├── postgres/
│   └── init/
│       └── 01_schemas.sql  # CREATE SCHEMA ref/norm/cyc/bid/eng/awd/perf/audit; create app role
└── README.md               # local up/down, how compose maps to backend/.env
```

Must-have: `docker-compose.yml`, `.env.example`, `postgres/init/01_schemas.sql`, `README.md`. `docker-compose.yml` must bring up a healthy Postgres and a backend that runs `alembic upgrade head` then serves `/health`.

---

## 5. `reference/` — the quarantine (input-only)

Purpose: isolated, read-only landing zone for (a) the as-built extract a dedicated worktree agent emits and (b) sponsor-uploaded sample files. **`backend/` must never import from here**; CI enforces it (ADR-0001).

```
reference/
├── README.md               # the boundary rule: INPUT ONLY; never imported; classification rule for samples
├── as-built-db/            # (on DEP-1 intake) extracted/validated schema + Alembic chain summary
│   └── .gitkeep
├── as-built-digest.md      # (on DEP-1 intake) knowledge digest: services, tests, ECLS content
└── samples/                # (on demand) real artifacts w/ provenance; classified before commit (Security owns)
    └── .gitkeep
```

Must-have now: `README.md` stating the boundary + the classification rule, and the `.gitkeep`'d subdirs. Contents arrive only on DEP-1 / sample-file intake; nothing here is wired into the build.

---

## 6. `.github/workflows/ci.yml` — CI

Purpose: enforce the standards from `PLAN.md §7` on every push/PR. One workflow, jobs run against a real Postgres service.

Must-have jobs in `ci.yml`:
1. **lint** — `ruff` (format + lint) on `backend/`.
2. **types** — `mypy` on `backend/`.
3. **clean-room guard** — runs `tests/test_cleanroom_import.py`: fail if `backend/` imports `reference/` (ADR-0001).
4. **migrations** — spin Postgres 15 service, `alembic upgrade head`, then `test_migrations_roundtrip.py` (up→down→up).
5. **tests** — `pytest` (unit engine tests + service/integration tests + tenant-isolation test) against the Postgres service.
6. **frontend** (light) — `package.json` installs and type-checks (placeholder; expands at Phase F).

Gate: PRs merge only on green. The clean-room guard and migration round-trip are non-negotiable from day one.

---

## 7. Root housekeeping files

| File | Purpose |
|---|---|
| `.gitignore` | Python/Node/OS ignores; `**/.env` (never commit real env); `reference/samples/*` unless classified |
| `.editorconfig` | consistent whitespace/encoding across Python + TypeScript |
| `README.md` | already present — update with "scaffold layout" pointer to this doc |

---

## 8. Build order for the scaffold (within Phase 0/A)

1. Root + `infra/docker-compose.yml` + `postgres/init/01_schemas.sql` → a healthy Postgres with eight empty schemas.
2. `db/baseline/` provenance + `NAMING_MAP.md` (DDL fills in as the Platform & Data deliverable lands).
3. `backend/` skeleton: `pyproject.toml`, `app/core/*`, `app/main.py`, `alembic/` with `0001_baseline`, `app/api/v1/health.py`.
4. `app/domain/ref/` wired end-to-end (tenancy + one reference entity) as the reference implementation pattern; other seven domain packages present as stubs.
5. `app/engine/{interface,stub}.py` — the frozen interface + deterministic stub (D2-independent).
6. `tests/` guards (health, migration round-trip, clean-room import, tenant isolation, engine stub).
7. `.github/workflows/ci.yml` green.
8. `frontend/` stub + `reference/README.md` boundary note.

**Exit (matches roadmap Phase A entry):** `docker-compose up` yields a healthy Postgres with eight schemas; `alembic upgrade head` applies the baseline clean; `/health` is green; CI passes including the clean-room and migration-round-trip guards; the engine interface is fixed with a stub behind it.

---

## Changelog

| Version | Date | Author | Change Summary |
|---------|------|--------|----------------|
| 0.1 | 2026-06-18 | Architect | Initial Phase 0/A skeleton spec: full monorepo layout, per-dir purpose + must-have starter files, scaffold build order and exit gate. |
