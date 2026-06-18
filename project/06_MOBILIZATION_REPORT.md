---
doc: Squad Mobilization Report
id: PM-006
version: 1.0
status: Final (Phase 0)
created: 2026-06-18
depends_on: PM-000..PM-005, all project/squads/*/PLAN.md, docs/adr/*
---

# Squad Mobilization Report

All six squads needed for Phase 0/A (plus the D2 spike) have been mobilized and have delivered their plans. This report integrates them: the per-squad outcome, the cross-squad dependencies and how they reconcile, the consolidated list of what we need from the sponsor, and the decisions now ready to ratify. It is the PM's hand-off from *planning* to *scaffolding*.

## 1. Mobilization status

| Squad | Plan | Headline outcome |
|---|---|---|
| Solution Architect | `squads/architecture/PLAN.md` + `SKELETON.md` | 8 layers → PG schemas → domain packages; engine behind a **frozen interface** (D2-independent); governance double-enforced; exact Phase 0/A skeleton spec |
| Platform & Data | `squads/platform-data/PLAN.md` | Re-express the 63-table baseline clean (ADOPT ~42 / CLEAN ~9 / ADD ~18); M0 + 10 additive + **2 breaking (G1/G2) shipped together after the pilot**; schema-qualified naming canonical |
| Engine & Domain | `squads/engine-domain/PLAN.md` + `SPIKE_D2_engine.md` | **D2 spike → Option A** (adopt v3 scoring+split; retire min-cost to a reference lens); `run()` library contract; decision-support only |
| Security & Compliance | `squads/security/PLAN.md` | `ref.client` tenancy with `client_id` **prepended to the 46 composite FKs** (structural isolation) + RLS backstop; author≠approver RBAC; in-transaction hash-chain audit writer; G9/G12 gates |
| Platform Eng / DevOps | `squads/platform-devops/PLAN.md` | dev→staging→prod with one promoted image; 6-job CI gate; default hosting AWS ECS Fargate + RDS (provider-neutral pending DEP-4); shared-schema+RLS default |
| Quality & Assurance | `squads/quality/PLAN.md` | Test pyramid on real Postgres; **golden-master** engine reproducibility; the **E-13 real-data pilot** as Phase B's exit gate (retires R1); invariant tests for the governance rules |

## 2. The D2 spike outcome (ready to ratify)

The Engine squad's spike recommends **Option A — adopt v3's five-factor banded scoring + `max_two_per_dc` split allocation as the engine; retire the as-built exact min-cost solver to "Scenario A = lowest-cost reference."**

Single strongest reason: only Option A is faithful to the verified real behavior — the sign-off deck splits DCs across suppliers and v3 decides on five factors (cost only 35%), both confirmed in code. Option B would install a single-lowest-cost-winner brain the primary evidence contradicts, then pay to re-grain every downstream `awd.*` consumer (R2 wrong-brain lock-in).

This matches the audit's and PM/Architect's lean. **It is now ready for sponsor ratification** (D2 is sponsor-accountable). The architecture froze the engine *interface* regardless of outcome, so the store/contract/tests build in parallel and nothing is blocked while D2 awaits sign-off. Detail: `squads/engine-domain/SPIKE_D2_engine.md`.

## 3. Cross-squad reconciliation (dependencies & conflicts resolved)

| Topic | Squads | Resolution |
|---|---|---|
| **Tenancy enforcement** | Security ↔ Platform&Data ↔ Architect | `client_id` is added to every governed row **and prepended to the as-built's composite-identity FKs**, so cross-tenant referential leakage is structurally impossible — not merely filtered. RLS is the backstop. Platform&Data's M10 (client/tenant) carries this; it is an early, not late, migration. |
| **Tenancy topology** (shared-schema+RLS vs DB-per-tenant) | DevOps ↔ Security | **Default = shared-schema + RLS** (both squads converge). Flagged OPEN to Sponsor because a data-classification mandate could force physical per-tenant DBs, which would reshape deploy + migration. → Sponsor ask C2. |
| **Audit-event sink** | Security ↔ DevOps | Stays **in-Postgres, in-transaction** (Security-owned, G11); DevOps keeps it inside PITR backup scope and surfaces only a chain-verify metric — never treats it as a droppable log target. |
| **Engine interface vs D2** | Architect ↔ Engine | Interface is **frozen now**, implementation deferred to the spike outcome. Store, API contract, and tests proceed against the interface + a deterministic stub. |
| **Naming canonicalization** | Platform&Data ↔ Architect | Schema-qualified brief-style names are canonical (`cyc.cycle`, `eng.scenario_award`); flat as-built names crosswalk in `db/baseline/NAMING_MAP.md` (ADR-0008). |
| **Breaking migrations G1/G2** | Platform&Data ↔ DevOps ↔ Engine | Feature-flagged (`split_award`, `scenario_lenses`), shipped **together**, deployed flag-off, expand/contract + blue/green, sequenced **after** the Phase-B real-data pilot. |
| **Clean-room boundary** | All | `reference/` is input-only; CI fails if `backend/` imports it; real samples are classified before commit (Security) and git-ignored until then. |

No blocking conflicts surfaced — the six plans are mutually consistent.

## 4. ADR backlog (raised by the squads, to be written as we build)

ADR-0001/0002/0003 are ratified. Next: **0004** tenancy model · **0005** RBAC/actor model · **0006** engine interface (post-spike) · **0007** error taxonomy · **0008** naming canonicalization · **0009** audit hash-chain mechanism · **0010** immutability enforcement · **0011** iTrade receipt grain · **0012** kickoff keystone model · **0015** data classification & retention. Owners per RACI (Security owns 0004/0005/0009/0015; Architect 0006/0007/0008/0010; Platform&Data 0011; Product 0012).

## 5. Consolidated asks for the sponsor

Squads independently converged on the same needs. Grouped and prioritized. **None blocks Phase 0/A scaffolding** — they gate Phase B (the pilot) and the engine reproducibility proof.

### A. The engine reproducibility pair (highest priority — without it we can lift v3's logic but cannot *prove* reproduction)
1. **A known-good v3 output workbook** for a real input — the **golden master**. *The single most important artifact* (Engine + QA).
2. **`rfp_analysis_engine_v3.py`** (md5 `c73ffc5…`) via the isolated reference intake (read, never imported) — to lift the exact band/strength-rank math.

### B. The real-data set for the Phase B pilot (DEP-2)
3. One **real iTrade export** with real headers — ideally both the **43-column "Data"** and **51-column "Query/Calendar"** variants (the intake's sample errored at step 3).
4. One **real bid round** — supplier workbooks (the **tomato flat sheet** and, ideally, the **onion 9-tab "Hybrid"**).
5. One **real kickoff/setup doc** for that cycle (objective, timeframes, weights, premium bands).
6. A real **KCMS extract** (scan movement / margin).

### C. Reference data & platform decisions
7. **`us_zip_centroids`** reference, and the **fiscal-calendar** source (to 2037).
8. A prior **sign-off deck** + **booking guide** (to template the generated outputs) — optional but valuable.
9. **DEP-4: target cloud + IdP/SSO** (forks all staging/prod IaC, secrets, auth edge).
10. The org's **data-classification & retention policy**, the **tenant grain** (internal BU vs external client), and the **tenancy topology** ruling (shared-schema+RLS vs DB-per-tenant).
11. The **role → person** mapping and separation-of-duties expectation (for RBAC).

Upload anything in A/B/C into the chat; it lands in `reference/samples/` and is classified on arrival (Security). The clean-room boundary keeps it isolated from the build.

## 6. Decisions now open for the sponsor

- **D2 — ratify Option A** (spike complete; recommended). Non-blocking; the interface is frozen either way.
- **Tenancy topology** (ask C2/C10) — confirm shared-schema+RLS or mandate per-tenant DBs.
- **DEP-4** — cloud + IdP, when available.

## 7. Next step: scaffold Phase 0/A

Per ADR-0003 (plan-then-scaffold) and the Architect's `SKELETON.md`, the PM now stands up the monorepo: a healthy local Postgres with eight schemas, the FastAPI/SQLAlchemy/Alembic backend skeleton with the tenancy + audit + immutability cross-cutting concerns, the frozen engine interface + stub, the CI gate (incl. the clean-room and migration-roundtrip guards), the `db/baseline/` provenance + naming map, and the `frontend/` stub. Exit gate: `docker-compose up` → healthy Postgres + eight schemas; `alembic upgrade head` clean; `/health` green; CI passes. (Reconciled DDL and engine implementation follow per the phase roadmap.)
