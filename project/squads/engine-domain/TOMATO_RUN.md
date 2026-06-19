---
doc: v3 Engine Run on real Field Tomatoes 2026 input — outcome
id: ENG-TOMATO-RUN
squad: Engine & Domain (Squad 2)
status: Run attempted 2026-06-19 — completed steps 1–5 + most of 6, crashed at step 6/9
created: 2026-06-19
source: |
  rfp_analysis_engine_v3.py (QUARANTINED/gitignored, read+run, never imported — ADR-0001)
  ran against reference/samples/tomato_2026_rfp_input.xlsx (QUARANTINED/gitignored)
data_handling: |
  STRUCTURE + OUTCOME ONLY. NO real award values, supplier-price specifics, prices, volumes, or
  totals. The engine produced NO output workbook (crashed before the save step); nothing real was
  written. Run was performed in an isolated /tmp dir; nothing engine-derived entered the repo.
relates: V3_ENGINE_LOGIC.md (§7 prior-round caveat), GOLDEN_MASTER.md, ADR-0006, E-13
---

# v3 Engine Run — real Field Tomatoes 2026 input

The v3 engine **is** present in `reference/v3-engine/rfp_analysis_engine_v3.py` (CLI:
`python rfp_analysis_engine_v3.py <input.xlsx>`). It was run against the real Tomato engine input
to see whether it reproduces the contract end-to-end on this cycle (companion to the clean Potato
golden-master reproduction).

## Environment

Fresh venv: **pandas 3.0.3, numpy 2.4.6, openpyxl 3.1.5** (matches the GOLDEN_MASTER validation
env). Input copied to an isolated `/tmp` dir so any output workbook would land outside the repo.

## Outcome — did NOT complete all 9 steps

The engine ran **steps 1–5 cleanly** and **most of step 6**, then **crashed in step 6/9
(Building scenarios)**. **No output workbook was produced** (it never reached step 9 save).

| Step | Result |
|---|---|
| 1 Load config | OK. Correctly read the (stale) identity, **R1-only single-round** cycle, TF1+TF2 active, and **renormalised the 120%-summed weights** (warned, divided by total) |
| 2 Schema validation | OK (lenient/warn-only) |
| 3 Load input | OK with warnings: **IN_Preferred / IN_VolumeLimits sheets absent** (skipped); **0 incumbent rows, 0 volume rows** loaded (those tabs are header-only in the file); 360 bid rows across 1 round; 40 DCs |
| 4 Data-quality checks | OK (non-blocking): logged missing All-In / FOB / vol-offered counts and "lots in bids missing from Volumes/Incumbents" — exactly the partial-population this cycle has |
| 5 Scoring engine | **OK** — built the group key `[DC_ID,Lot_ID,TF]`, scored the valid bids, applied eligibility. With no incumbents/volumes, historical baseline = none and coverage = all As-Needed; all scored bids came through eligible |
| 6 Build scenarios | **CRASH** — `TypeError: 'NoneType' object is not subscriptable` |
| 7–9 | not reached |

## Root cause — a genuine single-round engine bug (not a data problem)

The crash is at the **prior-round price lookup** (the exact code path flagged in
**V3_ENGINE_LOGIC.md §7, "prior-round price caveat"**):

```
r1_bids_pre = bids[bids['Round'].astype(str).str.strip() == prior_round['Round']] ...
```

CONFIG correctly sets `prior_round = None` for a single-round cycle (`round_rows` has length 1),
and the config/header code guards `prior_round` everywhere with `if prior_round else …`. **But
the step-6 prior-round price lookup does not guard it** and indexes `prior_round['Round']`
unconditionally → `None['Round']` → `TypeError`.

This path **never fired in the Potato golden run** because Potato is **multi-round** (R1+R2), so
`prior_round` was always a dict. The **real Tomato cycle is single-round (R1 only)**, which is the
first input to exercise the unguarded branch. So:

- This is **not** caused by the empty incumbents/volumes or the stale identity — those produced
  only warnings and the run sailed through scoring.
- It **is** a latent v3 defect: **v3 cannot complete on a single-round cycle.** Our lifted engine
  must guard the prior-round lookup (when `prior_round is None`, skip round-evolution / R1_Price
  derivation and emit lot-level-only deltas as §7 already prescribes).

Per clean-room rules the quarantined `.py` was **not modified** — the bug is reported, not
patched in-place.

## Reproduction value

- **Scoring (the primary reproduction target) ran to completion** on real Tomato data: config
  parse, weight renormalisation, group-key construction, the 5 banded factors, and eligibility
  all executed without error on 360 bid rows — independent corroboration that steps 1–5 of the
  lifted logic are sound on a second, structurally different real cycle.
- **New requirement surfaced for the lifted engine + its tests:** add a **single-round cycle**
  case to the golden/synthetic fixture matrix (the current synthetic plan is R1/R2 multi-round,
  so it would also miss this). Guarding the prior-round lookup is a hard prerequisite for running
  any single-round commodity (E-13).

## Data-handling confirmation

No output workbook was produced (crash preceded step 9). Nothing engine-derived was written into
the repo; the run happened in `/tmp` and the input copy + (absent) output stay outside version
control. No real prices, supplier-price specifics, award values, volumes, or totals appear in
this file.
