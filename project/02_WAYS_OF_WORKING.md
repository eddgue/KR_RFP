---
doc: Ways of Working
id: PM-002
version: 0.2
status: Draft
created: 2026-06-18
depends_on: PM-000, PM-001, PM-007
---

# Ways of Working

The operating model for the program: cadence, engineering standards, and the gates that keep an enterprise build honest.

## 1. Delivery model

- **Modular, prototype-fidelity — NOT MVP** (D19, sponsor directive). We do **not** build boiled-down MVPs. We build **well-bounded modules**, each delivered as a **functional prototype version of the full capability** (iterated v1→v2→…), never a thinnest-possible slice. "Done" for a module = a working prototype of the *whole* capability, not a stub. (The engine's deterministic stub was only a D2 placeholder; with D2 resolved it becomes the real v3 prototype.)
- **Phased, gate-driven** (Phases 0/A–F, `05_MILESTONE_ROADMAP.md`). Each phase exits on a **demonstrated outcome**, not a task count. Phases/epics are **modules**, each built to prototype fidelity.
- **Backend before frontend** (ADR-001). The web app is a view onto the store and does not start until the outward-facing half (Phase E) is proven.
- **Two changes ship together** (Ed's reconciliation): G1 (split) + G2 (scoring) land in the same engine increment because both touch the solver core.
- **Modules built end-to-end**: each is delivered as a coherent slice (schema → service → API → test → its UI when applicable), at real fidelity — not stubbed — so it stands as a usable prototype, not a demo shell.

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

Code + migration merged · unit/integration tests green · migration roundtrip passes · API contract updated · RBAC/tenancy honored · audit events emitted · docs/ADR updated · **pre-merge audit-impact review run, and the As-Built Audit + gap register updated in the same change if any audit trigger was hit (§8, D37/D39)** · demoable in a vertical slice · no new hard-delete or live-formula fragility introduced.

## 6. Quality gates (per phase)

1. CI green (lint, type, tests, migration roundtrip).
2. Security review passed for any new endpoint/entity (tenancy + RBAC + PII classification).
3. Architecture review passed for any change to a governance invariant.
4. **Real-data check** from Phase B onward: the slice works against the pilot dataset, not only synthetic fixtures.
5. **As-Built Audit current** — if the change hit an audit trigger (§8), `project/07_AS_BUILT_PROCESS_AUDIT.md` is updated in the same change; **a major version is not complete until it is** (D37).

## 7. Documentation standard

- Decisions → ADRs (in `docs/adr/`, numbered, status-tracked) + the decision log.
- The **Target Spec v1.0** is the living source of truth; the two original packages and the audit are frozen inputs under `specs/` and `audit/`.
- Every squad keeps its plan current in `project/squads/<squad>/`.

## 8. As-Built Audit — living model of reality, event-triggered, a release gate

The **As-Built Process Audit** (`project/07_AS_BUILT_PROCESS_AUDIT.md`, PM-007) is a **living model of reality** — it documents the system **as actually implemented**, not as intended. If implementation and the audit disagree, implementation is reviewed and the audit is corrected to match reality (D39). It is refreshed on **architecture events, not a calendar**. Its trigger conditions, standing questions, required sections, and release-gate states live in that doc (§12–§13). The headline rule:

> **No major version is complete until the As-Built Audit is updated.** (D37)

**Pre-merge audit-impact review (part of the DoD).** On every PR (including Codex review), ask whether the change touches **workflow · state transitions · persistence · runtime boundaries · permissions · governance · auditability · user-visible behavior · failure domains**. If **any** answer is yes, the audit **and the gap register** are reviewed and updated **in the same change, before merge** — the audit moves with the code.

**Re-audit triggers** (scope per PM-007 §12.1): new process stage / lifecycle transition / approval path / human interaction / automation · new table / file output / storage location / write path / system of record · new service / MCP tool / agent / orchestrator logic / execution boundary / integration · new role / permission / RBAC / approval / audit-logging change · new screen / workflow surface / operator action / user-visible state · new subsystem / dependency / runtime / deployment model · major version / pre-/post-production rollout.

**Release-gate states** (PM-007 §12.3): a major version yields **PASS** (audit reflects implementation; no critical control missing), **CONDITIONAL** (known risks documented and explicitly accepted in the gap register with an owner), or **FAIL** (audit doesn't reflect implementation or a critical control is missing — do not ship).

Each update records the **delta** (Added / Modified / Removed capabilities · Closed gaps · New gaps), so "when did this capability appear / when did this control disappear?" is answerable without reverse-engineering git. This makes the audit part of the development process rather than documentation that drifts into fiction.
