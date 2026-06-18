# Kickoff File Schema (the Setup File)

**Date:** 2026-06-17
**Source:** Extracted from four real kickoff docs (Field Tomato 2025/2026, HH Veg 2025, Wet+Pack Veg 2027-2028) and two prep workbooks (Kick-off Doc Prep, Kick-off Document Prep).

This is the keystone. The kickoff doc is the setup file. Today it is prose in Word, filled by hand, stored in a folder. The structure below is consistent across categories and years, so it can be lifted into fields. Rule held throughout: **structured fields drive the system; narrative blocks carry the why and stay prose.** Never force the narrative into fields.

---

## A. Cycle identity (structured)

| Field | Example from docs | Notes |
|-------|-------------------|-------|
| `category` | Field Tomatoes / Hothouse Veg / Wet + Packaged Veg | one cycle |
| `subcommodities_in_scope` | 59801 Cabbage Organic, 59802 Artichokes, … | list of SubCommodity codes. The scope anchor. |
| `annual_spend` | $102M / $391M / $640.2M | size of the prize |
| `timeframe_start` / `timeframe_end` | P4 2027 – P3 2028 | Kroger fiscal periods, with calendar dates |
| `dcs` | default ALL (national) | national is the 99.9% default; local is the exception |
| `objective` | savings / supply assurance / quality / diversification / strategic | the target; can be multi, with a primary |
| `prior_structure_note` | "full year, 4 timeframes negotiated separately" | last cycle's shape, for context |

---

## B. Pricing structure (structured — the decision layer)

This is the part the old spec pushed down to the bid line. It belongs here, declared once at kickoff.

| Field | Values seen in docs |
|-------|---------------------|
| `pricing_basis` | FIXED / INDEX / hybrid |
| `duration_cadence` | FULL_YEAR / SEASONAL / TIMEFRAMES(n) / PERIOD_BY_PERIOD(13) / QUARTERLY / MONTHLY / WEEKLY |
| `baseline_then_negotiate` | true/false ("set a year baseline, negotiate each timeframe separately") |
| `volume_split_rule` | how volume divides across suppliers/timeframes |

**Safeties** (each optional, attached to the cycle; the docs name all of these):

| Safety | Parameters |
|--------|-----------|
| Disaster trigger (escalator) | trigger conditions; supplier reprices up on a market spike |
| Inverse disaster trigger (de-escalator) | Kroger forces price down; moves inside the collar |
| Collar | `floor`, `cap` |
| Rolling midpoint | `window_weeks`, `reevaluation_cadence_weeks` |
| Tolerance band | `band_pct`, `hold_weeks`, `re_review_window` (move and hold, not move once) |

**Routing / cost options to collect** (from the bid-format notes): FOB corrugate, FOB RPC, delivered surcharge by DC, Kroger-managed freight vs vendor-delivered. `routing_basis` ∈ FOB / DELIVERED / XDOCK / CBS_FREIGHT.

**Per-period sourcing region:** supplier-stated grow origin, captured per period. Not auto-filled from iTrade ship-from (ship-from ≠ grow-origin).

---

## C. Scope and items (structured, partly manual)

| Field | Source | Notes |
|-------|--------|-------|
| `subcommodity_codes` | KCMS | the anchor; groups specs + packing variants |
| `in_scope_items` | KCMS GTIN export | ~9.8k rows raw, mostly noise (pharmacy, cola, dog food). Scoping = manual signal-from-noise. In-scope items show high variant counts; junk shows once. |
| `lot_assignment` | norm table (Ed's lot list) | map unique SKU → lot via category-filtered dropdown; sticky next cycle |
| `pack_normalization` | manual | a 50lb bin entered as "1 bin / each / 1lb"; human picks the path, system remembers. Raw under, normalized on top. |
| `projected_volume` | KCMS / planning | DC × item × period demand |

---

## D. Historical / baseline data (pulled at prep, structured)

**Category Overview metrics, current vs previous period** (from KCMS): Scanned Cost, Scanned Retail, Scanned Movement, Gross Margin $, Gross Margin %, FCB Unit Cost. Captured at subcommodity and GTIN grain.

**Supplier scorecard** (exact fields from the prep workbook): Volume (Cases), % of volume, % of cost, Avg Fill Rate, Avg Adjusted Fill Rate, Avg On-Time (DLVD only), Avg DC Rejection, Rejected Case Qty, Rejection Count, Avg Cost/Case, Avg Age at Receipt.

The scorecard is captured **twice, on different windows**: a kickoff snapshot and a sign-off snapshot. Both freeze. Freeze-and-layer, confirmed by the data.

**Historical awarded cost (PO):** from iTrade/SAP, FOB by commodity, period-stamped to both calendars.

---

## E. Supplier field (structured)

| Field | Example |
|-------|---------|
| `invited_suppliers` | 27 total (13 incumbent, 14 non-incumbent) |
| `rfi_question_set` | configurable list, category-specific |

RFI questions seen (the set evolves per cycle, so it is configurable, not fixed): harvest and transit times to each DC; grown vs sourced with grower names and locations; clean-sheet cost breakdown (% product / labor / packaging / production); TSA duty % included; packaging supplier (for group-buy analysis); RPC vs corrugate; Kroger-managed freight vs vendor-delivered.

---

## F. Commercial terms (structured)

| Field | Detail from docs |
|-------|------------------|
| PBA required | yes for all awarded suppliers |
| PBA metric thresholds | e.g. case fill rate 98%, promo volume support |
| PBA enforcement | business-removal language if metrics miss; tariff revert/block clauses |
| Working capital | target terms (NET 30); current terms by supplier (NET 21/25/30); quantified benefit ($1.4M–$2.7M) |
| KPM funding (84.51°) | amount ($200K–$400K); treatment (held separate or negotiated into COGS) |

---

## G. Timeline / rail (structured, per-cycle)

The Next Steps section is the process rail for this cycle, and it varies. Full version from the prep workbook:

Build RFI/RFP → QA Survey → Kickoff Meeting with Leadership → RFI/RFP responses due → QA Roundtable → Review Initial Bids and Set Targets → Send Target Guidance (Round 2) → Round 2 due → Review and Determine Alignment → Send Proposals (Round 3) → Round 3 due → Finalize Alignment and Phone Negotiation → **Sign-off Meeting with Leadership** → Send Awards and PBAs → Commitment Start.

Stored as an ordered list of `{event, date}`. Round count is variable (3 default, more if there is juice). The two leadership gates anchor each end. This list defines the rail the app renders for the cycle.

---

## H. Narrative blocks (prose, preserved, versioned)

Stored as rich text attached to the cycle. Do not field-ify these.

- Background (sourcing history of the category)
- Data Dive (household/consumer analytics: VPS/PS/LPS, leakage, promo uplift)
- Industry Insights (market, weather, tariffs, crop)
- Category Strategy (CM)
- Sourcing Strategy narrative (ES)
- General Goals

---

## Data lineage (where each block comes from)

| Block | Source feed |
|-------|-------------|
| Category Overview, scan metrics, GTIN/subcommodity scope | **KCMS** (Kroger Category Management System) |
| Historical awarded cost, FOB, commodity, fiscal stamping | **iTrade / SAP** |
| Supplier scorecard (fill, on-time, rejection, cost/case, age) | PO / receiving (SAP) |
| Pricing structure, safeties, objective, RFI set, PBA, terms, timeline | **declared at kickoff** (the meeting) |
| Background, strategy, industry, data dive | **authored** (prose) |

Two pulled feeds (KCMS scan, iTrade FOB), one performance feed (scorecard), one declared layer (the decisions), one authored layer (the narrative). The declared layer is the part that lives in people's heads today and is the core of the build.

---

## What this confirms and what it adds

Confirms: the two-gate model (kickoff and sign-off with leadership, in the doc's own timeline), the per-cycle rail, the pricing model (disaster clause / de-escalator / period-by-period / baseline-then-negotiate, in plain language), the SubCommodity anchor, freeze-and-layer (two scorecard snapshots).

Adds to the model: annual spend, the objective field, the PBA governance block, working-capital terms, KPM funding, a configurable RFI question set, the exact scorecard schema, and KCMS as the scan-out source distinct from iTrade.
