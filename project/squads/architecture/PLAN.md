---
doc: Target Architecture Plan
id: ARCH-001
version: 0.1
status: Draft (Phase 0)
created: 2026-06-18
owner: Solution Architect (`architect` agent)
depends_on: audit/00–04, specs/rfp-engine/BUILD_01-04, specs/original-engine/BUILD_01-02, ADR-0001, ADR-0002, ADR-0003
---

# Target Architecture — Kroger Produce RFP / Sourcing System of Record

The architecture the Phase 0/A scaffold (`SKELETON.md`) realizes. It states the target for an **enterprise system of record**, not a script with a database. Every choice here serves one of the three problems the program kills — historical blindness, non-standard process, manual dependence — and obeys the inheritance rule: *shape and intent from the BRIEF, constraint discipline and the seven KEEP capabilities from the AS-BUILT; never regress to the brief's thinner schema, never carry the as-built's wrong brain.*

This is binding under the ratified ADRs: clean-room reconciliation (ADR-0001), React/Next.js UI built last (ADR-0002), plan-then-scaffold backend-first (ADR-0003). No code appears in this document.

---

## 1. Architectural principles (non-negotiable)

1. **Store first; engine as a library; UI last.** The persistent governed store is the product. The engine is a callable library behind a stable interface, not a service the store depends on. The UI is a pure client of the API.
2. **Decision-support, never auto-assert.** The engine proposes scores, scenarios, and a recommendation; a human selects and promotes to award. No code path asserts a final award.
3. **Immutability by construction.** Sealed runs, freeze-and-layer of awards, no hard deletes, append-only audit — enforced at **both** the application layer (services) and the database layer (constraints, triggers, guard listeners). One layer is a convention; two layers is a control.
4. **Clean-room boundary.** `reference/` is input-only quarantine. `backend/` must never import from it; CI enforces this. The as-built schema is re-expressed cleanly under `db/baseline/`, never imported as code.
5. **Multi-tenant from the first migration.** `client` (tenant) is a first-class reference entity present before breadth hardens it out. Tenant context is threaded through every request and every row that needs isolation.
6. **Contract-first.** The OpenAPI contract is the source of truth between backend and frontend; frontend types are generated from it.
7. **Logical layers are physical schemas.** The eight layers (`ref`, `norm`, `cyc`, `bid`, `eng`, `awd`, `perf`, `audit`) are real PostgreSQL schemas, mirrored by Python domain modules. The layering is visible in the database, the code, and the migrations.

---

## 2. Logical layers mapped to modules

The eight-layer model is the spine of both the schema and the codebase. Each DB schema maps 1:1 to a domain package under `backend/app/domain/<layer>/`; the engine sits beside them as a library, and four cross-cutting concerns live under `app/core/`.

| Layer (PG schema) | Owns | Domain module | Key tables (target) | KEEP from as-built |
|---|---|---|---|---|
| `ref` | Reference dimensions + alias machinery + tenancy | `domain/ref/` | `client`, `commodity`, `subcommodity`, `dc`, `supplier(+alias)`, `item(+alias)`, `loading_location`, `fiscal_calendar`, `zip_centroid`, `master_data_quarantine` | typed alias kinds + partial-unique active index + quarantine queue |
| `norm` | Persistent cross-cycle lot store + attribute taxonomy | `domain/norm/` | `lot`, `attribute_def`, `lot_attribute`, `item_lot_map` (sticky), `source_artifact`, `normalization_run` | sticky resolution + file lineage (sha256 provenance) |
| `cyc` | Kickoff keystone (the in-gate) | `domain/cyc/` | `cycle`, `cycle_timeframe`, `cycle_round`, `cycle_dc`, `cycle_lot`, `cycle_objective`, `cycle_pricing`+`cycle_safety`, `cycle_pba_term`, `cycle_commercial_term`, `cycle_rfi_question`, `cycle_timeline_event`, `cycle_narrative`, `cycle_invited_supplier` | scope-consistency trigger; invited-supplier denominator |
| `bid` | Intake, eligibility, capacity, landed cost | `domain/bid/` | `bid_submission`, `bid`(line), `bid_price`, `bid_index_component`, `grow_origin`, `ship_from_zip`, `supplier_capability`, `capacity_statement`+`capacity_constraint`, `eligibility_result`+`gate_result`+`exception`, `landed_cost_result` | 5-mode landed cost; 7-gate eligibility; capacity scopes; demand≠capacity CHECK |
| `eng` | Sealed runs, scores, scenarios, split awards | `domain/eng/` | `analysis_run`(+`run_input`, version pins), `bid_score` (5-factor), `scenario` (A–G), `scenario_award` (split, `volume_share`), `round_analysis_snapshot` | sealed calc-run spine + hashed manifests + version pins |
| `awd` | Selected awards, freeze/layer, sign-off, outputs | `domain/awd/` | `award` (multi-row/cell, `frozen_at`), `award_layer`, `signoff`, `generated_document` | net-new (lift v1.4 generators to render *from records*) |
| `perf` | History feeds + scorecard | `domain/perf/` | `itrade_receipt` (receipt grain), `kcms_movement`, `supplier_scorecard` (2 snapshots), commercial-pricing tables (re-pointed to kickoff), VSP tables | importer discipline (flag-first, impossible-date reject); commercial component storage + replayable formula audit |
| `audit` | Live append-only event log | `domain/audit/` | `event_log` (hash-chained, live), `decision_note` | hash-chain **design** (made live, write-only enforced) |

**Reconciliation rule per layer.** Where the brief's table and an as-built table overlap, the brief gives the **shape/intent** and the as-built gives the **storage/constraints**. The breaking changes (`scenario_a_*` → `scenario`/`scenario_award`; single-winner → `volume_share`) ship together (G1+G2) and land in `eng`. Everything else is additive.

---

## 3. The engine as a library behind a stable interface

The decision logic (v3's five-factor scoring + `max_two_per_dc` split allocation + lenses A–G) is a **library**, not a service. It is called in-process by the Engine Runner service, which owns the transaction and the store I/O. The library never touches the database, the session, or HTTP — it takes a frozen input bundle and returns a result bundle.

- **Interface (stable, D2-independent).** A single entry point `run(inputs) -> result` over plain dataclasses/pydantic models: in = cycle config (weights, thresholds, `max_sup_dc`, splittable flags, active TFs) + scored/eligible bids + incumbent/historical cost; out = per-bid scores (5 banded factors → `rec_score` + eligibility + gate flags), scenarios A–G, and split `scenario_award` rows with `volume_share`. The interface and its types are frozen now; they do not change when the D2 spike resolves.
- **Internals stubbed until D2.** Per ADR-0003, D2 (adopt-v3 vs extend-as-built-Scenario-A) is **in spike**. The scaffold ships the interface plus a deterministic stub implementation behind it, selected by config. The spike (`squads/engine-domain/SPIKE_D2_engine.md`) resolves which real implementation lands; the surrounding store, runner, contract, and tests are built against the interface regardless.
- **Boundary discipline.** The library is pure (no I/O, no clock, no randomness except via injected config), so it is unit-testable in isolation and reproducible — a hard requirement for sealed runs and the real-data pilot (S2). The Runner seals the run: it freezes inputs, hashes input/output manifests, records version pins (metric/engine/config), and writes results append-only.

---

## 4. Cross-cutting concerns

These live under `app/core/` and apply across all eight layers.

### 4.1 Multi-tenant context
- `client` is a first-class `ref` entity. A request-scoped **tenant context** (set from the authenticated principal, never from a client-supplied body field) is threaded through the session. Tenant-scoped tables carry `client_id`; reads are filtered by the active tenant at the repository boundary.
- Enforcement is defense-in-depth: app-layer filtering now; PostgreSQL **Row-Level Security** policies as the DB-layer backstop (Security squad owns the policy set). Cross-tenant leakage is a tested invariant, not a hope.

### 4.2 Auth / RBAC boundary
- AuthN is delegated to an external provider (per Security squad + DEP-4); the backend trusts a verified principal (subject, tenant, roles) at the edge. The architecture does not couple to a specific IdP.
- AuthZ is an **explicit boundary** in `app/core/security/`: a role/permission model + dependency-injected guards on every route. Roles map to the actor model (e.g. sourcing analyst, approver, admin). The engine and domain services receive an already-authorized principal; they do not re-implement authz.
- The "sent" governance gate (G9) and Stage-0 in-gate (G12) are **approval objects** with approver + timestamp, gated by permission — not channel side-effects.

### 4.3 The live audit event bus
- Every state change (created, sealed, frozen, superseded, signed-off, sent) appends one row to `audit.event_log`. Population is **not** the caller's responsibility to remember: services emit domain events; a single audit writer subscribes and writes the hash-chained row (before/after state hash, prev/this event hash) inside the same transaction.
- Write-only is enforced at the DB layer (triggers reject UPDATE/DELETE on `event_log`) — the as-built's hash-chain *design* made *live* (G11). "Open last cycle" is then a query across cycle → rounds → bids → runs → scenarios → awards joined through the event trail, the capability a stateless engine cannot provide.

### 4.4 Immutability enforcement (app + DB)
- **App layer.** Services never edit or delete governed rows; corrections insert superseding rows. Sealed-run outputs and frozen awards are write-once in the service contract.
- **DB layer.** Guard listeners / triggers reject mutation of sealed `analysis_run` outputs and frozen `award` rows; `award_layer` is the only post-freeze write path; no table grants DELETE on governed data. This is the as-built's `calc_run_guards` discipline, re-modeled cleanly.

---

## 5. API style — contract-first OpenAPI

- **Contract-first.** The OpenAPI spec is authored/owned as the backend↔frontend contract. FastAPI generates the served schema; the frontend (ADR-0002) generates its TypeScript client and types from it. No hand-written client types.
- **Resource-oriented REST**, versioned under `/api/v1`. Resources follow the lifecycle: `/cycles`, `/cycles/{id}/rounds/{r}/bids`, `/runs/{id}/scenarios`, `/cycles/{id}/awards`, `/cycles/{id}/signoff`, `/cycles/{id}/documents`, plus ingestion endpoints (`/itrade/import`, `/kcms/import`, `/normalize/*`). The representative surface is in `specs/rfp-engine/BUILD_04`.
- **Decision-support verbs are explicit and human-gated.** Promotion (`/awards/select`), freeze (`/signoff/approve`), and send are distinct, permissioned, audited transitions — never implicit side-effects of a GET or a run.
- **Uniform error taxonomy** (see ADR backlog): a single problem-shaped error envelope with a stable machine code, so the importer's "quarantine with a reason" and the engine's "blocked, never guessed" surface consistently to clients.
- **Tenant + principal are ambient**, taken from the auth context, never from request bodies.

---

## 6. Component view (C4-ish, in prose)

**Context (L1).** Sourcing analysts and approvers (the users) operate the **RFP System of Record** through a web app. It ingests from external feeds — **iTrade** (PO receipts), **KCMS** (scan movement), and supplier **bid files** — and emits generated artifacts (booking guide, sign-off deck, letters, confirmation email). An external **IdP** provides authentication. The sponsor's **existing repo** is *not* a runtime actor; it is an offline, isolated reference (ADR-0001).

**Containers (L2).** Four runtime containers plus the database:
1. **Backend API** (FastAPI/SQLAlchemy/Alembic, Python 3.12) — the only writer to the store; hosts the domain services and, in-process, the engine library.
2. **PostgreSQL 15+** — the governed store; eight schemas; constraints, triggers, RLS, guard listeners carry half the governance.
3. **Web app** (Next.js/TypeScript, ADR-0002) — a pure API client, built last.
4. **Worker** (same image as the API, async entry) — long-running imports, engine runs, and document generation; same services, no separate codebase. (Synchronous in early phases; the seam is reserved.)

**Components (L3, inside the Backend API).** The API layer (routers) delegates to **domain services**, one cluster per layer: Reference/Tenancy, Normalizer, Cycle (kickoff), Bid Importer + Eligibility + Landed-Cost, **Engine Runner** (which wraps the engine **library**), Selection, Freeze, Document Generator, plus the feed loaders (iTrade, KCMS, Scorecard, Distance). Four **core** components cut across all: Config, DB/session, Security (authn-trust + RBAC + tenant context), and Audit (event writer + immutability guards). Services follow the transaction rule below: **add + flush, never commit** — the request/unit-of-work boundary owns the commit.

**Code (L4).** Domain packages mirror the schemas; the engine library is isolated and pure; repositories encapsulate tenant-scoped queries; Alembic migrations are the only mechanism that changes the schema. The clean-room rule (`backend/` never imports `reference/`) is a CI gate.

---

## 7. Tech standards

- **Config.** Single typed settings object (pydantic-settings) sourced from environment; no literals in code; secrets via environment/secret store, never committed. One config surface selects the engine implementation (stub vs real, per D2).
- **Typing.** Full type hints; `mypy` (or equivalent) in CI; SQLAlchemy 2.x typed mapped classes; pydantic models at the API and engine-interface boundaries. The frontend's types are generated, not authored.
- **Transaction discipline.** **Services `add` + `flush`, never `commit`.** A single unit-of-work per request (or per worker task) owns the transaction boundary and commits once. This makes multi-service operations atomic, keeps audit writes in the same transaction as the change they record, and matches the as-built convention.
- **Immutability.** Enforced twice (services + DB), per §4.4. No service exposes update/delete on governed rows.
- **Migrations.** Alembic only; baseline from `db/baseline/` (the re-expressed as-built schema); every migration reversible and round-trip tested (kills the SQLite-ism risk R8).
- **Naming/casing.** Canonical `snake_case` for DB identifiers; schema-qualified table names; one canonicalization pass reconciles the as-built's flat names (`rfp_cycle`, `scenario_a_*`) to the target schema-qualified names (`cyc.cycle`, `eng.scenario`) — recorded as an ADR so the mapping is auditable.
- **Testing.** Pyramid: pure unit tests for the engine library; service tests against a real Postgres; migration round-trip tests; reproducibility tests for sealed runs; the Phase B real-data pilot as the program gate. CI runs lint, type-check, tests, the clean-room import check, and a migration up/down check.
- **Observability.** Structured logging with tenant + request correlation; health/readiness endpoints; metrics seam reserved for DevOps.

---

## 8. ADR backlog (next 8–12)

These are the architecture decisions the scaffold and Phase A/B work force. Numbering continues the `docs/adr/` series (0001–0003 ratified). Each lands as `docs/adr/ADR-00NN-*.md`.

| ADR | Title | Decides | Gates |
|---|---|---|---|
| 0004 | **Tenancy model** | `client` grain, where `client_id` lives, app-filter + Postgres RLS as the isolation mechanism | Phase 0 schema; S7 |
| 0005 | **Audit-chain mechanism** | Hash-chain construction, the event-writer pattern (domain events → single writer), DB write-only enforcement, what counts as an event | Phase A; G11; S6 |
| 0006 | **Engine library interface** | The frozen `run(inputs)->result` contract + types, stub-behind-interface, the D2-independent boundary | Phase 0/D; D2 spike |
| 0007 | **Error taxonomy & API problem model** | The single error envelope, machine codes, how "blocked/quarantined" surface | Phase 0 API; §5 |
| 0008 | **Naming/casing canonicalization** | The as-built-flat → schema-qualified mapping; identifier conventions | Phase 0 baseline; §7 |
| 0009 | **RBAC / actor & permission model** | Roles, permissions, route-guard pattern, principal trust at the edge | Phase A; D5; S7 |
| 0010 | **Immutability enforcement strategy** | Which invariants are app-only vs DB-trigger vs guard-listener; the freeze-and-layer write path | Phase A; ADR-004 intent; S6 |
| 0011 | **Lot lifetime & normalization persistence** | Persistent cross-cycle `norm.lot` vs cycle-local `cycle_lot`; sticky `item_lot_map` semantics | Phase B; G8; schema-diff §2 |
| 0012 | **Pricing-at-kickoff & executable safeties** | Lift pricing to `cyc`, re-point commercial storage, the safety execution/visualization model | Phase C/D; G4; D3 |
| 0013 | **Migration strategy & baseline provenance** | Baseline from `db/baseline/`, additive vs the two breaking migrations, round-trip testing, SQLite-ism removal | Phase 0; R8 |
| 0014 | **Document generation architecture** | Render-from-records, template ownership, `generated_document` lifecycle, lift of v1.4 generators | Phase E; G3; D4 |
| 0015 | **Tenant-aware data classification & retention** | PII/commercial-data classification, retention, what may be committed vs sample-only | Phase A; D5; ADR-0001 sample rule |

(0004–0008 are needed for the scaffold; 0009–0015 land as their phases open.)

---

## 9. What this plan defers (honest boundaries)

- **The brain itself.** D2 is in spike; the engine *interface* is fixed here, the *implementation* is not. The scaffold ships a stub.
- **Concrete IdP / secret-store / cloud.** Delegated to Security (DEP-4) and DevOps; the architecture stays provider-neutral at the edge.
- **Async/worker depth.** The worker seam is reserved; early phases run synchronously. Promotion to a real queue is a later, additive decision.
- **The full reconciled schema.** This plan fixes the layer map and the KEEP/CHANGE/BUILD dispositions; the table-by-table reconciled DDL is the Platform & Data squad's first deliverable, baselined from `db/baseline/`.

---

## Changelog

| Version | Date | Author | Change Summary |
|---------|------|--------|----------------|
| 0.1 | 2026-06-18 | Architect | Initial target architecture for Phase 0/A; layer map, engine-as-library interface, cross-cutting concerns, contract-first API, C4-ish view, tech standards, ADR backlog 0004–0015. |
