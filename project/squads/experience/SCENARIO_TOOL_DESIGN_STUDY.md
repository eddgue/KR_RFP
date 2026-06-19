---
doc: Scenario Tool Design Study — four-way side-by-side + synthesized target + practitioner layer
id: EXP-SCEN-STUDY
squad: Experience / Output (Squad — Experience)
status: Verified (v3 golden reproduced + real allocation models analysed + redesign built 2026-06-19)
created: 2026-06-19
updated: 2026-06-19 (added §7 — the real Kroger allocation models + the practitioner layer built on
         top: Controls cockpit, savings-first Award Summary sign-off, FOB-vs-All-In, banded nav)
relates: D24 (formatted), D25 (interactive), D26 (alignment/comparison), D27 (manipulable),
         D23 (names not keys), ADR-0006 (decision-support), ADR-0016 (strategy-agnostic),
         project/squads/engine-domain/V3_ENGINE_LOGIC.md, backend/demo/run_cycle_demo.py
scope: FUNCTIONAL / STRUCTURAL / UX ONLY. Visual design-language (color, type, brand) is
       DEFERRED to the downstream design review — this study deliberately does not prescribe it.
quarantine: No real supplier names, prices, or commercial values appear here. The v3 golden
            output + the real Excel are gitignored reference (ADR-0001); only STRUCTURE (tab
            names, layout patterns, column-field labels, density, interaction model) is recorded.
---

# Scenario Tool Design Study

A design study for the scenario workbook — the team **alignment / comparison** deliverable
(D26) the buyer **plays with to decide** (D27). We ran the proven v3 engine on its multi-round
golden input, captured the full 20-tab output, and put three workbooks side by side to learn
**what works / what doesn't** (UI/UX), then synthesized the **target design** for our workbook.

**Three files compared:**

| Slot | File | What it is | Why chosen |
|---|---|---|---|
| **OURS** | `backend/demo/output/SCENARIO_WORKBOOK.xlsx` (7 tabs) | Our current generator output (re-run from the sealed `eng.*` records) | The thing we are redesigning |
| **V3-GOLDEN** | `Potato_2026_RFP_Analysis.xlsx` (20 tabs, 3.2 MB) | The **proven tool's** output — ran the gitignored v3 engine on the multi-round Potato golden input in a venv; completed clean (4 DQ issues logged, not fatal). Captured to a temp/gitignored path. | Strongest signal for "what works" — the analytical tool buyers actually used |
| **COMPLEX-REAL** | `bid_divine_r1.xlsx` (14 tabs; one tab 171 cols) + the 176-col `round2_ingestion_final.xlsx` as a secondary density point | The most structurally complex real Excel we hold (by tabs×cols) | The "great but messy / rich" reference (D27) — what richness looks like, and where it tips into messy |

**v3 RAN — confirmed.** Engine completed end-to-end on the multi-round Potato input; emitted the
full 20-tab analysis workbook. Tab inventory (the proven set): **Executive Summary · Award
Recommendations · Preferred Scenario · Regional Summary · Vol Utilisation · Share of Business ·
Recommendations · Scenario Comparison · Lowest Cost Check · Top 5 Bids · DC Constraint Review ·
Bidder Detail · Custom Scenario · Supplier Overview · TF Comparison · Round Evolution · Coverage
Analysis · Detailed Scoring · Missing Data · Glossary.**

---

## 1. Side-by-side — the key views

Rows = a logical view. Cells = how each of the three files realizes it (structure/UX, no values).

| View / capability | OURS (7 tabs) | V3-GOLDEN (20 tabs) | COMPLEX-REAL (14-tab bid / 176-col ingestion) |
|---|---|---|---|
| **Headline / exec read** | `Summary` — 2-col Item/Value card; cycle, scope, strategy, A-vs-B headline, how-to-use note | `Executive Summary` — a scenario-comparison matrix (A–G as labeled blocks) + KPI callouts up top | Bid `Cover Sheet` + `Instructions` (89 rows) — orientation, not analytics |
| **Which-lens (scenarios side by side)** | `Scenario Comparison` — **scenarios as ROWS** (A–G + LIVE Custom row), cols = spend/Δ-vs-A/savings-vs-baseline/savings-vs-STLY/#sup/#breach/#cells; + expandable drill + per-DC matrix | `Scenario Comparison` — **scenarios as COLUMN BLOCKS** (per cell row: `A_Supplier/A_Price/A_Cov/A_Sav … G_*`, 35 cols); `Share of Business` repeats the A–G blocks per supplier | (n/a — bid file is supplier-facing input, not analysis) |
| **Which-supplier (suppliers side by side, per cell)** | `Supplier Comparison` — **THE CENTERPIECE**: row per cell, one $/case col per supplier, MIN highlighted, incumbent+rec flagged, + impact-vs-baseline block | Split across `Bidder Detail` (long: row per bid), `Top 5 Bids` (ranked top-5 per group), `Award Recommendations` (the rec per cell w/ incumbent-bid context). **No single supplier-wide pivot — it's long-form.** | Bid `6. Vol and Pricing Capability` — **171 cols**: DC × pack × volume-band pricing matrix (one supplier, exploded wide) |
| **Lowest-cost discipline (B vs A)** | implied in `Scenario Comparison` Δ-vs-A only | `Lowest Cost Check` — **dedicated**: per cell, Price vs LowestPrice/PremVsLow/IsSameSupplier/Reason (why the rec ≠ cheapest) | n/a |
| **Per-cell allocation + split** | `Custom Scenario` (interactive) + drill | `Award Recommendations` (26 cols, the master rec) + `DC Constraint Review` (supplier-rank → lot-assign → cost summary; the max-2 split, cap status) | n/a |
| **Detailed scoring (the 5 factors)** | `Scored Bids` — 5 factors + RecScore + eligible + gate flags | `Detailed Scoring` (30 cols: MktMin/Avg/Std, Z, prem, bands, the 5 factor scores) + `Recommendations` (35 cols) | n/a |
| **Coverage / volume** | (folded into scores; no own view) | `Coverage Analysis` (req vs offered, ratios, band) + `Vol Utilisation` (awarded vs supplier max, over-limit) | Bid `7. DC Locations` + volume bands in the 171-col pricing tab |
| **Time dimension** | (none) | `TF Comparison` (TF1 vs TF2 per cell, split flag) + `Round Evolution` (R1→R2 price Δ, direction) | bid is one round per file (`_r1/_r2/_r3/_r4`) |
| **Supplier roll-up** | (none) | `Supplier Overview` (per-supplier bid stats) + `Share of Business` (spend %/conc per supplier × scenario) + `Regional Summary` | bid is one supplier |
| **Data-quality surface** | (none, silent) | `Missing Data` (flag/count/action — non-blocking) | implicit (`Bid Completeness` super-header in ingestion) |
| **Self-serve manipulation** | `Data (pivot me)` — real Excel Table (ListObject) one row per scenario×cell×supplier; drop a native PivotTable | (none — every cut is pre-baked as its own tab) | ingestion sheet = one flat 176-col table (pivot source, but raw) |
| **Live interactivity** | `Custom Scenario` — per-cell supplier **dropdowns** + live SUMIFS (spend/savings/cap-breach) + LIVE Custom column on Scenario Comparison | `Custom Scenario` — per-cell override cols + live award-spend/savings/util formulas (the capability we lifted) | bid uses data-validation dropdowns for input fields |
| **Legend / glossary** | how-to-use line on Summary | `Glossary` — measure / tab / definition | `Instructions` tab |
| **Navigation** | 7 flat tabs | 20 flat tabs (no index/hub) | 14 numbered tabs ("1." … "10." + hidden helpers) |
| **Density model** | clean; depth via drill/pivot (depth-on-demand) | **everything-at-once**: every cut is its own wide tab; rich but heavy | **messy-rich**: merged multi-row super-headers, banner rows, instruction text mixed with data, 171–176 col blowouts |

---

## 2. What works / what doesn't

### V3-GOLDEN — the proven tool (strongest "what works" signal)
**Works:**
- **One purpose per tab, named for the question it answers.** "Lowest Cost Check", "Coverage
  Analysis", "TF Comparison", "Round Evolution", "DC Constraint Review", "Missing Data" — a buyer
  goes straight to the question. This is the single biggest lesson.
- **Lowest-Cost Check as its own view.** A dedicated "why is the recommendation not the cheapest"
  reconciliation (PremVsLow, IsSameSupplier, Reason) — governance gold for an alignment call.
- **The 5 factors fully exposed** (`Detailed Scoring`, 30 cols incl. MktMin/Avg/Std/Z/bands) — the
  recommendation is *auditable*, not a black box. Reinforces recommends-not-asserts (ADR-0006).
- **Reference points everywhere** — incumbent, incumbent-bid rank, routing baseline, delta-vs-incumbent
  in $ and % carried on the rec tab. The team always sees against-what.
- **Coverage + volume-utilisation surfaced** (offered vs required; awarded vs supplier max, over-limit
  flag) — capacity reality, not just price.
- **Round Evolution + TF Comparison** — the time/negotiation story (R1→R2 movement; TF1 vs TF2 split).
- **DC Constraint Review is a genuine three-act view** — supplier ranking → per-lot assignment →
  cost summary; the max-2 split shown as *reasoning*, with cap status.
- **Missing-Data tab** — DQ surfaced, never silent, never fatal.

**Doesn't:**
- **Everything-at-once = 20 tabs, no hub, no index.** Navigation is "hunt the tab." High cognitive load.
- **Many tabs are very wide** (35 cols on Recommendations/Scenario Comparison; 30 on Detailed
  Scoring; 38 on Custom Scenario with 17 hidden supplier cols). Horizontal scroll fatigue.
- **No supplier-wide pivot per cell.** To compare suppliers for one cell you read long-form
  `Bidder Detail` (4,800+ rows) or the top-5 cut — you can't *scan* all suppliers across one row.
- **Massive long tabs** (Bidder/Round/Coverage/Detailed each ~4,800 rows) — powerful for audit,
  punishing to browse; no drill/collapse, no Excel Table/filter affordance baked in.
- **Redundancy** — A–G blocks restated on Exec Summary, Scenario Comparison, and Share of Business.
- **Custom Scenario hides 17 supplier columns** to make the override work — clever but opaque.

### OURS — clean, but light
**Works:**
- **The supplier-side-by-side `Supplier Comparison` is genuinely better than v3** — every supplier's
  $/case on one row, MIN auto-highlighted, incumbent+rec flagged, impact-vs-baseline block. This is
  the scan v3 *can't* do; keep it as the centerpiece.
- **Depth-on-demand done right (D27):** outline-grouped scenario→DC→supplier drill opens collapsed;
  `Data (pivot me)` is a real ListObject for native pivoting. Clean, not everything-at-once.
- **Live custom is strong:** per-cell dropdowns + live SUMIFS, AND a LIVE Custom row/column that
  recomputes alongside A–G on Scenario Comparison — the live-vs-scenarios ask (D27), which v3 lacks.
- **Presentation quality (D24)** and **names-not-keys (D23)** throughout; provenance strap on every tab.
- **Scenarios-as-rows** for the which-lens compare is more legible than v3's wide column-blocks.

**Doesn't (the gaps vs the proven tool):**
- **No Lowest-Cost Check** — the "why not cheapest" reconciliation is only an aggregate Δ-vs-A.
- **No Coverage view** — coverage is folded into a score; the team can't see offered-vs-required.
- **No time dimension** — no TF Comparison, no Round Evolution, despite us persisting **all 3 rounds**
  in `bid.bid_line` and **2 TFs** (the data is there; the views are missing).
- **No DQ surface** — quarantined/no-bid rows are printed to console, never shown in the workbook.
- **No exec landing / no nav hub** — `Summary` is a thin card; 7 flat tabs with no index.
- **Detailed scoring is shallow** vs v3 — we show the 5 factors + RecScore but not the market stats
  (MktMin/Avg/Std, Z, premium, bands) that *explain* them.
- **No supplier roll-up** — no per-supplier share-of-business / concentration view (we have the
  conc_thresh in config and the awards to compute it).

### COMPLEX-REAL — "great but messy / rich" (the D27 cautionary reference)
**Rich (what to admire):** genuinely multi-dimensional — DC × pack × volume-band pricing exploded
to 171 cols; grouped **super-headers** ("Product Details / Volume Estimates / Bid Completeness /
Supplier Bid") over sub-columns; per-tab instructions; data-validation dropdowns for input.
**Messy (what to avoid):** merged multi-row headers that machines (and eyes) can't parse cleanly
(our header scan returned *no* detectable header row on several bid tabs); banner/instruction rows
interleaved with data; 171–176 col horizontal blowouts; one giant flat table (176 cols × 1,028 rows)
with grouped headers as the *only* structure. This is exactly the "great but messy" the sponsor
named (D27): the richness is real, the legibility is not. **Lesson: get the richness via
depth-on-demand + named single-purpose views, NOT via width and merged banners.**

---

## 3. UI/UX lessons (synthesized)

1. **One tab = one question, named for it.** v3's biggest win. Adopt the discipline; resist
   omnibus tabs. (Lowest-Cost Check, Coverage, TF Comparison, Round Evolution, Data Quality.)
2. **Density: depth-on-demand beats everything-at-once and beats too-light.** v3 is everything-at-once
   (20 wide tabs); the real bid is messy-wide; ours is light. The target sits between: a small set of
   single-purpose tabs, each clean, with **drill (outline) + filter (Excel Table) + live formulas**
   for depth. (D27.)
3. **Comparison layout:** *suppliers* side by side reads best as **one column per supplier on a
   per-cell row** (ours — keep). *Scenarios* side by side reads best as **scenarios-as-rows** for the
   roll-up (ours) and as a **per-cell cross-tab** when you need WHERE they differ (add a compact
   version of v3's per-cell A–G block, but only the rec supplier + price + savings per lens, not 35 cols).
4. **Always show against-what.** Incumbent, baseline, STLY, market-low, min — on every comparison
   surface. v3 does this relentlessly; it's what makes it decision-grade.
5. **Expose the reasoning, recommend don't assert.** Keep the 5 factors visible AND add the market
   stats that explain the price score; keep the Lowest-Cost "why not cheapest" reconciliation. This
   is the governance posture (ADR-0006) made visible.
6. **Surface data quality; never hide it, never let it block.** A Data Quality tab (no-bids,
   missing coverage, quarantined rows) — v3's Missing Data, which we lack.
7. **Give the workbook a front door.** An exec landing with the headline + a one-line index/nav of
   the tabs (what each answers). 7→~12 tabs needs a hub; 20 tabs proved it.
8. **Keep our live-custom edge.** Per-cell dropdowns + live recompute + the LIVE Custom column on
   the comparison is ahead of v3 (its custom tab is more static). Keep and feature it.
9. **Never width-blow-out or merge-nest headers.** The real-file failure mode. Single header row,
   real Excel Tables, grouping/outline for depth — machine- and eye-legible.

**Where v3 is rich that we're light:** Lowest-Cost Check, Coverage, TF Comparison, Round Evolution,
Detailed Scoring depth, Data Quality, supplier roll-up, an exec read.
**Where v3/the real file is messy that we're clean:** 20-tab sprawl + no nav (v3); merged
super-headers + 171/176-col blowouts + instruction-data mixing (real bid). Keep our cleanliness.

---

## 4. Synthesized target design (functional/UX — visual language deferred)

Grounded in **our sealed records** — only views the schema supports (see §5). Tabs the buyer reads
left-to-right as a decision flow; depth is drill/filter/live, never dumped.

### Tabs — ADD / KEEP / CUT

| Tab | Disposition | Purpose / records it draws on |
|---|---|---|
| **Overview** | **KEEP + upgrade** (`Summary`→`Overview`) | Exec read: cycle/strategy + A-vs-B headline + savings vs baseline/STLY + a **tab index** (front door). KPI callouts. |
| **Scenario Comparison** | **KEEP** | A–G as rows + LIVE Custom row; Δ-vs-A, savings, #sup, #breach, #cells; expandable scenario→DC→supplier drill; per-DC matrix. (D26/D27) |
| **Supplier Comparison** | **KEEP** (centerpiece) | Per-cell, one col/supplier, MIN highlighted, incumbent+rec flagged, impact block. Our edge over v3. (D26) |
| **Lowest-Cost Check** | **ADD** (from v3) | Per cell: B price vs market-low, PremVsLow %, IsSameSupplier, a Reason ("why the rec ≠ cheapest"). From `eng.bid_score` (A vs B awards). Governance. |
| **Coverage** | **ADD** (from v3) | Per cell×supplier: req vs offered cases, weekly/total cover ratio, band, As-Needed flag, eligible? From `bid.bid_line` vol-offered + `cyc.cycle_projected_volume` + `eng.bid_score`. |
| **Detailed Scoring** | **ADD** (upgrade `Scored Bids`) | The 5 factors + RecScore + eligible + gate flags **plus** the market stats that explain them (MktMin/Avg/Std, Z, PremVsLow, bands) — computed per group from the persisted prices. Auditability. |
| **TF Comparison** | **ADD if >1 TF** (from v3) | Per DC×lot: TF1 vs TF2 rec supplier/price/spend, same-supplier?, split flag. We seed 2 TFs. |
| **Round Evolution** | **ADD if >1 round** (from v3) | Per cell×supplier: R1→…→Rn price Δ + direction. We persist all rounds in `bid.bid_line`; engine scores final only — this reads the priced history. |
| **Data Quality** | **ADD** (from v3 Missing Data) | No-bid cells, missing coverage, quarantined-on-ingest rows, low-bidder-count groups. Non-blocking, surfaced. |
| **Data (pivot me)** | **KEEP** | Flat ListObject, one row per scenario×cell×supplier; native pivot source. (D27) |
| **Custom Scenario** | **KEEP** | Interactive: per-cell supplier dropdowns + live SUMIFS spend/savings/cap-breach; drives the LIVE Custom column. (D25) |
| **_Prices (hidden)** | **KEEP** | Live-formula backing grid for Custom + the comparison. |
| **Glossary / how-to** | **ADD (light)** | Fold the how-to + a measure glossary into Overview or a thin tab; legend for bands/flags. |

**CUT / not adopted (deliberately):** v3's `Bidder Detail`, `Top 5 Bids`, `Share of Business`,
`Regional Summary`, `Preferred Scenario`, `Vol Utilisation` as **separate tabs** — their content is
reachable by **drilling Scenario Comparison** and **pivoting `Data (pivot me)`** (depth-on-demand,
D27), so we get the richness without the 20-tab sprawl. (Share-of-business/concentration can be a
small panel on Overview if the alignment call needs it, not a full tab.) We keep ~12 single-purpose
tabs vs v3's 20 — rich but clean.

### Layout & interaction (the binding model — D27 "play with data to decide")
- **Drill (outline grouping):** scenario total → per-DC → per-supplier, opens collapsed. (have it; keep)
- **Filter/pivot (Excel Tables):** every long/detail view (Coverage, Detailed Scoring, Round
  Evolution, Data) is a real ListObject with AutoFilter; `Data (pivot me)` is the native-pivot source.
- **Compare:** suppliers-as-columns (Supplier Comparison); scenarios-as-rows + per-DC matrix
  (Scenario Comparison); against-what reference points on every surface.
- **Custom (live):** per-cell dropdowns + live recompute + the LIVE Custom column. (D25)
- **Front door:** Overview headline + tab index so 12 tabs are navigable.
- **Single header row, no merged super-headers, no width blow-outs.** Depth via drill/filter, not width.

### Explicitly deferred
**Visual design-language — color palette, typography, brand, iconography, exact fills/fonts — is OUT
OF SCOPE here and deferred to the downstream design review.** This study fixes *structure, views,
density, navigation, and interaction*. The current generator's fills/fonts are functional
placeholders; the design review owns the final look.

---

## 5. Grounding in our schema (what the sealed records can support)

Every proposed view maps to real columns — no view requires data we don't seal:

| Proposed view | Backing records |
|---|---|
| Lowest-Cost Check | `eng.bid_score` (price per bid, A-award = min price per group, B-award = rec) + `eng.analysis_scenario_award` |
| Coverage | `bid.bid_line.volume_minimum_cases`/vol-offered + `cyc.cycle_projected_volume` + `eng.bid_score.coverage_score`/`is_eligible` |
| Detailed Scoring (+ market stats) | `eng.bid_score` (5 factors, rec_score, eligible, gate_flags) + per-group market stats computed from the persisted final-round `bid.bid_line` prices |
| TF Comparison | per-cell awards across the 2 seeded `cyc.cycle_timeframe`s in `eng.analysis_scenario_award` |
| Round Evolution | priced `bid.bid_line` rows across all `cyc.cycle_round`s (all rounds persisted; engine scores final) |
| Data Quality | ingest quarantine + no-bid cells (cells with no priced `bid.bid_line`) + `gate_flags` (low-bidder-count) + missing coverage |
| Supplier roll-up / concentration | `eng.analysis_scenario_award` aggregated per supplier × scenario; `EngineConfig.conc_thresh` |

Limitation noted (V3_ENGINE_LOGIC §7): prior-round price is keyed (lot, TF, supplier) without DC, so
round deltas are lot-level until prior bids carry DC pricing — our Round Evolution reads the
**actual per-cell priced `bid.bid_line`** we persist per round, so it is DC-resolved in the demo.

---

## 6. Provenance & quarantine

- v3 engine run as an **external script** in a throwaway venv (pandas/numpy/openpyxl); never imported
  into `backend/`; input copied to a temp dir first so the engine's in-place writeback never touched
  the reference (verified byte-identical after the run). Output captured to a temp/gitignored path.
- This study records **structure only** — tab names, layout patterns, column-field labels, density,
  interaction. **No real supplier names, prices, or commercial values.** The v3 output and the real
  Excel remain gitignored reference (ADR-0001); nothing from them is committed.

---

## 7. The real Kroger allocation models — the practitioner layer (added 2026-06-19)

After §1–6 were written, the sponsor uploaded the **actual allocation models the team runs today** —
the "most complex current Excel" the brief asked for. These are the human *decision* workbooks (not
the engine's output, not a supplier bid), and they reset the bar: the best file is the **union** of
the v3 engine's analytical depth **and** the practitioners' decision/sign-off ergonomics.

**Files studied (structure only; gitignored under `reference/samples/_allocation_models/`):**

| File | Tabs | Notable scale |
|---|---|---|
| `Sweet Potatoes Allocation model RD2` | 19 | `Scenario tool` 199×**504 cols**; `Data cube` 177×**702 cols**; `CBS freight data` **150,987 rows** |
| `Sweet Potatoes Allocation model RD4` | 20 | adds **`Booking Guide`** + **`Signoff tables`** into the model; `Scenario tool` 186×**540 cols** |
| `Hybrid Onions Allocation model RD4` | 19 | `Scenario tool` 308×**514 cols**; `Data cube` 271×**648 cols**; `Sign-off tables` w/ Conv/Org + vs-STLY |

### 7.1 The practitioner architecture (what the real models do that neither ours nor v3 did)

1. **Layered narrative via `>` divider tabs:** `Outputs >` → `Calcs >` → `Raw data >`. The workbook
   reads answer → math → source; depth is on-demand by *band*, not by hunting 20 flat tabs.
2. **A `Controls` cockpit** drives the model: commodity, **Horizon (Short vs Long)**, commitment
   window, weeks/periods, total cases. One place sets the run; everything traces to it.
3. **Savings-first `Sign-off tables`** — the money shot buyers sign: per DC **Incumbent → Recommended**,
   **Savings $** (not %), **+/- vs Incumbent**, **vs STLY (same-time-last-year)**, **round-over-round
   savings**, split **Conventional vs Organic**. Two baselines (Incumbent + STLY), two timeframes
   (Weekly + full Storage period), dollars first.
4. **`FOB analysis` + `RFP - Delivery Charge`** — freight stripped off the landed price; FOB-only
   compared with **regional min (West/East)**. The landed price is FOB + lane freight + cold-chain.
5. **The `Scenario tool` is a 500+-col Lot×DC surface** — rows = every item at every DC, suppliers
   fanned across columns. They build **composite keys** (`ATLANTAONIONS ORGANIC` = DC+Lot) *next to*
   readable names + UPC — exactly our key-ID (D21) + names-not-keys (D23) design. The real files
   **validate our architecture.**
6. **A `Data cube`** (648–702 cols) — the pivot backbone; and a **`Supplier mapping`** name↔ID
   crosswalk. RD4 even folds the **Booking Guide** into the model (our separate output, confirmed).
7. **"Great but messy" confirmed:** `delete` scratch tabs, `FOB Analysis - old`, instruction/data
   mixing — the richness is real, the legibility is not. Our job is the richness *without* the mess.

### 7.2 What we built on top of the §4 foundation (the practitioner layer)

The §4 redesign closed the gap to the v3 *engine* output (Lowest-Cost Check, Coverage, Detailed
Scoring, TF Comparison, Round Evolution, Data Quality, a front door). On top of it we added the
**practitioner decision layer** from the real allocation models — all grounded in the sealed records:

| Added | What it is | Backing records |
|---|---|---|
| **Controls** (cockpit) | How the cycle was run: horizon/scope/volume, the **two baselines**, recommended spend, **negotiation savings R1→Final**, and the frozen engine weights + rules. Banded key/value. | `EngineConfig` + seeded scope + `cyc.cycle_projected_volume` + the baselines |
| **Award Summary** (sign-off) | THE headline: per DC **Incumbent → Recommended**, recommended period spend, **Savings $ vs incumbent** (+ blended %), **Savings $ vs STLY**, **Negotiation R1→Final $**, a **TOTAL** row, and a **Conventional/Organic** split. | `eng.analysis_scenario_award` (rec scenario) + incumbent routing baseline + round-evolution prices |
| **FOB vs All-In** | Freight transparency: each bid decomposed **FOB → +Delivery → +VegCool → = All-In**, cheapest *landed* bid per (lot,DC) highlighted, + a **regional freight** summary (avg Delivery by lane). | `bid.bid_line` component columns `fob_case`/`delivery_surcharge_case`/`vegcool_surcharge_case` (migration 0007) + DC region |
| **Banded navigation** | The Overview tab index is grouped into the decision flow **Decide → Compare suppliers → Diligence → Build & slice** (the real models' `Outputs >/Calcs >/Raw data >` idea, applied to single-purpose tabs). | — |

Two supporting changes made the above real rather than illustrative:
- **Bid components now populated end-to-end.** `fill_template` decomposes the synthetic All-In into
  **FOB (farm-gate) + Delivery (lane freight, by region) + VegCool (cold-chain)**, persisted via the
  ingester to `bid.bid_line` (exercising the 0007 schema + the `ck_bid_line_no_double_discount`
  guard — no Lot Discount, so All-In stays the value the engine scores; every prior tab's numbers
  are unchanged).
- **Incumbent baseline recalibrated** to a realistic prior-period actual-paid (the incumbent's own
  final-round bid + the ~7% an RFP captures), so the headline shows genuine **savings** (~5.7% vs
  incumbent in the demo) instead of a synthetic-calibration loss.

### 7.3 The result — 15 single-purpose tabs, banded as a decision flow

`Overview` · `Controls` · **`Award Summary`** · `Scenario Comparison` · `Lowest-Cost Check` ·
`Supplier Comparison` · **`FOB vs All-In`** · `Coverage` · `Detailed Scoring` · `TF Comparison` ·
`Round Evolution` · `Data Quality` · `Custom Scenario` · `Data (pivot me)` · `_Prices` (hidden).

This is the union: **v3's analytical depth + the practitioners' savings-first sign-off ergonomics +
our interactivity edge** (live Custom, drill, pivot) — rich like the real models, clean like nothing
they have. Visual design-language remains **deferred to the downstream design review** (§4, §0).

### 7.4 Schema-backed vs DEMO-illustrative (honesty line)

- **Schema-backed (real records):** incumbent baseline + savings $, FOB/Delivery/VegCool components
  + regional freight, round-over-round negotiation capture, the 5 factor scores, coverage, the split.
- **DEMO-illustrative (clearly labelled in-file):** the **STLY** uplift (no STLY feed yet — modelled
  as +4% on the incumbent baseline) and **product type** (Conventional/Organic — no schema column
  yet, derived by lot). Both are flagged where they appear. Closing them is a feeds/schema roadmap
  item (an STLY iTrade slice; a product-type attribute on the lot), not an output-design item.

---

## 8. The negotiation frame — repeated game under asymmetric information (added 2026-06-19)

The sponsor named the governing model: **repeated-game sourcing under asymmetric information**, where
you manage four things at once — supplier incentives, your process credibility, relationship capital,
and information advantage — under the structural rule **"predictable in process, flexible only where
the economics justify it."** The file is therefore not a price report; it is a **negotiation decision
instrument**. We added the surfaces that make that frame legible, organised as **four lenses** with a
headline **KPI band** on the Overview.

| Lens | What it answers | Surfaces (added/extended) |
|---|---|---|
| **1 · Cost & savings** | What do we save, vs what baseline? | Award Summary, Controls, Scenario Comparison, Lowest-Cost Check |
| **2 · Hidden costs** | What does the headline price hide? | **Landed & Hidden Costs** (FOB+freight **+ transit days + freshness watch**); transit also live in the **builder** and in **Data (pivot me)** |
| **3 · Relationships** | Who carries the business, and is it healthy? | **Share & Relationships** — supplier×scenario share heatmap, **Preserve** (incumbent kept) vs **Create** (new earned in), **dependency** flag at the concentration threshold, + a relationship ledger (preserved / created / at-risk) |
| **4 · Negotiation / fairness** | Are we being treated fairly? | **Negotiation Dynamics** — each supplier's **concession** R1→Final, the **incumbent's move vs the field** (do they lean on tenure?), and a **real-risk-vs-theater** read (below-market Z<−2 = validate sustainability; priced-high-and-firm = leverage/theater) |

### 8.1 What the lens surfaces (the game-theoretic reads)

- **Reading supplier incentives from observable moves.** Concession behaviour separates the hungry
  (conceding hard for volume) from the margin-protectors and the leverage-players. In the demo the
  incumbent holds at **−0.7%** while the field concedes **−3.8%** → *"holding the installed base —
  test the leverage,"* and the fairness verdict reads *"you are paying partly for tenure, not
  competitiveness."* That is the asymmetry the buyer negotiates against.
- **Real risk vs negotiation theater.** A below-market bid with Z<−2 is a *real* sustainability risk
  to validate; a bid priced above market that refuses to move is a *leverage play* to test. The file
  uses the market structure it already computes (Z, premium-vs-low, bidder count) to tell them apart.
- **Relationship capital & dependency.** Preserve/Create framing + a dependency flag where any
  supplier's share crosses the concentration threshold — over-giving weakens your next-round position.
- **Process credibility = predictable rules + justified flexibility.** The engine applies one governed
  rule set (Controls shows the weights/thresholds); every deviation from lowest-cost is shown with its
  economic justification (Lowest-Cost Check), and every exception (cap-breach, fallback) is flagged —
  flexible only where the economics justify it.

### 8.2 Visual readability pass (NOT final design language)

Semantic, meaning-carrying visuals only — the downstream design review still owns brand/typography:
a four-lens **KPI band** on the Overview, **heatmap** on the share matrix (white→amber→red at the
concentration line), **data bars** on concession, **green/red** cues on savings, an **amber freshness
watch**, and incumbent shading. These encode *meaning* (magnitude, risk, direction), not a look.

### 8.3 Synthetic calibration for the demo (honesty)

To make the negotiation lens demonstrate something, the synthetic round-over-round movement now
varies by supplier — the incumbent concedes little (leans on tenure), challengers concede more (the
hungriest most). This is DEMO calibration of *behaviour*, clearly a synthetic illustration; on real
data the concessions come straight from the persisted per-round `bid.bid_line` prices. Transit time
is a labelled lane proxy (no schema column yet) — like STLY and product type, a feeds/schema roadmap
item, not an output-design one.

### 8.4 The result — 17 tabs across the four lenses + diligence + build

`Overview` (4-lens KPI band) · `Controls` · **`Award Summary`** · `Scenario Comparison` ·
`Lowest-Cost Check` · `Supplier Comparison` · **`Landed & Hidden Costs`** · **`Share & Relationships`** ·
**`Negotiation Dynamics`** · `Coverage` · `Detailed Scoring` · `TF Comparison` · `Round Evolution` ·
`Data Quality` · `Custom Scenario` (now with live transit) · `Data (pivot me)` (+ transit, relationship)
· `_Prices`. Still clean, still playable; now it reads as a negotiation instrument, not a price report.

### 8.5 Live custom — the dashboards move with the build (added 2026-06-19)

The automated dashboards read the recommended Scenario B. To answer *"see all the dashboards change
when I build a custom scenario, not just the automated one,"* a **`Custom Dashboard`** tab recomputes
the lenses **entirely from live Excel formulas** over the Custom Scenario builder rows — so changing a
supplier dropdown moves the rollup:

- **Cost:** total spend, savings vs incumbent $/% — `SUM`/`SUMPRODUCT` over the builder's live
  `Line Spend` and `Volume × Baseline` columns.
- **Hidden cost:** volume-weighted avg transit + freshness-watch count — `SUMPRODUCT`/`COUNTIF` over
  the builder's live transit column.
- **Relationships:** per-supplier custom share (`SUMIF`/total) with a live dependency flag at the
  concentration threshold (heatmap + rule), and live custom spend/savings per DC.
- Each beside the **Recommended (B)** value with a **Δ vs rec** column — "your build vs the rec" at a
  glance. On the B pre-fill every Δ is 0 (validated: total spend, savings, suppliers, freshness,
  volume-weighted transit all match the recommendation exactly), then it diverges as you build.

This uses the same proven live-formula mechanism as the existing builder (the `_Prices` SUMIFS grid);
no macros, recalculates on open (`fullCalcOnLoad`). The result is 18 tabs. **Charts and visual-layout
polish remain the downstream design review's job — to be added without changing the file or its
architecture; this study fixes structure, views, interactivity, and navigation only.**

### 8.6 Explanations are engine-derived, not boilerplate (D28, added 2026-06-19)

Governing principle (sponsor): every explanatory string in an output is the **engine's authoritative
computed reason, rendered from the sealed records** — specific to the row, deterministic, never a
generic catch-all and never generated at output time. First applied to the Lowest-Cost Check's
"why not lowest": the engine's per-cell **RecType** (V3 §5 — Lowest cost / Coverage advantage /
Comparable / Defensible / Risk-adjusted) was computed-but-unused; it is now produced by `V3Engine`
for the B picks, **sealed on `eng.analysis_scenario_award.rec_type`** (migration 0009), and rendered
specifically per cell (e.g. *"Coverage advantage — clears >120% of required volume; 2.8% over the
market low buys supply security"*) instead of one boilerplate clause. Single source of truth: the
engine decides the reason once, the output renders it (no re-derivation that can drift). Pinned by an
engine invariant test. New explanatory text must follow D28.
