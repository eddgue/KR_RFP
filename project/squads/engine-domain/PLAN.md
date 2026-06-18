---
doc: Engine & Domain Squad — Plan (engine-as-a-library)
id: ENG-PLAN
squad: Engine & Domain (Squad 2)
status: Draft
created: 2026-06-18
owns: G2 (bid_score), G1 (split allocation), scenarios A–G, G4 (pricing+safeties),
      the REST API; KEEP the calc-run spine, 5-mode landed cost, 7-gate eligibility
relates: BUILD_04 run() contract, ADR-005 (decision-support), ADR-0001/0003,
         E-15/E-18/E-19/E-20/E-25, SPIKE_D2_engine.md
---

# Engine & Domain — Plan

The engine is a **library behind a stable interface**, not an app. It reads bids + config
from the governed store, computes, and writes **sealed** records back. Outputs are
generated from those records (other squads). Decision-support only: the engine computes,
scores, compares, and proposes — **a human selects; it never auto-asserts an award.**

## 1. The stable interface (one line)

```
run(cycle_id, round_code, config) -> run_id
```

- **Reads:** `bid.bid` + `bid.bid_price` + `volume_requirement` / `volume_limit` for
  (cycle, round, active TFs); incumbent/historical cost from `perf.itrade_receipt`;
  config (weights, thresholds, `max_sup_dc`, `conc_thresh`, premium bands) from the cycle/run.
- **Computes:** `bid_score` (5 banded factors → `rec_score`) + eligibility/`gate_flags`;
  scenarios A–G including `max_two_per_dc` split allocation.
- **Writes (sealed):** `eng.analysis_run` (immutable, full `config_json`), `eng.bid_score`,
  `eng.scenario`, `eng.scenario_award`.

A correction is a **new run**, never an edit (ADR-004; KEEP the as-built calc-run spine —
hashed input/output manifests, version pins, required-inputs-by-contract).

## 2. Service decomposition

The library is a thin orchestrator over pure, independently testable services. Each is a
function of frozen inputs → records; none owns a transaction (add + flush, never commit —
KEEP the as-built rule).

| Service | Responsibility | KEEP / lift |
|---|---|---|
| **Eligibility consumer** | Read the as-built 7-gate result (12 reason codes) + `supplier_capability`; surface `eligible` + `gate_flags` as **scorer inputs** — not the decision. | KEEP as-built; consume, don't reimplement. |
| **Landed-cost consumer** | Read the as-built 5-mode `landed_cost_result` (8 blocking reasons, tolerance) → one comparable cost/case per supplier×cell. Enforce the **single All-In path** (no double-subtract). | KEEP as-built; the `no_double_discount` CHECK guards the footgun. |
| **Scorer** | The 5 banded factors → `rec_score`. Price .35 (≤3→100/≤7→80/≤12→50/>12→20), Coverage .25 (As-Needed=70, skip coverage), Historical .20, Z-Risk .10 (low-bidder <3 → unreliable flag), Continuity .10 (incumbent=100). Normalize weights to 100% if they sum off. Writes `eng.bid_score`. | **Lift v3 logic** (clean-room; logic only). |
| **Scenario builder (A–G)** | One pass per lens over scored bids: **A** lowest-cost reference (benchmark, never auto-applied), **B** risk-adjusted recommendation (the `rec_score` default), **C** incumbent defense (incumbent if within 3% at ≥80% coverage), **D** max-N per DC, **E** exclusion, **F** custom override, **G** preferred supplier. Writes `eng.scenario`. | Lift v3 lens semantics (Glossary, SESSION-06). |
| **Split allocator** | `max_two_per_dc`: per DC×TF rank by strength (60% avg score + lots covered + coverage), keep top N (`max_sup_dc`, default 2), award each lot to the best of those, fill uncovered lots from the wider field with a **fallback transparency flag**. Emits `eng.scenario_award` rows: one per awarded supplier per cell with `volume_share`, `awarded_price`, `cap_breach_flag`. **Permit-not-force:** default one supplier/DC; split only when the per-DC/per-lot `splittable` flag is set, bounded by `volume_limit` (`conc_thresh` 0.40 cap → `cap_breach_flag`). | **Lift v3 logic** (the *Allocation* core). |
| **Pricing-safety executor (G4)** | Read pricing basis + the five safeties declared at **kickoff** (`cyc.*`, G4); execute/visualize: disaster trigger, inverse trigger + collar (floor/cap), rolling midpoint (window/cadence), tolerance band (band%/hold-weeks), period-by-period. Reuse the as-built `commercial_*` component storage + replayable formula audit; re-point it to read kickoff params. | MERGE: as-built storage, brief placement. |
| **Engine runner** | Orchestrates the above behind `run()`; opens a sealed `analysis_run`, freezes inputs, fans out to scorer → scenario builder → split allocator, writes records, seals. | Lift v3 9-step pipeline (drop steps 8–9 Excel build/save). |

**Banned from the engine:** any code that asserts an award, writes to `awd.*`, or emits a
decision verb on the recommendation surface. The presenter keeps a `BANNED_DECISION_WORDS`
guard. Selection (`scenario` → `awd.award`) is a **separate** service owned downstream; the
engine only proposes.

## 3. What it writes (sealed, on the governed store)

All writes are append-only into immutable `eng.*`; the engine never updates a prior run.

- `eng.analysis_run` — one sealed row per run: `cycle_id`, `round_code`, `engine_version`
  (e.g. `v3.c73ffc5`), `config_json` (weights/thresholds/`max_sup_dc`/`conc_thresh`), `is_sealed`.
- `eng.bid_score` — PK `(run_id, bid_id)`: the 5 factor scores + `rec_score`, `prem_vs_low`,
  `z_score`, `eligible`, `gate_flags`.
- `eng.scenario` — `(run_id, code A..G)`, label, description.
- `eng.scenario_award` — **the split award**: one row per awarded supplier per
  `(scenario_id, dc_no, lot_id, tf_code)` with `volume_share`, `awarded_price`,
  `is_recommended`, `is_fallback`, `cap_breach_flag`.

**Breaking migration (Platform & Data own the DDL; we own the contract):** relax the
as-built `UNIQUE(run,dc,lot,tf)` single-winner constraint and add `volume_share`; generalize
`scenario_a_*` → `scenario` / `scenario_award`. Ships with E-18/E-20 as one increment.

## 4. REST API surface (representative)

Contract-first (E-25); every endpoint guarded (Security squad owns authn/authz/tenancy).

```
POST  /cycles/{id}/rounds/{r}/run        run the engine -> { run_id }   (async; 202 + poll)
GET   /runs/{id}                         run header + seal/config metadata
GET   /runs/{id}/scores                  per-bid bid_score + gate_flags  (paged)
GET   /runs/{id}/scenarios               scenarios A–G (codes + labels)
GET   /runs/{id}/scenarios/{code}/awards split scenario_award rows (volume_share, cap_breach_flag)
GET   /runs/{id}/scenarios/compare       side-by-side lens comparison (spend, premium, coverage)
GET   /cycles/{id}/pricing/safeties      executed/visualized safety calcs (G4)
```

Selection/freeze/sign-off/document endpoints (`/awards/select`, `/signoff`, `/documents`)
exist in the program API but are **owned by the awards/outputs work (E-21–E-23)**, not the
engine; the engine surface ends at `scenario_award`. Reads are decision-support shaped:
they compare and surface; they never return an "awarded" verdict.

## 5. Engine interface stub strategy (while D2 is open)

D2 is **in spike** (SPIKE_D2_engine.md recommends Option A; validation pending the golden
input/output pair). Per ADR-0003, the engine internals stay **stubbed behind the `run()`
interface** until the spike resolves. Strategy:

1. **Freeze the signature now.** `run(cycle_id, round_code, config) -> run_id` and the four
   write tables (`eng.*`) are the stable boundary. Everything upstream (bids, eligibility,
   landed cost) and downstream (selection, awards, outputs) builds against this contract,
   not the implementation.
2. **Ship a deterministic stub.** The stub reads real bids + config, runs the **as-built
   min-cost solver** as a placeholder, and writes *valid-shaped* `bid_score` (cost-only
   `rec_score`), a single `scenario` A, and single-winner `scenario_award` rows
   (`volume_share = 1.0`). This unblocks every consumer with real-shaped data while the
   true 5-factor/split logic is validated.
3. **Swap, don't rewrite.** When D2 finalizes (Option A validated against the golden pair),
   replace the stub body with the lifted v3 scorer + split allocator. Because consumers bound
   to the interface and the records — not the math — the swap is internal. The engine-
   reproducibility test (§5 of the spike, QA S2) is the gate that authorizes the swap.
4. **Guardrail.** The stub's `analysis_run.engine_version` is tagged `stub` so no stubbed run
   can be mistaken for a validated v3 run, and CI fails if `backend/` imports from `reference/`
   (ADR-0001 isolation).

## 6. Sequencing (this squad's slice of the roadmap)

- **Phase A/B (overlap):** consume the KEEP layers (eligibility, landed cost, calc-run spine);
  stand up the `run()` stub; "open last cycle" read model (E-07).
- **Phase C/D:** pricing lifted to kickoff + executable safeties (E-15 / G4).
- **Phase D (the brain, one increment):** lift v3 scorer → `bid_score` (E-18); scenarios A–G
  (E-19); split allocator + `volume_share` + cap-breach (E-20). **Exit gate:** a stored round
  runs and **reproduces v3** against the golden input (S2/S4).
- **Phase F:** REST API hardening (E-25), contract-first + guarded.

**Dependencies:** D depends on B (real cost/history feeds the scorer) and C (cycle config drives
the run). The stub keeps everyone unblocked until then.
