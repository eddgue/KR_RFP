---
doc: Data Model
id: DOC-002
version: 1.0
status: Draft
created: 2026-06-17
last_updated: 2026-06-17
depends_on: DOC-001 (System Overview & ADRs)
---

# Data Model

The companion to `BUILD_03_schema.sql`. This explains *why* each table exists and how the grain holds together. Read the ADRs (DOC-001) first; they justify the decisions this model encodes.

The model has eight layers, each a PostgreSQL schema: `ref`, `norm`, `cyc`, `bid`, `eng`, `awd`, `perf`, `audit`.

---

## The grain, stated once

Every priced fact resolves to: **supplier × lot × DC × timeframe × round × price**.

- **Lot** (parent product), not UPC, is the bid and award grain. UPC maps up to lot through the normalization layer.
- **Timeframe** is a dimension, never a forked workbook.
- **Round** is variable (R1..Rn), with `is_final` / prior as flags, not hardcoded stages.
- **Price** is a set of components (FOB, freight, delivered, xdock, VegCool, discount) that resolve to a landed number; for index basis the components are stored and the price computes.

---

## Layer 1 — `ref` (reference / dimensions)

| Table | Holds | Note |
|---|---|---|
| `commodity` | SAP commodity code → name | 619 Onions, 617 Tomatoes |
| `subcommodity` | The anchor code + description | Carries grouped specs + packing variants; `is_organic` / `pack_type` are parsed hints only |
| `dc` | Distribution center → region | Region drives FOB region in scoring |
| `supplier` + `supplier_alias` | Canonical supplier + name variants | Auto-upsert from bid intake; aliases collapse variants |
| `item` + `item_alias` | A physical case SKU + its identities | KLN, UPC, RMS Case SKU all resolve to one item |
| `fiscal_calendar` | Kroger fiscal date map (to 2037) | Enables STLY, the headline savings metric |
| `zip_centroid` | Zip → lat/lon | Ship-from → DC distance (freight proxy) |

---

## Layer 2 — `norm` (the lot store)

This is the layer the v3 engine does **not** have. It replaces the fragile `product&DC` string-concat match key with a real, sticky mapping.

| Table | Holds | Note |
|---|---|---|
| `lot` | The canonical parent product | e.g. "PREMIUM SNACKING 9OZ", "FIELD BEEFSTAKE 17LB" |
| `attribute_def` | The taxonomy | Universal core (ORGANIC, COLOR, SIZE, PACK) + per-commodity extensions (tomato: VARIETY, PROCESS; onion: PACK TYPE, STORAGE) |
| `lot_attribute` | The decomposition of each lot | Storing attributes lets you regroup (all organic, all field-process) without re-mapping |
| `item_lot_map` | UPC/item → lot, **sticky** | `status` = proposed (engine) → confirmed (human). Persists across cycles. One live lot per item. |

**Lifecycle:** the importer proposes a lot for each new item from its description (Ed's Norm-sheet logic, turned into rules). A human confirms the unsure ones. Confirmed maps stick — next cycle, the same UPC arrives already mapped. Raw item stays underneath; attributes and lot sit on top; nothing is overwritten.

---

## Layer 3 — `cyc` (the setup file / kickoff)

The keystone. Declared at the strategy kickoff (the in-gate) and drives every downstream read.

| Table | Holds | Note |
|---|---|---|
| `cycle` | Commodity, objective, pricing basis, horizon, dates, status | `status` traces the lifecycle through both gates |
| `cycle_timeframe` | The active timeframes | **Dimension, not a fork.** N TFs in one engine. |
| `cycle_round` | R1..Rn, bid type, final/prior | Variable rounds; flags not stage numbers |
| `cycle_dc` | DC scope | Default ALL (national) |
| `cycle_lot` | Lot scope | |
| `cycle_term` | PBA / program terms | Cost Structure, Food Safety, Service Level — accepted Y/N by supplier |

---

## Layer 4 — `bid` (intake + volumes)

Multiple intake templates (tomato flat sheet, onion 9-tab hybrid) collapse to **one destination grain**.

| Table | Holds | Note |
|---|---|---|
| `bid` | supplier × lot × DC × tf × round + completeness + both origins | `grow_origin` and `ship_from_zip` are separate and never auto-derived from each other |
| `bid_price` | Cost components | `all_in` primary; fallback = FOB + freight + VegCool − discount. **CHECK enforces the double-subtraction guard.** |
| `bid_index_component` | Index-basis pieces | Resolved price computes, not stored fixed |
| `volume_requirement` | Required volume per lot/DC/tf | "As needed" is a first-class value; coverage scoring skips it |
| `volume_limit` | Supplier capacity | Constrains the split allocation |

**The double-subtraction guard** (`no_double_discount` CHECK): if `all_in` is already net of discounts (`is_all_in_net_of_discount = true`), `lot_discount` must be blank. This is the footgun the engine glossary called out, moved from a note into the schema.

---

## Layer 5 — `eng` (immutable runs, scores, scenarios)

| Table | Holds | Note |
|---|---|---|
| `analysis_run` | One sealed run + full `config_json` | Reproducible, auditable. A correction is a NEW run. |
| `bid_score` | Per bid per run: 5 factors + composite + eligibility | Cost is 35% of `rec_score`, not 100%. `gate_flags` carry the reasons. |
| `scenario` | The lenses A–G | A benchmark, B recommendation, C incumbent defense, D max-N, E exclusion, F custom, G preferred |
| `scenario_award` | **The split award** | One row per awarded supplier per cell, each with `volume_share` |

`scenario_award` is the corrected grain: a cell (DC × lot × tf) is allocated across one *or more* suppliers, capacity-constrained, with `cap_breach_flag` surfacing when the max-per-DC is exceeded.

---

## Layer 6 — `awd` (selected awards, freeze/layer, outputs)

| Table | Holds | Note |
|---|---|---|
| `award` | The human-selected award, promoted from a scenario | Multiple rows per cell (split). `frozen_at` seals it at sign-off |
| `award_layer` | Post-freeze changes | Live/changed values layer on top, date-stamped; raw award always recoverable |
| `signoff` | The out-gate approval | Portfolio-level; savings vs STLY headline |
| `generated_document` | Booking guide, sign-off deck, letters, confirmation email | **Generated from records**, not hand-built |

**Freeze-and-layer:** once `award.frozen_at` is set, the row is immutable. Every later change writes to `award_layer`. The original award and the current state are both always reconstructable.

---

## Layer 7 — `perf` (iTrade, KCMS, scorecard)

| Table | Holds | Note |
|---|---|---|
| `itrade_receipt` | Every PO receipt + cost components + fiscal stamp + flags | **One feed, two jobs:** historical awarded cost AND the scorecard |
| `kcms_movement` | Scan movement / margin | A DISTINCT feed from iTrade |
| `supplier_scorecard` | Two frozen snapshots per cycle | Kickoff + sign-off; all metrics derive from `itrade_receipt` |

---

## Layer 8 — `audit` (the event log)

`event_log` is append-only and is the line between a system of record and a pile of file generators. Every state change (created, sealed, frozen, superseded, signed-off) is an event. **"Open last cycle"** is a query: `cyc.cycle` joined through its rounds, bids, runs, scenarios, and awards, with the event trail proving the order things happened.

---

## What this model fixes, mapped to the intake

| Old-spec / engine gap | Fixed by |
|---|---|
| String-concat match key | `norm.item_lot_map` (sticky lot mapping) |
| One supplier per cell (locked, wrong) | `eng.scenario_award` / `awd.award` rows per supplier with `volume_share` |
| Stateless, no history | The whole persistent model + `audit.event_log` |
| Auto-award solver | `eng.bid_score` (proposes) → human selects → `awd.award` |
| Timeframe forked per workbook | `cyc.cycle_timeframe` dimension |
| Live-formula fragility / silent overwrite | Immutable `analysis_run` + freeze-and-layer |
| Cost double-subtraction | `bid_price.no_double_discount` CHECK |
| Two origins conflated | Separate `grow_origin` / `ship_from_zip` |
| Booking guide / sign-off hand-built | `awd.generated_document` |

---

## Changelog

| Version | Date | Author | Change Summary |
|---------|------|--------|----------------|
| 1.0 | 2026-06-17 | Session | Initial draft from intake sessions 1–6 |
