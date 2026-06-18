# The v3 Engine + the Two-Codebases Fork

**Date:** 2026-06-17
**Source:** `RFP_Analysis_Engine.ipynb` — a Colab notebook that runs `rfp_analysis_engine_v3.py` (the actual engine, not included) against an input workbook.

This session reframes the engagement. Ed is not only bringing Excel models to build from. He is **already building the parameterized consolidation** as a Python engine (v3). It aligns with the target architecture, and it is mid-build.

---

## What the file is

A thin Colab harness: install pandas/openpyxl/numpy, upload `rfp_analysis_engine_v3.py` plus an input xlsx, run the engine, download the output. The engine logic lives in the .py (**not provided**). The notebook ran against `Tomato_2026_RFP_Input.xlsx`.

---

## What the run output reveals

The engine is a **9-step pipeline**. Step 1 (Loading configuration) printed:

- **Config-driven:** Commodity = Colored Potatoes, Cycle = Potato 2026. Set by config, not hardcoded.
- **Rounds as config:** "Rounds active: [R1, R2] → final=R2, prior=R1." Rounds are parameters, with a designated final round and a prior round for comparison.
- **Timeframes as config:** "TFs active: [TF1, TF2]." The timeframe fork from Session 3 is **already parameterized** — TFs are active config, not cloned sheets. This is the biggest efficiency win, and Ed has started it.
- **Weighted multi-criteria scoring:** "Weights sum to 120% — normalising." The engine scores suppliers on weighted criteria (not pure min-cost), normalizing weights to 100%. This **confirms and extends** the decision-support finding: cost plus service plus other weighted factors.

**Input schema:** CONFIG, IN_ tabs, DIM_ tabs. Config + input facts + dimension/reference tables. A clean normalized architecture.

**Output design (CUSTOM_SCENARIO tab):** Scenario A recommendation (green rows), a per-lot dropdown to override the award supplier, live updates to all-in price / spend / YoY savings, a TOTAL row with DC AutoFilter, and a column flagging **DC supplier cap breaches** (capacity modeled). Output is an interactive Excel for human what-ifs.

**Stated goal:** "The engine works for any commodity." One parameterized engine across categories — the consolidation target.

---

## The catch

The run **errored**. The engine loaded config, printed through step 1 of 9, and produced no output ("No output file found" at download). v3 is mid-build and this run did not finish. The engine code and input template were not provided, so the failure point is not yet visible.

---

## The fork that decides the engagement

There are now **two codebases**:

1. **The Streamlit + SQLAlchemy repo** (the original SYSTEM_SPEC): heavy, database-backed, sealed-run audit layer, 14 migrations, over-built at the edges, thin at the governance ends.
2. **The v3 Colab + pandas engine:** lightweight, config-driven, commodity-agnostic, spreadsheet-in / spreadsheet-out, aimed at the real workflow. The one Ed is actively running.

They cannot both be the foundation. The fork:
- **v3 is the real line** → the studio hardens and productizes the parameterized engine; the repo becomes reference or is retired.
- **The repo is the target** → v3 is a prototype that informs the repo.

Ed's behavior points to v3 (it is what he runs). Needs explicit confirmation — it decides the entire build path.

---

## What unblocks the next step

Two files:
- `rfp_analysis_engine_v3.py` — to see the 9 steps, the scoring/weighting logic, the allocation/split handling, and where the run broke.
- `Tomato_2026_RFP_Input.xlsx` (and/or `RFP_Input_Template.xlsx`) — to see the CONFIG/IN_/DIM_ schema in real form.

With both, the open technical questions collapse into one review: is v3 the spine to build on, and what does it need to finish.

---

## Open question added to the index

- **Which codebase is the real line of development: the Streamlit/SQLAlchemy repo, or the v3 Colab engine?** Decides whether the build hardens v3 or the repo.
