---
doc: Field Tomatoes 2026 — Cycle Structural Map (engine I/O, ingestion grain, booking output, raw-bid template)
id: PD-CYCLE-FIELDTOMATO
version: 1.1
status: Draft (derived from a real, near-complete RFP cycle)
framing: |
  AS-IS REFERENCE, NOT TARGET (D17 + D18). This maps a real cycle's spreadsheets to *extract the
  contract, data semantics, and levers* — never to mirror the layout or replicate the workflow. The
  cycle is one SINGLE-STRATEGY MOLD; we are building the STRATEGY-AGNOSTIC platform (ADR-0016) on
  which strategies are developed and run. KEEP: the contract/grain/cost-stack/config. BUILD OUR OWN:
  store, web app, generated outputs, RFP/bid template, process steps.
created: 2026-06-19
owner: Platform & Data + Engine squad
source: reference/samples/* (real Field Tomatoes 2026 cycle, QUARANTINED — gitignored, ADR-0001)
data_handling: |
  STRUCTURE ONLY (ADR-0001 §4, Security PLAN). Sheet names, column headers, the I/O contract,
  and format notes are schema, not sensitive. NO real values are recorded here — no real prices,
  volumes, award totals, or supplier-specific commercial data. Engine CONFIG values
  (weights/thresholds/presets) ARE recorded — they are logic, not commercially sensitive.
  Supplier names appear only where already public in our docs (DiVine / Marengo / Lipman = the
  three raw-bid sources named in the task).
relates: |
  ADR-0001 (clean-room), ADR-0006 (engine brain), ADR-0013/ADR-0014 (pricing storage + safeties),
  V3_ENGINE_LOGIC.md, GOLDEN_MASTER.md, FEEDS_ITRADE.md, SAMPLE_REGISTER.md,
  E-08 (bid importer), E-23 (award/booking doc), E-29 (safety visualizer/monitor), D11/D13
---

# Field Tomatoes 2026 — Cycle Structural Map

A **real, near-complete Field Tomatoes 2026 RFP cycle** was quarantined under
`reference/samples/`. Unlike the golden Potato pair (which is the *engine* reproducibility
anchor), this Tomato cycle is the **end-to-end artifact set**: the engine input, the supplier-
facing raw-bid template (in two file formats), the normalized intake (R2/R3), the award/booking
output, and a runnable pricing-safety visualizer. This file maps each artifact's **structure**
to our reconciled store and confirms the importer / safety requirements. Raw files stay
gitignored; only structure is recorded.

The cycle is **P6–P7 Field Tomatoes**, arrivals **June 21 – August 15, 2026**, with a
**four-week bridge** (May 29 – June 20) reverting to prior contracts between current contracts
and the new awards. Items in scope are Grape, Round (4×4 / 5×5 Value), and Roma (XL, plus a
size-reduced alternative spec). USDA market data (FVWTRDS report 1662) is the price reference.

---

## 1. Engine I/O contract — `tomato_2026_rfp_input.xlsx` (11 tabs)

Same template family as the golden Potato input (CONFIG + IN_* + DIM_*). Header at **row 4**
(IN_Custom at **row 6**). CONFIG is a key/value block (col A label → col B value). The Tomato
file ships **11** tabs (no IN_Preferred / IN_VolumeLimits sheets — the engine warns and skips;
they default to empty). `z_tomato_2026_rfp_input.xlsx` is a near-identical variant (DIM_DCs 5
cols vs 6 — the only structural delta).

> **Identity caveat (carried template):** CONFIG identity still reads `Commodity Name = Colored
> Potatoes`, `Bid Cycle Label = Potato 2026`, `Output File Prefix = Potato_2026`. The Tomato
> cycle was built by copying the Potato template and **the identity block was not re-stamped**.
> The data (bids/DCs/lots) is tomato; the labels are stale. Our store must key the cycle on its
> own `cyc.cycle` row, never on the spreadsheet's identity strings.

### 1.1 CONFIG block → `cyc.*` + run config

| CONFIG section / label (col A) | Value form | Maps to |
|---|---|---|
| BID CYCLE IDENTITY — `Commodity Name`, `Bid Cycle Label`, `Output File Prefix` | text | `cyc.cycle` (commodity, label, prefix) — **re-stamp on import** |
| TIME FRAMES — `TF1..TF4` rows (col B start date, col D weeks, col E `Active?`=YES/NO) | per-TF | `cyc.cycle_timeframe` (`tf_id`, start_date, weeks, active). Tomato: **TF1, TF2 active** (May 24 + Aug 16 windows); TF3/TF4 inactive |
| BID ROUNDS — `Number of Active Rounds`; `R1..R6` rows (col D `Active?`=YES/NO, col B label, col E notes) | per-round | `cyc.cycle_round` (`round_status`, label, bid_type). Tomato: **only R1 active** (R1 "Initial FOB bids — farm gate price only"); R2–R6 NO → **single-round cycle** |
| `…Final analysis always uses the highest active round as the primary price basis` (HOW-TO note) | rule | run config: **primary basis = highest active round**; prior = first if >1 round (here none) |
| AWARD CONSTRAINTS — `Max Suppliers per DC` | int (default 2) | run config `max_sup_dc` (split cap §4 of engine logic) → `eng.analysis_run.config_json` |
| AWARD CONSTRAINTS — `Single Supplier per Lot` = `YES` | flag | award rule (hard-coded one-award-per-group in scenario logic; recorded as cycle term) |
| AWARD CONSTRAINTS — `Global Premium Threshold` | pct | run config `global_thresh` (eligibility ceiling; per-lot override via IN_Premiums) |
| AWARD CONSTRAINTS — `Coverage Eligibility Floor` | pct | declared in CONFIG; the **0.80 floor is hard-coded** in scoring (CONFIG value is documentary) |
| SCORING WEIGHTS — preset block: `Balanced (Default)` / `Price Focus` / `Coverage Focus` / `Risk Averse` / `Custom`, each with Price/Coverage/Historical weights + Use-Case text | preset grid | run config preset catalog → `eng.analysis_run.config_json` (preset name + active weights) |
| ACTIVE WEIGHTS — `Price Weight` / `Coverage Weight` / `Historical Weight` (+ Z-Risk / Continuity defaults), `SUM CHECK` | per-weight | run config active weights. **Tomato weights sum to 120% → engine renormalises** (warns, divides by total). Z-Risk + Continuity not in the active block → engine defaults (0.10 each) before renormalisation |

Concentration threshold (`conc_thresh`, default 0.40) and the Comparable/Defensible/Max premium
bands (0.03 / 0.07 / 0.15 here) are read from CONFIG / defaults into the same run config.
**Per V3_ENGINE_LOGIC §8** for the full key list and defaults.

### 1.2 IN_ / DIM_ tabs → store (column contract)

| Tab (header row) | Columns | Maps to |
|---|---|---|
| **IN_Bids** (r4) | Round ID, Bid Type, Supplier, DC Name, Lot_ID, TF, Item Description, All-In $/case, FOB $/case, Delivery Surcharge, VegCool Surcharge, Lot Discount, Pricing Comments, Weekly Vol Offered, Total Vol Offered, Invested? (R1 only) | `bid.bid_line` / `bid.bid_price` (one row per Supplier×DC×Lot×TF×Round). Price = All-In primary, FOB+surcharges−discounts fallback (engine §7). Vol-offered cols drive coverage. `ref.supplier`/`ref.item`/`ref.dc` resolve identity |
| **IN_Incumbents** (r4) | Incumbent Supplier, DC Name, Lot_ID, Item Description, Incumbent FOB $/case, Incumbent Routing $/case, Contract Notes | `perf` incumbent baseline (**D11**): `Incumbent_Routing $/case` = delivered all-in baseline for Historical score + Scenario C; `is_incumbent` per (DC,Lot). Tomato file: **0 populated rows** (headers only) |
| **IN_Volumes** (r4) | DC Name, DC_ID, TF, Lot_ID, Item Description, Weekly Volume (cases), Total Volume (cases), Weeks | `cyc.volume_requirement` (DC×Lot×TF demand). Drives coverage ratio. Tomato file: **0 populated rows** → all bids fall to As-Needed coverage |
| **IN_Premiums** (r4) | Lot_ID, Item Description, Global/Suggested/Override/Effective Threshold, Rationale/Notes | `cyc.*` per-lot premium override (else `global_thresh`) — eligibility ceiling |
| **IN_Custom** (r6) | DC Name, TF, Lot_ID, Item Description, Your Award Supplier, Notes/Rationale | `cyc.*` Scenario-F override rules |
| **IN_Exclusions** (r4) | Scenario, Supplier, Supplier_ID, DC_ID, Lot_ID, TF, Reason | `cyc.*` Scenario-E exclusion set |
| **DIM_Suppliers** (r4) | Sup_ID, Supplier Name, Region, Notes | `ref.supplier` |
| **DIM_Lots** (r4) | Lot_ID, Item Description, Category, Pack Size, UOM, Notes | `ref.item` / `cyc.cycle_lot` |
| **DIM_DCs** (r4) | DC_ID, DC Name, Region, State, **Zip**, Notes | `ref.dc` (Region/State → cyc.dc; **Zip** present here, richer than golden's 5-col DIM_DCs → freight proxy via `ref.zip_centroid`, G7) |
| **DIM_Rounds** (r4) | Round ID, Round Label, Bid Type, Active, Notes | `cyc.cycle_round` dim |

CONFIG and the 13-tab schema (incl. IN_Preferred / IN_VolumeLimits when present) are documented
in full in **V3_ENGINE_LOGIC.md §8** and **GOLDEN_MASTER.md §1**; this section records only the
Tomato-specific deltas (11 tabs, single-round, stale identity, Zip column).

---

## 2. Ingestion grain — `round2_ingestion_final.xlsx` (RFP R2) / `round3_ingestion_corrections.xlsx` (RFP R3)

The **raw → normalized bridge** (E-08 importer target). One wide sheet each:
**RFP R2 = 1028×176**, **RFP R3 = 682×179**.

### Why "176 columns" — it is NOT 176 fields
**The 176/179 is the stored sheet width (trailing styled/merged columns), not the data grain.**
Body data occupies only **cols 2–39 (~37 columns) in R2** and **cols 2–27 (~23) in R3**; cols
40–176 carry **zero body data**. The width is **not** per-DC, per-TF, or per-round repeated
blocks. The actual shape is:

- **One row per Supplier × DC × Item bid line** (the normalized grain — body ≈ 1024 rows R2 /
  678 rows R3). DC names (ATLANTA, DELTA-MEMPHIS, …) and items run down the rows.
- **Two side-by-side bid blocks per row** (this is the only "repeat"):
  1. **Primary spec block** (R2 cols 14–23): FOB $/Case (Corrugate), FOB $/Case (RPC), Freight
     Rate, Dlvd Cost (calculated), Weekly Vol Cap, Total Vol Cap, FOB Location, Growing
     Location, Distance (mi) to DC, Comments.
  2. **Roma alternative-spec block** (R2 cols 28–37): the same 10 sub-fields, for a
     size-reduced Roma alt spec (Alternative Size / Color / Spec, cols 24–26), plus an alt-spec
     comment. This is the "lower-cost alternative" path, NOT a second DC.
- Identity/leading cols: FOB region, Supplier, DC Name, Product Description, Case UPC Number,
  Case Size, Ship Pack Qty, plus Volume Estimates (6/21–8/15 Weekly / Total) and a Bid
  Completeness gate ("Incomplete Bid" warning). Trailing: a `Potential volume issue` flag.

**R3 differs** (corrections round): Dlvd Cost appears both before and after FOB (recompute
check), explicit size-class columns (`L (120-150 Ct.)`, `L-XL (90-150 Ct.)`), and only the
primary block — no alternative-spec block (corrections narrowed scope).

**Map → `bid.bid_line`** (E-08 importer target):
- Each row → one or two `bid.bid_line` rows (primary + alt-spec, the alt as a distinct line
  with its own item/spec). `FOB $/Case (Corrugate)` / `(RPC)` → `bid.bid_price` variants;
  `Dlvd Cost` = delivered/landed; Freight → freight component; FOB Location / Growing Location →
  `ship_from` vs `grow_origin` (**kept separate**, G7); Distance → freight-proxy; Weekly/Total
  Vol Cap → coverage; Bid Completeness → an ingestion gate (reject/flag before math).
- **Importer rule:** do not trust `max_column`; key off the **header row (row 4)** and the
  block-pair pattern, not the sheet's declared width.

---

## 3. Award / booking output — `field_tomatoes_booking_guide.xlsx` (Sheet1 64×42, Sheet2 56×3)

The cycle's **award document** → `awd.generated_document` / `awd.award` (E-23). Sheet1 holds the
awarded line per DC×item; **headers at row 7** under a row-6 group band and a row-5 External /
Internal band. Populated columns 2–23 (24–42 spillover/empty).

| Group band (r6) | Header (r7, col) | Maps to (awd / award) |
|---|---|---|
| Product Details | Supplier (2), DC Name (3), Product Description (4), Case UPC Number (5), Case Size (6), Ship Pack Qty (7), **Primary Routing (8)** | awarded supplier per DC×item; `ref.dc`/`ref.item`; routing (Delivered/FOB) |
| Volume Estimates — **External** | 6/21–8/15 Weekly (9), Total (10) | external (RFP-facing) volume estimate |
| Volume Estimates — **Internal** | 6/21–8/15 Weekly (11), Total (12) | internal volume estimate (the External/Internal split is a real award-doc distinction) |
| (cost) | **FOB Cost (13), Delivered Cost (14)**, Notes (15) | awarded `FOB` + routing/landed cost per line |
| Checks | Hist cost (17), Cost impact (18), Contract cost (19), Cost impact vs contract [FX:(Bid−Contract)×Volume] (20), All-in cost (21), All-in cost check (22), Routing cost (23) | savings/impact validation columns: bid-vs-historical and bid-vs-contract deltas (D11 baseline), an all-in reconciliation check, routing cost. → `awd.award` savings fields + `award_layer` baseline |

Logistics fields (transit/MOQ/cases-per-pallet) live on the supplier template's DC Locations /
RPC Shipping tabs (§4), carried into the award record at booking. **Sheet2** (56×3) is a
supplier ↔ supplier crosswalk / routing-pair list (a small lookup, not the award grain).

---

## 4. Raw bid template — `blank_master_template.xlsx` + supplier rounds (the importer's parse target)

The **supplier-facing shape** the bid importer (E-08) must parse — fundamentally different from
the flat IN_Bids grain. **14 tabs**, identical across the blank template and every supplier
round:

`Cover Sheet`, `Instructions`, `1. Program Details`, `2. Product Specs`, `3. GTIN Requirements`,
`4. Traceability Requirements`, `5. Temp Monitoring`, `6. Vol and Pricing Capability`,
`7. DC Locations`, `8. 84.51 Details`, `9. Additional Capability`, `10. RPC Shipping`,
`Alternative Specs`, `Item List`.

- **Not flat.** Where IN_Bids is one row per Supplier×DC×Lot×TF×Round, the supplier template is a
  **multi-tab workbook** carrying compliance (Program Details Topic/Details/Penalties/Rewards/
  Acceptance grid), specs, GTIN, traceability, temp monitoring, DC locations, 84.51 data, and
  RPC shipping — alongside the pricing tab. The importer extracts pricing from one tab and
  metadata/compliance/logistics from the others.
- **Pricing tab = `6. Vol and Pricing Capability`** (78×171). Header at **row 17**, body one row
  per **DC × item**, with the **same two-block layout as the ingestion sheet**: a primary spec
  block (cols 10–19: FOB Corrugate, FOB RPC, Freight, Dlvd Cost, Wkly/Total Vol Cap, FOB
  Location, Growing Location, Distance, Comments) and a Roma alternative-spec block (cols
  24–33). 171 width = the same trailing-width inflation as §2 (real fields ≈ 33). **The
  ingestion sheet IS the stacked/normalized projection of every supplier's tab-6** — this is the
  raw→normalized bridge in one picture.
- **No-Bid handling:** a DC×item row a supplier declines carries `No Bid` (cols 9/23) — the
  importer must treat `No Bid` as a non-bid, not a zero price.
- **Cover Sheet** stamps cycle + window ("Kroger Bid Document — Field Tomatoes", "June 21 –
  August 15, 2026"); **Item List** enumerates the 4 in-scope items (Grape, Round 4×4, Roma XL,
  5×5 Value). These give the importer the cycle/window/item universe per file.

---

## 5. `.xlsb` requirement — Lipman rounds are **binary** (importer must handle both formats)

Confirmed: `bid_lipman_r1.xlsb`, `bid_lipman_r2.xlsb`, `bid_lipman_r3.xlsb` are **binary Excel
(.xlsb)** — OPC/ZIP container (`PK\x03\x04` magic), **not** readable by openpyxl; they require
**pyxlsb** (or equivalent). The DiVine and Marengo rounds are `.xlsx`. **All carry the identical
14-tab template** (sheet names below), so the importer must parse **one logical template across
two physical formats** — a real multi-format requirement, not an edge case.

Lipman `.xlsb` sheet names (identical to the `.xlsx` template):
`Cover Sheet`, `Instructions`, `1. Program Details`, `2. Product Specs`, `3. GTIN Requirements`,
`4. Traceability Requirements`, `5. Temp Monitoring`, `6. Vol and Pricing Capability`,
`7. DC Locations`, `8. 84.51 Details`, `9. Additional Capability`, `10. RPC Shipping`,
`Alternative Specs`, `Item List`.

**E-08 action:** the bid importer adds an `.xlsb` reader (pyxlsb) alongside `.xlsx` (openpyxl),
detects format by magic/extension, and maps both to the same tab-6 pricing grain. Round coverage
in the corpus: DiVine R1–R3, Marengo **R1–R4**, Lipman R1–R3 (`.xlsb`).

---

## 6. Price visualizer (HTML) — tolerance band / collar / midpoint logic (seeds E-29, confirms ADR-0014/D13)

`xl_roma_pricing_backtest.html` is a **self-contained, runnable** index-reset pricing backtest
("XL Roma index-reset pricing backtest"). It is the concrete, parameterised implementation of the
ADR-0014 pricing safeties — it confirms the **tolerance-band / collar / rolling-midpoint**
mechanics and seeds the safety monitor (E-29). Pure structure/logic (no commercial values); the
USDA prints it embeds are public market data.

**Market reference (the missing feed in ADR-0014, now identified):** USDA AMS National Shipping
Point Trends, **report FVWTRDS / My Market News report 1662** — Roma plum type, 25 lb cartons
loose, extra large, mid-mostly, Mexico crossings through Texas (Nogales fallback), Monday spot /
Tuesday release. Each weekly value = **midpoint of the printed "mostly" range** (single prints
stand as-is). This answers ADR-0014's open "where does the market reference come from."

**The mechanics it implements (parameters + formulas):**

| Safety element (ADR-0014) | Visualizer control | Logic implemented |
|---|---|---|
| **Tolerance band / collar** | `Band ±%` (5–30, default **15%**) | `outside = abs(m/baseRef − 1) > band/100`. A weekly print outside the band **starts the trigger clock**. The shaded corridor = base ± band%. Calibration guidance: **≈ 2× the reference's average absolute weekly move** (tight bands trigger on noise; wide bands sit silent) |
| **Persistence (the tolerance-band ≥2-week question)** | fixed `CONFIRM = 2`, `LAG = 1` | **Two consecutive weeks outside confirm** an interim adjustment; **two consecutive weeks back inside confirm reversion** to base; the move **takes effect one week after confirmation** (LAG=1). This is exactly ADR-0014's "outside the band AND persists ≥2 weeks (sustained, not a blip)" → reprice, then review |
| **Rolling midpoint / scheduled reset** | `Reset every (wks)` (4/8/12/**13**/26, default 13); `Reset trailing (wks)` (default **4**) | Base reference recalculates on schedule = **trailing average over `wR` weeks** (default 4). Maps to ADR-0014 rolling-midpoint (lookback 4); cadence here is **13 wks** (a quarter), not 8 — confirming ADR-0014's "windows/cadences are set per RFP, not fixed defaults" |
| **Interim reprice window** | `Interim trailing (wks)` (default **2**) | Once a trigger confirms, the interim price = trailing average over `wI` weeks (default 2 = "the two confirming prints"). Maps to ADR-0014 tolerance-band "temporary reprice to market midpoint, review at 2 weeks" |
| **Collar asymmetry / trigger rights** | `Trigger rights`: Automatic-bilateral vs **Kroger optional** | `auto` = fires both directions, either party. `opt` reproduces draft contract language: **fires only when it lowers Kroger's price** (`px < basePrice`), leaving the supplier holding upside until the next scheduled reset. This is the **floor-for-supplier / cap-for-Kroger asymmetry** of ADR-0014 §1 (Kroger keeps downside; supplier's protection is the reset) |
| **Discount form (the awarded bid)** | `Discount form`: $/carton off vs %-off; `Discount value` | `priceOf(ref) = ref − disc` ($ fixed) or `ref·(1 − disc/100)` (%). Fixed-$ keeps bids comparable across market levels; %-off scales with market (pushes spike-insurance into the bid) |
| **Re-mark (runaway second leg)** | `Re-mark` checkbox (default on) | An active interim **re-prices** if the market breaches the band measured **against the interim reference** for 2 consecutive weeks (`devI = m/interim.ref − 1`). Off = a frozen interim a second-leg move runs away from (recreates the lag one tier up) |

**Core simulation (`simulate()` in the HTML):** per week — apply any pending reprice (LAG=1);
on a scheduled reset, recompute base from trailing `wR` and clear interim state; compute
`dev = m/baseRef − 1`, track consecutive outside/inside counts; on 2× outside (and trigger-rights
gate) schedule an interim from trailing `wI`; on 2× inside schedule a revert; with re-mark, on 2×
outside-vs-interim schedule a re-mark. Outputs: avg contract cost, avg market-less-discount, gap
vs pass-through, weeks-on-interim, triggers / re-marks / resets, and a per-base-period spend
split. **This is the formulaic safety engine (collar + rolling midpoint + tolerance band)** ADR-
0014 §1–3 calls "computable / auto-visualizable"; the disaster triggers (§4–5) remain
discretionary and are not in this model.

**Seeds E-29:** the monitor consumes the FVWTRDS feed, applies band/reset/trailing/trigger-rights
parameters per cell, proposes formulaic reprices (collar-bounded), and records every move in
`awd.award_layer` (draft→sent, author≠approver per ADR-0014 §3).

---

## 7. What this proves / what's still partial

**Proves:**
- The engine I/O contract (CONFIG + IN_/DIM_) is **stable across commodities** (Tomato reuses the
  exact Potato template) — commodity-agnostic, as designed.
- The **raw→normalized bridge is real and visible**: supplier template tab-6 (per DC×item, two
  spec blocks) → stacked ingestion sheet (R2/R3) → flat IN_Bids. E-08's parse target is concrete.
- The importer must handle **two physical formats** (`.xlsx` + `.xlsb`) for one logical template —
  confirmed by the Lipman binary files.
- The pricing safeties are **runnable, not hand-wavy**: the HTML implements collar + rolling-
  midpoint + tolerance-band with the ADR-0014 persistence (2-week confirm / 1-week lag) and the
  Kroger-optional collar asymmetry, on an identified market feed (USDA FVWTRDS 1662). Seeds E-29.
- The booking guide gives the **award output grain** (awarded supplier per DC×item + FOB/
  routing/landed + savings checks + External/Internal volume) for `awd.generated_document` (E-23).

**Still partial:**
- **Single round only** — Tomato CONFIG has **only R1 active** (R2–R6 NO). Raw bids exist for more
  rounds (DiVine R1–R3, Marengo R1–R4, Lipman R1–R3), but the engine input was frozen at R1.
- **Ingestion exists for R2/R3 only** — no R1/R4 normalized intake in the corpus; R2 is the full
  intake, R3 a corrections pass (narrower, size-class columns).
- **Incumbents + Volumes empty** in the engine input (headers only) → no historical baseline and
  no real coverage in this run; all bids fall to As-Needed coverage. D11 baseline would come from
  `perf.itrade_receipt`, not this file.
- **Identity not re-stamped** (CONFIG still says Colored Potatoes / Potato 2026) — a data-hygiene
  gap the importer must correct.
- **No IN_Preferred / IN_VolumeLimits tabs** — Scenario G / volume-limit inputs absent (engine
  warns and skips). The cycle is near-complete, not complete.
