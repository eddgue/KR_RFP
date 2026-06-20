---
doc: Intake Template Design — REAL SOFTWARE (post-pilot). How buyers compose intake templates and
     how supplier-facing templates behave as governed forms.
id: EXP-INTAKE-TEMPLATE
squad: Experience / Output + Platform
status: Notes (captured from sponsor 2026-06-20; informs the post-pilot intake build — NOT the pilot)
created: 2026-06-20
relates: D20 (round-trip ingest), D21 (explicit key IDs), D23 (names not keys), D24 (presentation),
         EXP-PILOT-INPUTS (pilot input docs), bid template_schema (BidColumn set), migration 0011
scope: Forward-looking requirements for the REAL product's intake templates — the buyer-side template
       builder + column-mapping presets, and the supplier-side locked-form behaviour. Sponsor was
       explicit these are for the real software, not the pilot.
---

# Intake Template Design (real software)

Sponsor notes (2026-06-20), captured verbatim-in-intent so the post-pilot build inherits them. These
extend the principle already started in code: the bid column SET is a SUPERSET that is **always
available**, and any given process uses only the columns it needs (e.g. `Transit Days` was added as a
standard, optional, nullable column — migration 0011 — surfaced only when a submission supplies it).

## 1. Buyer-side: a column-selecting template builder with saved mapping presets

The buyer composes each cycle's intake template from the full column set, and the system remembers how
to read what comes back.

- **Full column superset, always available.** Every column the platform understands is part of the
  standard set. A process does not need all of them; unused columns are simply not selected. (Already
  realised for `Transit Days`; this generalises it.)
- **Natural column selection.** The buyer selects which columns this cycle's template carries in a
  natural way (pick from the set), rather than hand-editing a spreadsheet.
- **Grouping — including along the PERIOD axis, compact/expand.** Two kinds of grouping:
  - *Column grouping:* related columns read as labelled sections (cost stack: FOB + Delivery +
    VegCool − Lot Discount; the volume block; the lane/transit block) rather than a flat column run.
  - *Period grouping (the important one, sponsor 2026-06-20):* the platform records **every pricing
    component for EACH period (timeframe) in the fiscal year** — the granular per-period grain
    (already the bid grain: one row per DC × lot × item × **TF** × supplier, D12). The template must
    **compact and expand** over that period detail: expanded = every per-period entry visible;
    compact = the per-period rows rolled up / grouped by timeframe (e.g. periods → quarters → year).
    Realise this with **Excel row outline grouping** (the +/- collapse handles) keyed on the period
    dimension, so the buyer/supplier toggles between full per-period breakdown and a grouped summary
    without changing the underlying per-period data.
- **Saved presets → schema mapping.** The selection + grouping is saved as a reusable PRESET. The
  preset is what lets the system map a received file back to the canonical schema on ingest — the
  mapping is REMEMBERED per template/preset, not re-inferred on every upload. (Contrast the pilot's
  flexible `ingest_any` inference, which is the fallback for non-templated files; here the buyer's own
  template carries a known, saved mapping.)
- **Delivery as a guided walk-through.** Surface this as a template-builder wizard / walk-through:
  step the buyer through choosing columns, grouping them, and saving the preset.

## 1a. The period model — DATA is flat at the 13 fiscal periods; the TEMPLATE groups; intake fans out

The load-bearing pricing-intake decision (sponsor 2026-06-20, refined). The data structure stays
**flat and canonical**; the template does the grouping for supplier ease; intake expands the grouped
price back into the flat per-period rows. Chosen for **error-protection**: there is exactly ONE
storage grain, so every downstream calc/group/compare runs on a uniform structure.

- **Storage = FLAT at the 13 fiscal periods.** A fiscal year has **13 periods** (Kroger's 4-5-4
  retail calendar). Every offer/price is recorded in the database against **exactly ONE of the 13
  periods** — the database never stores a "grouped" or variable-grain price. This flat per-period
  table is the invariant the whole platform reads.
- **The TEMPLATE groups periods into a few timeframes (supplier-facing only).** A cycle's bid
  template defines a small number of timeframes, each = a contiguous span of periods, so the supplier
  prices a handful of timeframes instead of all 13. Example: **A = P1–2, B = P3–9, C = P10–12** → the
  supplier fills 3 price columns, not 13.
- **Intake FANS OUT the grouped price into the flat periods.** When a return comes in, each
  timeframe's price/components are written **flat to every period in that timeframe's span** —
  timeframe B (P3–9) priced once → periods 3,4,5,6,7,8,9 each get that price/components in the DB.
  "The grouping and calculating-out comes from the bid template" — the template carries the
  period→timeframe map; intake resolves it to the flat per-period rows. Keeps the **data structure
  flat and the supplier template easy** at the same time.
- **Compact/expand is a VIEW over the flat data (increment 2).** Excel row-outline grouping rolls the
  13 stored periods up into the template's timeframes (or quarters/year) for reading — the stored
  data never changes grain, only how much is shown.
- **Buyer trades precision vs supplier burden by choosing the timeframe grouping**, not the storage
  grain — fewer, wider timeframes = easier for the supplier (a flat year = one timeframe spanning all
  13); finer timeframes = more resolution. Storage is always the 13 periods regardless.

**Why this is the safest:** ONE canonical storage grain (13 periods) for every downstream consumer —
no variable-grain data ever enters the store; the supplier never faces 13 cells (the template groups
for them); the grouping is resolved at the boundary (intake fan-out), so a regrouping later is just a
different fan-out/roll-up over the same flat periods, never a re-collect.

## 2. Supplier-side: the sent template is a governed FORM

The template a supplier receives must behave like a true form, not an editable spreadsheet.

- **Only entry points are editable.** Price / volume / supplier-input cells are the only unlocked
  cells. Everything else — keys (D21), display names (D23), headers, structure, instructions — is
  hard-coded and the sheet is **password-protected** (locked cells + protected sheet), so a supplier
  cannot alter identity or structure, only answer.
- **Per-row readiness traffic light.** Each bid row shows a live status:
  - **Not bid** — no entry on the row (a declined cell; NOT a zero price).
  - **Bid incomplete** — some required entry points filled, others blank.
  - **Complete bid** — all required entry points for the row are present.
  This is the supplier-facing, live mirror of the ingester's completeness classes
  (`NO_BID` / `INCOMPLETE` / `BID`), so what the supplier sees as "complete" is exactly what ingests
  cleanly — fewer quarantines, less back-and-forth.

## Build status (graduating from notes to code)

- **§2 supplier governed form — DONE (2026-06-20).** The generated bid template is now a true
  locked form: raw key IDs hidden, only the price/volume entry cells unlocked (highlighted),
  password-protected sheets, and a per-row **Bid Status** traffic light (Not bid / Incomplete /
  Complete) — `app/domain/bid/template_generator.py`.
- **§1 column selection — DONE (increment 1).** `BidTemplatePreset`
  (`app/domain/bid/template_preset.py`) selects which entry columns a cycle's template carries from
  the superset; the generator emits exactly those, and a reduced preset still round-trips through
  ingest (test: `test_preset_reduces_columns_and_still_round_trips`). Built-in presets: full /
  all_in_simple / components.
- **§1 period model — calendar FOUNDATION DONE (increment 2a, 2026-06-20).** The authoritative
  Kroger fiscal calendar is now in the platform: `app/fiscal/calendar.py` + the reference table
  `app/fiscal/data/kroger_fiscal_periods.csv` (FY16..FY36, 273 rows, fully contiguous, derived from
  the sponsor's daily conversion table). It gives `period_for_date` (date → the one of 13 periods an
  offer lands in), `get_period`/`periods_in_year`, the timeframe presets
  (`fiscal_quarters`/`fiscal_halves`/`fiscal_year_timeframe`/`per_period` + a generic
  `group_periods` for arbitrary contiguous spans like A=P1-2,B=P3-9,C=P10-13), and `expand_to_periods`
  — the intake **fan-out** that writes a timeframe's price to each period in its span. Tested:
  `tests/fiscal/test_calendar.py` (11). **Confirmed facts** (use these, they correct earlier
  assumptions): 13 periods/year; quarters are **4-3-3-3** (Q1=P1-4, Q2=P5-7, Q3=P8-10, Q4=P11-13),
  not 3-3-3-4; most years are 52 weeks but a **53-week leap year** (~every 5-6 yrs: FY17/23/28/34)
  gives **Period 13 a 5th week**, so a period is **not always 28 days** — always read the span from
  the table, never assume a length. Stored authoritatively (data, not a date rule) so a future
  calendar quirk is a CSV update, not a code change ("protects us from future errors").
- **§1 period model (flat-13 STORAGE + fan-out on ingest + compact/expand view) — NEXT (increment
  2b), per §1a.** With the calendar in place, the remaining data-layer work: (a) store bids flat at
  the 13 fiscal periods (a `ref.fiscal_period` table seeded from the same CSV, and the bid grain
  carrying a period FK) and have intake call `expand_to_periods` to fan a timeframe's price out to
  each period; (b) the compact/expand VIEW rolls the 13 periods up into the template's timeframes.
  This is the schema work (the pilot's bid grain is currently one row per TF, single-period scope).
- **§1 renamed-column mapping, custom-preset persistence, the walk-through wizard — LATER.**

## Implementation anchors (already in place to build on)

- The fiscal calendar (period↔date, timeframes, fan-out): `app/fiscal/calendar.py` +
  `app/fiscal/data/kroger_fiscal_periods.csv`. The flat-13 grain everything below records against.
- The bid column set + ordering: `app/domain/bid/template_schema.py` (`BidColumn`, `PRICE_COLUMNS`).
- Completeness classification (the traffic-light source of truth): `bid_ingester` `Completeness`
  (`NO_BID` / `INCOMPLETE` / `BID`).
- Round-trip-by-key ingest the presets must preserve: D20 / D21 (`ingest_template`).
- The "always-available, optionally-used" column precedent: `Transit Days` (migration 0011).
