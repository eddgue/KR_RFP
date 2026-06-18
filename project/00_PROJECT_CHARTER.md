---
doc: Project Charter
id: PM-000
version: 0.1
status: Draft (pending sponsor ratification)
created: 2026-06-18
sponsor: Eduardo Guevara (Sourcing)
program_manager: PM (this engagement)
depends_on: audit/00–04, specs/rfp-engine, specs/original-engine
---

# Project Charter — Kroger Produce RFP / Sourcing Engine ("Project Spine")

## 1. Why we are here

We are building an **enterprise web application** that runs Kroger produce sourcing cycles end to end and stores every cycle, bid, and award so any past cycle reopens as a query. Two spec packages already exist — the intake-derived **BRIEF** (target) and the **AS-BUILT** inventory of an inherited codebase — and an audit (`audit/`) has shown that **neither is the product**: the brief has the right brain and outward-facing half on a thin data model; the as-built has an enterprise-grade spine but the wrong brain, inert pricing safeties, and no outward half. This program reconciles the two into one delivered system.

The system kills three problems Sourcing lives with today: **historical blindness** (look-back means hunting a shared drive), **non-standard process** (every RFP run differently, recorded nowhere), and **manual dependence** (booking guide, sign-off, letters hand-built every cycle).

## 2. Vision (the target, one sentence)

*The brief's brain and outward-facing half, built on the as-built's governed spine, with pricing lifted to kickoff and the five safeties made executable — delivered as a secure, multi-tenant web app and proven on one real cycle.*

## 3. Scope

**In scope**
- A governed PostgreSQL system of record (reconciled from the existing 63-table store).
- The decision-support engine (v3's 5-factor scoring + split allocation + seven scenario lenses) as a library on the store.
- The full cycle lifecycle: kickoff keystone → supplier field → multi-template bid intake → normalization → eligibility & landed cost → sealed runs → scenarios → **split awards → freeze → sign-off → generated outputs** (booking guide, sign-off deck, letters, confirmation email).
- Data feeds: iTrade (receipt grain), KCMS, supplier scorecard (two frozen snapshots).
- The twelve gaps (G1–G12, `audit/02`) and the seven "keep" capabilities.
- **Net-new enterprise layer**: multi-tenant (`client`), RBAC, PII/data-classification, retention, live audit, NFRs, CI/CD, observability.
- An enterprise web front end (stack = Decision D6) built last, as a view onto the store (ADR-001).

**Out of scope (this release)**
- Cleaning historical pre-system cycles ("the graveyard stays; we stop adding bodies").
- Contract authoring/e-signature beyond assembling specs+legal from award+kickoff terms.
- Real-time/high-throughput workloads — this is a system-of-record scale (tens of categories, dozens of DCs, hundreds of lots, single-digit-thousand bids/cycle, a handful of rounds).
- Non-produce categories (architecture stays commodity-agnostic; rollout is later).

## 4. Success criteria (measurable)

| # | Criterion | Measure |
|---|---|---|
| S1 | **Open last cycle** works | Any completed cycle reopens with full story (bids, runs, scenarios, awards, event trail) in one query, < 2s |
| S2 | **Real-data pilot passes** (retires the #1 risk) | One real iTrade pull + one real bid round run end-to-end; engine reproduces v3's verified scoring + split allocation |
| S3 | **Decision-support, not auto-award** | Engine proposes; a human selects; no award is ever auto-asserted; every selection carries a decision note |
| S4 | **Split awards** | A cell can be awarded to multiple suppliers with volume shares, capacity-constrained |
| S5 | **Generated outputs** | Booking guide, sign-off deck, and letters generate from records, not by hand |
| S6 | **Governance** | Immutable runs, freeze-and-layer, no hard deletes, live audit trail, draft→sent gate — all enforced |
| S7 | **Enterprise NFRs** | RBAC enforced, multi-tenant isolation proven, PII classified, audit immutable, CI green, observability live |
| S8 | **Savings vs STLY** | Portfolio savings-vs-STLY computes and rolls to a sign-off total |

## 5. Governance

- **Sponsor / Product authority:** Ed (Sourcing) — ground truth on process; ratifies decisions D1–D7.
- **Program Manager:** owns plan, RACI, risk, cadence, decision log.
- **Solution Architect:** owns the target architecture and ADRs.
- **Supersession:** a single **Target Spec v1.0** (Phase 0 output) supersedes both existing packages. Until then, on conflict the **BRIEF is ground truth on intent**, the **AS-BUILT is ground truth on what exists**, and the **audit is ground truth on the reconciliation**.

## 6. Key constraints & assumptions

- **A1** A real governed store already exists (63 tables, 14 migrations, 796 tests). Build path is reconcile-and-extend, **pending repo + ECLS access** (Decision D1 / dependency DEP-1).
- **A2** The v3 engine logic is verified and good; we lift its brain, not its Excel formatting.
- **A3** Postgres is ample for the workload; design for clarity and governance over throughput.
- **A4** Nothing has touched real data yet — the program's top risk; the Phase B pilot is the gate.
- **A5** Stack leans Python/FastAPI/SQLAlchemy/Alembic/Postgres (from both specs); front-end stack is Decision D6.

## 7. Top risks (full register in `audit/04_RISKS_DECISIONS_ROADMAP.md`)

R1 no real data yet (Critical) · R2 wrong-brain lock-in (High) · R3 greenfield rebuild of an existing store (High) · R5 inert safeties (High) · R7 no security/tenancy layer (High). Each has a named mitigation and a phase that retires it.

## 8. Milestones at a glance

Phase **0 Reconcile** → **A Spine hardening** → **B History + normalization + REAL-DATA PILOT** → **C Kickoff keystone + rail** → **D The brain (scoring + split, shipped together)** → **E Outward-facing half** → **F API hardening, then UI**. Gates are *demonstrated outcomes*, not table counts. Dates pending decisions D1–D7.

## 9. Definition of done (program level)

All eight success criteria met; Target Spec v1.0 delivered and current; the real-data pilot passed; security/NFR acceptance signed; the web app renders live and historic cycles identically from the store.
