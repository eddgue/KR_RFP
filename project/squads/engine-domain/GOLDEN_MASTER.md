---
doc: Golden-Master Reproducibility Test — design
id: ENG-GOLDEN-MASTER
squad: Engine & Domain (Squad 2)
status: Designed (golden pair verified to reproduce, 2026-06-18)
created: 2026-06-18
relates: ADR-0006 (Phase-D exit gate = reproduce v3), V3_ENGINE_LOGIC.md, SPIKE_D2_engine.md §5,
         backlog S2 ("engine reproduces v3"), backend/app/engine/interface.py
note: Structure + assertions only. NO real prices, supplier names, or award values are recorded.
      The real golden pair (potato_2026_*) is QUARANTINED/gitignored; CI uses a SYNTHETIC fixture.
---

# Golden-Master Reproducibility Test

The Phase-D exit gate (ADR-0006, S2): the lifted engine must **reproduce v3's scored/allocated
numbers** on a known input/output pair. This file designs that test.

**Validation already performed (2026-06-18):** v3 was run in a venv (pandas 3.0.3, numpy 2.4.6,
openpyxl 3.1.5) against the real golden input `potato_2026_rfp_input.xlsx`. It ran end-to-end
(all 9 steps, "COMPLETE"), and its output matched the golden `potato_2026_rfp_analysis_output.xlsx`
with **zero numeric diffs** across Detailed Scoring (95,251 cells), Recommendations (43,771), DC
Constraint Review (4,797), and Bidder Detail (36,781) — 180,600 numeric cells, plus Scenario
Comparison / Lowest Cost Check / Share of Business spot-checks. The produced workbook (real values)
was gitignored and deleted; nothing real was committed. **This confirms the golden pair is a valid
reference and the engine is deterministic on it** — so our lifted implementation has a fixed target.

---

## 1. INPUT schema — 13 tabs (structure only)

Header at row 4 (IN_Custom row 6). CONFIG is key/value (col A label → col B value).

| Tab | Role | Key columns |
|---|---|---|
| CONFIG | run params | labels → values (commodity, weights, max_sup_dc, thresholds, conc_thresh, TFs, rounds) — see V3_ENGINE_LOGIC §8 |
| IN_Bids | all bid rounds | Round_ID, Bid_Type, Supplier, DC Name, Lot_ID, TF, Item_Description, All-In_$/case, FOB_$/case, Delivery_Surcharge, VegCool_Surcharge, Lot_Discount, Pricing Comments, Weekly Vol_Offered, Total Vol_Offered, Invested?_(R1 only) |
| IN_Incumbents | current pricing | Incumbent Supplier, DC Name, Lot_ID, Item Description, Incumbent_FOB $/case, Incumbent_Routing $/case, Contract Notes |
| IN_Volumes | demand | DC Name, DC_ID, TF, Lot_ID, Item Description, Weekly_Volume (cases), Total_Volume (cases), Weeks |
| IN_Premiums | per-lot premium overrides | Lot_ID, Item Description, Global/Suggested/Override/Effective_Threshold, Rationale |
| IN_Custom | Scenario F | DC Name, TF, Lot_ID, Item Description, Your Award Supplier, Notes |
| IN_Exclusions | Scenario E | Scenario, Supplier, Supplier_ID, DC_ID, Lot_ID, TF, Reason |
| IN_Preferred | Scenario G | DC, TF, Lot_ID, Preferred_Supplier, Reason, Active (Y/N) |
| IN_VolumeLimits | capacity | Supplier, DC, Lot_ID, TF, Max Wkly Vol (cases/week), Max Total Vol (cases/period), Notes |
| DIM_Suppliers | dim | Sup_ID, Supplier Name, Region, Notes |
| DIM_Lots | dim | Lot_ID, Item Description, Category, Pack Size, UOM, Notes |
| DIM_DCs | dim | DC_ID, DC Name, Region, State, Notes |
| DIM_Rounds | dim | Round ID, Round Label, Bid Type, Active, Notes |

## 2. OUTPUT schema — 20 tabs (structure only; golden dims)

| Tab | Holds | Golden dims (rows×cols) |
|---|---|---|
| Executive Summary | headline KPIs, top savings | 40×10 |
| Award Recommendations | Scenario B awards per cell + cap-breach amber | 328×26 |
| Preferred Scenario | Scenario G awards + exceptions | 339×20 |
| Regional Summary | spend/savings by region, all scenarios | 77×25 |
| Vol Utilisation | awarded vs stated supplier limits | 17×20 |
| Share of Business | per-supplier spend %, **concentration flags ≥40%** | 71×30 |
| Recommendations | all scenarios A–G, one row per cell (filterable) | 2272×35 |
| Scenario Comparison | per-scenario KPIs (spend/savings/suppliers/risk) | 328×35 |
| Lowest Cost Check | **Scenario B vs A**, premium where they differ | 328×16 |
| Top 5 Bids | top bids per DC/Lot/TF group | 545×22 |
| DC Constraint Review | supplier ranking per DC/TF, lot assignments, cap | 1020×22 |
| Bidder Detail | every bid scored | 4824×20 |
| Custom Scenario | live what-if (Scenario F) | 339×38 |
| Supplier Overview | per-supplier rollup | 21×19 |
| TF Comparison | per-timeframe rollup | 198×16 |
| Round Evolution | R1→R2 deltas (lot-level) | 4824×21 |
| Coverage Analysis | coverage ratios/bands per bid | 4824×18 |
| **Detailed Scoring** | **the 5 factor scores + RecScore per bid** | 4824×30 |
| Missing Data | DQ issues logged | 18×10 |
| Glossary | plain-English methodology | 48×14 |

The **Detailed Scoring** tab is the primary reproduction target (per-bid factor scores +
RecScore); **DC Constraint Review** proves the split; **Lowest Cost Check** proves Scenario A.

---

## 3. Assertion set — what proves reproduction

Compare our `EngineResult` against v3's tabs. Tolerance **≤ 0.5** on each band score / RecScore
(they are integer-band-derived, so exact in practice); spend/savings exact to the cent;
flags/codes exact (string equality).

### 3.1 Scoring (→ `eng.bid_score`, vs Detailed Scoring)
- **Band-edge rows** — synthetic rows placed exactly at the boundaries to prove the cascade:
  - Price: PremVsLow = 0.00 → 100; 0.03 → 100; 0.0301 → 80; 0.07 → 80; 0.0701 → 50; 0.12 → 50; 0.1201 → 20.
  - Coverage: TotalCovRatio = 0.49 → 0; 0.50 → 40; 0.79 → 40; 0.80 → 70; 0.99 → 70; 1.00 → 100; 1.20 → 100; 1.21 → 95; NaN → 30; As-Needed → 70.
  - Historical: DeltaVsHistPct = −0.11 → 100; −0.10 → 100; −0.03 → 85; +0.03 → 70; +0.07 → 45; +0.08 → 20; no baseline → 50.
  - Z-Risk: ZScore = 0 → 100; −2.1 → 60; +2.1 → 40; +1.5 → 80.
  - Continuity: Supplier==Incumbent → 100; else 0.
- **Composite:** RecScore = weighted sum (round 2) for each edge row, with default and a
  renormalized weight set (e.g. weights summing to 1.20 → assert renormalization to 1.0).

### 3.2 Eligibility (→ `gate_flags`, vs Detailed Scoring / Missing Data)
Assert each reason code fires on a crafted row: `No valid price` (Price≤0), `Price premium
exceeds threshold` (PremVsLow>MaxPremThresh), `Insufficient volume (<80%)`, `Low price outlier`
(Z<−2), `High price outlier` (Z>2), `Low bidder count (<3)`. Assert `eligible` true/false matches
the three hard gates (valid price, premium ≤ threshold, coverage ≥ 0.80-or-As-Needed).

### 3.3 Split allocation (→ `scenario_award`, vs DC Constraint Review)
- **Top-N selection:** for a DC×TF with ≥3 suppliers, assert the same top-`max_sup_dc` set by
  `SupRankScore = AvgScore·0.60 + LotsCovered·5 + clip(AvgCoverage,0,1.2)·10` (tie-break AvgPrice asc).
- **Per-lot split:** assert the same lot→supplier assignment within the kept set.
- **Fallback flag:** a lot only coverable outside the top-N is awarded from the wider field with
  `is_fallback = True`.
- **Cap breach:** a DC×TF whose Scenario-B award uses > `max_sup_dc` suppliers → `cap_breach_flag = True`.
- **Concentration:** a supplier whose Scenario-B RecSpend ≥ `conc_thresh` (0.40) of category spend
  is flagged (Share of Business).

### 3.4 Scenarios (→ `eng.scenario` + `scenario_award`)
- **Scenario A lowest-cost total:** sum of cheapest-eligible-per-cell Price·TotVolReq equals v3's
  Lowest Cost Check / Scenario Comparison "A" spend (exact).
- **Scenario C:** incumbent retained iff `Supplier==Incumbent ∧ PremVsLow≤0.03 ∧ coverage≥0.80`,
  else equals B's pick for that cell.
- **B = default recommendation** (highest RecScore via the deterministic sort, §6 of logic doc).

### 3.5 Cost construction
- **All-In primary:** when All-In present, Price = All-In (no recompute).
- **Fallback:** when All-In blank, Price = FOB + Delivery + VegCool − LotDiscount − AllLotDiscount.
- **No double-subtract:** a row with All-In present **and** Lot_Discount populated must NOT
  subtract the discount again (assert Price == All-In, not All-In − discount).
- **Prior-round price is lot-level:** assert the R1 lookup keys (Lot,TF,Supplier) with no DC.

---

## 4. Durable fixture strategy — the committable synthetic golden

The real Potato pair is **quarantined/ephemeral** (real commercial values; `reference/samples/*`
is gitignored). CI needs a **non-sensitive, committable** golden. Plan:

1. **Author a synthetic input** — a hand-built `synthetic_rfp_input.xlsx` (same 13-tab schema)
   with **generic placeholders**: suppliers `S01..S06`, DCs `DC01..DC03` (2 regions), lots
   `LT01..LT04`, TFs `TF1..TF2`, rounds R1/R2. Round prices are chosen so that **every band edge
   and every branch fires** at least once:
   - price premiums landing on 0.03 / 0.07 / 0.12 edges;
   - coverage ratios at 0.49/0.50/0.80/1.00/1.20/1.21, one As-Needed lot, one missing-volume lot;
   - historical deltas at −0.10/−0.03/+0.03/+0.07; one lot with no incumbent baseline;
   - one Z-outlier (a deep low and a high bid) and one <3-bidder group;
   - one DC×TF with 3+ suppliers (forces top-2 + a fallback-flagged lot);
   - one supplier engineered to ≥40% category spend (concentration flag);
   - one exclusion (E), one custom override (F), one preferred rule incl. a no-bid exception (G);
   - one All-In-blank row (fallback path) and one All-In-present-with-Lot_Discount row (footgun).
   Target ~30–60 bid rows — small enough to commit, large enough to exercise the matrix.
2. **Generate expected output once, locally** — run v3 (the quarantined `.py`, in the same venv)
   against the synthetic input **a single time**. Because the input is synthetic/placeholder, its
   output carries **no real values** and is safe to commit.
3. **Distill to a committed expectations file** — extract from that run only the asserted numbers
   (per-bid factor scores + RecScore, gate_flags, the D split + fallback/cap flags, the A total,
   the all-in/fallback Prices) into a small `golden_expectations.json` (or CSV) committed under
   `backend/tests/fixtures/`. Commit the synthetic input `.xlsx` alongside it. **Do NOT commit the
   full 20-tab workbook** (unnecessary; the expectations file is the contract).
4. **CI test** — `test_engine_reproduces_v3`: load the synthetic input into the store fixtures,
   call `Engine.run(EngineInputs)`, and assert each `BidScore` / `ScenarioAward` against
   `golden_expectations.json` within tolerance. This is the Phase-D exit gate (S2) and the guard
   that authorizes swapping the stub for the real v3 logic.
5. **Regeneration discipline** — the synthetic input + v3 script + venv pins are recorded so the
   expectations file can be regenerated if v3 changes; the regenerate step runs the quarantined
   `.py` (never imported into `backend/`). A second, larger real-pair check (Potato) may be run
   **locally only**, never in CI, as a confidence cross-check (it reproduced cleanly today).

**Why synthetic, not the real pair:** the real pair proves v3 is deterministic and gives us the
exact target (done), but it cannot live in CI (real prices/suppliers). The synthetic fixture is
designed to hit the same branches, so passing it proves the lifted logic without exposing data.
