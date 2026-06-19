---
doc: Sample Register — sponsor-supplied kickoff corpus (sanitized, tracked)
id: REF-SAMPLE-REGISTER
owner: Product / BA squad
classification: STRUCTURAL ONLY — no sensitive commercial values in this file
created: 2026-06-18
relates: ADR-0001 (clean-room quarantine), Security PLAN §reference/samples rule,
         specs/rfp-engine/intake/SESSION-02 (extraction), audit/02 G5, E-14
---

# Sample Register

Catalog of source artifacts the sponsor uploaded for the kickoff-keystone work (gap G5 /
epic E-14). The files themselves contain **real commercial values** (annual spend, supplier
names, performance metrics, payment terms, funding amounts) and are **quarantined** under
`reference/samples/*` — gitignored, never committed (ADR-0001 §4; Security PLAN).

This register is the **only tracked record** of what arrived. It carries clean names, type,
category, and cycle year — **no sensitive values**. The structural schema extracted from these
files lives in `project/squads/product/KICKOFF_KEYSTONE_SPEC.md` (also sanitized).

| # | Clean name | Type | Category (generic) | Cycle year | Classification | Received | Provenance |
|---|---|---|---|---|---|---|---|
| 1 | Field-grown produce kickoff (A) | `.docx` (Word, narrative) | Field-grown produce | 2026 | Contains real commercial values — QUARANTINED, gitignored, not committed | 2026-06-18 | Sponsor upload |
| 2 | Greenhouse produce kickoff (B) | `.docx` (Word, narrative) | Greenhouse / protected produce | 2025 | Contains real commercial values — QUARANTINED, gitignored, not committed | 2026-06-18 | Sponsor upload |
| 3 | Processed-pack produce kickoff (C) | `.docx` (Word, narrative) | Wet + packaged produce | 2027–2028 | Contains real commercial values — QUARANTINED, gitignored, not committed | 2026-06-18 | Sponsor upload |
| 4 | Kickoff doc prep workbook (small) | `.xlsx` (Excel, prep) | Field-grown produce | (prep) | Contains real commercial values — QUARANTINED, gitignored, not committed | 2026-06-18 | Sponsor upload |
| 5 | Kickoff document prep workbook (full) | `.xlsx` (Excel, prep) | Greenhouse / protected produce | (prep) | Contains real commercial values — QUARANTINED, gitignored, not committed | 2026-06-18 | Sponsor upload |

## Workbook tab inventory (structural only)

- **Workbook 4** — `Scorecard`, `Scorecard Export`, `Next Steps`.
- **Workbook 5** — `Scorecard Export`, `Scorecard USE`, `Scorecard (Signoff)`, `Scorecard (Signoff) USE`, `KCMS (subcomm) Export`, `KCMS (GTIN) Export`, `Next Steps`.

The `Scorecard` vs `Scorecard (Signoff)` tab pair confirms **two frozen scorecard snapshots**
(kickoff window + sign-off window). The `KCMS (subcomm)` vs `KCMS (GTIN)` pair confirms the
scan feed at **two grains** (subcommodity and GTIN). Both findings carried into the keystone spec.

## Additional feed samples (non-kickoff)

| # | Clean name | Type | Purpose | Classification | Received |
|---|---|---|---|---|---|
| 6 | iTrade by commodity (with calendar) | `.xlsx` — 43-col "Data" sheet, ~114k rows | Real iTrade receipt feed → `perf.itrade_receipt` importer (E-08); derived structure in `project/squads/platform-data/FEEDS_ITRADE.md` | Real commercial values — QUARANTINED, gitignored | 2026-06-18 |
| 7 | rfp_analysis_engine_v3 | `.py` — 4,198 lines | **The v3 engine source.** Clean-room: logic LIFTED into our own engine, never imported, raw never committed (ADR-0001). In `reference/v3-engine/` | Proprietary code — QUARANTINED, gitignored | 2026-06-18 |
| 8 | RFP_Analysis_Engine | `.ipynb` — Colab harness | The runner notebook for v3 | Proprietary code — QUARANTINED, gitignored | 2026-06-18 |
| 9 | Potato 2026 RFP **input** | `.xlsx` — 13 sheets (CONFIG / IN_* / DIM_*) | **Golden-master INPUT.** Drives the engine-reproducibility test (E-13) | Real commercial values — QUARANTINED, gitignored | 2026-06-18 |
| 10 | Potato 2026 RFP **analysis output** | `.xlsx` — 20 sheets | **Golden-master OUTPUT** (known-good v3 result). The thing the new engine must reproduce | Real commercial values — QUARANTINED, gitignored | 2026-06-18 |

(iTrade: two byte-identical copies uploaded; one retained; the 51-column "Query/Calendar" variant is still outstanding. Items 7–10 are the long-awaited golden v3 pair + engine source — the linchpin for Phase D + the pilot.)

## Allocation models (the real human decision workbooks — "most complex current Excel")

| # | Clean name | Type | Purpose | Classification | Received |
|---|---|---|---|---|---|
| 11 | Sweet Potatoes allocation model (RD2) | `.xlsx` — 19 sheets, ~32 MB | The team's live allocation/decision workbook, round 2. Drove the scenario-tool **design study §7** (structure only) | Real commercial values — QUARANTINED, gitignored (`reference/samples/_allocation_models/`) | 2026-06-19 |
| 12 | Sweet Potatoes allocation model (RD4) | `.xlsx` — 20 sheets, ~31 MB | Same model, round 4 — adds Booking Guide + Signoff tables into the model | Real commercial values — QUARANTINED, gitignored | 2026-06-19 |
| 13 | Hybrid Onions allocation model (RD4) | `.xlsx` — 19 sheets, ~7 MB | Another commodity's live allocation model; Conv/Org + vs-STLY sign-off | Real commercial values — QUARANTINED, gitignored | 2026-06-19 |

**Tab inventory (structural only).** The shared architecture across all three: `Controls` cockpit ·
layered `Outputs >`/`Calcs >`/`Raw data >` divider tabs · `Scenario tool` (Lot×DC rows × 500+
supplier/scenario cols) · `Baseline scenario` · `Supplier overview` (wide) · `Summary` · `FOB
analysis` + `RFP - Delivery Charge` · `Data cube` (650–700 cols) · `[Commodity] RFPs`/`Historicals`
raw · `Supplier mapping` (name↔ID) · `Sign-off tables` (per-DC Incumbent→Recommended, Savings $, vs
STLY, round-over-round, Conventional/Organic). RD4 additionally folds in a `Booking Guide` tab.
Findings + the practitioner layer they drove are written up in
`project/squads/experience/SCENARIO_TOOL_DESIGN_STUDY.md §7` (structure only — no commercial values).

## Handling rules (binding)

1. Raw files stay under `reference/samples/*` — gitignored. Never copy contents verbatim into a
   tracked file.
2. Only **structure** (field names, types, structured-vs-narrative class, cardinality, source
   feed) may be committed. Any example value must be an obviously generic placeholder
   (`$XXXM`, `<SupplierA>`, `<SubComm-1>`).
3. The reference-intake path (ADR-0001) emits **schema + digest only** across the quarantine
   boundary — never raw commercial rows.

## Changelog

| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-06-18 | Product/BA squad | Register created on receipt of the 5-file kickoff corpus. |
| 1.1 | 2026-06-19 | Experience squad | Registered items 11–13 (Sweet Potatoes RD2/RD4, Hybrid Onions RD4 allocation models) — the real decision workbooks behind the scenario-tool design study §7. |
