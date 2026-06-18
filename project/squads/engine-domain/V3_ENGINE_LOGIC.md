---
doc: V3 Engine Logic — implementation-ready extraction
id: ENG-V3-LOGIC
squad: Engine & Domain (Squad 2)
status: Verified (reproduced the golden output, 2026-06-18)
created: 2026-06-18
source: rfp_analysis_engine_v3.py (4,198 lines, QUARANTINED/gitignored — read, never imported)
relates: ADR-0006 (adopt v3 brain), ADR-0001 (clean-room), SPIKE_D2_engine.md, PLAN.md,
         backend/app/engine/interface.py (frozen interface we implement against),
         GOLDEN_MASTER.md (the reproducibility test this logic must pass)
note: This file describes v3's LOGIC only (algorithms, thresholds, weights) with line refs.
      No verbatim engine code, no real prices/supplier names/award values are recorded here.
---

# V3 Engine Logic

The clean-room logic extraction of `rfp_analysis_engine_v3.py`. Constants (band thresholds,
weights, caps) are reproduced exactly — they are logic, not sensitive. Line references are to
the source as read. **Validation status:** the engine was run against the golden Potato 2026
input and reproduced the golden output with **zero numeric diffs** across the Detailed Scoring,
Recommendations, DC Constraint Review, and Bidder Detail tabs (180,600 numeric cells). See
`GOLDEN_MASTER.md`.

The engine is a stateless, file-in/file-out monolith: ~1,500 lines of logic (steps 1–7,
lines 117–1335) and ~2,700 of openpyxl formatting (steps 8–9, lines 1336–4198). **We lift
steps 1–7; steps 8–9 are replaced by the Document generator (other squad).** Our Runner reads
from the store, freezes inputs, runs the lifted scorer → scenario builder → split allocator,
and writes sealed `eng.*` records (PLAN §3).

---

## 1. The 9-step pipeline

| # | Step | Lines | Real behavior (lifted) |
|---|------|-------|------------------------|
| 1 | Load config | 117–202 | Read CONFIG (key/value, header=None). `cfg(df,label,default)` is a case-insensitive label lookup in col A → value in col B. Parses commodity/cycle/prefix, `max_sup_dc`, weights, premium thresholds, active TFs (3-char `TFn` rows with col E = `YES`), active rounds (rows under a `Round ID` marker with col D = `YES`). Final round = last active; prior = first if >1. |
| 2 | Schema validation | 204–218 | `validate_schema` warns (does not fail) on missing required columns. Required: IN_Bids `[Round_ID, Supplier, DC Name, Lot_ID, TF]`; IN_Incumbents `[DC Name, Lot_ID]`; IN_Volumes `[DC Name, Lot_ID, TF]`. **Lenient — warnings only.** |
| 3 | Load input | 220–519 | `load_tab(file, sheet, hdr, required)` reads each tab at its header row (IN_/DIM_ = row index 3 i.e. 4th row; IN_Custom = 5). Renames many column aliases to internal standard (`std_bids`/`std_inc`/`std_vol`, 246–313). Derives `DC_ID` from `DC` when missing/blank. Coerces numerics. Builds per-lot premium map, exclusion set, custom overrides, DC→Region map, preferred rules, volume-limit rules. |
| 4 | Data-quality checks | 521–577 | Non-blocking. `dq(flag,count,detail)` appends to `dq_issues` when count>0: duplicate bid rows, missing required fields, missing AllIn/FOB price, missing vol offered (→ As-Needed fallback), missing incumbent routing, lots in bids missing from Volumes/Incumbents. **Surfaced in the Missing Data tab; never halts the run.** |
| 5 | Price construction & scoring | 579–813 | Filter to final round; construct `Price` (§7); merge incumbent + volume + region; compute market stats, Z-score, premium, coverage; apply the five banded factors → `RecScore`; apply eligibility gates → `Eligible` + `GateFlag`. **The core.** |
| 6 | Scenarios | 815–1111 | Build A–G over the eligible set; `max_two_per_dc` allocator (D); scenario KPIs. |
| 7 | Analytics | 1113–1335 | Lowest-cost check (B vs A), supplier overview, TF comparison, round evolution, consolidation plan, vol utilisation, concentration. |
| 8 | Build workbook | 1336–4125 | openpyxl formatting of 20 tabs. **Not lifted** — replaced by Document generator. |
| 9 | Save | 4126–4198 | Writes `<prefix>_RFP_Analysis.xlsx`. **Not lifted** — our Runner writes sealed records. |

---

## 2. Scoring — the five banded factors (lines 726–782)

All factor scores are 0–100. The composite `RecScore` is a weighted sum, `.round(2)`.

### 2.1 Price score — banded on premium-vs-lowest (PremVsLow), lines 729–733
`PremVsLow = (Price − MktMin) / MktMin`, where `MktMin` is the min Price within the group key
`[DC_ID, Lot_ID, TF]` (line 688, 679).

| Premium vs low | Price score |
|---|---|
| ≤ 3% (0.03) | **100** |
| ≤ 7% (0.07) | **80** |
| ≤ 12% (0.12) | **50** |
| > 12% | **20** |

(`np.select` cascade; first matching band wins. Default `nan` → treated as 0 in the composite.)

### 2.2 Coverage score — banded on TotalCovRatio, lines 743–755
`TotalCovRatio = TotVolOffered / TotVolReq` (NaN when As-Needed or req missing/0, lines 707–711).
**As-Needed → fixed 70** (line 744). Otherwise:

| TotalCovRatio | Coverage score |
|---|---|
| NaN (missing, manual review) | **30** (penalty) |
| < 0.50 | **0** |
| < 0.80 | **40** |
| < 1.00 | **70** |
| ≤ 1.20 | **100** |
| > 1.20 | **95** (surplus capped) |

### 2.3 Historical score — banded on DeltaVsHistPct, lines 760–769
`DeltaVsHistPct = (Price − IncRouting) / IncRouting` (positive = pricier than incumbent).
`IncRouting` is the incumbent delivered all-in baseline (`Incumbent_Routing $/case`).

| DeltaVsHistPct | Hist score |
|---|---|
| IncRouting is NaN (no baseline) | **50** |
| ≤ −10% (≥10% cheaper) | **100** |
| ≤ −3% | **85** |
| ≤ +3% | **70** |
| ≤ +7% | **45** |
| > +7% | **20** |

### 2.4 Z-Risk score — banded on ZScore, lines 736–740
`ZScore = (Price − MktAvg) / MktStd` within `[DC_ID, Lot_ID, TF]`.

| ZScore | Z-Risk score |
|---|---|
| in [−1, +1] | **100** |
| < −2 (low outlier — validate sustainability) | **60** |
| > +2 (high outlier) | **40** |
| otherwise (between 1 and 2 either side) | **80** (default) |

### 2.5 Continuity score — line 773
`IncumbentContinuityScore = (Supplier == Incumbent) ? 100 : 0`. Marginal tie-break only.

### 2.6 Composite RecScore (lines 776–782) and weights
```
RecScore = PriceScore·w_price + CoverageScore·w_cov + HistScore·w_hist
         + ZRiskScore·w_zrisk + IncumbentContinuityScore·w_cont          (round 2)
```
NaN factor scores are `.fillna(0)` before weighting (continuity is never NaN). Default weights:

| Factor | Weight | CONFIG key |
|---|---|---|
| Price | **0.35** | `Price Weight` |
| Coverage | **0.25** | `Coverage Weight` |
| Historical | **0.20** | `Historical Weight` |
| Z-Risk | **0.10** | `Z Risk Weight` |
| Continuity | **0.10** | `Continuity Weight` |

**Weight normalization (lines 143–146):** `total_w = sum(weights)`. If `|total_w − 1.0| > 0.01`,
print a WARNING and divide every weight by `total_w` (so e.g. weights summing to 120% are
renormalized to sum 1.0). Otherwise leave as-is. **Cost is 35% of the decision, not 100%.**

---

## 3. Eligibility gates (lines 785–800)

A bid is **Eligible** iff ALL hold (line 785–790):
1. `Price` not NaN **and** `Price > 0`, **and**
2. `PremVsLow ≤ MaxPremThresh` (per-lot threshold from IN_Premiums, else global; line 657), **and**
3. As-Needed **or** `TotalCovRatio` is NaN **or** `TotalCovRatio ≥ 0.80` (coverage floor).

Eligibility gates the **awardable** universe (scenarios run over eligible bids); scoring still
runs on all valid-priced bids. `GateFlag` is an accumulated `; `-joined string (lines 793–800):

| Reason code (string) | Fires when |
|---|---|
| `No valid price` | Price NaN or ≤ 0 |
| `Price premium exceeds threshold` | PremVsLow > MaxPremThresh |
| `Insufficient volume (<80%)` | not As-Needed and TotalCovRatio < 0.80 |
| `Low price outlier: validate sustainability` | ZScore < −2 |
| `High price outlier` | ZScore > +2 |
| `Low bidder count (<3): Z-score less reliable` | BidderCount < 3 (group has <3 suppliers) |

Note: the outlier and low-bidder-count flags are **advisory** — they are recorded in `GateFlag`
but do **not** by themselves make a bid ineligible (only gates 1–3 set `Eligible=False`).

---

## 4. Allocation — `max_two_per_dc` split (lines 963–1000)

Per `(DC, TF)` group (Scenario D). The two-supplier-per-DC split (the sign-off deck's split award) as an algorithm.

**4.1 Supplier-strength ranking** (lines 969–981). Aggregate each supplier within the DC×TF:
- `AvgScore` = mean RecScore, `LotsCovered` = nunique Lot_ID, `AvgPrice` = mean Price,
  `AvgCoverage` = mean of `TotalCovRatio.fillna(1.0)`.
- **Strength formula (one line):**
  `SupRankScore = AvgScore·0.60 + LotsCovered·5 + clip(AvgCoverage, 0, 1.2)·10`
- Sort by `[SupRankScore desc, AvgPrice asc]`; take top `max_sup_dc` (default **2**) suppliers.

**4.2 Per-lot award within the kept set** (lines 982–986): restrict the group to the top-N
suppliers; award each lot to the best by `deterministic_sort` (§6), one row per lot.

**4.3 Fallback fill with transparency flag** (lines 987–995): any lot the top-N cannot cover is
awarded to the best eligible bid from the **wider** field (whole DC×TF group) and tagged
`_D_Fallback = True`. This is the transparency flag — the lot was filled outside the consolidated
set. If the top-N set is empty, fall back to the whole group (line 983).

**4.4 Cap-breach detection** (lines 1909–1912, output side): per `(DC_ID, TF)` in Scenario B,
`SupCount = nunique(Supplier)`; `CapBreach = SupCount > max_sup_dc`. Breach rows are amber-flagged
("Manual decision required") in Award Recommendations / DC Constraint Review. → our
`cap_breach_flag` on `scenario_award`.

**4.5 Concentration cap 0.40** (lines 3998–4001, 4060–4075): on Scenario B, per supplier
`conc_pct = supplier_RecSpend / total_B_RecSpend`; flag `conc_pct ≥ conc_thresh` (default **0.40**).
This is a **category-spend concentration flag** (supply-risk), distinct from the per-DC supplier
cap in 4.4. Both surface; neither auto-rejects (decision-support).

---

## 5. Scenario lenses A–G (lines 913–1085; Glossary 2516–2524)

All scenarios run over the **eligible** set and award one supplier per group key `[DC_ID,Lot_ID,TF]`
(except D, which is per DC×TF). The deterministic tie-break sort (§6) governs B/C/D/E/F/G.

| Lens | Label | Definition |
|---|---|---|
| **A** | Lowest Cost (Benchmark) | Cheapest eligible bid per group: sort by `[group, Price asc, Supplier]`, take first (917–920). No scoring, no extra gate beyond eligibility. **Benchmark, never auto-applied.** |
| **B** | Risk-Adjusted (Recommended) | Highest `RecScore` per group via `deterministic_sort` → first (922–942). **The main recommendation.** A `RecType` label is assigned (937–941): `Lowest cost` (PremVsLow≤2%), `Coverage advantage` (WeeklyCovRatio>1.2), `Comparable premium` (≤3%), `Defensible premium` (≤7%), else `Risk-adjusted`. |
| **C** | Incumbent Defense | Incumbent candidates = eligible rows where `Supplier==Incumbent` **and** `PremVsLow ≤ 0.03` (Comparable threshold) **and** (As-Needed or coverage NaN or `TotalCovRatio ≥ 0.80`) (947–951). For lots where the incumbent qualifies use them; **else fall back to B** (the risk-adjusted pick). The "within 3% at ≥80% coverage" rule. |
| **D** | Max-N per DC | The `max_two_per_dc` split allocator (§4). Top-N strongest suppliers per DC×TF, best lot assignments within that set, fallback fill flagged. |
| **E** | Exclusion Applied | Drop suppliers in the IN_Exclusions set, then re-run B's selection (1002–1011). If no exclusions, E = B (labeled "no exclusions"). |
| **F** | Custom Override | Start from B; for each IN_Custom row, replace the award at `(DC,Lot,TF)` with the named supplier **if that supplier has a valid eligible bid there** (else WARN + skip) (1013–1037). |
| **G** | Preferred Supplier | Start from B; for each IN_Preferred rule (Lot + optional DC/TF wildcards), force the preferred supplier where they have an eligible bid; **if no eligible bid → log an exception and keep B's pick** (1039–1076). |

---

## 6. Deterministic tie-break sort (lines 903–911)

Used by B/C/D/E/F to make the "best per group" pick reproducible:
sort by `[RecScore desc, Price asc, TotalCovRatio desc, _IncBoost desc, Supplier asc]`, where
`_IncBoost = (Supplier == Incumbent)`. Take `.first()` per group. **This sort order is
load-bearing for reproduction** — any reimplementation must match it exactly (it determines
which bid wins on RecScore ties).

---

## 7. Cost construction — All-In primary + fallback (lines 589–603)

`Price` per bid (final round):
```
Price = AllIn   if AllIn is present
        else  FOB + DeliverySurcharge + VegCoolSurcharge − LotDiscount − AllLotDiscount
```
- **Primary:** `All-In_$/case` from the bid (assumed already net of discounts).
- **Fallback (All-In blank):** `FOB + Delivery Surcharge + VegCool Surcharge − Lot Discount
  − AllLot Discount`. (VegCool = a cold-chain cost component.)
- **The double-subtract footgun:** if All-In is already net of discounts **and** Lot Discount is
  also populated, a naive recompute double-subtracts. v3 avoids it by only applying discounts in
  the fallback branch (`fillna`). **Our store must enforce ONE path** (the `no_double_discount`
  CHECK, PLAN §2) — do not leave it to a note.
- After construction, rows with `Price` NaN or ≤ 0 are dropped (line 603).

**Prior-round price caveat (lines 884–896):** the prior-round (R1) price lookup keys on
`(Lot_ID, TF, Supplier)` — **no DC**. A single prior price maps to all DCs for that lot, so
round-over-round deltas are **lot-level only** until prior bids carry DC pricing. Fix at the
source in the bid store.

---

## 8. CONFIG schema — every key the engine reads

| CONFIG label (col A) | Internal | Default | Used for |
|---|---|---|---|
| `Commodity Name` | commodity | 'Commodity' | labels |
| `Bid Cycle Label` | cycle_label | 'RFP' | labels |
| `Output File Prefix` | file_prefix | 'RFP' | output filename |
| `Max Suppliers per DC` | max_sup_dc | **2** | split cap (§4) |
| `Global Premium Threshold` | global_thresh | **0.12** | default max premium |
| `Concentration Threshold` | conc_thresh | **0.40** | category concentration flag |
| `Price Weight` | w_price | **0.35** | scoring |
| `Coverage Weight` | w_cov | **0.25** | scoring |
| `Historical Weight` | w_hist | **0.20** | scoring |
| `Z Risk Weight` | w_zrisk | **0.10** | scoring |
| `Continuity Weight` | w_cont | **0.10** | scoring |
| `Comparable Premium Threshold` | THRESH_COMPARABLE | **0.03** | RecType, Scenario C gate |
| `Defensible Premium Threshold` | THRESH_DEFENSIBLE | **0.07** | RecType, high-premium count |
| `Max Premium Threshold` | THRESH_MAX | = global_thresh | eligibility ceiling |
| `TF Label` rows (`TFn`, col E=`YES`) | tf_rows | TF1 | active timeframes |
| `Round ID` rows (`Rn`, col D=`YES`) | round_rows | R1/R2 | active rounds; final/prior |

Note: in the golden CONFIG the **active weights** appear under a "PRESET / ACTIVE WEIGHTS"
block (Balanced/Price Focus/Coverage Focus/Risk Averse/Custom presets); the engine reads the
labeled rows `Price Weight`/`Coverage Weight`/`Historical Weight` (+ Z/Continuity defaults).
`Coverage Eligibility Floor` and `Single Supplier per Lot` keys are present in CONFIG but the
0.80 floor and per-group single-award are hard-coded in the scoring/scenario logic.

### Input tab → column contract (golden, header at row 4 except IN_Custom row 6)

| Tab | Columns (header row) |
|---|---|
| IN_Bids | Round_ID, Bid_Type, Supplier, DC Name, Lot_ID, TF, Item_Description, All-In_$/case, FOB_$/case, Delivery_Surcharge, VegCool_Surcharge, Lot_Discount, Pricing Comments, Weekly Vol_Offered, Total Vol_Offered, Invested?_(R1 only) |
| IN_Incumbents | Incumbent Supplier, DC Name, Lot_ID, Item Description, Incumbent_FOB $/case, Incumbent_Routing $/case, Contract Notes |
| IN_Volumes | DC Name, DC_ID, TF, Lot_ID, Item Description, Weekly_Volume (cases), Total_Volume (cases), Weeks |
| IN_Premiums | Lot_ID, Item Description, Global_Threshold, Suggested_Threshold, Override_Threshold, Effective_Threshold, Rationale/Notes |
| IN_Custom | DC Name, TF, Lot_ID, Item Description, Your Award Supplier, Notes/Rationale |
| IN_Exclusions | Scenario, Supplier, Supplier_ID, DC_ID, Lot_ID, TF, Reason |
| IN_Preferred | DC, TF, Lot_ID, Preferred_Supplier, Reason/Note, Active (Y/N) |
| IN_VolumeLimits | Supplier, DC, Lot_ID, TF, Max Wkly Vol (cases/week), Max Total Vol (cases/period), Notes |
| DIM_Suppliers | Sup_ID, Supplier Name, Region, Notes |
| DIM_Lots | Lot_ID, Item Description, Category, Pack Size, UOM, Notes |
| DIM_DCs | DC_ID, DC Name, Region, State, Notes |
| DIM_Rounds | Round ID, Round Label, Bid Type, Active, Notes |

Volume-limit rule resolution (lines 498–511) is most-specific-match:
Supplier+DC+Lot+TF → … → Supplier (priority score `DC·4 + Lot·2 + TF·1`, blanks treated as wildcards).

---

## 9. Mapping to our reconciled store (cyc / bid / eng)

The engine reads from a workbook; our Runner must feed the same values from the governed store
and write sealed records instead of an Excel.

| Engine input | Source tab | Our store column |
|---|---|---|
| Final-round bid `Price` (All-In/fallback) | IN_Bids | `bid.bid_price` (landed cost per case) + `bid.bid` for Lot/DC/TF/Supplier/Round |
| Volume requirement (Wkly/Tot, Weeks) | IN_Volumes | `cyc.volume_requirement` (DC×Lot×TF) |
| Volume offered (Wkly/Tot) | IN_Bids | `bid.bid` (vol-offered columns) |
| Incumbent + routing/FOB baseline | IN_Incumbents | `perf.itrade_receipt` (historical cost) + an incumbent flag per DC×Lot |
| Per-lot premium thresholds | IN_Premiums | `cyc.*` lot threshold override; else `EngineConfig.global_thresh` |
| Weights, max_sup_dc, conc_thresh, premium bands | CONFIG | `eng.analysis_run.config_json` (frozen `EngineConfig`) |
| Exclusions / Custom / Preferred / VolumeLimits | IN_* | `cyc.*` scenario-rule tables (E/F/G inputs) |
| DC→Region | DIM_DCs | `cyc.dc` (region/state) |

**Writes:** `eng.analysis_run` (sealed header + `config_json`), `eng.bid_score` (the 5 factor
scores + `rec_score` + `eligible` + `gate_flags`), `eng.scenario` (A–G headers),
`eng.scenario_award` (one row per awarded supplier per `(scenario, dc, lot, tf)` with
`volume_share`, `awarded_price`, `is_recommended`, `is_fallback`, `cap_breach_flag`).

### Gap — what our reconciled schema must close (the top item)
1. **Split grain (the top gap).** v3 awards multiple suppliers per DC×TF (Scenario D) and the
   golden output shows fallback-flagged lots. Our as-built `scenario_award` carries
   `UNIQUE(run,dc,lot,tf)` (single-winner) and **no `volume_share` / `is_fallback` /
   `cap_breach_flag`**. **Relax the unique constraint to per-supplier-per-cell and add those
   three columns** — without this the engine cannot persist a split award, which is the whole
   point of ADR-0006. (Platform & Data own the DDL; we own the contract. Ships with E-18/E-20.)
2. **Incumbent identity per DC×Lot.** Scoring (continuity, historical, Scenario C) needs a
   reliable `is_incumbent` per `(DC, Lot)` and an incumbent routing baseline; the as-built has
   eligibility/landed-cost but the incumbent linkage from `perf.itrade_receipt` must be explicit.
3. **Volume-offered columns on `bid.bid`.** Coverage scoring needs `WklyVolOffered` /
   `TotVolOffered` per bid line; confirm these are captured at intake (they drive the 0.80 floor).
4. **Prior-round price keyed (Lot, TF, Supplier) only** — no DC. Either accept lot-level deltas
   or add DC to prior bids at the source (§7 caveat).
5. **Per-lot premium override + As-Needed flag** must be carried on the cycle (IN_Premiums /
   IN_Volumes VolumeType) so the engine's eligibility ceiling and coverage skip reproduce.

The frozen `Engine.run(EngineInputs) -> EngineResult` interface (interface.py) already models
weights, `max_sup_dc`, `conc_thresh`, the five `BidScore` factors, and `ScenarioAward` with
`volume_share`/`is_fallback`/`cap_breach_flag` — so the gaps are in the **store DDL and feeds**,
not the engine contract.
