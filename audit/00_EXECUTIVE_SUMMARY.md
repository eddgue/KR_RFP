---
doc: Audit — Executive Summary
id: AUDIT-000
version: 1.0
status: Final
created: 2026-06-18
depends_on: None
audience: Sponsor (Ed / Sourcing), Architect, Build lead
---

# Audit — Executive Summary

## 0. What was audited, and the one interpretation to confirm

Two five-document spec packages for the **Kroger produce RFP / sourcing engine**, deliberately authored in the *same shape* so they can be diffed:

| Tag | Package | Lineage | Status in its own header | What it is |
|---|---|---|---|---|
| **BRIEF** | `specs/rfp-engine/` (was `RFP_Engine.zip`) | **Intake process** — a six-session structured intake (`intake/SESSION-01..06`) run against Ed's *real* artifacts | Draft v1.0, 2026-06-17 | A forward-looking **target spec** + build package. 36-table greenfield schema. |
| **AS-BUILT** | `specs/original-engine/` (was `OriginalEngine.zip`) | **Vibe-coding process** — an inherited codebase grown stage-by-stage from an older written spec | As-Built v1.0, 2026-06-18 | A **descriptive inventory** of code that exists today. 63 tables, 14 migrations, 796 passing tests, synthetic SQLite. |

**Scope requested:** (1) a full audit of the documents, and (2) a full analysis of **gaps**. I read "gsps" as **gaps** — the gap analysis between the two engines — because that is the explicit, stated purpose of both packages ("so it can be diffed, side-by-side, against the brief"; "so the gap analysis can be precise"). No string `GSP` appears anywhere in either package. If "GSP" meant something specific to you (e.g. a named *Global Sourcing Process* deliverable, or your internal name for these spec packages), say so and I will re-cut section emphasis — but the analysis below covers that reading regardless, since the spec packages *are* the subject.

This summary is the 2-page read. Depth lives in:
- `01_DOCUMENT_AUDIT.md` — the documents as artifacts (quality, completeness, traceability, enterprise-readiness scorecard, defects).
- `02_GAP_ANALYSIS.md` — the heart: ADR-by-ADR and capability-by-capability diff, severity, keep / relax / add.
- `03_SCHEMA_DIFF.md` — table-level diff of 63 vs 36 tables across the eight logical layers.
- `04_RISKS_DECISIONS_ROADMAP.md` — enterprise risks, the open decisions only you can make, a recommended target architecture and phased roadmap.

---

## 1. The headline finding

**Neither package is the product, and the two are not competitors — they are the two halves of one system.** This is the same verdict the intake itself reached about the two *codebases* (Session 6: "v3 is the brain, the repo is the spine, neither alone"), now true one level up, about the two *specs*:

- The **BRIEF** has the right **target shape, the right brain, and the right governance philosophy** — lot-grain via sticky normalization, split (allocation) awards, five-factor decision-support scoring with seven lenses, pricing declared at kickoff, freeze-and-layer, a live event log, "sent" as a governance gate, and the whole outward-facing half (booking guide, sign-off deck, letters) generated from records. But its **data model is thin and under-constrained**, several of its load-bearing ideas (the five pricing *safeties*) are described in prose yet never modeled, and **nothing in it has touched real data**.

- The **AS-BUILT** has a **deep, genuinely enterprise-grade data and governance spine** — 63 tables with 67 CHECK constraints and 46 composite-identity foreign keys that the brief does not have a single instance of; sealed calculation runs with hashed input/output manifests; a five-mode landed-cost standardizer with eight blocking reasons; a seven-gate eligibility engine; a demand-vs-capacity separation enforced by a database CHECK; a ten-table commercial-pricing layer with a replayable formula audit. But it implements the **wrong brain** (an exact minimum-cost, single-winner solver), **at the wrong pricing layer** (commercial/bid level, with the safeties stored inert), and it is **missing the entire outward-facing half** (no award object, no freeze, no sign-off, no generated documents).

**The enterprise target is the brief's brain and target shape, implemented with the as-built's constraint discipline, with the named divergences reconciled.** Concretely: keep the as-built spine where it is already right; *relax* the single-winner constraint to permit splits; *replace/augment* the min-cost solver with the brief's (v3's) five-factor scoring and `max_two_per_dc` allocation; *lift* pricing to kickoff and make the five safeties executable; and *build* the missing award/sign-off/output layer plus the supplier scorecard and KCMS feed.

---

## 2. The single most important fact the two packages, together, establish

The BRIEF's **number-one open item** — repeated in its README, its System Overview, and its tech spec — is:

> "⚠️ Verify before greenfield. Confirm whether the live app writes to a database or just returns a zip *before* building this store from scratch."

The AS-BUILT package **answers it**: yes, a durable, governed store already exists — 63 tables under Alembic, 14 migrations, DB-enforced immutability, 796 passing tests. So the build path is **not** greenfield. It is **reconcile-and-extend** against a real codebase. Neither document closes this loop explicitly because they were written a day apart and never cross-referenced; **closing it is the first thing this audit does, and it changes the entire plan** (see `04`, Decision D1).

---

## 3. Verdict by dimension (enterprise-readiness scorecard)

Scored 1–5 (1 = absent, 3 = adequate, 5 = strong). Full rubric in `01`.

| Dimension | BRIEF | AS-BUILT | Target needs |
|---|:---:|:---:|---|
| Requirements traceability (evidence → decision) | **5** | 3 | Keep the brief's intake/discrepancy-log discipline |
| Business-process fidelity (matches how Ed really works) | **5** | 2 | The brief is ground truth; as-built diverged |
| Engine / decision logic | 4 *(specified)* | 2 *(wrong model, but built)* | Brief's 5-factor + splits, on real code |
| Data-model rigor (constraints, identity integrity) | 2 | **5** | Adopt the as-built's discipline |
| Governance & audit spine | 3 | **4** | As-built calc-run ledger; brief's live event log |
| Outward-facing half (awards, sign-off, outputs) | 4 *(specified)* | 1 *(absent)* | Build it; brief specifies it well |
| Pricing model + safeties | 3 *(right layer, unmodeled)* | 3 *(rich storage, wrong layer, inert)* | Merge: kickoff layer + executable safeties |
| Non-functional requirements (security, NFRs, ops) | 1 | 2 | **Neither is adequate — net-new work** |
| Verified against real data | **1** | **1** | The top program risk for both |

**Net:** the brief wins on *what to build and why*; the as-built wins on *how to build it to enterprise standard*. Both fail the same two tests — **no real-data validation** and **no non-functional/security/operability layer at all**. Those two are net-new and belong in the target spec from day one.

---

## 4. The gaps, ranked (full detail in `02`)

| # | Gap | Direction | Severity | Note |
|---|---|---|:---:|---|
| G1 | Single-winner award grain vs **split allocation** | as-built must change | **Critical** | A `UNIQUE(run, dc, lot, tf)` constraint physically forbids splits today. Foundational. |
| G2 | Min-cost solver vs **5-factor decision-support scoring** | as-built must change | **Critical** | As-built has the *restraint* but not the *scoring model*; only Scenario A vs lenses A–G. |
| G3 | **Entire `awd` layer absent** (award, freeze, layer, sign-off, generated docs) | as-built must build | **Critical** | The thinnest part of the code; the brief's outward-facing half. |
| G4 | Pricing at bid/commercial layer + **safeties inert** vs at kickoff + executable | both must move | **High** | As-built over-built storage at the wrong layer; brief named the safeties but never modeled them. |
| G5 | Kickoff keystone is **thin** in both relative to the real kickoff docs | both must extend | **High** | Annual spend, objective, PBA governance, working-capital, KPM, RFI set, timeline rail, narrative blocks. |
| G6 | **Supplier scorecard + KCMS feed** absent in as-built | as-built must build | **High** | Brief: one iTrade feed → cost + scorecard (two frozen snapshots); KCMS distinct. |
| G7 | **Two origins + zip-centroid distance** not built in as-built | as-built must build | Medium | Principle agreed; no `grow_origin`/`ship_from_zip` pair, no distance calc. |
| G8 | **Lot attribute taxonomy** absent in as-built | as-built must build | Medium | Conv/Organic split is load-bearing in the sign-off deck; can't regroup without it. |
| G9 | "**Sent**" governance gate vs drafts-only | as-built must change | Medium | Conceptual reversal: as-built treats "never sends" as a virtue; brief calls it wrong. |
| G10 | Hardcoded 10-stage rail vs **rail generated from the cycle** | as-built must change | Medium | This *is* the "non-standard process" fix. |
| G11 | Audit hash-chain is a **scaffold** (looks present, isn't live) | as-built must finish | Medium | Enterprise risk: false sense of auditability. |
| G12 | **Stage-0 governance in-gate** not implemented | as-built must build | Medium | No real cycle can run on real data without it. |
| — | **No real data, no security/NFR layer** | both | **High (program)** | Net-new; see `04`. |

**Where the as-built is ahead of the brief** (and must be *kept*, not rebuilt): composite-identity referential integrity, the sealed calc-run governance, the five-mode landed-cost standardizer, the seven-gate eligibility engine, the demand≠capacity CHECK, the typed-alias + quarantine identity system, and the volume-&-scope-prep maturity. `02 §6` and `03` enumerate these.

---

## 5. Decisions only you can make (full framing in `04`)

1. **D1 — Build path: reconcile-and-extend, not greenfield.** The store exists. Recommendation: migrate the existing 63-table schema forward; do not rebuild. *(Resolves the brief's own #1 open item.)*
2. **D2 — The brain: adopt v3's five-factor scoring + split allocation as the engine**, retiring the as-built's min-cost Scenario A to a "lowest-cost reference" lens (which is exactly the brief's Scenario A). Per Ed's 2026-06-17 reconciliation, G1 and G2 ship *together* because both touch the solver core.
3. **D3 — Pricing: lift the model to kickoff and make the five safeties executable/visualizable**, keeping the as-built's commercial component storage.
4. **D4 — Sequencing of the outward-facing half** (awards → freeze → sign-off → generated outputs) and which generated artifact lands first (recommend booking guide).
5. **D5 — Net-new non-functional scope**: security/RBAC, tenancy ("Clients" as a first-class reference entity per Session 1), retention, real-data pilot. None of this exists in either package.

---

## 6. Recommended immediate next step

Authorize a **single reconciled target specification** ("v1.0 Build Spec") that supersedes both packages, built by:
- taking the **brief's `BUILD_01/02/04`** as the structural template (it is ground truth on process and intent),
- importing the **as-built's constraint discipline and the seven spine capabilities it already gets right** (kept verbatim where correct),
- resolving the twelve gaps above with the five decisions, and
- adding the **missing enterprise layer** (security, NFRs, real-data pilot) that neither package contains.

This audit is the input to that spec. `04` contains a phased roadmap (A→F) aligned to the brief's own build sequence, re-baselined onto the existing code.
