# ADR-0003 — Execution model: plan-then-scaffold, backend-first

- **Status:** Accepted (sponsor-ratified 2026-06-18)
- **Relates:** Decision D7, ADR-001 (UI last)

## Decision

Run the engagement as **plan-then-scaffold**: the squads produce detailed plans, then we immediately stand up Phase 0/A running ground in this clean repo — a validated PostgreSQL schema baseline, a FastAPI/SQLAlchemy/Alembic backend skeleton, the multi-tenant + RBAC foundation, CI, and local infra (docker-compose). Implementation proceeds **backend-first**; the Next.js front end (ADR-0002) is built last, at Phase F.

## Consequences

- There is runnable ground from day one, but breadth follows the phase gates (roadmap `PM-005`).
- Ratified decisions (D1, D6, D7) are binding; D2 is treated as in-spike and the engine internals are stubbed behind an interface until the spike resolves.
- The scaffold targets the as-built schema baseline (ADR-0001), not the brief's thinner schema.
