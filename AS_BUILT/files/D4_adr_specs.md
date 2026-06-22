---
doc: AS-BUILT AUDIT — SLICE D4 — ADRs + Specs (original-engine fork + rfp-engine + intake)
slice: D4
scope: docs/adr/** (all present ADRs) + specs/** (original-engine, rfp-engine BUILD_*, intake/SESSION-*)
status: COMPLETE
method: find both trees → cross-check FILE_CENSUS.md → read each file end-to-end → cross-ref every ADR decision to the live code
contract: /CLAUDE.md (ABSOLUTE REQUIREMENTS honored); /AS_BUILT/AUDIT_STANDARD.md (substance bar)
files_audited: 27 (10 ADRs + 5 original-engine + 5 rfp-engine BUILD + 7 intake)
generated: 2026-06-22
---

# SLICE D4 — ADRs + Specs — Exhaustive As-Built Audit

This slice documents the project's **decision record** (the ADRs under `docs/adr/`) and the **two spec
packages** (`specs/original-engine` = the FORKED legacy as-built spec; `specs/rfp-engine` = our build
spec, including the six intake sessions that captured the requirements). Per the audit standard, every
ADR is documented **in full** (number, title, status, decision, context, consequences, detailed WHY,
and whether it is reflected in the live code, cross-referenced). Every spec gets path · what · detailed
WHY · structured outline. Nothing summarized away.

## D4.0 — Census cross-check + scope reconciliation

All 27 files were located with `find docs/adr -type f` and `find specs -type f`, then cross-checked
against `AS_BUILT/FILE_CENSUS.md`. **Every one is present in the census** (ADR rows 254–263; spec rows
557–573). No empty files in this slice. All non-empty (`empty=no`), all `owned=y`.

| Census row | Path | ext | bytes | lines | created | modified |
|---|---|---|---|---|---|---|
| 254 | docs/adr/ADR-0001-clean-room-reconciliation.md | md | 4151 | 50 | 2026-06-18 | 2026-06-18 |
| 255 | docs/adr/ADR-0002-frontend-stack.md | md | 2113 | 30 | 2026-06-18 | 2026-06-21 |
| 256 | docs/adr/ADR-0003-execution-model.md | md | 1372 | 16 | 2026-06-18 | 2026-06-21 |
| 257 | docs/adr/ADR-0004-tenancy-model.md | md | 2708 | 36 | 2026-06-18 | 2026-06-18 |
| 258 | docs/adr/ADR-0006-engine-brain.md | md | 3060 | 30 | 2026-06-18 | 2026-06-18 |
| 259 | docs/adr/ADR-0013-pricing-storage-and-display.md | md | 4074 | 44 | 2026-06-18 | 2026-06-18 |
| 260 | docs/adr/ADR-0014-pricing-safeties.md | md | 6567 | 63 | 2026-06-19 | 2026-06-19 |
| 261 | docs/adr/ADR-0016-strategy-agnostic-platform.md | md | 3949 | 40 | 2026-06-19 | 2026-06-19 |
| 262 | docs/adr/ADR-0017-hosting-platform.md | md | 5974 | 82 | 2026-06-21 | 2026-06-21 |
| 263 | docs/adr/ADR-0018-storage-model.md | md | 6538 | 73 | 2026-06-21 | 2026-06-21 |
| 557 | specs/original-engine/BUILD_00_README.md | md | 5333 | 72 | 2026-06-18 | 2026-06-18 |
| 558 | specs/original-engine/BUILD_01_SYSTEM_OVERVIEW_AND_ADRS.md | md | 12587 | 124 | 2026-06-18 | 2026-06-18 |
| 559 | specs/original-engine/BUILD_02_DATA_MODEL.md | md | 13365 | 217 | 2026-06-18 | 2026-06-18 |
| 560 | specs/original-engine/BUILD_03_schema.sql | sql | 63573 | 1336 | 2026-06-18 | 2026-06-18 |
| 561 | specs/original-engine/BUILD_04_TECH_SPEC.md | md | 10803 | 156 | 2026-06-18 | 2026-06-18 |
| 562 | specs/rfp-engine/BUILD_00_README.md | md | 3511 | 60 | 2026-06-18 | 2026-06-18 |
| 563 | specs/rfp-engine/BUILD_01_SYSTEM_OVERVIEW_AND_ADRS.md | md | 9008 | 120 | 2026-06-18 | 2026-06-18 |
| 564 | specs/rfp-engine/BUILD_02_DATA_MODEL.md | md | 8096 | 152 | 2026-06-18 | 2026-06-18 |
| 565 | specs/rfp-engine/BUILD_03_schema.sql | sql | 25792 | 521 | 2026-06-18 | 2026-06-18 |
| 566 | specs/rfp-engine/BUILD_04_TECH_SPEC.md | md | 9485 | 159 | 2026-06-18 | 2026-06-18 |
| 567 | specs/rfp-engine/intake/00_INDEX.md | md | 15685 | 161 | 2026-06-18 | 2026-06-18 |
| 568 | specs/rfp-engine/intake/SESSION-01_intake-recap.md | md | 8356 | 92 | 2026-06-18 | 2026-06-18 |
| 569 | specs/rfp-engine/intake/SESSION-02_kickoff-schema.md | md | 8086 | 139 | 2026-06-18 | 2026-06-18 |
| 570 | specs/rfp-engine/intake/SESSION-03_data-and-engine-layer.md | md | 9891 | 124 | 2026-06-18 | 2026-06-18 |
| 571 | specs/rfp-engine/intake/SESSION-04_signoff-gate-and-split-awards.md | md | 4309 | 54 | 2026-06-18 | 2026-06-18 |
| 572 | specs/rfp-engine/intake/SESSION-05_v3-engine-and-codebase-fork.md | md | 3973 | 66 | 2026-06-18 | 2026-06-18 |
| 573 | specs/rfp-engine/intake/SESSION-06_engine-verdict-and-fork-resolution.md | md | 9939 | 107 | 2026-06-18 | 2026-06-18 |

> **Census note (minor, non-blocking):** the census `bytes` column matches all 27 files exactly. The
> census `created`/`modified` timestamps differ from on-disk `stat` by a few minutes / a recert push
> (e.g. ADR-0001 census = `2026-06-18T05:24:06` vs disk `05:15:50`) — this is the census-capture time
> vs. the file-write time and is expected (the census was generated after the files). No content drift.

> **SCOPE GAP (flagged):** the prompt names "all ADRs 0001–0018." **Only 10 ADR files exist on disk.**
> The numbering is sparse — **0005, 0007, 0008, 0009, 0010, 0011, 0012, 0015 do not exist as files** in
> `docs/adr/`. Confirmed by `find` and by census (only rows 254–263 carry `docs/adr/` paths). The gap is
> *intentional, not a loss*: the ADR numbers are reserved to align with the **Decision Log** (D1, D6, D7,
> D8, D2, D12, D3/G4, D18, etc. — each ADR's `Relates:` line maps it to a `D-xx`), and not every
> decision got promoted to a standalone ADR file. The missing numbers' substance lives in
> `project/03_DECISION_LOG.md` (e.g. the eight as-built ADR-001..008 in `specs/original-engine/BUILD_01`
> are a *different, internal* ADR series belonging to the legacy fork, not the project's `docs/adr` series).
> This audit documents the **10 ADR files that exist**, in full, as required.

---

# PART 1 — THE ADRs (`docs/adr/**`)

The project's Architecture Decision Records. Each is a markdown file `ADR-NNNN-slug.md`. They are the
**ratified, durable** architecture decisions (distinct from the rolling `project/03_DECISION_LOG.md`
D-numbers, which each ADR cross-references via its `Relates:` line). **Detailed WHY for the series:**
ADRs exist so that an architecture decision — and the *reasoning and the rejected alternatives behind
it* — survives context loss and personnel change; without them a future builder re-litigates settled
questions or silently drifts from a ratified call. Each ADR below is given fully: status, deciders,
relations, context, the decision, consequences, rejected options, and a **code cross-ref** (is it
reflected in the build? where? any drift?).

---

## ADR-0001 — Clean-room reconciliation: new codebase, existing DB schema as baseline

- **Number/Title:** 0001 — Clean-room reconciliation: new codebase, existing DB schema as baseline
- **Status:** Accepted (sponsor-ratified 2026-06-18)
- **Deciders:** Sponsor (Ed), PM, Solution Architect
- **Supersedes/relates:** Decision D1, dependency DEP-1, audit `04` D1

**CONTEXT (verbatim substance).** The audit established a real enterprise-grade governed store already
exists in the sponsor's private GitHub (the AS-BUILT: 63 tables, 67 CHECK constraints, 46
composite-identity FKs, a sealed calc-run spine). The naive "reconcile" reading would build *inside*
that existing repo, but the sponsor's constraint is explicit: *"the repo is in my github, but i dont
want it contaminating this build … have an agent read it and provide the db but keep it isolated from
current repo and codebase."* The existing codebase also carries the **wrong brain** (a min-cost
single-winner solver) and SQLite-shaped, partially no-op DDL. We want its **schema discipline and the
seven KEEP capabilities**, not its application code.

**DECISION.** Adopt **clean-room reconciliation** — four parts:
1. This repository is a **fresh, clean codebase**; no application code from the existing repo is ever
   copied in.
2. The existing AS-BUILT **schema is the migration baseline** — *schema only*, re-expressed as clean
   PostgreSQL and re-validated, landing under `db/baseline/` as our own artifact, not an import.
3. The old repo is an **isolated, read-only reference**. A single dedicated agent reads it in an
   isolated git worktree and emits exactly two things into `reference/` (clearly marked external,
   never wired into the build): (a) `reference/as-built-db/` — the extracted/validated schema + Alembic
   chain summary; (b) `reference/as-built-digest.md` — a knowledge digest. Nothing else crosses.
4. **Sample-file intake on demand** — squads request real artifacts; sponsor uploads to
   `reference/samples/` with provenance, never committed if they contain real commercial data without
   classification (Security squad owns the rule).

**ISOLATION PROTOCOL (the boundary).** The ADR draws the one-way boundary: existing repo → `reference/`
(quarantine) **informs** but is never imported → `db/baseline/` + `backend/` (our own code). Rule:
`reference/` is **input only**; **CI fails if `backend/` imports from `reference/`.**

**CONSEQUENCES.** Keep the as-built's rigor (composite FKs, calc-run spine, landed cost, eligibility,
VSP) by *re-modeling* cleanly, not inheriting. Drop the wrong brain + SQLite-isms by construction.
DEP-1 partially satisfiable today (we hold `specs/original-engine/BUILD_03_schema.sql`); full
reconciliation (ECLS, tests, migration history) waits on isolated access — **non-blocking** for Phase 0.

**DETAILED WHY.** This is the founding decision of the whole repo. Its priority is **longevity + drift
reduction** (decision rubric #1/#4): copying the legacy app would inherit a wrong brain and SQLite no-op
DDL permanently; re-modeling the schema cleanly keeps the hard-won data rigor while shedding the liability.
The quarantine boundary exists because the sponsor literally cannot let his private commercial repo
"contaminate" the build — it is a contractual/IP constraint, not a preference. Without ADR-0001 the team
would have no rule for what may cross from the old code, and the clean-room guarantee would silently erode.

**CODE CROSS-REF — REFLECTED, verified.**
- `reference/` quarantine dir **exists** with the exact prescribed contents: `as-built-db/`, `samples/`,
  `v3-engine/`, plus `incoming/`, `README.md`, `SAMPLE_REGISTER.md`.
- `db/baseline/` **exists** with `schema.sql` (64 tables — see note), `NAMING_MAP.md`, `README.md` —
  i.e. the schema landed as our own artifact, exactly as specified.
- The CI boundary check is real: `.github/workflows/ci.yml` line ~75 carries the comment "*Must FAIL the
  build if backend/ imports reference/*", enforcing rule #4. **No drift found.**

---

## ADR-0002 — Front-end stack: React / Next.js + TypeScript SPA

- **Number/Title:** 0002 — Front-end stack: React / Next.js (App Router) + TypeScript
- **Status:** Accepted (sponsor-ratified 2026-06-18); **late-phasing clause SUPERSEDED 2026-06-21**
- **Deciders:** Sponsor (Ed), PM, Solution Architect, Experience lead — **Relates:** Decision D6

**CONTEXT.** The mandate is an **enterprise-level web app**. The AS-BUILT front end is **Streamlit**,
which the intake flagged as "structurally a bad UI on a stateless engine" (Session 6, Addendum 2). An
enterprise system of record needs real auth/RBAC, multi-tenant context, a design system, and a clean
store/API ↔ view separation (ADR-001: UI is a view onto the store).

**DECISION.** **React + Next.js (App Router) + TypeScript**, SPA/SSR hybrid, a pure client of the
FastAPI backend. TypeScript end-to-end (types generated from backend OpenAPI); a component/design
system; auth/RBAC at the edge; tenant context threaded through every request. Originally **built last**
(Phase F).

**SUPERSESSION (2026-06-21, embedded in the ADR).** The "built last / Phase F" phasing is **superseded**
— the frontend was brought forward and is **operational** (login, dashboard, intake, alignment, awards)
per PM-007 (`project/07_AS_BUILT_PROCESS_AUDIT.md`). The **stack decision stands**; only the late-phasing
is superseded.

**CONSEQUENCES.** Clean API boundary; same store renders live and historic cycles identically. Streamlit
is **retired** (not hardened). DevOps plans a separate frontend build/deploy + SSR hosting.

**REJECTED.** Harden Streamlit — faster to a demo but weak on auth/RBAC/UX/governance; contradicts the
enterprise mandate.

**DETAILED WHY.** Drives by **full functionality** (rubric #2): an enterprise system of record needs a
real auth/RBAC/multitenant surface that Streamlit cannot give; a stateless-engine UI is structurally
capped at "bad" (the intake's own finding). Choosing Next.js/TS now (not later) is what made bringing
the frontend forward possible. Without this ADR the project risks shipping a Streamlit demo that fails
the enterprise mandate.

**CODE CROSS-REF — REFLECTED, verified (incl. the supersession).**
- `frontend/` exists as a Next.js app: `package.json` pins `"next": "^14.2.5"`, `"react": "^18.3.1"`,
  `"typescript": "^5.5.4"`; App Router dirs `frontend/app/`, `frontend/components/`, `frontend/lib/`.
- **Supersession confirmed in code:** the frontend is *built and operational* (its own dir tree +
  Dockerfile), not deferred — matching the 2026-06-21 supersession note.
- **Minor honest gap:** `package.json`'s `gen:api` script is still a **placeholder no-op** ("*at Phase F,
  generate the typed client from the backend OpenAPI contract … No-op stub for now*"). So the
  OpenAPI→TS codegen pledge of ADR-0002 is **not yet wired** even though the frontend shipped. Drift to
  note: typed-client generation is still a stub (the only stub-shaped item in this ADR's path).

---

## ADR-0003 — Execution model: plan-then-scaffold, backend-first

- **Number/Title:** 0003 — Execution model: plan-then-scaffold, backend-first
- **Status:** Accepted (sponsor-ratified 2026-06-18); **"D2 in-spike / engine stubbed" clause SUPERSEDED 2026-06-21**
- **Relates:** Decision D7, ADR-001 (UI last)

**DECISION.** Run the engagement as **plan-then-scaffold**: squads produce detailed plans, then stand up
Phase 0/A running ground in this clean repo — a validated PostgreSQL schema baseline, a
FastAPI/SQLAlchemy/Alembic backend skeleton, the multi-tenant + RBAC foundation, CI, and local infra
(docker-compose). Implementation proceeds **backend-first**; the Next.js front end is built last (Phase F).

**CONSEQUENCES.** Runnable ground from day one, but breadth follows the phase gates (roadmap PM-005).
Ratified decisions (D1, D6, D7) are binding; D2 treated as in-spike and **engine internals stubbed
behind an interface** until the spike resolves. The scaffold targets the **as-built schema baseline**
(ADR-0001), not the brief's thinner schema.

**SUPERSESSION (2026-06-21, embedded).** The "D2 in-spike / engine internals stubbed" language is
**superseded**: **D2 is RATIFIED and ADR-0006 accepted**; the clean-room **v3 engine is implemented and
operational** behind the frozen `run()` interface (5-factor scoring, 7 lenses, split allocation) — per
PM-007. The plan-then-scaffold / backend-first model itself **stands**.

**DETAILED WHY.** Drives by **error reduction + full functionality**: standing up a validated schema +
backend skeleton first gives "runnable ground from day one" so every later slice integrates against real
infra, not vapor; backend-first guarantees the UI is a view onto a proven store (pairs with ADR-0001/0002).
The engine-stub clause was the temporary bridge while D2 (which brain?) was still a spike; once ADR-0006
ratified the v3 brain, the stub was replaced by the real engine behind the *same frozen interface* — which
is exactly why the supersession was non-breaking.

**CODE CROSS-REF — REFLECTED, verified (incl. supersession).**
- Backend skeleton exists: `backend/app/` (FastAPI), SQLAlchemy domain models, Alembic chain
  (`backend/alembic/versions/` through `0019_pilot_run.py`), `docker-compose.yml`, `.github/workflows/ci.yml`.
- Schema baseline targets the **as-built** (64-table `db/baseline/schema.sql`), per the ADR.
- **Supersession confirmed:** `backend/app/engine/v3.py` exists with the real `run()` implementation
  (5 factors, scenarios A–G, `max_two_per_dc`) — the stub (`backend/app/engine/stub.py`) is retained as
  the deterministic fallback but the live brain is the real v3. **No drift.**

---

## ADR-0004 — Tenancy model: multi-tenant-capable, single-tenant-operated

- **Number/Title:** 0004 — Tenancy model: multi-tenant-capable, single-tenant-operated
- **Status:** Accepted (PM/Architect 2026-06-18; sponsor confirmed "one org")
- **Deciders:** PM, Solution Architect, Security lead; Sponsor — **Relates:** D8, Security/DevOps plans,
  mobilization §3/§6, intake Session 1 ("Clients" as reference entity)

**CONTEXT.** Security & DevOps flagged "tenancy topology" as their biggest open fork (shapes the data
model + deployment, expensive to change late). The sponsor reasonably had no view — this is a Kroger
sourcing tool for **one org**, not a product sold to external customers; the intake's "Clients" =
internal stakeholders/categories, not external paying tenants. No contractual/compliance need for
physical separation. Two axes: **tenant grain** (one org vs divisions vs external) and **isolation
topology** (shared-schema + RLS vs DB-per-tenant).

**DECISION.** **Build multi-tenant-*capable*, operate single-tenant** — four parts:
1. **One logical tenant** (Kroger Sourcing): a single seeded `ref.client` row.
2. **Keep `client_id` on every governed row** and **prepended to composite-identity FKs** — near-zero
   cost now, structurally future-proof; cheap insurance, not active multi-tenancy.
3. **Isolation = shared schema + Postgres RLS** as backstop pattern; tenant context from the **verified
   token only**, never the request body.
4. **DB-per-tenant explicitly deferred** — only revisited if a trigger fires.

**TRIGGERS THAT REVISIT (and only these).** Divisions must be cryptographically/contractually walled
off; a SaaS decision to sell externally; a Kroger compliance rule mandating physically separate DBs.
If any fires, the `client_id`-everywhere groundwork makes the move incremental, not a rebuild.

**CONSEQUENCES.** Unblocks Security (RBAC/RLS policy set) and DevOps (shared-schema deploy, one DB). No
per-tenant overhead now. The model stays honest (no multi-tenancy claimed that isn't built, but the door
isn't foreclosed).

**DETAILED WHY.** Drives by **longevity + error reduction**: tenancy is the most expensive thing to
retrofit, so the ADR pays the near-zero cost of `client_id`-everywhere as insurance while *not* building
the operational complexity of true multi-tenancy that one org would never use. Taking tenant context only
from the verified token is a security invariant (never trust the body). Without this ADR, the team would
either over-build DB-per-tenant (wasted effort, more error surface) or hard-code single-tenant and face a
rebuild if Kroger ever divisionalizes.

**CODE CROSS-REF — REFLECTED with a DELIBERATE, DOCUMENTED PHASING (drift-to-note).**
- `client_id` **is** present in `db/baseline/schema.sql`, `db/baseline/README.md`, `NAMING_MAP.md`.
- **Important nuance / partial:** the baseline schema explicitly **defers the full `client_id` weave** to
  a later migration. `db/baseline/schema.sql` (~line 24): "*TENANCY (M10, NOT M0): ADR-0004's broad
  client_id weave across all 63 tables is a LATER migration (M10 / E-03). M0 keeps client_id ONLY where
  it already exists: ref.client (the tenant root) and ref.commodity (the tenant-scoping demonstrator).*"
- **Verdict:** ADR-0004's *intent* (capable-not-operated, RLS-ready, `ref.client` root) is reflected;
  the **"`client_id` on every governed row + prepended to all composite FKs" part is staged to M10/E-03
  and not yet applied to all tables.** This is consistent with the ADR (the weave is "cheap insurance"
  done incrementally) but a builder must know it is **not yet universal in the baseline.** Flagged as a
  partial/phased item, not a contradiction.

---

## ADR-0006 — Engine brain: adopt v3's five-factor scoring + split allocation

- **Number/Title:** 0006 — Engine brain: adopt v3's five-factor scoring + split allocation
- **Status:** Accepted (sponsor-ratified 2026-06-18 — "D2 Spike ok!")
- **Deciders:** Sponsor (Ed), PM, Solution Architect, Engine lead — **Relates:** D2, spike
  `project/squads/engine-domain/SPIKE_D2_engine.md`, gaps G1/G2, ADR-0001 — **Supersedes:** the as-built's
  exact min-cost single-winner solver as *the* engine

**CONTEXT.** The two original codebases carried different brains. The as-built repo implemented an **exact
minimum-cost, single-winner solver** (Scenario A). The verified `rfp_analysis_engine_v3.py` implements
**decision-support**: five banded factors (Price 0.35, Coverage 0.25, Historical 0.20, Z-Risk 0.10,
Continuity 0.10) → a recommendation score, with split (allocation) awards via `max_two_per_dc`. The real
evidence — the leadership sign-off deck splitting DCs across suppliers, and cost being only 35% of the
decision — backs v3. The Engine spike recommended v3 (Option A); the sponsor ratified it.

**DECISION.** **Adopt v3 engine logic as the brain**, lifted clean into a library behind the frozen
`run(cycle_id, round_code, config) -> run_id` interface (ADR-0001: logic only, no Excel-formatting,
never imported from the isolated repo):
1. **Scoring** — `eng.bid_score` with the five banded factors + weighted composite. Cost is 35%, not 100%.
2. **Scenarios** — the seven lenses A–G. **Scenario A becomes the "lowest-cost reference" lens** (a
   context benchmark), not the award mechanism. The old min-cost solver is retired into this lens.
3. **Split allocation** — `eng.scenario_award` carries one row per awarded supplier per cell, each with
   `volume_share` and `cap_breach_flag`; `max_two_per_dc` is the default cap, **permit-not-force** (a
   cell defaults to one supplier but may split when its per-DC/per-lot splittable flag is set),
   capacity-constrained.
4. **Decision-support only** — engine computes/scores/compares/proposes; a human selects. Never
   auto-asserts an award; the `BANNED_DECISION_WORDS` guard stays on the recommendation surface.

**CONSEQUENCES.** G1 (split) + G2 (scoring) ship together as one engine increment, after the Phase-B
real-data pilot, behind `split_award` / `scenario_lenses` feature flags. The frozen engine **interface
does not change** — only the implementation behind the deterministic stub is replaced — so the store/API/
tests already built remain valid. Validation is by **golden-master reproduction** (reproduce v3's
verified scoring + split on a known input/output pair — the top sponsor ask). The as-built's eligibility
(7 gates) + landed-cost (5 modes) layers are **kept** and feed the scorer.

**DETAILED WHY.** This is the single most consequential domain decision (rubric #2 full functionality +
#3 error reduction). The legacy min-cost solver *automates the one judgment the sponsor deliberately makes
by hand* — picking among cost + supply security + quality + incumbent + risk — which is provably wrong
against his real artifacts (split awards on every sign-off slide; cost is only 35%). Adopting v3 behind a
**frozen interface** is what let the engine be swapped without breaking the store/API/tests. The
`BANNED_DECISION_WORDS` guard exists so the machine never says "awarded/winner" — it proposes, the human
decides — preserving the human-in-the-seat invariant that is core to the product's correctness.

**CODE CROSS-REF — REFLECTED, verified in detail (the strongest cross-ref in this slice).**
- `backend/app/engine/v3.py` — real `run()` (line 75); `max_two_per_dc` split allocator (line 11);
  per-DC×TF `cap_breach` flags wired through every scenario (lines 212–271).
- `backend/app/engine/interface.py` — the **exact** five weights match the ADR: `weight_price=0.35`,
  `weight_coverage=0.25`, `weight_historical=0.20`, `weight_zrisk=0.10`, `weight_continuity=0.10`
  (lines 140–144). Premium bands match too: `comparable=0.03`, `defensible=0.07`, `max=0.12` (147–149).
- **Seven lenses A–G** present: `ScenarioCode` enum (interface.py 36–45): A=lowest-cost reference,
  B=risk-adjusted rec, C=incumbent defense, D=max-N per DC, E=exclusion, F=custom override,
  G=preferred supplier — i.e. exactly the ADR's mapping, with A as the *reference* lens.
- `BANNED_DECISION_WORDS` guard exists: `backend/app/engine/guards.py` (+ enforced in `v3.py`, asserted
  by `backend/tests/engine/test_engine_invariants.py`). **No drift. Fully reflected.**

---

## ADR-0013 — Pricing: period-grain storage, setup-file-driven display

- **Number/Title:** 0013 — Pricing: period-grain storage, setup-file-driven display
- **Status:** Accepted (sponsor-raised 2026-06-18)
- **Deciders:** Sponsor, PM, Solution Architect, Product, Engine lead — **Relates:** D12; intake Session 1
  "locked truths" #1 (period grain) & #5 (setup file drives the read); D3/G4; D9 (one model per RFP)

**CONTEXT.** From the intake: *"Price and components are preset; the system knows from the setup file how
to display them when calling an RFP, live or historic."* Separates two concerns the original specs
blurred: **how pricing is STORED** (normalized, period grain, as components) vs **how pricing is
DISPLAYED** (driven by the cycle's setup file, so the same facts render consistently live or historic).
This separation is what makes "open last cycle" render correctly and lets one engine handle fixed/index/
full-year/period-by-period deals without forking.

**DECISION — Store period-grain facts; render through the setup file.**
- *Storage (facts):* priced grain = **supplier × lot/item × DC × period × price** (period a first-class
  dimension, never a forked workbook). Prices stored as **components** (FOB, freight, delivered,
  cross-dock, VegCool, discount; for index basis, basis/market reference/adder + QDP). **Fixed** deals
  repeat the agreed price across periods. **Index** deals store components and the effective price
  **resolves** (computed), never a frozen number — *worked example: Visalia onions priced market mid −
  discount; store holds {market reference/mid, discount}, price resolves to mid − discount; FOB falls
  out.* **Period-by-period** deals carry their own price/components per period (no special case). One
  pricing table; the **basis** decides which columns carry weight. The double-subtraction guard
  (`no_double_discount`) is enforced **in the store**.
- *Display (render contract):* the **setup file** (`cyc.cycle` pricing declaration: basis, cadence —
  FULL_YEAR / SEASONAL / TIMEFRAMES(n) / PERIOD_BY_PERIOD(13) / QUARTERLY / MONTHLY / WEEKLY — which
  components show, the safeties) tells the system **how to render** stored pricing. **Same render live
  or historic** because the setup file is stored *with* the cycle — the concrete mechanism behind "open
  last cycle."

**CONSEQUENCES.** Clean split: `bid.*` holds period-grain component facts; `cyc.*` holds the declared
render contract; a view/renderer composes them. The engine reads facts uniformly regardless of
basis/cadence; presentation differences are config, not code forks (kills the Colored-Potato per-timeframe
clone). Historic fidelity is structural. Pairs with D11 (savings baseline) and the safeties (D3/G4).

**REJECTED.** Storing a single resolved price per line (loses index reconstruction + contracted-vs-effective
+ component audit). Letting the UI/workbook layout define presentation per cycle (the bespoke-fork failure;
breaks "same render live or historic").

**DETAILED WHY.** Drives by **error reduction + drift reduction**: storing the *resolved* number would
make index deals unreconstructable and break the contracted-vs-effective audit story; storing *components*
+ a *declared render contract* makes the same facts replayable identically forever. This is the structural
answer to the #1 user problem (historical blindness): "open last cycle" works because the cycle *is* its
setup file. Without ADR-0013 you regress to bespoke per-cycle workbooks (the exact failure mode the system
exists to kill).

**CODE CROSS-REF — REFLECTED.**
- Component storage + market reference present in `db/baseline/schema.sql`:
  `perf.commercial_market_reference` (market_reference_price/mid, collar_floor/cap — lines ~1368–1394),
  the commercial pricing layer (FOB/freight/delivered/cross-dock components per the original-engine
  commercial layer carried into baseline).
- Cadence vocabulary surfaces in the pilot setup template (`backend/app/pilot/setup_template.py`) and the
  cyc domain (`backend/app/domain/cyc/`). The `no_double_discount` guard is a schema CHECK (per the spec's
  `bid_price` model carried into baseline). **Reflected; the render-contract/cadence is config-driven as
  specified.**

---

## ADR-0014 — Pricing safeties are contractual execution-layer terms, not engine inputs

- **Number/Title:** 0014 — Pricing safeties are contractual execution-layer terms, not engine inputs
- **Status:** Accepted (sponsor-specified 2026-06-18); tolerance-band + collar mechanics later CONFIRMED
  via the sponsor's `xl-roma-pricing-backtest.html`
- **Deciders:** Sponsor, PM, Solution Architect, Engine lead, Product — **Relates:** G4, D3, D12/ADR-0013,
  E-28 (contracted-vs-effective), award freeze-and-layer (G3) — **Supersedes the framing of:** "make the
  safeties executable in the engine"

**CONTEXT.** The intake called the five pricing safeties "the real product," and the original specs stored
them as inert parameters. The PM's prior framing assumed the *engine* fires them. **The sponsor corrected
this:** safeties are **contractual terms, not bid terms.** They **incentivize suppliers to participate**
(shared risk) and **do not affect the scoring/allocation math.** They govern how the awarded price **moves
over the life of the contract** (execution); price changes are recorded against the frozen award
(freeze-and-layer).

**DECISION.**
1. Safeties declared at **kickoff** (the setup file) as **contract terms** on the cycle/award, configurable.
2. **The engine (scoring + allocation) does NOT consume them** — out of the solver entirely (keeps the
   engine clean; removes the old "fire the safeties in the engine" scope).
3. A **contract/execution module** applies/records reprices when a safety triggers, post-award. Formulaic
   safeties computed/visualized; discretionary ones record a human reprice decision. Every move lands in
   `award_layer` (date-stamped, who/why); raw award never overwritten.
4. They feed **contracted-vs-effective** (E-28) and the savings baseline (D11).

**THE FIVE SAFETIES (mechanics as specified — all windows/cadences/bands set per-RFP; the figures are
illustrative defaults).** *Governing objective: let the awarded price move up when warranted (hike) and
back down (drop) within governed bounds — controlled, bidirectional flexibility so a deal can breathe
without reopening the contract.*
1. **Collar (cap/floor)** — both fixed and market/index. **Cap** = how far up Kroger lets the price go in
   a hike (Kroger's upside protection). **Floor** = the **supplier's** downside protection (Kroger willing
   to go to 0; the floor exists for the supplier). Params: `cap`, `floor`.
2. **Rolling midpoint** — market/index. Every **8 weeks**, take the midpoint of the trailing **4 weeks**;
   that midpoint becomes the price for the next 8 weeks. Params: `lookback_weeks` (4), `reset_cadence_weeks` (8).
3. **Tolerance band** — anomaly reprice, works with the collar. Price moves **outside the band** and
   **persists ≥ 2 weeks** → **temporary reprice to market midpoint, bounded below the collar cap, for 2
   weeks**, then review. Params: `band`, `min_duration_weeks` (2), `reprice_window_weeks` (2).
4. **Disaster trigger (escalator)** — discretionary. A generalized market disaster spikes price → Kroger
   **evaluates and reprices up** (human judgment). **Temporary:** reverts to contract after the disaster.
5. **Inverse disaster trigger (de-escalator)** — discretionary mirror: generalized drop → reprice down;
   same "revert to contract" invariant.
*Formulaic vs discretionary:* #2/#3 computable/auto-visualizable; #1 a bound on any move; #4/#5
human-evaluated with a hard "revert to contract" rule. System computes/proposes/records; a human approves
discretionary moves (author≠approver, draft→sent gate).

**CONFIRMED (2026-06-18, via `xl-roma-pricing-backtest.html`).** Tolerance-band mechanic CONFIRMED
(±band% corridor, HTML default **15%**, around a scheduled-reset base — HTML 13-wk reset / 4-wk trailing,
per-RFP configurable; a print outside starts a clock, 2 consecutive weeks confirm an interim reprice with
1-wk lag, 2 weeks back inside revert). Collar asymmetry CONFIRMED (Kroger-optional — fires only when it
*lowers* Kroger's price; cap protects Kroger, floor is the supplier's; plus a re-mark rule for runaway
second legs). Market feed identified: USDA **`FVWTRDS-1662`** → **DEP-6** (closes "where does the market
reference come from"). All windows still per-RFP-flexible.

**CONSEQUENCES.** **Engine unaffected** — no safety logic in scoring/allocation; the pilot is independent
of safeties. Safeties are a **Phase-E+ contract-execution feature**. Data model: `cyc.cycle_safety`
stores declared terms+params; `awd.award_layer` records actual reprices; a future execution/monitoring
surface computes formulaic moves + flags disaster events. Strengthens E-28.

**OPEN / TO CONFIRM.** Final per-RFP default values at template time.

**DETAILED WHY.** This is a *correction of a wrong design* (rubric #3 error reduction): the prior framing
would have polluted the scoring/allocation math with safety logic, breaking the engine's golden-master
reproducibility and conflating contract execution with bid evaluation. The sponsor's insight is that
safeties are how a deal *breathes post-award*, not how a bid is scored — so they belong in the
execution/freeze-and-layer layer, recorded as `award_layer` rows. Keeping them out of the solver is what
preserves engine determinism (and lets the pilot validate the engine without them).

**CODE CROSS-REF — REFLECTED (declaration layer built; execution module is the specified future phase).**
- Safety **declaration** is wired into the pilot setup template: `backend/app/pilot/setup_template.py`
  line ~285 — a "SAFETIES (optional, ADR-0014) — collars / cadence / tolerances" section with explicit
  `Collar Cap` / `Collar Floor` money fields. So safeties are captured at kickoff as **contract terms**,
  exactly per the ADR.
- `setup_ingest.py` (line ~220) explicitly distinguishes engine knobs from `cyc.cycle_safety` ("*distinct
  from cyc.cycle_safety, the [safety terms]*") — i.e. the **engine does not consume them**, matching
  decision #2.
- `cyc.cycle_safety` modeled (`backend/app/domain/cyc/models.py` references migration
  `0003_cyc_cycle_safety.py`); `collar_floor/collar_cap` live in `perf.commercial_market_reference`.
- **Correctly-deferred per the ADR:** the **post-award execution/monitoring module** that *fires*
  formulaic safeties + flags disasters is the named Phase-E+ feature and is **not yet built** — this is
  *expected*, not drift. Declaration ✔, execution = future. Flagged so a reader knows the safeties are
  *stored* but not yet *computed/visualized live*.

---

## ADR-0016 — Strategy-agnostic platform: strategies are first-class, developed and run

- **Number/Title:** 0016 — Strategy-agnostic platform
- **Status:** Accepted (sponsor-stated 2026-06-18) — **foundational**
- **Deciders:** Sponsor, PM, Solution Architect, Engine lead — **Relates:** D18; D17; ADR-0006; D9/D12/D13;
  intake locked-truth #8 (process per-cycle); the engine's commodity-agnostic CONFIG + weight presets;
  the as-built `scenario_config_version` / `metric_definition_version` / `engine_release` version pins

**CONTEXT.** The uploaded reference files are each a **single-strategy mold** — one RFP's particular
approach baked into a spreadsheet. The risk is building the *system* as a hardcode of one such mold. The
sponsor's principle: **we are building a strategy-agnostic platform on which strategies are developed and
run.** The v3 engine already points this way ("commodity-agnostic," CONFIG-driven, "change Active Weights
and re-run"); generalize from *commodity*-agnostic to *strategy*-agnostic. **Commodity-agnostic ⊆
strategy-agnostic.**

**DECISION.** **A `Strategy` is a first-class, named, versioned, reusable configuration object** that
parameterizes how a cycle is set up, analyzed, and awarded. Nothing strategy-specific is hardcoded in
engine/store/UI. A strategy comprises the levers: **objective(s)** (savings/continuity/quality/
diversification/strategic, multi with primary); **pricing model** (basis, cadence,
baseline-then-negotiate, volume split + the safeties, per-RFP); **scoring** (weights/preset — Balanced /
Price Focus / Coverage Focus / Risk Averse / Custom — or fully custom); **award constraints**
(max-suppliers-per-DC, single-supplier-per-lot, global/per-lot premium thresholds, coverage eligibility
floor); **scenario lenses to run** (A–G + custom/preferred/exclusions); **process rail/steps** (per-cycle
timeline from the setup file, not a fixed 10/13-stage hardcode); **preferences/exclusions**. Strategies
are **developed** (composed, saved as reusable templates/presets, versioned so a past cycle reproduces
under its exact strategy version) and **run** (bound to a cycle; the same bids can be re-run under
different strategies to compare). The reference corpus informs the **primitives**, never *is* the system.

**CONSEQUENCES.** Elevate the as-built version pins + the engine's CONFIG presets into a first-class
**`strategy` (template) + per-cycle strategy binding**. The platform must let users **define, save,
version, apply** strategies and A/B them on the same cycle data. Reusable templates/presets are a product
feature. Every run records the **strategy version** → reproducibility + faithful historic render. Guards
against the #1 failure mode (digitizing one strategy's spreadsheets); reinforces D17.

**REJECTED.** Hardcoding any single strategy's weights/lenses/steps/pricing into the engine or UI.

**DETAILED WHY.** Drives by **longevity + drift reduction**: the #1 way this build could fail is by
quietly becoming a digital copy of *one* RFP's spreadsheet. Making the strategy a first-class versioned
object means the platform outlives any single sourcing approach and that a 2026 cycle still reproduces
under its 2026 strategy version even after the house strategy evolves. Without ADR-0016 the levers leak
into hardcode and the platform ossifies around whatever the first cycle happened to do.

**CODE CROSS-REF — PARTIALLY REFLECTED (intent honored via config; the *named, versioned `strategy`
object* is not yet a dedicated table — drift-to-note).**
- The **primitives** are first-class and config-driven: `EngineConfig` (interface.py) carries weights,
  presets (`COVERAGE_FOCUS` etc., line ~53), premium bands, max-suppliers-per-DC, lens selection — i.e.
  the levers are NOT hardcoded in the engine (the core of ADR-0016 ✔).
- The as-built **version pins** (`scenario_config_version`, `metric_definition_version`, `engine_release`)
  are carried into the baseline `eng` schema.
- **Not-yet-materialized:** a **dedicated `strategy` (template) table + per-cycle strategy binding** does
  not yet exist in `db/baseline/schema.sql` (grep for a `strategy` table returns nothing). The reusable
  *named/saved/versioned strategy template* product feature (define/save/version/apply + A/B on the same
  cycle) is **not yet built as a first-class object** — it currently lives as per-cycle/per-run config +
  version pins. **Flagged: ADR-0016's spirit (no hardcoded strategy) is met; its concrete `strategy`
  object is a forward item.** This is the most "aspirational vs built" of the ADRs in this slice.

---

## ADR-0017 — Hosting platform: GCP (Cloud Run + Cloud SQL for PostgreSQL)

- **Number/Title:** 0017 — Hosting platform: GCP (Cloud Run + Cloud SQL for PostgreSQL)
- **Status:** Accepted (2026-06-21) — sponsor delegated the choice to the decision methodology with
  constraints
- **Deciders:** Sponsor, PM, Solution Architect, DevOps — **Relates:** DEP-4 (hosting+IdP); ADR-0003 (two
  runtimes); ADR-0002 (Next.js/Node 20, Python 3.12); D30 (per-run isolated DBs); DEP-6 (USDA key →
  secret store); the CI image build; gaps G-C/G-J (RBAC/tenancy → future IdP)

**CONTEXT.** The platform is ready to choose where it runs (resolving the hosting half of DEP-4). System
is FastAPI + SQLAlchemy + Alembic + **PostgreSQL 16** (governed system of record incl. audit hash-chain) +
a Next.js console; CI already **builds a container image**. Sponsor's frame: **hard exclusion — not
Azure**; **"best for longevity"** (durable vendor, low lock-in, clean exit); **budget "modest monthly OK
for reliability"** (reliability over cheapest); standing principle **full functionality with least margin
for error**.

**DECISION.** **Host on GCP: web console as a container on Cloud Run, backed by Cloud SQL for PostgreSQL
16, with Secret Manager for secrets and Artifact Registry for images.**
- **Compute — Cloud Run** runs the CI-built image directly (no rearchitecting), **scales to zero**
  between pilot runs (near-zero idle), `min-instances=1` as the "modest monthly" no-cold-start dial.
- **Database — Cloud SQL for PostgreSQL 16**, managed, **automated backups + PITR** (the durability the
  governed record + audit hash-chain require). The MCP harness's **per-run isolated DBs (D30)** are
  separate logical databases on the same instance, keeping the two-runtime model intact.
- **Secrets — Secret Manager** for the USDA MARS key (DEP-6), session-signing key, vault git credentials.
- **Images — Artifact Registry**, deployed by digest from CI on push to `main`.
- **Identity (IdP half of DEP-4) — deferred.** Phase 1 single-operator keeps own auth + TOTP 2FA; when
  tenancy/RBAC (G-C/G-J) is built, **Google Identity Platform** is the native path (not committed now).

**METHODOLOGY.** A weighted criteria table compares **A. GCP** vs **B. AWS (App Runner/Fargate + RDS)** vs
**C. PaaS (Render/Fly.io)** across longevity/low-lock-in, not-Azure, least-margin-for-error/ops-simplicity,
managed-Postgres durability, cost at pilot scale, fit to CI image + 2 runtimes, future IdP. **GCP wins**
on the two highest-weighted (longevity + least-margin-for-error) without giving up durability/cost, and
runs the container with least change.

**CONSEQUENCES.** DevOps stands up Artifact Registry, a Cloud SQL PG16 instance (private IP + backups/PITR),
Cloud Run services, Secret Manager entries, and the `main`-branch build-push → deploy-to-staging
continuation of `ci.yml`. `DATABASE_URL` stays the single connection var (only host/creds differ). DEP-4
hosting half = **resolved (GCP)**; IdP half stays deferred. Prod = **manual promotion** of the
staging-validated digest (workflow_dispatch behind environment approval), never automatic. Low exit cost:
a move to AWS is a redeploy + a Postgres dump/restore, not a rewrite.

**REJECTED.** Azure (hard-excluded). AWS (equally durable, **documented fallback**, but loses on ops
simplicity + idle cost for a pilot — App Runner has no true scale-to-zero, Fargate/ECS heavier). Managed
PaaS Render/Fly.io (lowest cost/simplest but **fails "best for longevity"** — smaller-vendor continuity
risk + weaker IdP/RBAC path). Self-managed VMs/k8s (max control, max ops surface; violates
least-margin-for-error for a one-operator pilot).

**DETAILED WHY.** Drives explicitly by the sponsor's **longevity + least-margin-for-error** frame: the
governed system of record (with an audit hash-chain) needs managed Postgres durability (backups + PITR)
above all, and a one-operator pilot cannot absorb heavy ops surface. Cloud Run was picked because it runs
the *already-built CI image* unchanged (zero rearchitecting) and scales to zero (cost discipline without
sacrificing the "modest monthly" reliability dial). The low-lock-in design (standard container + standard
Postgres) keeps the rejected AWS path a cheap future switch — the decision is reversible, which is itself
a longevity hedge.

**CODE CROSS-REF — REFLECTED as a documented target (provisioning is the named future step, consistent
with the ADR's own "not yet provisioned" status).**
- `deploy/gcp/README.md` **exists** (the GCP deployment doc), and GCP/Cloud Run is referenced across
  `project/squads/platform-devops/PLAN.md`, `project/NO_FILE_STORAGE_PLAN.md`, `VAULT.md`.
- The CI image build is real: `.github/workflows/ci.yml` builds a container; backend + frontend
  `Dockerfile`s exist; `docker-compose.yml` for local infra. The `main`-only build-push+deploy stanza is
  the commented continuation the ADR describes ("*Push to main: … image build-push + deploy-to-staging —
  those land when [enabled]*").
- **Expected non-build:** Cloud Run / Cloud SQL / Artifact Registry / Secret Manager are **not yet
  provisioned** — the ADR itself says GCP is "*decided … but not yet provisioned*." So this is a decided
  target with the deploy scaffolding present, not a contradiction. No drift.

---

## ADR-0018 — Storage model: DB is the system of record; deliverables render on request, uploads not persisted

- **Number/Title:** 0018 — Storage model (DB authoritative; render-on-request; uploads not persisted) —
  and NO storage change before the live RFPs
- **Status:** Accepted (2026-06-21); **IMPLEMENTED (2026-06-21)** — sponsor **LIFTED the timeline
  deferral** ("forget the timeline, get it working fully") and made no-server-side-file-storage a HARD
  requirement before the live RFPs. All 6 slices landed + reviewed (commits `15d957e` s0 · `847140b` s1 ·
  `c4507a8` s2 · `a73fa3a` s3 · `3c2074b` s4 · `e12e26a` s5 · `ed2d26a` s6); **247 tests pass**, migration
  `0019_pilot_run` round-trips. The §3 "do not change before the live RFPs" clause is **superseded**.
- **Deciders:** Sponsor, PM, Solution Architect — **Relates:** ADR-0017 (GCP/Cloud Run stateless compute);
  ADR-0003 (two runtimes); D30 (per-run vault + isolated DB); E-39 (canonical formula registry —
  deterministic renders); E-31 (gate-closure backup export); `norm.source_artifact`; As-Built §16

**CONTEXT.** Question: are output files generated **on request** or **stored server-side**, and should
uploads persist after ingest? *Today (at writing):* generated deliverables (alignment workbook,
booking/supplier guides, post-award docs) are written to the run's `outputs/` folder on disk; uploads
kept in `inputs/`; downloads read bytes off disk; the whole "vault" is git-committed and (on web)
auto-pushed with a `run_data.json` + a `db/` DB snapshot. Sponsor's principle: **DB is the single source
of truth — render deliverables on request, never store them; don't keep uploaded files (re-extract via
the standard template + DB).** Decisive constraint at the time: **two live RFPs start this coming week**,
running on the **MCP harness** (per-run isolated DB + vault); GCP decided but not yet provisioned.

**DECISION (by the Decision Doctrine, PM-008).**
1. **Strategic target — ratified.** The **PostgreSQL database is the system of record.** All generated
   deliverables **render on request and are not persisted**; uploads are **streamed → ingested → not
   retained as derived copies.** Sound because the generators are already **pure, deterministic
   DB-renders** (E-39 → byte-identical regeneration).
2. **Delivery binding — Category B, with the Cloud Run deployment, AFTER the live RFPs.** The refactor is
   an enhancement within the existing architecture, and Cloud Run statelessness *requires* it anyway
   (local disk doesn't survive scale-to-zero). Ships **with** the GCP web-console deployment.
3. **Pre-live-RFP — change nothing now.** The two live RFPs run on the harness, whose **per-run vault
   (files + git history + DB snapshot) is RETAINED** — the run's portable, recoverable record across
   ephemeral boxes (D30), a **safety feature**, not tech debt. Refactoring a working, recovery-critical
   storage layer the week of go-live is the highest-margin-for-error move available → don't.
4. **One open sub-decision (resolve at deployment).** When the web console goes stateless, the
   **raw-as-received *flexible* upload** is the only governed input not reconstructable from the DB.
   **Recommended:** retain *that one artifact class* in **object storage (GCS)** for audit/dispute (its
   `norm.source_artifact` SHA-256 needs something to verify against), render everything else on request.
   *Sponsor leans pure-discard;* the single audit-safety exception — confirm at deployment. E-31's
   gate-closure export is likewise an intentional user-initiated snapshot → GCS, never the request path.

**CONSEQUENCES.** *This week:* live RFPs proceed on the proven harness/vault; confirm autopush/rehydrate
as a live-run readiness check. *At Cloud Run provisioning (the B work):* download endpoints
generate-and-stream from Cloud SQL; the run-zip builds every deliverable into an in-memory zip on request;
`outputs/` persistence removed; uploads stream straight to ingest; the retained raw flexible artifact (if
kept) + E-31 exports go to a GCS bucket. `DATABASE_URL` stays the single connection var. Low risk: every
output is a deterministic DB-render (E-39) → generate-on-request yields the same bytes as the stored files.

**REJECTED.** Refactor storage before the live RFPs (highest margin for error; strips the harness recovery
net). Persist generated outputs on disk under Cloud Run (doesn't survive statelessness; redundant given
deterministic renders). Discard the raw flexible upload too (loses the only irreproducible governed input;
held as the open sub-decision).

**DETAILED WHY.** The ADR is two decisions in one (rubric: #2 full functionality vs #3 error reduction,
adjudicated by timing). The *strategic target* (DB-authoritative, render-on-request) is the no-file-storage
contract from CLAUDE.md ABSOLUTE REQUIREMENT #4 — it's sound *because* every render is deterministic
(E-39), so discarding stored copies loses nothing. The *original timing* clause was pure error-reduction:
do not refactor a recovery-critical storage layer the week two live RFPs go out, for zero benefit that
week. The sponsor **later overrode the timing** ("forget the timeline, get it working fully") and made it a
HARD pre-live requirement — so the implementation was pulled forward. Without ADR-0018 the app would write
files to disk (violating the no-storage contract) and break under Cloud Run statelessness.

**CODE CROSS-REF — REFLECTED, IMPLEMENTED, verified (the most heavily-implemented ADR in this slice).**
- Migration **`backend/alembic/versions/0019_pilot_run.py` exists** (run identity in `pilot.run`), matching
  the ADR's "run identity in `pilot.run`."
- The discriminator is real: `PilotService(db_runs=True, persist_outputs=False)` via
  `backend/app/api/v1/pilot_common.py::service()`; the web console writes **zero** files (uploads stream to
  ingest; deliverables render on request) while **the MCP harness is unchanged** (`db_runs=False,
  persist_outputs=True`) and **kept as the live-run verification oracle** — exactly the ADR's two-runtime
  split. Files: `backend/app/pilot/service.py`, `pilot/deliverables.py`, `pilot/run_repo.py`,
  `pilot/models.py`, `pilot/backfill_runs.py`; API `backend/app/api/v1/runs.py`, `bids.py`.
- The "no server-side file storage" requirement traces directly to **CLAUDE.md ABSOLUTE REQUIREMENT #4**
  and `project/NO_FILE_STORAGE_PLAN.md`. **No drift; the supersession (implemented-now) is real in code.**

### ADR cross-ref summary (reflected-in-code scorecard)

| ADR | Decision in one line | In code? | Where / note |
|---|---|---|---|
| 0001 | Clean-room: new code, schema baseline, `reference/` quarantine, CI boundary | **Yes** | `reference/`, `db/baseline/`, ci.yml import-guard |
| 0002 | Next.js + TS SPA, pure FastAPI client (brought forward) | **Yes** (1 stub) | `frontend/` Next 14/React 18/TS 5; `gen:api` still a no-op stub |
| 0003 | Plan-then-scaffold, backend-first (engine no longer stubbed) | **Yes** | `backend/app/`, alembic chain, real `v3.py` |
| 0004 | Multi-tenant-capable, single-tenant-operated; `client_id` insurance | **Partial/phased** | `ref.client` root; full `client_id` weave deferred to M10/E-03 |
| 0006 | v3 brain: 5 factors (.35/.25/.20/.10/.10), 7 lenses A–G, split alloc | **Yes (exact)** | `engine/v3.py`, `interface.py`, `guards.py`, tests |
| 0013 | Period-grain component storage; setup-file render contract | **Yes** | commercial pricing layer + cyc render contract |
| 0014 | Safeties = contract terms, OUT of the engine; declared at kickoff | **Decl. yes / exec future** | `setup_template.py` safeties block; `cyc.cycle_safety`; exec module = Phase-E+ |
| 0016 | Strategy = first-class, named, versioned, reusable object | **Partial** | levers config-driven (no hardcode); dedicated `strategy` table not yet built |
| 0017 | GCP Cloud Run + Cloud SQL PG16 | **Decided/scaffolded** | `deploy/gcp/`, ci.yml image build; not yet provisioned (per ADR) |
| 0018 | DB authoritative; render-on-request; uploads not persisted | **Yes (implemented)** | `pilot.run` (mig 0019), `PilotService(persist_outputs=False)`; harness kept |

---

# PART 2 — SPECS (`specs/**`)

Two spec packages, **same five-document shape** (README + System Overview & ADRs + Data Model + schema.sql
+ Tech Spec), deliberately so they can be **diffed side-by-side**:
- **`specs/original-engine/`** — the **FORKED legacy as-built spec.** Documents the inherited, half-built
  codebase *as it actually exists* (descriptive, not aspirational). This is the legacy repo ADR-0001 keeps
  isolated; its schema is the migration baseline. **It is NOT our build** — it is the reference we
  re-modeled from.
- **`specs/rfp-engine/`** — **our build spec** (from the six-session intake) + the `intake/` requirement-
  capture history.

**Relationship to our build (stated once):** the original-engine spec is the *AS-IS* inventory (what to
keep / relax / add); the rfp-engine spec is the *TO-BE* we built. ADR-0001 (clean-room) is the bridge: we
re-expressed the original-engine **schema** as our `db/baseline/schema.sql` and built the rfp-engine
**design** on top, adopting the v3 brain (ADR-0006) instead of the legacy min-cost solver. The live
`db/baseline/schema.sql` is the **merge** of both — 64 tables (the original-engine's 63 governed tables +
the pilot/tenant additions), using the rfp-engine's 8-schema layout (`ref/norm/cyc/bid/eng/awd/perf/audit`).

---

## 2A — `specs/original-engine/` (the forked legacy as-built spec)

### original-engine/BUILD_00_README.md
- **Path:** `specs/original-engine/BUILD_00_README.md` (72 lines)
- **What:** Index + reading order + the "honest reality" framing for the legacy as-built package.
- **DETAILED WHY:** Establishes the package as **descriptive, not aspirational** — every table/service/rule
  named is present in the running code (`main @ 8d96004`, Alembic head `j29e0cpm01`, 14 migrations, 63
  tables, SQLAlchemy 2.0 + Streamlit, synthetic SQLite, no real data). The WHY for its existence: it must
  be **diffable against the brief** to author a final spec — so it's cut into the brief's five-doc shape.
  Carries the load-bearing rule "*the brief is ground truth where the two disagree*" and a **status legend**
  (BUILT / SCAFFOLD / CONTRACT-ONLY / PARKED / NOT BUILT) used package-wide.
- **OUTLINE:** Index table (docs 0–4) · "the one thing to know before diffing" (brief = ground truth) ·
  the 5 biggest known divergences (single-winner vs split; min-cost solver vs decision-support; only
  Scenario A vs 7 lenses A–G; never-sends vs "Sent" gate; pricing at bid-layer vs at kickoff incl. 5
  safeties) · "what the code already gets right" (lot-grain via sticky alias, two origins as principle,
  immutable runs, timeframe-as-dimension, demand≠capacity CHECK, one feed powers historical cost) ·
  honesty notes (aggregator removed; two Streamlit entrypoints, only one is product; scaffolds/placeholders
  flagged) · status legend.

### original-engine/BUILD_01_SYSTEM_OVERVIEW_AND_ADRS.md
- **Path:** `specs/original-engine/BUILD_01_SYSTEM_OVERVIEW_AND_ADRS.md` (124 lines; id `ORIG-001`)
- **What:** What the legacy system *is today* + **8 internal as-built ADRs** (ADR-001..008) the running
  code already embodies. **NOTE:** this is the legacy fork's *own* ADR series — distinct from the project's
  `docs/adr/` series in Part 1.
- **DETAILED WHY:** Records the decisions the code *already* implements (in `models.py`/services/migrations,
  covered by tests) so the gap analysis is precise. It is the counterpart to the brief's BUILD_01, written
  to be diffed.
- **OUTLINE (the 8 legacy ADRs, each with status + divergence):**
  - **ADR-001 Store-first, governed spine, console on top** — Implemented; agrees with brief in spirit.
  - **ADR-002 Lot is the grain; aliases make it sticky** (DC×lot/item×supplier×TF; 4-table alias +
    quarantine; resolver `master_data_alias.py` 1,145 ln) — agrees; *gap:* no first-class
    `attribute_def`/`lot_attribute` taxonomy.
  - **ADR-003 One supplier per cell (single-winner)** — **KNOWN DIVERGENCE (MEDIUM)**; `volume_share`
    doesn't exist; brief permits split via per-DC/per-lot splittable flag.
  - **ADR-004 Immutable calculation runs; append-only** — Implemented; agrees strongly; *but* the brief's
    freeze-and-layer (`award.frozen_at` + `award_layer`) **not built** (no award object yet).
  - **ADR-005 Standardize landed cost across 5 bases; block never guess** (5 modes, 8 blocking reasons; 7
    eligibility gates, 12 reason codes; `landed_cost.py` 545 ln, `eligibility.py` 677 ln) — agrees,
    richer than brief.
  - **ADR-006 Decision-support is PARTIAL; no final award asserted** — **KNOWN DIVERGENCE (LARGE)**; has
    the *restraint* (`BANNED_DECISION_WORDS`, no auto-award) but only min-cost Scenario A, no 5-factor
    scoring, no lenses B–G.
  - **ADR-007 Pricing model at commercial/bid layer (not kickoff)** — **KNOWN DIVERGENCE (MEDIUM)**;
    10-table commercial layer, 6 pricing models, three-value rule, 18 validation codes, but safeties
    **inert** (stored, never executed); brief declares at kickoff incl. 5 safeties.
  - **ADR-008 Timeframe is a dimension; demand≠capacity by CHECK** (`ck_vsp_capacity_never_active_demand`;
    `volume_scope_prep.py` 747 ln) — agrees on both.
  - Two-line gap summary + changelog.

### original-engine/BUILD_02_DATA_MODEL.md
- **Path:** `specs/original-engine/BUILD_02_DATA_MODEL.md` (217 lines; id `ORIG-002`)
- **What:** The legacy 63-table data model, *mapped onto the brief's 8 logical layers* (ref/norm/cyc/bid/
  eng/awd/perf/audit — logical, since the legacy code doesn't literally use PG schemas) for layer-by-layer
  diffing.
- **DETAILED WHY:** Explains *why each table exists and how the grain holds*, and — crucially — names
  every place the legacy model **does not yet** match the brief, so the build backlog is exact.
- **OUTLINE:** Conventions (UUID `String(36)` PKs; money `Numeric(18,6)`; CHECK enums; append-only;
  services flush-never-commit) · the grain (supplier × lot/item × DC × TF × round × price; single-winner
  today) · the 8 layers with per-table notes and per-layer "gap vs brief":
  - L1 `ref` (BUILT): supplier/dc/commodity/subcommodity/item/loading_location masters + alias trio +
    `master_data_quarantine`; *gap:* no `zip_centroid` → **no distance/freight-proxy calc at all**, no
    scorecard ref.
  - L2 `norm` (BUILT partial): aliases + `source_artifact` + normalization runs; *gap:* no first-class
    `lot`/`attribute_def`/`lot_attribute` taxonomy.
  - L3 `cyc` (BUILT): rfp_cycle (12 states), cycle_round (8-state forward-only), cycle_tf, cycle_lot,
    item-scope, projected_volume, invited_supplier; *gap:* no `cycle_term`, no pricing/safeties at kickoff.
  - L4 `bid` (BUILT): bid_submission (8 statuses), bid_line (7/9/5 reason taxonomies), supplier_capability,
    capacity at 5 scopes, eligibility (7 gates/12 codes), landed_cost (5 modes/8 reasons); honesty note:
    two-origins agreed in spirit only, no zip_centroid.
  - L5 `eng` (BUILT single-winner): calculation_run (sealed, hashed manifests), version pins, scenario_a_*
    (single-winner, no volume_share); *the big gap* — no `bid_score`, only Scenario A.
  - L6 `awd` (MOSTLY NOT BUILT): no award / award_layer / signoff / generated_document — essentially the
    whole outward-facing layer.
  - L7 `perf` (BUILT partial): historical award (parent/child, price-never-volume), fiscal_date_conversion
    (loaded lookup 2020–2037, validated not seeded), Volume+Scope Prep (DEMAND/CAPACITY CHECK), 10
    commercial_* tables; *gap:* no scorecard, no KCMS, safeties inert.
  - L8 `audit` (SCAFFOLD): `audit_event` hash-chain scaffold; `decision_note` BUILT; NoteThread
    CONTRACT-ONLY.
  - "What this model already fixes" vs "what it does NOT yet fix" tables + changelog.

### original-engine/BUILD_03_schema.sql
- **Path:** `specs/original-engine/BUILD_03_schema.sql` (1336 lines, 63 CREATE TABLE)
- **What:** The real PostgreSQL DDL generated from the legacy SQLAlchemy models — the actual 63 tables.
- **DETAILED WHY:** It is the **migration baseline** ADR-0001 names: the *schema discipline* we keep by
  re-modeling. The single largest file in the slice (63,573 bytes); its rigor (composite-identity FKs,
  CHECK enums, partial unique indexes) is the asset clean-room reconciliation preserves.
- **OUTLINE (all 63 tables, alphabetical as emitted):** audit_event · bid_line · bid_submission ·
  calculation_run · calculation_run_input · capacity_constraint · capacity_statement ·
  commercial_lot_market_delta · commercial_market_kickoff_snapshot · commercial_market_proxy_basis ·
  commercial_market_reference · commercial_price_component · commercial_pricing_formula_audit ·
  commercial_pricing_model · commercial_pricing_validation_issue · commercial_pricing_window ·
  commercial_qdp · commodity_master_db · cycle_invited_supplier · cycle_item_scope · cycle_lot ·
  cycle_lot_item · cycle_projected_volume · cycle_round · cycle_tf · dc_alias · dc_master_db ·
  decision_note · eligibility_exception · eligibility_gate_result · eligibility_result · engine_release ·
  fiscal_date_conversion · historical_award_assignment · historical_awarded_cost_ingestion_issue ·
  historical_awarded_price_basis · item_alias · item_master · landed_cost_result · loading_location ·
  master_data_quarantine · metric_definition_version · normalization_run · normalization_run_source ·
  normalized_volume_scope · rfp_cycle · round_analysis_snapshot · round_feedback_issued ·
  round_field_reduction_decision · round_supplier_participation · scenario_a_capacity_usage ·
  scenario_a_cell_assignment · scenario_a_line_detail · scenario_a_result · scenario_config_version ·
  source_artifact · subcommodity_master · supplier_alias · supplier_capability · supplier_master ·
  volume_scope_override · volume_scope_prep_issue · volume_scope_source_row.
  *(Note: flat table names, no PG schema prefixes — the legacy code uses logical layers only.)*

### original-engine/BUILD_04_TECH_SPEC.md
- **Path:** `specs/original-engine/BUILD_04_TECH_SPEC.md` (156 lines; id `ORIG-003`)
- **What:** The legacy components that exist/run today, data flow, the Streamlit surface, the build
  sequence as it actually happened, and the remaining gap as a sequence.
- **DETAILED WHY:** Gives the gap analysis a **spine** — names every BUILT vs NOT-BUILT component and the
  order they were built, so the build backlog inherits a dependency order.
- **OUTLINE:** Stack table (SQLAlchemy 2.0 modeled-PG, demo SQLite, Alembic 14 migrations roundtrip-clean,
  hand-built services not the real v3, pandas/openpyxl + 7-step wizard, **no output rendering**, Streamlit
  console, stdlib+sqlalchemy only) · component map (BUILT: schema, alias resolver, bid intake, eligibility,
  landed cost, calc-run ledger, round lifecycle, Scenario A optimizer + presenter, historical cost, fiscal
  calendar, VSP, commercial pricing; **NOT BUILT:** iTrade loader, KCMS loader, scorecard, distance calc,
  decision-support scorer, lenses B–G, selection→freeze→layer, document generator; **SCAFFOLD:** event
  logger) · 11-step data flow with real failure modes (quarantine not guess; block not silent-zero;
  capacity-never-active-demand CHECK; bad volume row kept with issue code) · governance model · the 10-stage
  Streamlit surface (Stages 0–7 BUILT/PARTIAL, 8–9 NOT BUILT; **rail hardcoded**, brief wants it generated)
  · tests (54 files, 796 passed/1 skipped, all synthetic) · build sequence (2.5–2.9E) · the remaining build
  as a 7-item sequence (decision-support scoring + split awards first, both touch Scenario A core) ·
  changelog.

---

## 2B — `specs/rfp-engine/` (our build spec)

### rfp-engine/BUILD_00_README.md
- **Path:** `specs/rfp-engine/BUILD_00_README.md` (60 lines)
- **What:** Index for our backend-first build package; turns the six-session intake into buildable artifacts.
- **DETAILED WHY:** States the core thesis — **the v3 scoring/allocation engine already exists and is good;
  what's missing is a persistent governed STORE under it** (the engine is stateless → cannot do "open last
  cycle"). Carries the load-bearing pre-build verification: *confirm whether the live Streamlit app writes
  to a DB or just returns a zip* before building greenfield (if a store exists, migrate; if file-in/file-out,
  build as specified).
- **OUTLINE:** Read-order table (docs 0–4) · "the one thing to verify before code" (persistence check via
  `_event_log.py`, `init_cycle.py`, the Streamlit data layer) · the 3 foundational corrections (awards are
  split; decision-support not auto-award; persistence is the point) · build sequence A–F (data → history+norm
  → cycle+bid → engine → awards+outputs → API then UI) · document-header convention.

### rfp-engine/BUILD_01_SYSTEM_OVERVIEW_AND_ADRS.md
- **Path:** `specs/rfp-engine/BUILD_01_SYSTEM_OVERVIEW_AND_ADRS.md` (120 lines; id `DOC-001`, status Draft)
- **What:** What our system is + **8 build ADRs** (DOC-001's ADR-001..008) that lock in the intake's
  corrections. **NOTE:** this is the rfp-engine spec's own ADR series — again distinct from `docs/adr/`.
- **DETAILED WHY:** Each ADR *resolves a finding verified across the intake* (not opinion). This is the
  design contract the live build implements.
- **OUTLINE (the 8 build ADRs):**
  - **ADR-001 Store first, engine as a library, UI last** — build the data layer first; wrap v3 as a
    `run()` library; drop the ~2/3 Excel-formatting, lift the ~1/3 logic.
  - **ADR-002 Lot is the grain; normalization is a first-class store** — lot (parent) the grain; sticky
    `item_lot_map` (propose→confirm→reuse); join on lot never on a concat string.
  - **ADR-003 Awards are split (supplier shares per cell)** — one row per awarded supplier per cell with
    `volume_share`; capacity load-bearing; corrects the single-winner grain.
  - **ADR-004 Immutable runs; freeze-and-layer; nothing deleted** — sealed `config_json` runs, corrections
    = new runs; `award.frozen_at` + `award_layer`; append-only `event_log`.
  - **ADR-005 Decision-support, not auto-award** — engine proposes (min shown as reference), human selects
    & promotes to awards.
  - **ADR-006 Two origins kept separate** — `grow_origin` vs `ship_from_zip`, never auto-derived; distance
    via `zip_centroid`.
  - **ADR-007 One feed (iTrade) powers cost and the scorecard** — land iTrade once; derive both; KCMS
    distinct; scorecard = two frozen snapshots.
  - **ADR-008 Timeframe is a dimension, not a fork** — one engine run handles N timeframes (largest
    efficiency gain).
  - System overview (3 problems killed: historical blindness / non-standard process / manual dependence) ·
    "verify before greenfield" · scale assumptions · changelog.
- **CROSS-REF:** These 8 build ADRs are the *direct precursors* of the project `docs/adr/` series — e.g.
  this ADR-003 (split) → project ADR-0006 (split allocation); this ADR-005 (decision-support) → project
  ADR-0006 (decision-support brain); this ADR-001 (store-first/UI-last) → project ADR-0002/0003. The live
  code implements them (split awards, 5-factor scoring, freeze-and-layer, 8-schema store) per Part 1's
  cross-refs.

### rfp-engine/BUILD_02_DATA_MODEL.md
- **Path:** `specs/rfp-engine/BUILD_02_DATA_MODEL.md` (152 lines; id `DOC-002`, status Draft)
- **What:** Our 8-layer (8 PG schemas) data model, the grain, and what each table fixes vs the legacy/intake.
- **DETAILED WHY:** Explains *why each table exists and how the grain holds* for the TO-BE design — the
  blueprint the baseline schema implements.
- **OUTLINE:** The grain (supplier × lot × DC × timeframe × round × price) · 8 layers:
  - `ref` (commodity, subcommodity, dc, supplier+alias, item+alias, fiscal_calendar to 2037, zip_centroid)
  - `norm` (lot, attribute_def, lot_attribute, sticky item_lot_map) — *the layer v3 lacks*
  - `cyc` (cycle, cycle_timeframe, cycle_round, cycle_dc, cycle_lot, cycle_term)
  - `bid` (bid w/ two origins, bid_price w/ `no_double_discount` CHECK, bid_index_component,
    volume_requirement, volume_limit)
  - `eng` (analysis_run sealed config_json, bid_score 5-factor, scenario A–G, **scenario_award split**)
  - `awd` (award + frozen_at, award_layer, signoff, generated_document)
  - `perf` (itrade_receipt one-feed-two-jobs, kcms_movement distinct, supplier_scorecard 2 snapshots)
  - `audit` (event_log append-only; "open last cycle" = a query)
  - "what this model fixes, mapped to the intake" table + changelog.
- **CROSS-REF:** This 8-schema/36-table design is the layout of the **live** `db/baseline/schema.sql`
  (which uses the identical 8 schemas `ref/norm/cyc/bid/eng/awd/perf/audit`) — but the live baseline merged
  the legacy 63 tables in, so it carries **64 tables**, not 36. The rfp-engine spec is the *target shape*;
  the baseline is the *realized superset*.

### rfp-engine/BUILD_03_schema.sql
- **Path:** `specs/rfp-engine/BUILD_03_schema.sql` (521 lines, 36 CREATE TABLE, 8 CREATE SCHEMA)
- **What:** The runnable PostgreSQL DDL for our target model — 8 schemas, 36 tables.
- **DETAILED WHY:** The concrete TO-BE store the build stands up; smaller and cleaner than the legacy 63
  because it's the *designed* spine, not the inherited inventory.
- **OUTLINE (8 schemas → 36 tables):**
  - `ref` (9): commodity, subcommodity, dc, supplier, supplier_alias, item, item_alias, fiscal_calendar,
    zip_centroid
  - `norm` (4): lot, attribute_def, lot_attribute, item_lot_map
  - `cyc` (6): cycle, cycle_timeframe, cycle_round, cycle_dc, cycle_lot, cycle_term
  - `bid` (5): bid, bid_price, bid_index_component, volume_requirement, volume_limit
  - `eng` (4): analysis_run, bid_score, scenario, scenario_award
  - `awd` (4): award, award_layer, signoff, generated_document
  - `perf` (3): itrade_receipt, kcms_movement, supplier_scorecard
  - `audit` (1): event_log
- **CROSS-REF:** The live `db/baseline/schema.sql` uses these **exact same 8 schemas** (verified: the
  schema-comment lines match almost verbatim) but expands to 64 tables by folding in the legacy governed
  tables (calc-run ledger, eligibility/landed-cost detail, commercial pricing, VSP, etc.).

### rfp-engine/BUILD_04_TECH_SPEC.md
- **Path:** `specs/rfp-engine/BUILD_04_TECH_SPEC.md` (159 lines; id `DOC-003`, status Draft)
- **What:** Components, data flow, **how v3 plugs in**, the API surface, the build sequence (backend before
  frontend), and open items carried from the intake.
- **DETAILED WHY:** The handoff doc — defines exactly how the verified v3 engine is lifted to a `run()`
  library on the store and the order to build, so it needs no verbal explanation.
- **OUTLINE:** Stack (PostgreSQL 15+, FastAPI + SQLAlchemy 2.x + Alembic, v3 logic refactored to a library,
  pandas+openpyxl ingest, templated output, UI deferred) · component map (iTrade/KCMS loaders, normalizer,
  bid importer, distance calc, scorecard builder, engine runner, selection/freeze services, document
  generator, event logger, API, UI) · 11-step data flow + failure modes · **engine integration** — the
  frozen signature `run(cycle_id, round_code, config) -> run_id` (reads bids+volumes+incumbent cost+config;
  computes bid_score 5-factor + eligibility + scenarios A–G incl. `max_two_per_dc`; writes analysis_run +
  bid_score + scenario + scenario_award); required refactors (argparse→signature, file-read→store-read,
  workbook-write→table-write, keep the math + banding + `max_two_per_dc` exactly) · governance model ·
  representative REST API surface · build sequence Phase A–F with exit criteria · 4 open items (verify live
  app persistence; attribute-taxonomy confirmation pass; prior-round price is lot-level no DC — fix at
  source; kickoff structure one-vs-many) · changelog.
- **CROSS-REF:** The frozen `run()` signature here is the **exact** interface the live engine implements
  (`backend/app/engine/v3.py::run`, behind `EngineConfig` in `interface.py`) — ADR-0006 and this spec agree
  to the letter; the live weights/bands/lenses match (Part 1, ADR-0006 cross-ref).

---

## 2C — `specs/rfp-engine/intake/` (the requirement-capture history)

Seven files: an index + six dated session records. **DETAILED WHY (the set):** this is the **evidence
base** behind every rfp-engine design decision — a customer-intake interview run "one question at a time,"
treating the legacy `SYSTEM_SPEC.md` as a *claim, not truth* and verifying every claim against real
artifacts (real kickoff docs, real iTrade pulls, the leadership sign-off deck, the real v3 engine). It
exists so the design's WHY is auditable to its source. Below, **each session's decisions are summarized**
as required.

### intake/00_INDEX.md
- **Path:** `specs/rfp-engine/intake/00_INDEX.md` (161 lines)
- **What:** The canonical "where are we" — session log, the frame (two governance gates + operational
  middle), the **8 locked truths (the spine)**, the corrected end-to-end process (Phase -1 … 8), the data
  foundation, a **20-row Discrepancy Log** (doc-vs-reality), open questions, and the priority build sequence.
- **KEY DECISIONS / CONTENT:**
  - **8 locked truths:** (1) period grain; (2) parent product is the grain not UPC (SAP SubCommodity
    anchor); (2a) **awards are split** not single-winner; (3) freeze-and-layer; (4) nothing deleted;
    (5) setup file drives the read (same render live/historic); (6) draft→sent is a governance gate (the
    old "never sends" was wrong); (7) two origins kept separate; (8) process shape per-cycle (rounds vary;
    the old 10/13-stage hardcodes are both wrong).
  - **Discrepancy log (20 rows)** pairs each spec claim with reality + a type tag — the headline
    corrections being #14 (the "exact min-cost solver" is backwards — the real engine is decision-support),
    #19 (single-winner grain is a foundational error — cells split), #6 (safeties inert where they matter
    most), #18 (timeframe forks the engine by hand — parameterize it).
  - **Corrected process** Phase -1 Prep → 0 Strategy Kickoff (GATE in) → 1 Supplier Refresh+Qual → 2 Build
    +Release → 3 Round Loop → 4 Final Scenario → 5 Internal Alignment → 6 Sign-Off (GATE out) → 7 Awards →
    8 Contracting+Execution.
  - **Resolved across sessions:** v3 = brain, repo = spine instinct; split awards YES routinely;
    confirmation email is the official record under draft-to-sent; pricing model declared at kickoff;
    attribute taxonomy = universal core + per-category extensions; scenario engine = decision-support.

### intake/SESSION-01_intake-recap.md
- **Path:** `specs/rfp-engine/intake/SESSION-01_intake-recap.md` (92 lines, 2026-06-17)
- **Focus:** Process end-to-end + data foundation + first doc-vs-build gaps (input: `SYSTEM_SPEC.md` only,
  no repo).
- **DECISIONS CAPTURED:** The **3 problems** the system kills (historical blindness; non-standard process;
  manual dependence) → all cured by *declare structure once at kickoff, store it, render from it*. Added
  **Phase -1 (prep)** the spec never had. **Kickoff (Phase 0)** decides 3 independent axes (pricing basis;
  duration/cadence; volume split) + the objective. Named the **5 safeties** (disaster trigger, inverse +
  collar cap/floor, rolling midpoint, tolerance band, period-by-period) and flagged them stored-inert.
  Resolved **period grain** (fixed repeats price; index stores components, price resolves). **Freeze-and-
  layer** confirmed. **Setup file = keystone** (closes the loop on all 3 problems). Architecture correction:
  not one big table — reference data + a unified transactional core (one bid-line store → one award table).
  **Draft→sent is a governance gate** (kills "never sends"). Process shape variable (3 rounds default).
  **Normalization** — parent product is the grain, SAP SubCommodity is the hard anchor, pack-size cleanup
  needs human reasoning but the system remembers it. **Two origin fields** (ship-from ≠ grow-origin) from
  the iTrade caveat. Hard finding: nothing has touched real data (the biggest risk).

### intake/SESSION-02_kickoff-schema.md
- **Path:** `specs/rfp-engine/intake/SESSION-02_kickoff-schema.md` (139 lines, 2026-06-17)
- **Focus:** Real kickoff docs reviewed (Field Tomato, HH Veg, Wet+Pack Veg + 2 prep workbooks); the
  **kickoff-file (setup-file) schema extracted**; spine validated against real artifacts.
- **DECISIONS CAPTURED:** The kickoff doc *is* the setup file; consistent across categories/years → liftable
  to fields. Rule: **structured fields drive the system; narrative blocks stay prose** (never force narrative
  into fields). Extracted 8 field groups: **A** cycle identity (category, subcommodities-in-scope,
  annual_spend, timeframe start/end as Kroger fiscal periods, DCs default ALL, objective multi-with-primary,
  prior-structure note); **B** pricing structure (basis FIXED/INDEX/hybrid; duration_cadence enum
  FULL_YEAR/SEASONAL/TIMEFRAMES(n)/PERIOD_BY_PERIOD(13)/QUARTERLY/MONTHLY/WEEKLY; baseline_then_negotiate;
  volume_split_rule; the 5 safeties with params; routing_basis FOB/DELIVERED/XDOCK/CBS_FREIGHT; per-period
  sourcing region); **C** scope/items (SubCommodity codes, ~9.8k-row GTIN export = manual signal-from-noise,
  sticky lot assignment, pack normalization); **D** historical/baseline (KCMS category overview metrics +
  the **exact supplier-scorecard schema**, captured **twice** kickoff+sign-off both frozen; PO historical
  cost); **E** supplier field (invited suppliers incumbent/non, configurable RFI question set); **F**
  commercial terms (PBA required + metric thresholds + enforcement; working-capital terms; KPM 84.51°
  funding); **G** the per-cycle timeline/rail (ordered {event,date}, variable round count, two leadership
  gates anchor each end); **H** narrative blocks (prose, versioned). Data lineage table maps each block to
  its feed (KCMS / iTrade / PO-receiving / declared-at-kickoff / authored).

### intake/SESSION-03_data-and-engine-layer.md
- **Path:** `specs/rfp-engine/intake/SESSION-03_data-and-engine-layer.md` (124 lines, 2026-06-17)
- **Focus:** The full data+engine layer — iTrade feed, normalization, multi-template bid intake, the engine,
  the timeframe fork, the booking guide. (Sources: 6 iTrade pulls, the Norm sheet, 8 supplier bids, the HO
  booking guide, the tomato R3 file, 3 RD2 Allocation models.)
- **DECISIONS CAPTURED:** **iTrade = every PO receipt** (43-col Data export), **one feed two jobs**
  (historical cost + scorecard); importer rules (trust flags first; sanity-check date spans; key off
  commodity/subcom codes inside the data never the filename; handle 43-col vs 51-col variants).
  **Normalization** = UPC→lot decomposition into a fixed attribute set (universal ORGANIC/COLOR/SIZE/PACK +
  tomato VARIETY/PROCESS + onion PACK-TYPE/STORAGE), store raw + attributes + LOT FINAL, propose→confirm→
  sticky; storing attributes (not just the lot) lets you regroup later. Critical: the engine's
  **string-concat match key** (`=TRIM(product)&TRIM(DC)`) silently misaligns → replace with the normalized
  lot. **Multi-template bid intake, one destination grain** (tomato flat sheet vs onion 9-tab hybrid w/ PBA
  tab); per-template mapping not one parser; both origins captured in the bid itself. **Engine** = the
  3-layer Allocation model (Raw→Calcs→Outputs, Data cube + Controls panel = the parameterized setup file);
  scenarios are **a set of lenses** (baseline/incumbent, min, no-disc, supplier-excluded) compared vs **STLY
  + Latest** (STLY = where the loaded fiscal calendar earns its keep). **Timeframe fork = the biggest single
  win** (Colored Potato forks the whole engine per TF by hand → treat TF as a dimension). **Booking guide**
  is the award table + execution logistics, hand-built today → generate it. **The correction that matters
  most:** the old spec's exact-min-cost auto-solver is wrong; the real tool is decision-support (keep the
  human in the seat). Fragility catalogue (live formulas, #REF!, sheets named "delete", suppliers-as-columns).

### intake/SESSION-04_signoff-gate-and-split-awards.md
- **Path:** `specs/rfp-engine/intake/SESSION-04_signoff-gate-and-split-awards.md` (54 lines, 2026-06-17)
- **Focus:** The leadership sign-off deck (`20260528_P&O_Leadership_Sign-Off.pptx`, 16 slides) → the second
  governance gate + **the split-award correction** (the most important structural correction in the intake).
- **DECISIONS CAPTURED:** **Split awards are real and routine** — recommendation tables award a single DC to
  **multiple suppliers** ("Onions52, Owyhee"; "Keystone, Onions52, Owyhee"). A DC×lot×TF cell is **not** won
  by one supplier; volume is allocated across N suppliers, capacity-constrained, human-decided — *this breaks
  the old spec's "locked, everything depends on it" single-winner rule.* Award grain corrected: cell =
  DC×lot×TF; award = a **set of supplier shares**, each with own volume+price. The **sign-off deck** =
  generated-from-record, four parts (strategy recap; recommendation per category — incumbent→recommended,
  R4 savings vs STLY, +/- vs incumbents, conv/organic split; financial impact rolled to a **portfolio**
  total; sign-off scorecard = the second freeze). Confirms **STLY is the headline metric** leadership
  approves; conventional/organic split runs through every recommendation; the gate is **portfolio-level**
  (one sign-off spans many category cycles → needs a portfolio view above the single-category model). R4 =
  this cycle ran 4 rounds (rounds variable).

### intake/SESSION-05_v3-engine-and-codebase-fork.md
- **Path:** `specs/rfp-engine/intake/SESSION-05_v3-engine-and-codebase-fork.md` (66 lines, 2026-06-17)
- **Focus:** The v3 engine *notebook* (`RFP_Analysis_Engine.ipynb`, the Colab harness; the .py itself not
  yet provided) + surfacing **the two-codebases fork** that decides the whole engagement.
- **DECISIONS CAPTURED:** Reframes the engagement — Ed is **already building the parameterized
  consolidation** as the v3 Python engine, mid-build. Run output reveals: **config-driven** (commodity/cycle
  set by config), **rounds as config** (final+prior), **timeframes as config** (TFs active — the Session-3
  fork already parameterized), **weighted multi-criteria scoring** ("weights sum to 120% — normalising" →
  not pure min-cost). Input schema CONFIG / IN_ / DIM_. Output = an interactive CUSTOM_SCENARIO tab (Scenario
  A green rows, per-lot override dropdown, live all-in/spend/YoY, DC supplier-cap-breach flag — capacity
  modeled). **The catch:** the run **errored** at step 1-of-9 (no output) — v3 is mid-build, failure point
  not yet visible. **The fork:** two codebases (the heavy Streamlit+SQLAlchemy repo vs the lightweight v3
  Colab engine) cannot both be the foundation — Ed's behavior points to v3 but it needs explicit
  confirmation. Open question added: which codebase is the real line of development?

### intake/SESSION-06_engine-verdict-and-fork-resolution.md
- **Path:** `specs/rfp-engine/intake/SESSION-06_engine-verdict-and-fork-resolution.md` (107 lines, 2026-06-17)
- **Focus:** The full v3 engine code read (`rfp_analysis_engine_v3.py`, 4,198 lines) → **the verdict that
  resolves the central question** + three addenda that correct it.
- **DECISIONS CAPTURED:** **Verdict: v3 is the brain, not the spine** — build v3's engine logic on a
  persistent governed data layer the repo only gestured at. Verified in code: a **9-step pipeline**; **five
  banded factors** Price 0.35 (bands ≤3%→100/≤7%→80/≤12%→50/>12%→20), Coverage 0.25, Historical 0.20,
  Z-Risk 0.10, Continuity 0.10 → composite RecScore (cost is only 35%); **eligibility gates with reason
  codes**; **split-award allocation `max_two_per_dc`** (rank by 60% avg score + lots covered + coverage,
  keep top N default 2, award each lot to the best, fill uncovered with a transparency flag — the
  "Onions52, Owyhee" split as an algorithm); **seven scenario lenses A–G** (incl. Exclusion E, Custom F,
  Preferred G); **config-driven, commodity-agnostic** (CONFIG/IN_/DIM_); rich ~14-tab output. **What it is
  NOT:** stateless (no DB/history — cannot do "open last cycle"); no normalization (assumes Lot_ID input);
  no governance (no sealed runs/freeze/audit); no front end; a 4,198-line monolith (~2/3 Excel formatting);
  brittle input contract (the test run died at the input/schema seam). **Resolution:** neither codebase is
  the product — **build = v3's scoring/allocation engine lifted out of the monolith, set on a persistent
  governed data layer** generating booking guide + sign-off from records.
  - **Addendum:** a later iteration (md5 `c73ffc5`, 4,244 ln) reviewed — verdict unchanged (output-layer
    only: Custom Scenario mid-refactor, Glossary built out confirming lens semantics A–F). Three details to
    carry: **All-In cost fallback** (= FOB + Delivery Surcharge + **VegCool Surcharge** − Lot Discount;
    **footgun** = double-subtraction if All-In already net AND Lot Discount populated → spine must enforce
    one path) and **prior-round price is lot-level only (no DC)** → fix at the source in the bid store.
  - **Addendum 2 (UI):** the notebook UI is *structurally* bad — a stateless engine can only have a bad UI;
    the build does **not** start with a UI (a good front end is a view onto the persistent layer).
  - **Addendum 3 (VERDICT CORRECTION):** the engine is **one of ten scripts** in `RFP_Workflow_Package_v1.4`
    (init_cycle, generate_bid_templates, intake_bids, reconcile_intake, calculate_distances, the v3 engine,
    generate_feedback_letters, generate_final_letters, generate_booking_sheet, _event_log + HTML templates).
    Corrects the "front/back/comms/booking-guide/audit don't exist" claim — they exist as code. The genuinely
    open question narrows to: **is there a durable governed store under the workflow** (does the live
    Streamlit app persist state / solve "open last cycle"), or is it still file-in/file-out? The fork ("v3
    brain on a new spine") is **paused pending** sight of the package source + the app's persistence layer.

**INTAKE → BUILD CROSS-REF.** The intake's open question ("is there a durable store?") is exactly what
ADR-0001 resolved (clean-room: build the governed store, isolate the legacy repo as read-only reference)
and the verified v3 findings here (5 factors, 7 lenses, `max_two_per_dc`) are exactly what ADR-0006 ratified
and `backend/app/engine/{v3,interface,guards}.py` implements to the letter (Part 1). The VegCool /
double-subtraction footgun (Addendum) is the `no_double_discount` CHECK in `bid.bid_price` (ADR-0013).

---

## D4 — Gaps, drift, and open items (consolidated)

1. **SCOPE GAP — ADR numbering is sparse.** Prompt says "ADRs 0001–0018"; only **10 ADR files exist**
   (0001, 0002, 0003, 0004, 0006, 0013, 0014, 0016, 0017, 0018). **Missing as files: 0005, 0007–0012,
   0015.** Intentional (numbers reserved to align with Decision-Log D-numbers; not every D got a standalone
   ADR file). Documented all 10 that exist. *Recommend: a stub index in `docs/adr/` noting the reserved/
   skipped numbers so the gap is legible, not accidental.*
2. **ADR-0002 drift (minor):** the OpenAPI→TypeScript typed-client generation (`gen:api`) is still a
   **no-op placeholder stub** in `frontend/package.json`, even though the frontend shipped — the one
   stub-shaped item in this slice's path.
3. **ADR-0004 phased/partial:** the "`client_id` on every governed row + prepended to all composite FKs"
   weave is **deferred to migration M10/E-03**; the baseline keeps `client_id` only on `ref.client` +
   `ref.commodity` today. Capable-not-operated intent is met; the universal weave is not yet applied.
4. **ADR-0016 partial:** the *named, versioned, reusable `strategy` object* is **not yet a dedicated table**;
   the levers are config-driven (intent met, no hardcoded strategy) but the "define/save/version/apply +
   A/B" product feature is a forward item.
5. **ADR-0014 expected-future:** safeties are **declared/stored** (setup template + `cyc.cycle_safety`) but
   the **post-award execution/monitoring module** that fires/visualizes them is the named Phase-E+ feature
   (not built — consistent with the ADR).
6. **ADR-0017 expected-future:** GCP is **decided + deploy-scaffolded** (`deploy/gcp/`, ci.yml image build)
   but **not yet provisioned** (per the ADR's own status).
7. **Census timestamp skew (cosmetic):** census `created/modified` for the ADRs differ from on-disk `stat`
   by minutes (capture-time vs write-time). Byte sizes match exactly; no content drift.
8. **Spec status = Draft / two internal ADR series:** both spec packages still carry `status: Draft` (and
   each has its *own* internal ADR-001..008 series, distinct from the project `docs/adr/` series) — a reader
   must not conflate the three ADR series. Original-engine spec is descriptive AS-IS legacy (the fork); not
   our build.
9. **Live baseline is a superset, not the spec:** the rfp-engine spec defines 8 schemas / 36 tables; the
   legacy spec 63 tables; the **live `db/baseline/schema.sql` = 64 tables** under the rfp-engine's 8 schemas
   (the merge). Anyone diffing the spec schema against the live DB must expect the superset.
