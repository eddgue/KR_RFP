# ADR-0001 — Clean-room reconciliation: new codebase, existing DB schema as baseline

- **Status:** Accepted (sponsor-ratified 2026-06-18)
- **Deciders:** Sponsor (Ed), PM, Solution Architect
- **Supersedes/relates:** Decision D1, dependency DEP-1, audit `04` D1

## Context

The audit established that a real, enterprise-grade governed store already exists (the AS-BUILT: 63 tables, 67 CHECK constraints, 46 composite-identity FKs, a sealed calc-run spine). The naive "reconcile" reading would build *inside* that existing repository. But the sponsor's constraint is explicit:

> "the repo is in my github, but i dont want it contaminating this build … have an agent read it and provide the db but keep it isolated from current repo and codebase. and/or agents can ask for sample files and i can upload current manual wf files as needed."

The existing codebase also carries the **wrong brain** (a min-cost single-winner solver) and SQLite-shaped, partially no-op DDL (`audit [D-6]`). We want its **schema discipline and the seven KEEP capabilities**, not its application code.

## Decision

Adopt **clean-room reconciliation**:

1. **This repository is a fresh, clean codebase.** No application code from the existing repo is ever copied in.
2. **The existing AS-BUILT schema is the migration baseline** — but only the *schema*, re-expressed as clean PostgreSQL and re-validated. It lands under `db/baseline/` as our own artifact, not as an import of the old project.
3. **The old repo is an isolated, read-only reference.** If/when the sponsor grants access, a *single dedicated agent* reads it **in an isolated git worktree** and emits exactly two things into `reference/` (clearly marked external, never wired into the build): (a) `reference/as-built-db/` — the extracted/validated schema + the Alembic chain summary, and (b) `reference/as-built-digest.md` — a knowledge digest (services, tests, the ECLS content). Nothing else crosses the boundary.
4. **Sample-file intake on demand.** Squads may request specific real artifacts (a kickoff doc, an iTrade pull, a manual booking guide); the sponsor uploads them; they land under `reference/samples/` with provenance, never committed if they contain real commercial data without classification (Security squad owns the rule).

## Isolation protocol (the boundary)

```
  YOUR GITHUB (private)                 THIS REPO (clean build)
  ┌───────────────────┐   one-way       ┌──────────────────────────┐
  │ existing repo      │   read-only     │ reference/   (quarantine) │
  │  models.py, tests, │ ───────────────▶│  as-built-db/, digest.md, │
  │  migrations, ECLS  │  via isolated   │  samples/                 │
  └───────────────────┘  worktree agent  └───────────┬──────────────┘
        never imported                                │ informs (not imported)
                                                       ▼
                                          db/baseline/  +  backend/  (our own code)
```

Rule: `reference/` is **input only**. Build code lives in `backend/`, `frontend/`, `db/`. CI fails if `backend/` imports from `reference/`.

## Consequences

- We keep the as-built's rigor (composite FKs, calc-run spine, landed cost, eligibility, VSP) by **re-modeling** it cleanly, not inheriting it.
- We drop the wrong brain and the SQLite-isms by construction.
- DEP-1 is partially satisfiable *today*: we already hold the as-built schema (`specs/original-engine/BUILD_03_schema.sql`) and can baseline from it; full reconciliation (ECLS, tests, migration history) waits on isolated access.
- A small one-time cost: the reference-intake agent and the `reference/` quarantine discipline.

## Status of inputs

- Have now: as-built schema, both spec packages, the audit.
- Awaiting (DEP-1): isolated read access to the existing repo (for ECLS + test/migration verification) — **non-blocking** for Phase 0 scaffolding.
