# backend — Kroger Produce RFP / Sourcing system of record

The only writer to the governed store. FastAPI + SQLAlchemy 2.x + Alembic, Python 3.12.
Realizes `project/squads/architecture/PLAN.md`; scaffold spec in `architecture/SKELETON.md`.

## Layout

- `app/core/` — cross-cutting concerns: config, db/session (owns commit), security
  (tenant context + RBAC), audit (hash-chained event writer + immutability guards), errors.
- `app/domain/<layer>/` — one package per PG schema: `ref norm cyc bid eng awd perf audit`.
  `ref` is wired end-to-end (tenancy + reference) as the reference pattern; the other seven
  are present-but-empty stubs.
- `app/engine/` — the pure decision-support library behind a frozen `Engine.run(inputs)`
  interface, with a deterministic stub (D2 in spike). No db/http/clock.
- `app/api/` — `/api/v1` HTTP surface (health is live; the rest are present-but-empty routers).
- `alembic/` — migrations. `0001_baseline` creates the eight schemas and applies
  `db/baseline/schema.sql` if present, else a minimal `ref` seed.

## Run locally

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env            # then edit DATABASE_URL
```

Serve the API (requires a reachable Postgres):

```bash
alembic upgrade head            # migrate
uvicorn app.main:app --reload   # http://localhost:8000  ->  /api/v1/health
```

Or via Docker (migrates then serves): `docker build -t kr-rfp-backend . && docker run -p 8000:8000 kr-rfp-backend`.

## Migrate

```bash
alembic upgrade head            # apply
alembic downgrade base          # revert (round-trip tested in CI)
alembic revision -m "message"   # new migration
```

## Test

```bash
pytest -m "not integration"     # PURE tests only — no DB needed (clean-room + engine stub)
pytest                          # full suite — requires a Postgres (see tests/conftest.py)
ruff check . && ruff format --check . && mypy app
```

The two PURE guards (`tests/test_cleanroom_import.py`, `tests/engine/test_engine_stub.py`)
pass with just `pip install` — no database.

## Invariants (do not regress)

- Services `add` + `flush`, **never** `commit`. The request-scoped unit of work owns the commit.
- Tenant context comes from the verified token only, never from a request body.
- `backend/` must never import from `reference/` (ADR-0001, CI-enforced).
- Governed rows are append-only; corrections insert superseding rows.
