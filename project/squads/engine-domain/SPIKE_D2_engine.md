---
doc: D2 Architecture Spike — The Engine Brain
id: ENG-SPIKE-D2
squad: Engine & Domain
status: Spike (recommends; does not assume the answer)
created: 2026-06-18
relates: D2 (audit/04 §2), R2 (wrong-brain lock-in), G1 (split), G2 (scoring),
         E-18/E-19/E-20 (backlog), ADR-005 (decision-support), ADR-0001 (clean-room),
         BUILD_04 run() contract
---

# D2 — The Engine Brain: v3 scoring/allocation vs. as-built min-cost solver

## 1. The decision, stated once

We have two brains for the engine and can keep only one at the core:

- **Option A — Adopt v3 as the engine.** Lift v3's 5-factor banded scoring
  [Price .35 (≤3%→100 / ≤7%→80 / ≤12%→50 / >12%→20), Coverage .25, Historical .20,
  Z-Risk .10, Continuity .10 → `rec_score`] **and** the `max_two_per_dc` split
  allocator as the engine library. The as-built exact min-cost single-winner solver is
  **retired to "Scenario A = lowest-cost reference"** — one lens, a benchmark, never
  auto-applied. Ships G1 (split) + G2 (scoring) together.
- **Option B — Keep the as-built Scenario A as the core** (exact min-cost, single-winner)
  and bolt scoring + splits on top as a later layer.

This spike compares both **against the verified v3 behavior** (SESSION-06, the
4,198-line `rfp_analysis_engine_v3.py` read in code) on four axes: fidelity to real
behavior, rework, R2 (wrong-brain lock-in), and how cleanly G1+G2 ship together.

## 2. What "the real behavior" is (the bar both options are measured against)

Verified in code (SESSION-05/06), not asserted:

1. **The decision is multi-criteria, not min-cost.** Five config-weighted **banded**
   factors → composite `RecScore`. **Cost is 35% of the decision.** Min-cost is the
   *Scenario A benchmark only* (v3 Glossary: "A = lowest-cost benchmark, no gate";
   "B = risk-adjusted main recommendation").
2. **Awards are split.** `max_two_per_dc`: per DC×TF, rank suppliers by strength
   (60% avg score + lots covered + coverage), keep top N (default 2), award each lot to
   the best of those, fill uncovered lots from the wider field **with a transparency
   flag**. Confirmed in the sign-off deck ("Onions52, Owyhee"). The models are literally
   named *Allocation* models.
3. **A human selects; the engine never awards** (ADR-005 / decision-support). The
   recommendation surface must carry a `BANNED_DECISION_WORDS` guard.
4. **Eligibility gates and landed cost are inputs to the scorer, not the decision.**
   The as-built's 7-gate eligibility (12 reason codes) and 5-mode landed cost are
   richer than the brief's and are **KEEP** — they feed `bid_score` as inputs.

A brain that defaults to a single lowest-cost winner is, by this bar, **the wrong brain**.

## 3. Evaluation

| Axis | Option A (adopt v3, retire min-cost to a lens) | Option B (keep min-cost core, bolt on) |
|---|---|---|
| **Fidelity to real behavior** | **High.** Reproduces the deck's split awards and the 5-factor recommendation directly. Min-cost survives as exactly what it is in v3 — the Scenario A benchmark. | **Low at the core.** The default output is a single lowest-cost winner the deck disproves on every slide; scoring/splits are a veneer over a contradicting engine. |
| **Rework** | **Lower net.** Two breaking migrations now (relax `UNIQUE(run,dc,lot,tf)` + add `volume_share`; generalize `scenario_a_*` → `scenario`/`scenario_award`), then everything outward is built once on the right grain. The brief schema (`eng.bid_score`, `eng.scenario`, `eng.scenario_award`) already encodes the A-target. | **Higher net.** Less work today, but every `awd.*` consumer (award → freeze → sign-off → booking guide) is first built on single-winner, then re-grained. Pays the G1 migration **plus** a downstream rewrite. |
| **R2 — wrong-brain lock-in** | **Retires R2.** The grain (G1) and decision model (G2) are corrected before any breadth is built on them. | **Realizes R2.** Breadth hardens on a grain and a decision model the brief proves wrong; the cost of changing the core rises with every consumer added. |
| **G1 + G2 ship together** | **Native.** Both touch the solver core; v3 *is* both (it scores, then allocates split). One increment (E-18 + E-20 are a single backlog increment per Ed). | **Fights the design.** Splits the two changes the sponsor explicitly said ship together; scoring lands against a solver that can't represent a split award. |
| **What's preserved** | KEEP list intact: eligibility, landed cost, calc-run spine, identity FKs all feed/wrap the v3 logic unchanged. | Same KEEP list, but wrapped around a solver that will be demoted anyway. |

**Clean-room note (ADR-0001).** "Adopt v3" means **lift v3's LOGIC only** — the scoring
math, the bands, `max_two_per_dc` — re-expressed as clean library code in `backend/`.
**No Excel-formatting code is ported** (~2/3 of the monolith); the openpyxl output is
replaced by the Document generator. v3's `.py` enters only via the ADR-0001 isolated
reference intake (one dedicated agent, isolated worktree, emits to `reference/`); it is
**read, never imported** into the build.

## 4. RECOMMENDATION — **Option A.** Adopt v3; retire min-cost to Scenario A.

**Single strongest reason:** it is the only option that is **faithful to the verified
real behavior at the core** — the deck splits DCs across suppliers and the engine decides
on five factors with cost at 35%, both confirmed in code. Option B installs a brain
(single lowest-cost winner) that the primary evidence contradicts, then spends the rest
of the program building outward on it and paying to re-grain. Option A also retires **R2**
(wrong-brain lock-in) and lets **G1 + G2 ship together** as the single increment Ed
directed — which Option B structurally cannot.

This matches the audit recommendation (D2-A) and the brief's `eng.*` schema, which already
encodes the Option-A target (`bid_score`, `scenario` A–G, `scenario_award` with
`volume_share`). The as-built's min-cost solver is **not discarded** — it becomes the
Scenario A = lowest-cost reference lens, shown as a benchmark, never auto-applied
(preserving the `BANNED_DECISION_WORDS` restraint the as-built already has).

**Scope guard (permit-not-force).** The auto scenario still *defaults* to one supplier
per DC; a cell **may** split only when a per-DC/per-lot `splittable` flag is set, bounded
by capacity (`volume_limit` / `capacity_constraint`). We permit the split; we do not
force every cell to fan out.

## 5. Validation method — reproduce v3 against a known input

The spike is **not finalized** until the lifted logic is proven to reproduce v3 bit-for-bit
on the scored/allocated outputs. Method:

1. **Golden input.** Obtain one real `*_RFP_Input.xlsx` (CONFIG / IN_ / DIM_ schema) that
   v3 has successfully run end-to-end, plus the v3 output workbook for the same input.
2. **Harness.** Load the same bids+config into the store; call `run(cycle_id, round_code, config)`.
3. **Assert on the numbers, not the formatting:**
   - per-bid `price_score / coverage_score / hist_score / zrisk_score / continuity_score`
     and composite `rec_score` match v3's Detailed Scoring tab (tolerance ≤ 0.5 on each band);
   - the band boundaries fire correctly at the 3% / 7% / 12% premium edges (edge-case rows);
   - eligibility `gate_flags` match (no-valid-price, premium-too-high, insufficient-volume,
     price-outlier, low-bidder-count <3);
   - the `max_two_per_dc` allocation selects the **same top-N suppliers per DC×TF** and the
     **same lot→supplier split**, with `cap_breach_flag` / fallback transparency-flag rows
     matching v3's DC Constraint/Consolidation tab;
   - Scenario A reproduces v3's "Lowest Cost Check" total.
4. **Footguns to assert (SESSION-06 addenda):** the **All-In fallback** path
   (FOB + Delivery + VegCool − Lot Discount) must **not double-subtract** the discount;
   prior-round price is **lot-level only** (no DC) — round-over-round deltas are lot-level
   until prior bids carry DC pricing.

This becomes the engine-reproducibility test (QA squad, Phase D exit gate; backlog **S2**:
"engine reproduces v3").

## 6. What I need to finalize the spike (sponsor / ADR-0001 intake)

Both are blocked on sponsor upload; the recommendation stands without them, but the
**validation** cannot close until they arrive:

1. **`rfp_analysis_engine_v3.py`** (the verified iteration, md5 `c73ffc5…`, ~4,244 lines)
   via the **ADR-0001 isolated reference intake** — one dedicated agent, isolated worktree,
   emits the logic digest to `reference/`; never imported. Needed to lift the exact band
   math, the strength-rank formula (60% avg score + lots + coverage), and the fallback order.
2. **One golden input workbook** — a real `*_RFP_Input.xlsx` (CONFIG/IN_/DIM_) that v3 ran
   clean, **plus its v3 output** — to serve as the golden fixture for §5. (The intake's
   `Tomato_2026_RFP_Input.xlsx` errored at step 3; we need one that *completed*.)

**Single most important file to request first:** the **golden input + its v3 output pair** —
without a known-good input/output, even with the `.py` in hand we cannot prove reproduction,
which is the whole point of the validation. The `.py` lets us lift; the golden pair lets us
*verify*.

## 7. Decision record

- **Recommendation:** **Option A** — adopt v3's 5-factor scoring + `max_two_per_dc` split
  as the engine; retire the as-built min-cost solver to **Scenario A = lowest-cost reference**.
- **Ship together:** G1 (split / `volume_share`) + G2 (scoring / `bid_score`) as one
  increment (E-18 + E-20), Phase D.
- **Restraint preserved:** decision-support only; `BANNED_DECISION_WORDS` guard on the
  recommendation surface; human selects, engine never auto-asserts an award.
- **Status:** RECOMMENDED, pending validation against the golden input/output pair.
