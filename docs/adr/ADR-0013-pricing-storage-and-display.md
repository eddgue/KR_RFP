# ADR-0013 — Pricing: period-grain storage, setup-file-driven display

- **Status:** Accepted (sponsor-raised 2026-06-18)
- **Deciders:** Sponsor (Ed), PM, Solution Architect, Product, Engine lead
- **Relates:** Decision D12; intake Session 1 "locked truths" #1 (period grain) & #5 (setup file drives the read); D3/G4 (pricing declared at kickoff); D9 (one model per RFP)

## Context

From the intake (Session 1, and the `00_INDEX` locked truths): *"Price and components are preset; the system knows from the setup file how to display them when calling an RFP, live or historic."* This separates two concerns the original specs blurred:

- **How pricing is STORED** — normalized, at the period grain, as components.
- **How pricing is DISPLAYED** — driven by the cycle's setup file, so the same stored facts render consistently live or historic.

Getting this separation right is what makes "open last cycle" render correctly (a historic RFP reopens and displays exactly as it did live) and what lets one engine handle fixed, index, full-year, and period-by-period deals without forking.

## Decision

**Store pricing as period-grain facts; render it through the setup file.**

### Storage (facts)
- The priced grain is **supplier × lot/item × DC × period × price** (period is a first-class dimension, never a forked workbook — ADR-008/timeframe-as-dimension).
- Prices are stored as **components**, not a single opaque number: FOB, freight, delivered, cross-dock, VegCool, discount; for index basis, the **basis / market reference / adder** (and QDP where applicable).
- **Fixed** deals: the agreed price repeats across the periods it covers.
- **Index** deals: the components are stored and the effective price **resolves** (computed), not stored as a frozen number.
  - *Worked example (sponsor):* **Visalia onions** are priced **market mid − discount** today — an index basis where the store holds `{market reference / mid, discount}` and the price resolves to `mid − discount` (FOB falls out). Never a frozen number; re-resolves as the market moves.
- **Period-by-period** deals (e.g. weakly-correlated commodities priced across all 13 periods, each with its own sourcing region): each period carries its own price/components — the period grain already supports this with no special case.
- One pricing table; the **basis** determines which columns carry the weight. The double-subtraction guard (no_double_discount) is enforced in the store, not left to a note.

### Display (render contract)
- The **setup file** (`cyc.cycle` pricing declaration: basis, cadence — FULL_YEAR / SEASONAL / TIMEFRAMES(n) / PERIOD_BY_PERIOD(13) / QUARTERLY / MONTHLY / WEEKLY — which components are shown, the safeties) tells the system **how to render** the stored pricing.
- The system renders each RFP **from stored structure + the setup file**, never from a person's memory or a bespoke workbook layout.
- **Same render live or historic:** because the setup file is stored *with* the cycle (it is the cycle), reopening a past RFP reproduces its original presentation. This is the concrete mechanism behind "open last cycle."

## Consequences

- Clean split: `bid.*` (and the commercial pricing layer) hold period-grain component facts; `cyc.*` holds the declared render contract. A view/renderer composes them.
- The engine reads facts uniformly regardless of basis/cadence; presentation differences are config, not code forks (kills the Colored-Potato per-timeframe clone).
- Historic fidelity is structural: the stored setup file guarantees a past cycle displays as it did.
- Pairs with D11 (the savings baseline) and the safeties (D3/G4): contracted components are stored, effective (iTrade actual) is comparable against them, and the setup file says how to show the deal.

## Rejected

- Storing a single resolved price per line (loses index reconstruction, the contracted-vs-effective story, and component-level audit).
- Letting the UI/workbook layout define presentation per cycle (the bespoke-fork failure mode; breaks "same render live or historic").
