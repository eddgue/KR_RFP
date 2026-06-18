---
doc: Audit — Risks, Decisions & Roadmap
id: AUDIT-004
version: 1.0
status: Final
created: 2026-06-18
depends_on: AUDIT-000, AUDIT-001, AUDIT-002, AUDIT-003
audience: Sponsor, Architect, Build lead, PM
---

# Audit — Risks, Decisions & Roadmap

Turns the findings into (1) a ranked enterprise risk register, (2) the decisions only the sponsor can make, (3) a recommended target architecture, and (4) a phased roadmap re-baselined onto the code that already exists.

---

## 1. Risk register

Scored **Likelihood × Impact** (H/M/L). Ordered by exposure.

| # | Risk | L | I | Exposure | Mitigation | Owner |
|---|---|:--:|:--:|:--:|---|---|
| R1 | **Nothing has run on real data.** Every "BUILT"/"specified" is validated only against author-designed fixtures (`[X-1]`, Discrepancy #10). The system exists to absorb mess it has never met. | H | H | **Critical** | Phase B real-data pilot: one real iTrade pull + one real bid round end-to-end before any further breadth. Treat the first real cycle as a test, not a delivery. | Sponsor + Build |
| R2 | **Wrong-brain lock-in.** If breadth is built on the as-built's min-cost single-winner solver, every downstream consumer inherits a grain (G1) and a decision model (G2) the brief proves wrong. | M | H | **High** | Decide D2 *before* building outward; ship G1+G2 together (Ed's direction) as the first engine change. | Architect |
| R3 | **Greenfield rebuild of an existing store.** Building the brief literally ("greenfield backend") would discard 63 tables, 46 identity FKs, and the calc-run spine — months of correct work. | M | H | **High** | Decide D1 = reconcile-and-extend. Make the as-built schema the migration baseline. | Architect |
| R4 | **False audit assurance.** The hash-chain *looks* operative but is a scaffold (`[D-7]`, G11). An auditor or a control review could be misled. | M | M | Med | Either finish population + write-only enforcement (Phase A) or relabel the control until it is live. | Build |
| R5 | **Safeties remain decorative.** Both packages store safety parameters and neither fires them, yet the intake calls them "the real product" (`[D-2]`, G4). The commercial deal's core governance is inert. | M | H | **High** | G4: lift to kickoff + build the execution/visualization path; pilot one safety (disaster trigger) on real terms. | Build |
| R6 | **The ECLS (stated source of truth) is missing**, and the as-built's quantitative claims are unverifiable from the package (`[D-5]`). Plans built on unverified claims can slip. | M | M | Med | Obtain the ECLS, `SYSTEM_SPEC.md`, `models.py`, migrations, and the test report; reconcile before committing the roadmap dates. | Architect |
| R7 | **No security/tenancy/NFR layer in either package** (`[D-4]`). Commercial bid/award data with no RBAC, PII handling, or retention is an enterprise non-starter. | H | M | **High** | Open the net-new NFR/security spec now; design tenancy (`client`) into the schema before breadth hardens it out. | Architect |
| R8 | **SQLite-shaped DDL as the Postgres baseline** (`[D-6]`): boolean 0/1, a vacuous CHECK. Migrating an unexercised schema risks semantic surprises. | M | M | Med | Regenerate + validate on real Postgres; add the migration roundtrip test the as-built claims it already has. | Build/DBA |
| R9 | **Single-key-person knowledge.** The whole truth (real process, real artifacts, which codebase is "the line") lives with Ed; the intake repeatedly hit "it's in the repo / behind a door." | M | M | Med | Capture decisions in the target spec + discrepancy register; reduce reliance on recall. | PM |
| R10 | **Scope sprawl from over-built edges.** The as-built shows a tendency to deepen the middle (10 commercial tables) while the value ends stay thin (`[D-9]`). | M | M | Med | Roadmap gates each phase on an *outcome* (a real artifact generated), not on table count. | PM |

---

## 2. Decisions for the sponsor

Each is a genuine fork the audit cannot resolve unilaterally. Recommendations included; the first option is the recommended one.

### D1 — Build path · **Recommend: Reconcile-and-extend**
The brief's #1 open item ("verify before greenfield") is answered by the as-built: a real governed store exists. Options:
- **(A, recommended) Reconcile-and-extend** the existing 63-table store; additive migrations for breadth, two breaking migrations for the grain. Preserves the identity integrity and calc-run spine.
- (B) Greenfield the brief's 36-table schema and port logic. Cleaner naming, but discards proven work and re-incurs the rigor the as-built already has.

### D2 — The brain · **Recommend: Adopt v3 (scoring + split), retire min-cost to a lens**
- **(A, recommended)** Lift v3's five-factor scoring + `max_two_per_dc` allocation as the engine library; the as-built's min-cost solver becomes **Scenario A = lowest-cost reference**. Ship G1 (split) + G2 (scoring) together.
- (B) Keep the as-built Scenario A and bolt scoring on top. Less rework now, but keeps a single-winner grain at the core and contradicts the brief's ground truth.

### D3 — Pricing · **Recommend: Lift to kickoff, keep storage, fire the safeties**
- **(A, recommended)** Declare pricing + the five safeties at kickoff (brief's placement); keep the as-built's commercial component storage and formula audit; build the safety-execution/visualization path.
- (B) Leave pricing at the commercial layer. Contradicts the real kickoff docs (Discrepancy #3/#11) and keeps safeties inert.

### D4 — Outward-facing sequence · **Recommend: Booking guide first**
Order to build `awd.*`: **award object → freeze → sign-off → generated outputs**, with the **booking guide** as the first generated artifact (most-used; it is the award table + logistics; v1.4 already has `generate_booking_sheet`). Then sign-off deck, then letters/email.

### D5 — Net-new enterprise scope · **Recommend: Tenancy + security in from the start; real-data pilot as Phase B gate**
Add `client`/tenant as a first-class reference entity now (cheap before breadth; expensive after). Author the security/RBAC/NFR spec in parallel with Phase A. Make a successful real-data pilot the **exit gate of Phase B** — no breadth ships until one real cycle runs.

---

## 3. Recommended target architecture (one diagram in prose)

```
                         ┌─────────────────────────────────────────────┐
   KICKOFF (in-gate) ───▶│  cyc.*  setup keystone: objective, pricing   │
   real kickoff doc      │  basis + 5 SAFETIES, PBA, terms, RFI set,    │
   becomes the rail      │  timeline rail, narrative (G5, G4, G10, G12) │
                         └───────────────┬─────────────────────────────┘
                                         │ declares structure, drives every read
   FEEDS                                 ▼
   iTrade receipts ──┐      ┌────────────────────────┐   ┌───────────────────────┐
   KCMS scan ────────┼─────▶│ perf.*  history +      │   │ norm.*  persistent lot │
   scorecard ────────┘      │ scorecard (2 snaps,G6) │   │ + attribute taxonomy   │
                            └───────────┬────────────┘   │ (G8) over alias+        │
                                        │                 │ quarantine (KEEP)      │
   BIDS (multi-template) ──────────────▶│                 └───────────┬────────────┘
                                        ▼                             ▼
                            ┌──────────────────────────────────────────────────┐
                            │ bid.*  one grain; two origins + distance (G7);    │
                            │ KEEP: 5-mode landed cost · 7-gate eligibility ·   │
                            │ capacity scopes · demand≠capacity CHECK           │
                            └───────────────────────┬──────────────────────────┘
                                                    ▼
                            ┌──────────────────────────────────────────────────┐
                            │ eng.*  SEALED runs (KEEP calc-run spine) +        │
                            │ bid_score 5-factor (G2) + scenarios A–G +         │
                            │ scenario_award SPLIT w/ volume_share (G1)         │
                            └───────────────────────┬──────────────────────────┘
                                                    ▼  human selects (decision-support, never auto)
                            ┌──────────────────────────────────────────────────┐
                            │ awd.*  award → freeze_at → award_layer →          │
                            │ signoff (portfolio) → generated_document (G3)     │
                            │ draft→SENT governance gate (G9)                   │
                            └───────────────────────┬──────────────────────────┘
   SIGN-OFF (out-gate) ◀─────────────────────────────┘  booking guide · deck · letters · email

   audit.*  LIVE hash-chained event_log (G11) under everything  ·  "open last cycle" = one query
   cross-cutting: client/tenant + RBAC + NFRs (net-new)  ·  rail generated from cyc timeline (G10)
   UI last: a thin view over the store (ADR-001, both agree)
```

**Inheritance rule (restated):** for every layer, take the brief's *shape and intent* and the as-built's *constraint discipline and the seven KEEP capabilities* — never regress to the brief's thinner schema, never keep the as-built's wrong brain.

---

## 4. Phased roadmap (re-baselined onto existing code)

Aligned to the brief's own A–F sequence (`BUILD_04`), but starting from "a store already exists" rather than greenfield. Each phase exits on a **demonstrated outcome**, not a table count (mitigates R10).

| Phase | Goal | Key work (gaps) | Exit gate |
|---|---|---|---|
| **0 · Reconcile** | Lock the foundation | Obtain ECLS + code + tests (R6); regenerate schema on real Postgres, kill SQLite-isms + no-op CHECK (`[D-6]`); record D1–D5; author NFR/security + `client` tenancy spec (R7) | Decisions ratified; schema migrates clean on Postgres; target spec v1.0 supersedes both packages |
| **A · Spine hardening** | Make the governed store enterprise-true | Finish/relabel the audit hash-chain → live (G11); add `client`/RBAC; keep calc-run spine, identity FKs, landed cost, eligibility, VSP (the KEEP list) | Live event log proven; "open last cycle" query returns full story; RBAC enforced |
| **B · History + normalization + REAL DATA PILOT** | Prove it on reality | `itrade_receipt` (receipt grain) + `kcms_movement` + `supplier_scorecard` (G6); persistent `norm.lot` + attribute taxonomy (G8); two-origins + `zip_centroid` distance (G7) | **One real iTrade pull lands; items propose lots; a human confirms; scorecard snapshot computes — the program's top risk (R1) retired** |
| **C · Kickoff keystone + rail** | The in-gate, for real | Rich `cyc.*` (objective, pricing+safeties, PBA, working capital, KPM, RFI set, timeline, narrative — G5); rail generated from timeline (G10); Stage-0 in-gate (G12) | A cycle is declared from a real kickoff doc and the console renders its rail from the cycle |
| **D · The brain** | Right engine, shipped together | Lift v3 scoring → `bid_score` (G2); scenarios A–G; **relax single-winner + add `volume_share` split (G1)**; safeties executable/visualizable (G4) | A stored round runs and reproduces v3's verified scoring + split allocation against a known input |
| **E · Outward-facing half** | Close the loop | `awd.award`→freeze→`award_layer`→`signoff`; `generated_document` (booking guide first, then deck, letters, email) from records (G3); draft→SENT gate (G9); lift v1.4 generators | A chosen scenario becomes frozen awards; the booking guide + sign-off deck generate from records; savings-vs-STLY computes |
| **F · API hardening, then UI** | A view onto the store | Finalize API; build the front end last (ADR-001, both agree) | UI renders live and historic cycles identically from the store |

**Dependencies:** 0 → A → B → C → D → E → F. B and C can overlap once A is done. D depends on B (real cost/history feeds the scorer) and C (cycle config drives the run). **The UI does not start until E is proven** — a good front end is a view onto the store, and on a stateless or half-built store it can only be a nicer way to forget everything each run (Session 6, Addendum 2).

**Note on payoff timing (from the intake):** the historical benefit starts at cycle 2 and compounds; cycle 1 *produces* the record, it does not consume one. So Phase B's pilot is the inflection point — until one full cycle completes on real data, the system's reason-for-being (cure historical blindness) returns zero.

---

## 5. What this audit did *not* resolve (honest boundaries)

- It could not verify the as-built's quantitative claims (63 tables it *can* see; 14 migrations, 796 tests, the ECLS it **cannot** — `[D-5]`, R6).
- It could not test either schema on real Postgres or real data (R1, R8) — those are Phase 0/B gates, not desk-audit work.
- It assumes "gsps" = **gaps**; if you meant a specific named deliverable, the section emphasis (not the findings) would shift.
- The roadmap dates are deliberately omitted — they depend on D1–D5 and on obtaining the missing source-of-truth documents (R6). Sequence is firm; calendar is not yet estimable.
