# infra/ — local dev + deploy infrastructure

Local stands up Postgres 15 + the backend with one command. Cloud/IaC (Terraform, managed
Postgres, secrets) is the DevOps squad's later deliverable, gated on **DEP-4** (cloud + IdP);
this phase ships **dev only** (DevOps `PLAN.md` §4).

## What's here

| File | Purpose |
|---|---|
| `docker-compose.yml` | `db` (postgres:15, healthcheck, volume), `backend` (migrate then serve), `adminer` (DB UI) |
| `.env.example` | compose-level env (`POSTGRES_*`, backend `DATABASE_URL`) — copy to `.env`, never commit |
| `postgres/init/01_schemas.sql` | idempotent bootstrap: the 8 schemas + a least-privilege app role |

## Quick start

```bash
cd infra
cp .env.example .env          # safe placeholders; edit if you like. .env is gitignored.
docker compose up -d          # starts db (waits healthy), then backend runs migrations + serves
docker compose ps             # db should be "healthy"; backend "running"
```

- API:     http://localhost:8000  (`GET /health` should be green once migrations are at head)
- Adminer: http://localhost:8080  (System: PostgreSQL, Server: `db`, the `POSTGRES_*` creds)

```bash
docker compose logs -f backend   # watch `alembic upgrade head` then uvicorn
docker compose down              # stop (keeps the named volume / your data)
docker compose down -v           # stop AND wipe the db volume (fresh schemas next up)
```

## How compose maps to `backend/.env`

The backend reads one typed setting, `DATABASE_URL` (pydantic-settings; see `backend/.env.example`).
Compose injects it for the `backend` service from `infra/.env`. The only thing that changes
between contexts is the **host**, never the variable's shape:

| Context | `DATABASE_URL` |
|---|---|
| `backend` service in compose | `postgresql+psycopg://kr_rfp:kr_rfp@db:5432/kr_rfp` (host = service name `db`) |
| backend run on the host (outside compose) | `postgresql+psycopg://kr_rfp:kr_rfp@localhost:5432/kr_rfp` |
| CI `test` / `migration-roundtrip` jobs | `postgresql+psycopg://postgres:postgres@localhost:5432/kr_rfp` (Actions service container) |
| staging / prod | same name, injected from the secret store (DevOps `PLAN.md` §4) |

The driver is `psycopg` (v3), matching SQLAlchemy 2.x + Alembic in `backend/`.

## Migrations on startup

The `backend` service command is `alembic upgrade head && uvicorn app.main:app ...`. Rev `0001`
executes `db/baseline/schema.sql` (the re-expressed-clean as-built baseline). The init script
(`postgres/init/01_schemas.sql`) and the baseline both `CREATE SCHEMA IF NOT EXISTS` for the
eight schemas, so they are safe in either order.

## Boundaries

- **No secrets in git.** `.env` is gitignored (ADR-0001 §4). `.env.example` holds placeholders only.
- The DB **data volume** (`infra/postgres/data/`) and named docker volumes are gitignored.
- The least-privilege `kr_rfp_app` role is a local convenience; staging/prod roles come from IaC.
