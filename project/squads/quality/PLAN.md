---
doc: Quality & Assurance Squad — Plan (test strategy, governance tests, the real-data pilot)
id: QA-PLAN
squad: Quality & Assurance (Squad 6)
status: Draft
created: 2026-06-18
owns: the test pyramid, engine-reproducibility (S2), governance/invariant tests (S6),
      the REAL-DATA PILOT (E-13, Phase B exit gate, retires R1), UAT with Sourcing,
      per-phase quality gates
relates: audit/04 (R1, Phase B), audit/01 ([X-1], [D-6]), SESSION-03/06 (verified v3),
         E-13/E-01/E-18/E-20, ADR-005 (decision-support), ADR-0001 (clean-room),
         DEP-2 (real iTrade + bid round), S1–S8 (charter), WoW §5/§6 (DoD, gates)
coordinates_with: Security (E-03/E-04 tenancy+classification), Platform&Data (E-01/E-08/E-11),
                  Engine (SPIKE_D2, the run() contract), DevOps (E-27 CI)
---

# Quality & Assurance — Plan

The program's #1 risk (R1 / `[X-1]`) is that **nothing has run on real data** — both
packages are validated only against fixtures their own authors designed. Our charter
deliverable is the **real-data pilot (E-13)** that retires R1 at the Phase B exit gate.
Everything else in this plan exists to make that pilot trustworthy and repeatable: a test
pyramid that proves the parts, reproducibility tests that prove the engine *is* v3, and
invariant tests that prove the governance is real and not decorative.

Principle: **a test against author-designed synthetic data proves the code does what the
author expected; only the pilot proves it survives the mess it exists to absorb.** We treat
the first real cycle as a test, not a delivery (audit/04, R1 mitigation).

---

## 1. Test strategy & the automation pyramid

Five layers, widest at the base. Every layer runs in CI (E-27); the migration-roundtrip and
cleanroom guards are merge-blocking from Phase 0 (architecture SKELETON ships them on day one).

| Layer | Scope | Substrate | Examples |
|---|---|---|---|
| **Unit** (most) | Pure domain logic, no I/O | In-process, synthetic fixtures | Scoring bands fire at the 3/7/12% edges; eligibility reason codes; STLY period map; landed-cost All-In fallback; weight-normalization |
| **Integration** | Services on a **real Postgres** | Testcontainers/compose (`conftest.py`) | CHECK/identity-FK constraints reject bad rows; the migration roundtrip; guard-listeners block mutation; tenant RLS |
| **Contract** | API ⇄ OpenAPI | Schemathesis against the live app | Every endpoint matches its schema; reads never return an "awarded" verdict; authn/authz on every route |
| **E2E** | A full cycle, end to end | Seeded synthetic cycle through the real API | iTrade import → normalize → bid intake → run → scenarios → select → freeze → booking guide, with the event trail intact |
| **Pilot** (the apex) | One **real** cycle on **real** artifacts | Pilot dataset (clean-room) | §5 — the centerpiece; reproduces a known-good v3 output |

**Unit — what must be covered.**
- **Domain rules:** the five banded factors as pure functions (§2); 7-gate eligibility (12 reason
  codes); the `max_two_per_dc` strength rank (60% avg score + lots covered + coverage); the All-In
  fallback (FOB + Delivery + VegCool − Lot Discount) asserted **not to double-subtract** the
  discount; STLY period→period mapping.
- **Scoring bands:** parameterized edge tests at every boundary — Price at 3.0/3.01/7.0/7.01/12.0/
  12.01% premium; Coverage at <50/50/80/100/120%; "As Needed" → 70; Continuity incumbent=100/else 0;
  Z-Risk low-bidder (<3) → unreliable flag.
- **CHECK constraints (logic side):** mirror each DB CHECK as a unit (demand≠capacity,
  `no_double_discount`, fiscal-range bounds) so a regression is caught before it reaches the DB.

**Integration — on real Postgres, never SQLite** (closes `[D-6]`/R8).
- **CHECK & identity-FK enforcement:** a bid whose lot belongs to another cycle → composite FK
  rejects; a negative/zero price → CHECK rejects; a capacity row duplicating
  `(cycle,supplier,dc,lot,tf)` → rejected (the as-built heap bug, `[D-3]`, must not survive).
- **Migration roundtrip (E-01):** `upgrade head → downgrade base → upgrade head`, clean and
  idempotent on **PG15** in CI before any merge (SKELETON `test_migrations_roundtrip.py`). Asserts no
  SQLite idioms (booleans are `boolean`) and the no-op `length(x) >= 0` CHECK is gone (`[D-6]`). The
  breaking G1 migration (relax `UNIQUE(run,dc,lot,tf)`, add `volume_share`) gets its own roundtrip +
  a **data-preservation** assertion (existing single-winner rows survive as `volume_share = 1.0`).
- **Services own no transaction:** `add + flush, never commit` (KEEP) — a service that commits fails.

**Contract — OpenAPI is the boundary.** Schemathesis drives every endpoint from the published
schema (E-25): response conforms; no read endpoint returns a decision verb (ties to §3 BANNED
guard); 401/403 on missing/forbidden principal; tenant scoping on every list.

**E2E — the full cycle on synthetic data.** A scripted run through the real API exercises the whole
chain (SESSION-03) and asserts the event trail is complete and "open last cycle" returns the full
story <2s (S1). This is the **dress rehearsal** for the pilot — when it is green on synthetic data,
the pilot swaps in real artifacts and changes nothing else.

**How synthetic fixtures stay synthetic (clean-room, ADR-0001).**
- Synthetic fixtures live **only** in `backend/tests/fixtures/`, are clearly fabricated
  (vendor names like `ACME-SYN`, round-number prices), and carry no real vendor, DC, or price.
- Real sample data lands **only** in `reference/samples/` with a Security classification header
  (§5); it is **never** a test fixture and is **never** committed (gitignored, §5 data-handling).
- A CI guard (`test_no_real_data_in_tests.py`) greps the test tree for the pilot's real
  vendor/DC tokens and **fails** if any real datum leaked into a fixture. The existing
  `test_cleanroom_import.py` already fails if `backend/` imports `reference/`.

---

## 2. Engine reproducibility — proving the new engine *is* v3 (S2/S4)

The engine is a clean-room re-expression of v3's logic (SPIKE_D2, Option A). "Reproduces v3"
is not a claim we assert — it is a **golden-master test** we run. This is the Phase D exit gate
and a precondition the pilot inherits.

**Golden-master approach.** Take one real `*_RFP_Input.xlsx` (CONFIG/IN_/DIM_ schema) that v3
ran clean end-to-end, plus **v3's own output workbook** for that input. Load the same bids+config
into the store, call `run(cycle_id, round_code, config)`, and assert the new engine's records
match the numbers in v3's output tabs — **on the numbers, not the openpyxl formatting** (we port
zero formatting code). The v3 output is the frozen golden master; the test diffs against it.

**Assertions (from SPIKE_D2 §5, the verified v3 behavior):**
1. **The five banded factors** per bid match v3's *Detailed Scoring* tab (tolerance ≤ 0.5 per
   factor): Price .35 (≤3→100/≤7→80/≤12→50/>12→20), Coverage .25 (As-Needed=70), Historical .20,
   Z-Risk .10, Continuity .10 — and the composite `rec_score` (weighted sum, **cost only 35%**).
2. **Band edges fire** at the 3/7/12% premium boundaries and the coverage breakpoints (dedicated
   edge-case rows, not just the happy path).
3. **Eligibility `gate_flags`** match v3: no-valid-price, premium-too-high (> max threshold),
   insufficient-volume (coverage < 80% and not as-needed), price-outlier (low/high z), low-bidder
   count (<3 → z unreliable). The scoreable-vs-awardable gate, reproduced.
4. **`max_two_per_dc` allocation** selects the **same top-N suppliers per DC×TF** (strength rank
   = 60% avg score + lots covered + coverage), the **same lot→supplier split**, and the same
   fallback/transparency-flag rows as v3's *DC Constraint/Consolidation* tab — including the
   `cap_breach_flag` when the 0.40 concentration cap is hit.
5. **Scenario A** reproduces v3's *Lowest Cost Check* total (the min-cost solver survives only as
   this benchmark lens — never auto-applied).
6. **Footgun assertions** (SESSION-06 addenda): the All-In fallback does **not** double-subtract
   the Lot Discount; prior-round price is **lot-level only** (no DC) so round deltas are lot-level.

**Stub→swap gate.** Until D2 finalizes, the engine is a deterministic stub (engine-domain PLAN §5).
The reproducibility suite is the **gate that authorizes the swap** from stub to lifted v3 logic:
no run tagged `engine_version != stub` may merge unless this suite is green. A CI check forbids
`engine_version = stub` runs from being used in the pilot.

---

## 3. Governance / invariant tests (S6) — proving the safeties are not decorative

audit/04 R4/R5 warn the audit chain and the safeties "look operative but are scaffolds." We test
each invariant from WoW §3 explicitly, at the layer that enforces it (DB + app), so "enforced" is
demonstrated, not asserted.

| Invariant | Test (the negative case is the real test) |
|---|---|
| **Immutable sealed runs** | `UPDATE`/`DELETE` on a sealed `eng.analysis_run` (or its `bid_score`/`scenario_award` children) is **rejected** by the guard-listener/trigger; a "correction" must create a *new* run with a new `run_id`. Editing a sealed row raises, not silently succeeds. |
| **Freeze-and-layer of awards** | After `frozen_at` is set, a change writes an `award_layer` row; the **raw award is byte-recoverable** from the layer chain; the original row is never overwritten (S6). |
| **No hard deletes anywhere** | A repo-wide static check: **no code path issues `DELETE`** against governed tables (AST/grep guard in CI); at the DB layer, a delete attempt on a governed row is rejected. Supersession is via new rows only. |
| **Live audit event log** | Every state-changing operation (import, normalize-confirm, run, select, freeze, sign-off, send) **emits exactly one event**; the hash-chain links (`prev_event_hash`→`event_hash`) verify end-to-end; tampering with a mid-chain row is **detectable** (the chain breaks). This is the test that R4 ("false audit assurance") is retired — the chain must be **live**, not SCAFFOLD. |
| **Decision-support only (BANNED_DECISION_WORDS)** | The recommendation/presenter surface is fed outputs that *would* read as an award verdict; the guard **raises** and blocks them. No API read endpoint returns "awarded"; the engine never writes `awd.*`. A test asserts the guard's banned-word list is non-empty and enforced (S3). |
| **Draft→SENT gate** | A document/letter cannot reach `SENT` without an approver + timestamp; the engine still never auto-asserts (the guard and the gate coexist — engine proposes, a human promotes). |

These run as integration tests on real Postgres (the guards are DB-layer) plus unit tests for the
BANNED guard. They are merge-blocking from the phase that introduces each invariant.

---

## 4. Tenancy / security test hooks (coordinate with Security, E-03/E-04)

Security owns the tenancy model (ADR-0004: `client` grain + Postgres RLS) and the RBAC middleware;
QA owns the **isolation test suite** that proves it (S7). We co-author these so the assertions match
the mechanism.

- **Cross-tenant read returns nothing** (`test_tenant_isolation.py`, in the SKELETON): a principal
  scoped to tenant A querying B's cycles/bids/runs/awards gets **zero rows** at both the API and the
  DB (RLS) layer — belt and suspenders, so an app-filter bug can't leak.
- **Cross-tenant write rejected:** A cannot create/mutate a row owned by B.
- **RBAC route guards:** every endpoint enforces its role; unprivileged → 403; unauthenticated → 401.
- **PII / classification:** each entity carries a data-classification tag (E-04); no endpoint emits a
  `restricted` field to a role not cleared for it.
- **Pilot tenancy:** the pilot runs in a dedicated `KR-PILOT` tenant; an isolation test proves real
  pilot data is invisible to every other tenant before any real datum is loaded.

---

## 5. THE REAL-DATA PILOT (E-13) — the centerpiece, Phase B exit gate

**This retires R1.** One real iTrade pull + one real bid round, end-to-end, with the engine
reproducing v3's verified scoring + split allocation against a known-good v3 output. Until this
passes, every capability claim on both packages is unproven (audit/04: "treat the first real cycle
as a test, not a delivery").

### Objectives
1. Prove the system **ingests real mess** (43- and 51-col iTrade variants, flag-first validation,
   impossible date spans, mislabeled files keyed off commodity codes not filenames — SESSION-03 §1).
2. Prove **real items propose lots**, a human confirms, the map sticks (E-11 / G8).
3. Prove a **scorecard snapshot** computes from real receipts (E-10).
4. Prove the **engine reproduces v3** on a real input (the §2 golden master, but on the real cycle).
5. Prove **governance holds on real data**: sealed run, no hard delete, live audit, no auto-award.

### Exact real artifacts needed from the sponsor (DEP-2 / DEP-1)
The pilot **cannot start** without all of these; QA + Security receive them via the clean-room intake.

| # | Artifact | Why / shape | Source |
|---|---|---|---|
| A | **One real iTrade export** (the "Data" sheet, real 43-col headers; ideally one 51-col variant too) | The transactional spine — real PO-receipt rows with real DC/UPC/vendor/cost/date columns and real flag mess (SESSION-03 §1). The intake's Tomato file *errored at step 3*; we need one that completes. | DEP-2 |
| B | **One real bid round** — the supplier workbooks for that commodity (e.g. the flat tomato template **and**, ideally, a multi-tab onion "Hybrid" workbook) | Real bids at UPC×DC×TF in the real per-template shapes, incl. FOB/Delivered, two origins, PBA terms, No-Bid/Incomplete flags (SESSION-03 §3). | DEP-2 |
| C | **One real kickoff / setup doc** for that cycle | Declares objective, timeframes, weights, thresholds, premium bands — drives Controls/the run (SESSION-03 §4). | DEP-2 |
| D | **One known-good v3 output workbook** — the v3 result for input A+B+C (the *golden master*) | The thing we diff against to prove reproduction (§2). **Single most important artifact** — without a known-good output we can lift the logic but cannot *verify* it (SPIKE_D2 §6). | DEP-2 / DEP-1 |
| E | **The v3 engine source** (`rfp_analysis_engine_v3.py`, md5 `c73ffc5…`) via the ADR-0001 isolated intake | To lift the exact band math, strength-rank formula, and fallback order. **Read, never imported.** | DEP-1 |
| (opt) | Norm sheet + booking guide for that cycle | Cross-check normalization output and the generated booking guide against Ed's hand-built versions. | DEP-2 |

### Entry criteria (gate to *start* the pilot)
- Phase A done: live audit log proven, RBAC + tenant isolation enforced, "open last cycle" <2s (S1).
- Phase B feeds built: `itrade_receipt` import (E-08), persistent `norm.lot` (E-11), scorecard (E-10).
- The engine-reproducibility suite (§2) is **green on the synthetic golden fixture**, and the E2E
  synthetic cycle is green (the dress rehearsal passed).
- All artifacts A–E received, **classified by Security**, and landed in `reference/samples/`.
- A dedicated `KR-PILOT` tenant exists and isolation is proven empty (§4).

### End-to-end run steps
1. **Classify & land** A–D in `reference/samples/` (Security sets classification); E via the
   ADR-0001 isolated worktree, logic-digest only.
2. **Import iTrade (A):** flag-first validation; reject impossible date spans (the "received 2
   months after shipped" row, SESSION-03 §1); key off commodity/subcom codes, not filename.
3. **Normalize:** the system proposes attributes/lot from real descriptions; a human confirms the
   unsure ones; assert the map **sticks** and the LOST-DESCRIPTION path handles the unresolved.
4. **Scorecard snapshot (E-10):** compute the kickoff snapshot from real receipts; sanity-check it.
5. **Intake the real bid round (B):** per-template mapping into the one destination grain
   (supplier×lot×DC×period); two origins captured; No-Bid/Incomplete flagged.
6. **Declare the cycle from the kickoff doc (C):** objective, TFs, weights, thresholds, bands.
7. **Run the engine:** `run(cycle_id, round_code, config)` → sealed `analysis_run`; produces
   `bid_score`, scenarios A–G, split `scenario_award`. (`engine_version` must be the validated v3
   build, **not** `stub`.)
8. **Compare to the golden master (D):** assert the reproducibility suite (§2) passes **on the real
   cycle** — scores, band edges, gate flags, the split allocation, Scenario A total, footguns.
9. **Decision-support check:** a human selects a scenario with a decision note; assert **no award was
   auto-asserted** (S3) and the BANNED guard held.
10. **Governance replay:** attempt to mutate the sealed run (rejected); verify the audit chain links
    every step end-to-end; confirm no `DELETE` path was taken.

### Pass / fail acceptance
**PASS (all required):**
- Real iTrade pull lands; bad rows are **flagged/rejected, not silently computed**.
- Real items propose lots; a human confirms; the map sticks across a re-run (no re-mapping).
- A scorecard snapshot computes from the real receipts.
- The engine **reproduces v3** on the real input within tolerance (§2 assertions 1–6 all green) —
  **this is the line that retires R1.**
- A human selection is recorded with a decision note; **no auto-award**; BANNED guard held.
- The run is sealed and immutable; every state change emitted an audit event; the chain verifies;
  no hard delete occurred.

**FAIL (any):** any reproducibility assertion misses tolerance; the import silently swallows a bad
row; normalization can't propose a real lot or the map doesn't stick; a sealed run can be mutated;
a state change emitted no event; the engine asserts an award. A fail does **not** advance Phase B —
we fix and re-run (the pilot is a test, not a delivery).

### Data-handling (clean-room, with Security)
- All real artifacts live **only** in `reference/samples/` with a Security classification header;
  **never** copied into `backend/tests/` (the §1 leak guard enforces this).
- `reference/samples/` is **gitignored**; real data is **never casually committed**. If a sample
  must be referenced, it is referenced by a sanitized synthetic derivative, not the real file.
- The v3 source (E) enters via the ADR-0001 isolated worktree (one dedicated agent), emits a logic
  digest, and is **read, never imported** — CI's `test_cleanroom_import.py` enforces the boundary.
- The pilot runs in the isolated `KR-PILOT` tenant; pilot data is provably invisible to others (§4).

### What success proves (the charter criteria)
- **S2** — the real-data pilot passes; **R1 is retired** (the program's #1 risk).
- **S1** — "open last cycle" returns the real pilot's full story in one query <2s.
- **S4** — a real cell is awarded to multiple suppliers with volume shares, capacity-constrained.
- **S3** — the engine proposed; a human selected; no award was auto-asserted (decision-support).
- Bonus coverage toward **S6** (governance held on real data) — the invariant replay in step 10.

---

## 6. UAT with Sourcing & per-phase quality gates

**UAT (Ed / Sourcing — the sponsor is the domain authority, charter §5).**
- Ed validates the **pilot outputs against his own Excel reality**: the normalized lots match his
  Norm sheet, the scenario splits match the "Onions52, Owyhee" deck, the scorecard matches his
  read, and the generated booking guide matches the one he builds by hand (SESSION-03 §6).
- UAT is **structured, not ad-hoc**: a per-cycle checklist (each S-criterion → an observable),
  Ed signs off each, mismatches become discrepancy-log rows (carry the brief's living register).
- UAT sign-off by Sourcing is a **required input** to the Phase B and Phase E gate reviews.

**Per-phase quality gates (extends WoW §6).**
| Phase | QA gate (in addition to CI green) |
|---|---|
| **0** | Migration roundtrip green on real PG15; SQLite-isms + no-op CHECK gone (`[D-6]`); cleanroom + no-real-data-in-tests guards live |
| **A** | Live audit-chain verification test green (R4 retired); tenant isolation suite green (S7); "open last cycle" <2s (S1) |
| **B** | **THE PILOT PASSES** (E-13 acceptance above) + UAT sign-off by Sourcing → **R1 retired**, Phase B exits |
| **C** | A cycle declared from a real kickoff doc; Stage-0 in-gate test (a cycle can't open on real data without approval) |
| **D** | Engine-reproducibility suite green against the golden master (S2/S4); the stub→v3 swap is authorized only by this gate |
| **E** | Freeze-and-layer + no-hard-delete + draft→sent invariant tests green (S6); booking guide/deck generate from records (S5); savings-vs-STLY (S8) |
| **F** | Full contract suite (Schemathesis) green; every endpoint guarded; live + historic cycles render identically |

**Standing gate from Phase B onward (WoW §6.4):** every slice must work against the **pilot
dataset**, not only synthetic fixtures. A green synthetic suite is necessary but no longer
sufficient — real-data is the bar once the pilot has run.
