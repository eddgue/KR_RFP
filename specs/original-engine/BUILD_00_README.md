# Original Engine — As-Built Documentation Package

This package documents the **codebase that actually exists today** — the inherited, half-built RFP/sourcing engine — in the *same five-document shape* as the `RFP_Engine.zip` build package (README + System Overview & ADRs + Data Model + schema.sql + Tech Spec). It is written so it can be **diffed, side-by-side, against the brief** to author a final spec.

It is **descriptive, not aspirational.** Every table, service, and rule named here is present in the running code as of the state below. Where the code does *not* do something, this package says so plainly rather than describing the intended target.

- **Code state:** `main` @ `8d96004`.
- **Database version (Alembic head):** `j29e0cpm01`. 14 migrations in the chain.
- **Tables in the live schema:** 63 (see `BUILD_03_schema.sql`).
- **Stack:** Python + SQLAlchemy 2.0 ORM, Alembic, Streamlit. One synthetic SQLite database for the demo. No real Kroger or supplier data anywhere in the repo.
- **Governing internal document:** `docs/RFP_ENGINE_CONTROL_LAYER_SPEC_v1_0.md` (the "ECLS"). On any conflict, that spec wins. This package describes what exists in code; the ECLS describes the intended target.

---

## Read in this order

| # | File | What it is | For |
|---|------|------------|-----|
| 0 | `BUILD_00_README.md` | This file. Index + how to read + the honest reality. | Everyone |
| 1 | `BUILD_01_SYSTEM_OVERVIEW_AND_ADRS.md` | What the system actually is + the 8 architecture decisions the code already embodies. | Architect, gap analysis |
| 2 | `BUILD_02_DATA_MODEL.md` | The as-built data model: the 8 logical layers across 63 tables, grain rules, lifecycle. | Architect, backend dev |
| 3 | `BUILD_03_schema.sql` | The real PostgreSQL DDL, generated directly from the SQLAlchemy models. The actual 63 tables. | Backend dev |
| 4 | `BUILD_04_TECH_SPEC.md` | Components, services, data flow, the Streamlit surface, and the build sequence as it actually happened. | Backend dev, gap analysis |

The authoritative as-built narrative behind this package is `docs/SYSTEM_SPEC.md` in the repo (the two-view spec). This package re-cuts it into the brief's shape for diffing.

---

## The one thing to know before diffing

The brief (`RFP_Engine.zip`) was written from Eduardo's **real** RFP artifacts — kickoff docs, iTrade pulls, the Norm sheet, real supplier bids, the leadership sign-off deck, and the real `rfp_analysis_engine_v3.py`. **This codebase was mostly built from an older written spec.** Where the two disagree, **the brief is ground truth.**

So this package is not a competing design. It is an **inventory of what is already standing**, so the gap analysis can be precise: what to keep, what to relax, what to add. The biggest known divergences (carried verbatim from the as-built spec's own reconciliation) are:

1. **Awards are single-winner in code; the brief allows splits.** Scenario A *forbids* more than one supplier per cell. The brief allows multiple suppliers per cell with a `volume_share`, as an edge case (e.g. organics).
2. **The code's engine is an exact minimum-cost solver; the brief's is decision-support.** Scenario A picks the lowest feasible benchmark. The brief scores 5 banded factors (Price .35, Coverage .25, Historical .20, Z-Risk .10, Continuity .10) and a human picks.
3. **The code has only Scenario A; the brief has 7 lenses (A–G).**
4. **The code never sends; the brief makes "Sent" a governance gate.**
5. **The code declares the pricing model at the bid/commercial layer; the brief declares it at kickoff**, including the five pricing safeties.

These are named again, in detail, in `BUILD_01` (ADRs) and `BUILD_04` (reconciliation).

---

## What the code already gets right (agrees with the brief)

- **Lot is the grain, not UPC**, via a sticky alias map (the alias layer).
- **Two origins kept separate** (ship-from ≠ grow-origin) — *as a principle*; see the honesty note in `BUILD_02`.
- **Immutable runs, append-only, nothing deleted, an audit backbone.**
- **Timeframe is a dimension, not a forked workbook.**
- **Demand ≠ capacity** — enforced by a database CHECK.
- **One feed powers historical cost** (the scorecard half is not built yet).

---

## Honesty notes (so absence is legible, not accidental)

- A recent commit mentions an "aggregator" / "Cycle Setup" upload tool. That feature was **removed** from the code and is **not** part of the live product. The live product is the 10-stage Process Console.
- There are **two** Streamlit entrypoints in the repo. Only `streamlit_app.py → app_scenario_a_preview.py` is the product. `app.py` is an older Charter form, not routed.
- Several capabilities exist only as **scaffolds, contracts, or placeholders** (audit hash-chain, NoteThread, decision-justification taxonomy, the whole of Stages 8–9). Each is flagged where it appears.

---

## Status legend (used throughout this package)

| Mark | Meaning |
|------|---------|
| **BUILT** | Implemented in code, has tests, runs today. |
| **SCAFFOLD** | Table or stub exists but the logic behind it is not implemented. |
| **CONTRACT-ONLY** | A written specification exists but no code yet. |
| **PARKED** | Deliberately not started; awaiting authorization. |
| **NOT BUILT** | Named in the process but no code and no contract yet. |
