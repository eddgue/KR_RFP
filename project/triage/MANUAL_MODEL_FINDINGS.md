---
doc: Manual allocation-model findings — verification of the modality / cost-construction calcs
id: PM-007-MMF
status: VERIFICATION FINDINGS (separate from live specs; confirm against our pipeline before acting)
created: 2026-06-22
source: reference/samples/_allocation_models/2026.05.19_Sweet Potatoes Allocation model RD4_vCurrent.xlsx
        (cross-checked structure vs the 2026.04.28 RD2 file; the MANUAL RFP model, NOT the golden output
        potato_2026_rfp_analysis_output.xlsx — sponsor: "make sure its the manual not the golden output file")
relates: project/03_DECISION_LOG.md (D43, D42), project/RECONCILIATION_SEAMS.md, backend/app/engine/interface.py,
         backend/app/engine/formulas.py, backend/app/domain/bid/{template_schema.py,bid_ingester.py}
---

# Manual allocation-model findings (modality + cost construction)

Purpose: the sponsor pointed at the **manual potato RFP allocation model** to verify the pricing-modality /
cost-breakdown calcs (D43) rather than rely on recollection ("there are the calcs"). These are **findings to
reconcile against our pipeline**, recorded SEPARATELY so they don't corrupt the live build plan or specs.
Confirm each before changing live code.

## What the manual model is
A large human-built Excel allocation model (~32 MB). Relevant sheets:
- **Controls** — scope/setup: commodity · horizon (Short/Long) · commitment start/end · weeks · **periods (= weeks/4)** · cases · DC vol %.
- **RFP - FOB Bid** — the supplier FOB bid input (by round RD1/RD2/RD3) + discounts + RPC + capability + should-cost %s.
- **RFP - Delivery Charge** — per (supplier|DC|item) routing surcharges: **Delivery Surcharge Per Case** + **VegCool XDOCK Surcharge Per Case** + loading location (e.g. "VegCool Xdock") + transit days.
- **Sweet Potato RFPs** — the assembly sheet: INDEX/MATCH pulls FOB + RPC + discounts + delivery/XDOCK surcharges onto one row per supplier|DC|item.
- **Baseline scenario** — tracks **FOB price and Routing (delivered/landed) price side by side** + spend (weekly / annualized) + FOB savings.
- **Data cube** — the wide (~700-col) calc cube that constructs per-supplier per-modality price (cols YS/YV/ZC: RFP Routing / Bid FOB / Bid Routing price).
- **CBS freight data** — `Freight Unit Cost Amount` (a freight reference / lane cost).
- **FOB analysis**, **Supplier overview**, **Summary**, **Signoff tables**, **Booking Guide**, **Sweet Potato Historicals**, **Supplier mapping**.

## VERIFIED — confirms D43
1. **Modality is real and is called "Routing."** `Baseline scenario` row 7: `Old FOB`/`Bid FOB` **and** `Old Routing price`/`Bid Routing price`, with `Routing` / `RFP Routing` labels. The model deliberately shows BOTH the FOB basis and the routed (delivered) basis so the buyer can compare/decide — exactly the modality picker ("even with full data we may pick FOB / DELIVERED / XDOC").
2. **The cost catalog maps to our EXISTING engine fields** (`engine/interface.py` `BidComponents`):

   | Manual column | Our field | Notes |
   |---|---|---|
   | `Bid Price ($/Case, FOB)` (RD1/RD2/RD3) | `fob` | by round |
   | `Delivery Surcharge Per Case` | `delivery_surcharge` | DELIVERED routing leg |
   | `VegCool XDOCK Surcharge Per Case` | `vegcool_surcharge` | **XDOC routing leg = our "vegcool"** |
   | `% Discount for Full-Lot Award` | `lot_discount` | **% in manual** (see finding A) |
   | `Incremental % Discount` | `all_lot_discount` | **% in manual** (see finding A) |
   | `RPC Cost Impact (+/- $/Case)` (gated `RPCs? Y/N`) | — | **no distinct field** (see finding B) |
   | `CBS freight` `Freight Unit Cost Amount` | — | freight reference (FOB lane) |

3. **XDOC mechanics (corrects the earlier provisional leg-split).** XDOC = a routing through a **named cross-dock** ("VegCool Xdock", the supplier loading location) with a **supplier-stated per-case XDOCK surcharge**; price = **FOB + that surcharge**. It is **NOT** modeled as "supplier covers origin→cross-dock, Kroger covers cross-dock→DC." Our `vegcool_surcharge` already is this leg.

## FINDINGS to reconcile (do NOT silently change live code — confirm first)

### A. Discounts: PERCENT in the manual, DOLLARS in our engine — ✅ RESOLVED 2026-06-22 (discounts = % of FOB)
- Manual: `% Discount for Full-Lot Award`, `Incremental % Discount` — **percentages** (of the FOB bid price).
- Ours (today): `construct_price_from_parts` does `fob + delivery + vegcool − lot_discount − all_lot_discount` treating them as **$ amounts**; the ingester reads `lot_discount = _to_decimal(raw.get(BidColumn.LOT_DISCOUNT.value))` — **no %→$ conversion**.
- **Resolution (D43, refined 2026-06-22):** a discount is a **cost line (sign −) whose base is a buyer-selected set of ONE OR MANY cost lines** (FOB only, FOB + delivery, …), **configured on setup** (the A1 cost-line manager). Unit `%` (preferred — **grain-robust**: a % scales with whatever it multiplies, per-period or timeframe, where a fixed `$` would differ by grain) or `$`. Default base = FOB. *(Unit-default `%` is my call on the evidence; sponsor can override.)*
- **Action (E-44):** switch `construct_price_from_parts` from flat `$`-subtraction to `−(pct × Σ selected-base-lines)` (or `$`), in the declared apply-order; ingester reads the stated %/`$`; the known-template adapter converts any legacy `$`-stated discount; add a test (a % discount changes the price proportionally, is stable across grains, and honors its selected base set).

### B. RPC is a first-class cost line in the manual; not a distinct engine component
- Manual: `RPC Cost Impact (+/- $/Case)` gated by `Is Kroger Requesting this item in RPCs?` / `RPCs? (Y/N)`.
- Ours: only `fob / delivery / vegcool / lot_discount / all_lot_discount` (+ `all_in`). RPC has **no explicit field** — today it can only ride inside All-In.
- **Action (to confirm):** add **RPC as a D43 toggleable cost line** (sign = +/-, unit = $/case, gated by the RPC request flag), not folded into All-In.

### C. Grain reality — manual is HORIZON-grain, not per-period-13
- Manual collects one bid per supplier|DC|item by **round** (RD1/RD2/RD3) over a **horizon** (Short/Long; `Pricing comments — 3 periods` ⇒ short horizon = 3 periods). It does **not** collect 13 per-period prices.
- Our **D35/D38/D42 flat-13 per-period** collection (FOB by period, freight by period) is therefore an **enhancement** beyond the manual (to seed E-35 timeframe discovery), **not** the manual's method. Keep this straight when comparing harness vs manual vs app: the per-period grain is ours.

## Use as the verification oracle
These manual files + our **MCP harness** (the live-run oracle) are how we compare app vs harness vs manual during the
live RFPs. Findings A/B/C are the first concrete reconciliation items to close when D43 is built.
