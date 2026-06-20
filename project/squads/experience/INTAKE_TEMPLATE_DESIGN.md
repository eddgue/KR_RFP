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
- **Grouping.** Related columns can be grouped (e.g. the cost stack: FOB + Delivery + VegCool − Lot
  Discount; the volume block; the lane/transit block) so the template reads as labelled sections, not
  a flat column run.
- **Saved presets → schema mapping.** The selection + grouping is saved as a reusable PRESET. The
  preset is what lets the system map a received file back to the canonical schema on ingest — the
  mapping is REMEMBERED per template/preset, not re-inferred on every upload. (Contrast the pilot's
  flexible `ingest_any` inference, which is the fallback for non-templated files; here the buyer's own
  template carries a known, saved mapping.)
- **Delivery as a guided walk-through.** Surface this as a template-builder wizard / walk-through:
  step the buyer through choosing columns, grouping them, and saving the preset.

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

## Implementation anchors (already in place to build on)

- The bid column set + ordering: `app/domain/bid/template_schema.py` (`BidColumn`, `PRICE_COLUMNS`).
- Completeness classification (the traffic-light source of truth): `bid_ingester` `Completeness`
  (`NO_BID` / `INCOMPLETE` / `BID`).
- Round-trip-by-key ingest the presets must preserve: D20 / D21 (`ingest_template`).
- The "always-available, optionally-used" column precedent: `Transit Days` (migration 0011).
