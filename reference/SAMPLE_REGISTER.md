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

(Two byte-identical copies were uploaded; one retained. The 51-column "Query/Calendar" variant is still outstanding.)

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
