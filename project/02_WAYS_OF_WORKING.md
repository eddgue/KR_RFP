---
doc: Ways of Working
id: PM-002
version: 0.1
status: Draft
created: 2026-06-18
depends_on: PM-000, PM-001
---

# Ways of Working

The operating model for the program: cadence, engineering standards, and the gates that keep an enterprise build honest.

## 1. Delivery model

- **Phased, gate-driven** (Phases 0/A–F, `05_MILESTONE_ROADMAP.md`). Each phase exits on a **demonstrated outcome**, not a task count.
- **Backend before frontend** (ADR-001). The web app is a view onto the store and does not start until the outward-facing half (Phase E) is proven.
- **Two changes ship together** (Ed's reconciliation): G1 (split) + G2 (scoring) land in the same engine increment because both touch the solver core.
- **Vertical slices inside a phase**: each backlog epic is delivered as a thin end-to-end slice (schema → service → API → test) so value is demonstrable continuously.

## 2. Cadence & ceremonies

| Ceremony | Frequency | Purpose |
|---|---|---|
| Program standup (async) | Per working session | Squad status, blockers, decisions needed |
| Backlog grooming | Per phase entry | Product + Architect refine the phase's epics into ready stories |
| Architecture review | On each ADR | Architect + affected squad leads ratify a design decision |
| Decision review | On any OPEN decision reaching due-by | PM escalates to Sponsor; logged in `03_DECISION_LOG.md` |
| Phase gate review | End of each phase | Sponsor + PM + leads confirm the exit gate is met before advancing |
| Risk review | Per phase | PM walks the register; updates likelihood/impact/mitigation status |

## 3. Engineering standards

**Source control & branching**
- Trunk-based with short-lived feature branches; PRs require review by the owning squad lead.
- Branch naming `squad/<area>/<short-desc>`; commits reference the epic ID (E-nn) and gap (G-n).
- No direct commits to the default branch; current development branch: `claude/wizardly-pasteur-n4acb8`.

**Database & migrations**
- Every schema change is an **Alembic migration**; the as-built chain is the baseline once validated on real Postgres.
- Migrations must be **roundtrip-tested** (upgrade→downgrade→upgrade) in CI before merge.
- **Additive first**: breaking migrations (G1 grain, G2 generalization) are isolated, feature-flagged, and sequenced deliberately.
- No SQLite idioms in the canonical schema; booleans are Postgres `boolean`; every enum is a real constraint (no prose-only enums).

**Code & API**
- Python/FastAPI/SQLAlchemy 2.x typed; services never own a transaction (add+flush, never commit) — carried from the as-built convention.
- The engine is a **library with a single `run()` entry point**; no Excel-formatting code is ported.
- API is contract-first (OpenAPI); every endpoint authn/authz-guarded (Security squad owns the middleware).

**Governance invariants (non-negotiable, enforced in code + DB)**
- Immutable sealed runs; corrections are new runs.
- Freeze-and-layer of awards; raw never overwritten.
- No hard deletes anywhere; supersede via new rows.
- Append-only, **live** audit event log (not a scaffold).
- Decision-support only: the engine never auto-asserts an award (`BANNED_DECISION_WORDS` guard kept on the recommendation surface).

## 4. Definition of Ready (a story can start)

Acceptance criteria written · gap/epic linked · data-model impact identified · test approach noted · security/tenancy impact reviewed · dependencies resolved or flagged.

## 5. Definition of Done (a story is complete)

Code + migration merged · unit/integration tests green · migration roundtrip passes · API contract updated · RBAC/tenancy honored · audit events emitted · docs/ADR updated · demoable in a vertical slice · no new hard-delete or live-formula fragility introduced.

## 6. Quality gates (per phase)

1. CI green (lint, type, tests, migration roundtrip).
2. Security review passed for any new endpoint/entity (tenancy + RBAC + PII classification).
3. Architecture review passed for any change to a governance invariant.
4. **Real-data check** from Phase B onward: the slice works against the pilot dataset, not only synthetic fixtures.

## 7. Documentation standard

- Decisions → ADRs (in `docs/adr/`, numbered, status-tracked) + the decision log.
- The **Target Spec v1.0** is the living source of truth; the two original packages and the audit are frozen inputs under `specs/` and `audit/`.
- Every squad keeps its plan current in `project/squads/<squad>/`.
