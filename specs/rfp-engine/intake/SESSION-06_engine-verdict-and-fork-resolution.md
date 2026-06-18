# Engine Verdict + Fork Resolution

**Date:** 2026-06-17
**Source:** `rfp_analysis_engine_v3.py` (4,198 lines), the real engine behind the Colab notebook.

This resolves the central question of the intake: which codebase is the foundation. Answer: **v3 is the brain, not the spine.** Build the engine logic from v3, on a persistent governed data layer the repo only gestured at.

---

## What the engine does (verified in code)

**A 9-step pipeline:** load config → schema validation → load input → data-quality checks → scoring → scenarios → analytics → build workbook → save.

**Multi-criteria weighted scoring (not min-cost).** Five banded factors, config-weighted:
- **Price (default 0.35)** — banded on premium vs lowest: ≤3%→100, ≤7%→80, ≤12%→50, >12%→20.
- **Coverage (0.25)** — banded on volume coverage ratio (<50%→0 … 100–120%→100). "As Needed" = 70.
- **Historical (0.20)** — banded on delta vs incumbent price (cheaper scores higher).
- **Z-Risk (0.10)** — price-outlier/sustainability check on z-score.
- **Continuity (0.10)** — 100 if incumbent, else 0.
- Composite `RecScore` = weighted sum. **Cost is only 35% of the decision.** This is the quantified form of "cost + supply security + quality + incumbent + risk."

**Eligibility gates with reason codes:** valid price > 0, premium ≤ max threshold, coverage ≥ 80% (or as-needed). Failures flagged: no valid price, premium too high, insufficient volume, price outlier (low/high), low bidder count (<3 → z-score unreliable). The scoreable-vs-awardable gate, in code.

**Split-award allocation, parameterized.** `max_two_per_dc`: per DC×TF, rank suppliers by strength (60% avg score + lots covered + coverage), keep top N (`Max Suppliers per DC`, default 2), award each lot to the best of those, fill uncovered lots from the wider field with a transparency flag. This is the "Onions52, Owyhee" split as an algorithm: consolidate to the strongest 2 per DC, split lots between them. Confirmed, capped, configurable.

**Seven scenario lenses (A–G)**, including Exclusion (E), Custom Override (F), Preferred Supplier (G). Scenarios are first-class.

**Config-driven, commodity-agnostic:** commodity, cycle, rounds (final/prior), timeframes, weights, thresholds (premium bands: comparable 3% / defensible 7% / max 12%; concentration cap 0.40) all from the CONFIG tab. Input schema is CONFIG / IN_ / DIM_.

**Rich output:** ~14+ formatted tabs (Exec Summary, Recommendations, Lowest Cost Check, Scenario Comparison, Supplier Overview, TF Comparison, Round Evolution, Coverage, Detailed Scoring, Missing Data, Award Recommendations, DC Constraint/Consolidation, Bidder Detail, Custom Scenario with live formulas, Glossary). ~1,500 lines of logic, ~2,700 of openpyxl formatting.

---

## What it is NOT (the spine it lacks)

- **Stateless.** Reads one input xlsx, writes one output xlsx. No database, no stored history, no accumulation across cycles. **It does not cure historical blindness (Problem #1).** "Open last cycle" is exactly what it cannot do.
- **No normalization.** Assumes input already at `Lot_ID`. The UPC→lot decomposition (the Norm sheet) still happens upstream, by hand, in Excel. The engine inherited a clean lot grain it did not build.
- **No governance.** Outputs regenerate each run. No immutable/sealed runs, no audit, no freeze-and-layer.
- **No front end.** CONFIG holds run parameters, but the kickoff strategy, the why, the safeties, the PBA are not captured. v3 is the analysis middle only.
- **Monolith.** 4,198 lines, ~2/3 Excel formatting. The logic is clean and separable, but it is one script.
- **Pushes fragility back to Excel.** The Custom Scenario tab uses live IF formulas for what-ifs.
- **Strict, brittle input contract.** The test run died at the input/schema seam (step 2–3): the hand-built file did not conform (its CONFIG said Colored Potatoes while the file was tomato). An engine fed by hand-built workbooks keeps breaking there.

---

## The resolution

Neither codebase is the product:
- The **heavy repo** had the right instinct (persistence, governance, audit) buried under over-engineering with no real workflow.
- **v3** has the real workflow and an excellent brain, with no spine under it.

**The build = v3's scoring/allocation engine, lifted out of the monolith, set on a persistent governed data layer** (normalization store, bid store, award store with supplier-share allocation, immutable runs, the setup file), generating the booking guide and sign-off from stored records instead of from a fresh Excel each cycle. v3 is the engine that drops into that spine.

This also maps to the shape we found in Session 1: Ed builds the middle first. v3 is the middle, mature. The front (setup + normalization persistence) and the back (governed award store + history + generated outputs) are what remain.

---

## Open question resolved

- **Which codebase is the real line?** → v3 for the engine logic; the repo's persistence/governance instinct for the spine. Build v3's brain on a real data layer. Neither alone.

---

## Addendum — later iteration reviewed (md5 `c73ffc5…`, 4,244 lines)

A more mature iteration of the same engine was reviewed (Ed's words: "another iteration before a commit"). **The verdict is unchanged.** Config, weights, bands, eligibility, and the split-award allocation are identical; still stateless, no persistence, no normalization, no governance. Only the output layer moved:

- **Custom Scenario tab is mid-refactor** — the old tile/capacity-panel builder is stubbed out ("rebuilt below with wide TF layout"). Work in progress.
- **Glossary fully built out**, documenting the engine in plain English. Confirms scenario semantics: A = lowest-cost benchmark (no gate), B = risk-adjusted main recommendation, C = incumbent defense (incumbent preferred if within 3% of market low at ≥80% coverage), D = max-N per DC, E = exclusion, F = custom override.

Three details worth carrying into the data-layer spec:
- **All-In cost has a defined fallback:** primary = All-In $/case from the bid; if blank → FOB + Delivery Surcharge + **VegCool Surcharge** − Lot Discount. **Footgun:** if All-In is already net of discounts and Lot Discount is also populated, the cost double-subtracts. The spine should enforce one path, not leave it to a note. (VegCool = a cold-chain cost component, newly named.)
- **Prior-round price is lot-level only (no DC):** a single prior price maps to all DCs for that lot, so round-over-round deltas are lot-level, not DC-specific, until prior bids carry DC pricing. Fix at the source in the bid store.

---

## Addendum 2 — delivery/UI surface reviewed

The delivery surface (the Colab notebook harness) was reviewed. Ed's own verdict: the UI was horrible. Confirmed, and it is **structural, not cosmetic**: a 5-cell run-in-order notebook, both files re-uploaded every session (no persistence), output a 14-tab Excel with live formulas edited by hand. The test run still fails at step 3 (load input) and produces no output.

**Key reframe:** a stateless engine can only have a bad UI. Every desirable front-end feature (remember my data, open last cycle, compare to history, adjust an award live) requires state the engine lacks. "The UI was horrible" and "it's a brain with no spine" are the same finding. The build therefore does **not** start with a UI — a good front end is a view onto the persistent governed layer, which must exist first. Repainting the notebook on a stateless engine yields a nicer way to forget everything each run.

---

## Addendum 3 — VERDICT CORRECTION: the engine is one of ten scripts

**The "brain with no spine" verdict was built on the single engine file and is materially incomplete.** Past-conversation recall (chat "Converting to a web app for selective uploads", 2026-05-24) shows the engine is one script in `RFP_Workflow_Package_v1.4`, which contains:

- `init_cycle` — stand up a new cycle from templates (front / setup)
- `generate_bid_templates` — produce supplier bid sheets
- `intake_bids` — ingest returned bids
- `reconcile_intake` — validate/reconcile intake
- `calculate_distances` — freight distance from `us_zip_centroids.csv`
- `rfp_analysis_engine_v3` — scoring/allocation (the brain)
- `generate_feedback_letters` — per-round supplier letters
- `generate_final_letters` — award / no-award letters
- `generate_booking_sheet` — **generates the booking guide** (not hand-built)
- `_event_log` — event log
- Templates: RFP_Input, Cycle_Calendar, Supplier_Contact_List, Award_Letter.html, No_Award_Letter.html, Per_Round_Feedback_Letter.html

**What this corrects:** the prior claim that the front end, back end, supplier comms, generated booking guide, and audit "don't exist" is wrong. They exist as code. Cycle setup, comms, award letters, booking sheet, and an event log are all built.

**What remains genuinely open (narrowed):** whether a durable, governed **store** sits under the workflow, or whether it is still file-in/file-out per run. In the 2026-05-24 chat the architecture was Pyodide (stateless, "nothing leaves the machine") and `_event_log` was "just a utility." If that is still the shape, the ten scripts are verbs acting on files and do **not** solve "open last cycle." But the **deployed** artifact is a Streamlit app (likely built later in Claude Code), and Streamlit can hold state / sit on a DB — so the persistence model of the live app is **unconfirmed**.

**To close it:** need the package source, especially `_event_log.py`, `init_cycle.py`, and whatever the Streamlit app uses to persist between runs. The front end / deploy was likely a Claude Code session, not retrievable from chat search.

**Status:** the fork ("v3 brain on a new spine") is **paused pending** sight of the workflow package + the live app's persistence layer. The system may be closer to complete than the engine-only read implied.
