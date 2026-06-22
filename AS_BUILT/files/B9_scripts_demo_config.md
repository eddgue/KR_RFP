# SLICE B9 — `backend/scripts/**`, `backend/demo/**`, backend config, `deploy/gcp/**`, root compose + CI

**As-built exhaustive audit (Layer-1 data/flows + Layer-2 per-file/process/decisions).** Read-only.
Contract honored: `CLAUDE.md` ABSOLUTE REQUIREMENTS + `AS_BUILT/AUDIT_STANDARD.md` (every file, every
function, every transformation/decimal, detailed WHY, empty files explained, nothing skipped).

Cross-checked against `AS_BUILT/FILE_CENSUS.md` (rows cited per file). Sizes/dates from the census +
filesystem `stat`. The two `*.pyc` files under scope are accounted for in the census's
`__pycache__` vendored/generated bulk line (4671 files, excluded from per-file audit) — they are
byte-compiled caches of the two `.py` files audited below, not authored source, and are listed here
only so the slice has NO silent skip.

**Owner coordination:** R1 owns repo-root dotfiles; B9 owns `deploy/`, CI, and backend config. The
legacy workbook `reference/samples/potato_2026_rfp_input.xlsx` (census row 538) and the frozen
demo `*.xlsx` artifacts' *generator* modules (`app/output/*`) belong to other slices — B9 audits the
two **driver scripts** (`potato_legacy_dryrun.py`, `run_cycle_demo.py`) and the **emitted demo
artifacts** as files, cross-referencing their generators by name only.

---

## SLICE FILE INVENTORY (census cross-ref)

| # | Path | Ext | Bytes | Lines | Empty? | Census row | Tracked |
|---|------|-----|------:|------:|:------:|-----------:|:-------:|
| 1 | `backend/scripts/potato_legacy_dryrun.py` | py | 36657 | 918 | n | 180 | y |
| 2 | `backend/scripts/__pycache__/potato_legacy_dryrun.cpython-312.pyc` | pyc | 43259 | — | n | (in `__pycache__` bulk) | n |
| 3 | `backend/demo/__init__.py` | py | 0 | 0 | **YES** | 163 | y |
| 4 | `backend/demo/run_cycle_demo.py` | py | 51784 | 1169 | n | 168 | y |
| 5 | `backend/demo/__pycache__/__init__.cpython-312.pyc` | pyc | 139 | — | n | (in `__pycache__` bulk) | n |
| 6 | `backend/demo/__pycache__/run_cycle_demo.cpython-312.pyc` | pyc | 57617 | — | n | (in `__pycache__` bulk) | n |
| 7 | `backend/demo/output/RECOMMENDATION.md` | md | 7316 | 80 | n | 165 | n (untracked artifact) |
| 8 | `backend/demo/output/BOOKING_GUIDE_INTERNAL.xlsx` | xlsx | 8078 | (binary) | n | 164 | n |
| 9 | `backend/demo/output/SCENARIO_WORKBOOK.xlsx` | xlsx | 108992 | (binary) | n | 166 | n |
| 10 | `backend/demo/output/SUPPLIER_AWARD_GUIDES.xlsx` | xlsx | 8292 | (binary) | n | 167 | n |
| 11 | `backend/pyproject.toml` | toml | 3335 | 93 | n | 174 | y |
| 12 | `backend/Dockerfile` | (none) | 3105 | 54 | n | 20 | y |
| 13 | `backend/.dockerignore` | (dotfile) | 556 | 25 | n | 18 | y |
| 14 | `backend/README.md` | md | 2450 | 60 | n | 21 | y |
| 15 | `backend/alembic.ini` | ini | 756 | 41 | n | 22 | y |
| 16 | `deploy/gcp/README.md` | md | 8497 | 197 | n | 250 | y |
| 17 | `deploy/gcp/deploy.sh` | sh | 21596 | 449 | n | 251 | y |
| 18 | `deploy/gcp/seed.py` | py | 14200 | 319 | n | 252 | y |
| 19 | `docker-compose.yml` | yml | 5556 | 133 | n | 253 | y |
| 20 | `.github/workflows/ci.yml` | yml | 9071 | 223 | n | 5 | y |

No `*.cfg` files exist in `backend/` root. The only `*.ini`/`*.toml` in backend root are
`alembic.ini` (#15) and `pyproject.toml` (#11); both audited. `find` over the scope returned exactly
the inventory above — nothing else exists in `backend/scripts/**` or `backend/demo/**`.

---

# ============================================================================
# FILE 1 — `backend/scripts/potato_legacy_dryrun.py`  ⚠️ ACTIVE D45 DATA-FIDELITY VIOLATION
# ============================================================================

**Path:** `/home/user/KR_RFP/backend/scripts/potato_legacy_dryrun.py` · **ext** `.py` · **918 lines /
36,657 bytes** · **not empty** · census row 180 (created/modified 2026-06-22T13:50:36).

## WHAT
A standalone **migration-fidelity / dry-run harness** (NOT a product path) that takes the REAL legacy
standalone-engine potato workbook (`reference/samples/potato_2026_rfp_input.xlsx`, the 14-tab vertical
format), **converts** it into OUR two intake workbooks (Setup/Kickoff + filled bid template), drives
the WHOLE pilot loop through `PilotService` against a REAL governed Postgres, then reads OUR A–G lens
**scenario comparison** and prints it **side-by-side** with the legacy GOLDEN analysis output
(`potato_2026_rfp_analysis_output.xlsx`, "Executive Summary"). The unit of work is **rolled back** at
the end (line 797) so the dry run leaves no governed cycle behind.

## DETAILED WHY (why it exists, why shaped this way, what breaks without it)
- **Why it exists:** to prove OUR V3 engine reproduces the legacy engine's *lens ordering* and
  *per-cell prices* on the real dataset — the migration confidence signal. It is the verification
  oracle for "does our pipeline land the same answer the client's old spreadsheet engine did."
- **Why shaped this way:** it must convert *between two different data shapes* — the legacy 14-tab
  format (header row 4, data row 5, vertical CONFIG sheet, TF *labels* `TF1..TF4`, FOB/Delivered
  round split `R1`/`R2`) and OUR setup/bid template shapes (header rows from `setup_template` /
  `template_schema`, TF *codes* `TF01/TF02`, key-validated bid intake). The conversion is the whole
  point and the whole risk.
- **What breaks without it:** there is no automated, end-to-end check that the real legacy data
  flows through OUR pipeline to a comparable answer. Its converters are ALSO reused by
  `deploy/gcp/seed.py::seed_potato()` (FILE 18) to seed the committed POTATO cycle — so this file is
  load-bearing for the deployed demo, not just a throwaway.

## ⚠️ D45 STATUS — THIS FILE IS THE NAMED VIOLATION
`project/03_DECISION_LOG.md` **D45** (RATIFIED 2026-06-22) names this converter explicitly:
> "the potato dry-run was seeded by a converter that took shortcuts (single Delivered round only,
> 141 demand rows dropped, regions flattened to a closed set, lot names replaced by raw Lot_IDs,
> values force-positived). All of this **violates D19 (NO MVP)**."

The file is **self-aware** of every shortcut (its module docstring lines 19–32 list them and the
`_print_comparison` parity notes at lines 899–914 explain the resulting ~+27% spend gap as a
"gating/coverage SEMANTIC difference"). The shortcuts are documented, not hidden — but per CLAUDE.md
§3 (DATA FIDELITY IS PART OF NO-MVP) documenting a fudge does not make it compliant: dropping rows /
flattening dimensions / renaming entities to raw IDs / force-positiving values / collapsing a
multi-round RFP to a single round are **forbidden**; bad/ambiguous data must be **quarantined**, not
silently coerced. **The file remains a live violation as of 2026-06-22.**

### THE 5 NAMED SHORTCUTS — exact file:line + faithful behavior each should have

**SHORTCUT 1 — Single Delivered round (collapse a multi-round RFP to one round).**
- **Where:**
  - Parse keeps ONLY `R2` rows, counts/drops `R1`: lines **346–373** (`if rid == "R1": r1_rows += 1; continue` line 350–352; `if rid != "R2": continue` line 353).
  - Emits `"Rounds": 2` in the setup but only ingests/analyses round 1: setup write lines **426–446** (the `"Rounds": 2` literal is line **438**), with the rationale comment lines 434–437.
  - The pipeline only ever calls `generate_bid_template(…,1)` / `ingest_bids(…,1)` / `run_round(…,1)`: lines **755, 769, 780**.
- **Why the shortcut exists (stated):** the platform CHECK `ck_cycle_round_count_range CHECK (round_count BETWEEN 2 AND 6)` (verified in `db/baseline/schema.sql:346`) forbids a 1-round cycle, so the script models a single Delivered round as a 2-round cycle with round 2 left empty. The legacy `R1` (FOB, blank DC) is treated as the *prior basis*, and the golden's landed comparison is on the Delivered/Routing basis that `R2` provides.
- **Faithful behavior it SHOULD have:** ingest BOTH legacy rounds as two real rounds — `R1` (FOB basis) as round 1 and `R2` (Delivered) as round 2 — so the round-over-round structure (and the negotiation/concession lens that depends on multi-round bids) is preserved; analyse the final round (round 2) as the platform expects. The `round_count BETWEEN 2 AND 6` constraint is satisfied *honestly* by two populated rounds rather than by one populated + one empty placeholder round. If the FOB→landed basis difference between R1 and R2 makes them non-comparable as "rounds," the correct move is to map them as two **price bases on the same round** (not invent an empty round) — never to drop R1's ~`r1_rows` of pricing.

**SHORTCUT 2 — 141 dropped volume rows (drop demand rows with blank Weekly).**
- **Where:** `parse_legacy` IN_Volumes loop lines **308–324**; the drop is line **321–323** (`if weekly is None: dropped += 1; continue`). The count is surfaced (not hidden) at lines 384, 707 (`dropped {data.dropped_volume_rows} blank-Weekly`).
- **Why the shortcut exists (stated):** the legacy IN_Volumes sheet carries rows whose volume is expressed *weeks-only* (blank "Weekly Volume (cases)"), and OUR setup ingester rejects a non-numeric Weekly (the `WEEKLY_X_WEEKS` method needs a numeric weekly). Rather than convert those rows, the script silently drops ~141 of them.
- **Faithful behavior it SHOULD have:** convert (not drop) — if a row carries a TOTAL/period figure or a different volume-input method, map it through the correct method (e.g. a period-total method) so the demand total is preserved; if a row is genuinely uninterpretable, **quarantine** it with a reason (CLAUDE.md §3: "Bad/ambiguous data is surfaced as quarantine, never silently fudged") and reconcile the kept+quarantined counts to the legacy source row count. Dropping 141 demand rows silently changes the per-cell volume base that every landed-spend number is computed against — exactly the "drop rows to make data appear" failure D45 forbids.

**SHORTCUT 3 — Region flatten → Central (flatten/coerce a dimension to a closed set).**
- **Where:**
  - The remap table `REGION_REMAP` lines **99–110**; the coercion `remap_region` lines **113–114** — anything not in the 10-key table falls back to the literal `"Central"`.
  - Applied at DC parse line **283** (`region = remap_region(...)`).
  - Re-coerced again on setup write line **451** (`"Region": region if region in REGIONS else "Central"`).
- **Why the shortcut exists (stated):** OUR setup template's Region dropdown domain is the closed set `REGIONS = ("East","South","West","Midwest","Central")` (verified in `app/pilot/setup_template.py:40`). The legacy DCs carry richer regions (Southeast, Northeast, Mountain, Southwest, Pacific NW, So Cal, …) that don't map 1:1, so unrecognised ones collapse to "Central." The script's own comment (lines 96–98) admits the setup ingester does NOT validate DC region against the closed set today — so this flatten is **cosmetic** (I verified: no region validation/reject/quarantine logic exists in `app/pilot/*.py`).
- **Faithful behavior it SHOULD have:** carry the legacy region through faithfully. Because the ingester does not enforce the closed set (confirmed), the correct move is to preserve the real region string (or widen the closed set / add a documented crosswalk that is 1:1 and reversible), NOT to coerce distinct regions (Mountain, Southwest, Pacific NW, So Cal → all "West"; anything unknown → "Central"). Flattening loses the regional dimension the freight/landed lens reasons over and renames an entity's attribute to a default — the "flattening/coercing dimensions" failure D45 forbids.

**SHORTCUT 4 — Lot Name == Lot_ID (rename an entity to its raw ID).**
- **Where:** setup LOTS write, the dict key `"Lot Name": lot_id` line **460** (with the comment "Lot Name == legacy Lot_ID so the bid match joins exactly"). The Item Description IS carried from `DIM_Lots` (`desc`, line 461, parsed at line 295), so only the *Lot Name* is the raw ID; the volume/incumbent rows reuse the same `lot_id` as the Lot Name (lines 499, 519).
- **Why the shortcut exists (stated):** OUR bid match joins by *display label* — `fill_bid_template` matches a generated template row to a legacy R2 bid on `(Supplier, DC Name, Lot, TF-label)` (lines 588). Making the Lot Name identical to the legacy `Lot_ID` guarantees the by-name join is exact, sidestepping a name↔ID crosswalk.
- **Faithful behavior it SHOULD have:** give each lot its real human-readable name (the legacy `DIM_Lots` "Item Description" is already parsed into `desc` and could seed a proper Lot Name) and maintain a Lot Name↔Lot_ID crosswalk so the by-name bid join still resolves. Using the raw `Lot_ID` as the displayed Lot Name is the "renaming entities to their raw IDs" failure D45 forbids — the human-facing output (D23 — names display, keys join) then shows an opaque ID where a name belongs.

**SHORTCUT 5 — `_as_positive` force (force-positive / alter values).**
- **Where:**
  - Helper `_as_positive` lines **145–154** — returns the float only when `out > 0`, else `None` (drops 0 and negatives to NULL).
  - Applied to every priced cell in `fill_bid_template`: All-In line **597**, FOB line **598**, weekly line **606**, total line **607**; the "only write when strictly positive" writes at lines **602–611**.
  - In parse, the `R2` bid keep also substitutes FOB for a missing All-In (line **369**, `"all_in": all_in if all_in is not None else fob`).
- **Why the shortcut exists (stated):** the `bid_line` CHECK constraints require prices be NULL or strictly `> 0` — verified `ck_bid_all_in_positive CHECK (submitted_all_in_case IS NULL OR submitted_all_in_case > 0)` and `ck_bid_fob_positive` (`db/baseline/schema.sql:771–772`). A handful of legacy Delivered rows carry `FOB == 0` (All-In is always `> 0`), so the script writes only strictly-positive cells and blanks the rest, relying on the engine scoring on All-In.
- **Faithful behavior it SHOULD have:** a legacy `FOB == 0` is a real datum (often "FOB not separately quoted / Delivered-only"). Faithful handling preserves that meaning — record it as an explicit "FOB not provided / Delivered basis" (NULL with a recorded reason, or a price-basis flag), or **quarantine** the row if the zero is ambiguous — rather than silently blanking it to satisfy a CHECK. The current `_as_positive` SILENTLY coerces 0/negative values to "absent" for All-In, FOB, weekly AND total volume; that "force-positiving or otherwise altering values" is exactly what D45/CLAUDE.md §3 forbids, and blanking weekly/total volumes also silently shrinks the volume base behind landed spend.

### Module docstring (lines 1–40) — every claim
States: it's a DRY-RUN/migration-fidelity harness, NOT a product path (line 3); reads the 14-tab
legacy workbook (header row 4, data row 5, vertical CONFIG — line 5–6); converts into (1) OUR Setup
workbook via `build_setup_workbook` and (2) OUR filled bid template via `template_generator` (lines
8–9); drives `start_run → ingest_setup → generate_bid_template(1) → ingest_bids(1) → run_round(1)`
(lines 13); reads `scenario_comparison` and prints side-by-side with the GOLDEN Executive Summary
(lines 15–17). Lines 19–32 enumerate the KEY CONVERSION DECISIONS = the 5 shortcuts above + the
strategy mapping. Lines 33–39 give the run command and note it leaves a (real) cycle residue — but
NOTE: the actual code rolls back (line 797), so the docstring's "leaves a (real) cycle in the DB"
(line 39) is **stale/contradicted** by the rollback (minor doc drift; the rollback is the truth).

### Module constants
- `_REPO_ROOT` line 88 — `Path(__file__).resolve().parents[2]` (scripts→backend→repo-root).
- `LEGACY_INPUT` line 89, `GOLDEN_OUTPUT` line 90 — the two reference samples.
- `LEGACY_HEADER_ROW = 4`, `LEGACY_DATA_ROW = 5` lines 93–94 — the legacy geometry (header row 4,
  data from row 5). **WHY:** the legacy DIM_/IN_ tabs are not header-row-1; row 4 carries the headers.
- `REGION_REMAP` lines 99–110 — see SHORTCUT 3.

### Every function (signature · inputs · outputs · side-effects · raises)
- **`remap_region(raw: str|None) -> str`** (113–114). Looks up the stripped region in `REGION_REMAP`,
  defaults to `"Central"`. Pure. **WHY:** SHORTCUT 3 coercion.
- **`_norm(value: object) -> str`** (120–125). Strip + collapse internal whitespace/newlines (legacy
  headers carry `\n`); `None → ""`. Pure. **WHY:** legacy headers have embedded newlines; normalize
  so header→column lookups match.
- **`_header_cols(ws, header_row) -> dict[str,int]`** (128–136). Map normalized header text → 1-based
  column index across `ws.max_column`. Pure (reads ws). **WHY:** column positions vary; resolve by
  name.
- **`_cell(ws, row, col|None) -> str`** (139–142). Normalized cell value; `col is None → ""`. **WHY:**
  tolerate missing columns (`cols.get(...)` returns None).
- **`_as_positive(value) -> float|None`** (145–154). float() then `>0` gate. **WHY:** SHORTCUT 5
  coercion to satisfy `bid_line > 0` CHECKs. Raises nothing (TypeError/ValueError caught → None).
- **`_parse_config(wb) -> LegacyConfig`** (187–223). Reads the vertical CONFIG key/value sheet (cols
  A/B), builds a `{label→value}` map (`setdefault` — first wins, lines 193–196); pulls Commodity
  Name, Bid Cycle Label, Global Premium Threshold (→`premium`, default 0.15), Coverage Eligibility
  Floor (→`coverage`, default 0.8), Max Suppliers per DC (→`max_sup`, default 2); scans rows where col
  A ∈ {TF1..TF4} with a start date + weeks>0 into `timeframes` (lines 205–213). **Forces**
  `weight_preset="balanced"` (line 221) with the comment "CONFIG active weights == Balanced preset
  (0.4/0.35/0.25)" — NOTE this is a hardcode, not read from the workbook (a 6th, smaller assumption:
  the preset is asserted, not parsed). Returns frozen `LegacyConfig`. **WHY:** the CONFIG sheet is the
  strategy source; the preset hardcode assumes the legacy active weights equal our Balanced preset.
- **`_to_decimal(raw) -> Decimal|None`** (226–232). Strips `,` and `$`, parses Decimal; bad → None.
  **WHY:** legacy money cells may carry thousands separators / currency glyphs.
- **`_to_int(raw) -> int|None`** (235–242). `_to_decimal` then int(); bad → None.
- **`_parse_date_label(raw) -> str`** (245–260). Tries `%b %d, %Y`, `%B %d, %Y`, `%Y-%m-%d`,
  `%m/%d/%Y`; falls back to the raw string if unparseable. **WHY:** the setup ingester accepts several
  date forms; an unparseable date only defaults the timeframe span (does not affect the comparison).
- **`parse_legacy(path) -> LegacyData`** (263–387). THE conversion read. Loads the workbook EAGERLY
  (NOT `read_only`) — the lines 264–270 docstring explains why: read-only streaming makes random
  `ws.cell` O(n) per call → O(n²) over the 5291-row IN_Bids sheet (never finishes); eager makes it
  O(1) (<1s). Parses: DIM_DCs (276–285, region remapped + state truncated to 2 chars line 284),
  DIM_Lots (288–297, desc defaults to lot_id — feeds SHORTCUT 4), DIM_Suppliers (300–306), IN_Volumes
  (309–324, SHORTCUT 2 drop), IN_Incumbents (327–339, **uses Routing not FOB**, line 336; skips rows
  with no routing), IN_Bids (342–373, **keeps only R2 Delivered priced rows** keyed by
  `(supplier, dc, lot_id, tf)` — SHORTCUT 1; skips No-Bid/unpriced where both all_in & fob are None,
  line 366–367). Returns `LegacyData`. Side-effect: `wb.close()` (375). **WHY:** single normalized
  read of the whole legacy workbook into a typed model that the emitters consume.
- **`_setup_header_col(ws, header) -> int`** (393–397). Finds a setup-template column by header on
  `SETUP_HEADER_ROW`; **raises AssertionError** if not found (line 397). **WHY:** fail loud if the
  owned setup template's header set drifts from what the converter writes.
- **`_write_setup_rows(ws, rows)`** (400–411). Writes rows from `EXAMPLE_START_ROW`, then NULLs 3
  extra rows below the data (407–411). **WHY:** the owned setup template ships greyed EXAMPLE rows;
  clearing past the data prevents example rows leaking into ingest. Side-effect: mutates ws.
- **`build_setup_bytes(data) -> bytes`** (414–530). Loads `build_setup_workbook()` (the owned blank
  setup), computes `horizon` = sum of TF weeks (or 13 fallback, line 420) and `earliest` = min TF
  start (line 421–424), writes TAB_CYCLE (426–446 — emits `"Rounds": 2` SHORTCUT 1), TAB_DCS (448–454
  — region re-coerced SHORTCUT 3), TAB_LOTS (456–468 — `"Lot Name": lot_id` SHORTCUT 4), TAB_SUPPLIERS
  (470–473), TAB_TIMEFRAMES (475–486), TAB_VOLUMES (488–505 — only in-scope DC/Lot/TF), TAB_INCUMBENTS
  (507–526 — **deduped to one routing baseline per (DC,Lot)** since setup grain is DC×Lot, lines
  507–516). Returns workbook bytes. **WHY:** renders OUR setup workbook from the parsed legacy model.
- **`_bid_header_cols(ws) -> dict[str,int]`** (536–542). Header→column map on `BID_HEADER_ROW` for the
  bid template. **WHY:** resolve bid columns by name.
- **`fill_bid_template(template_bytes, data, tf_code_to_label) -> (bytes, FillStats)`** (553–616). THE
  bid fill. Opens the generated owned template, resolves the scope columns (Supplier/DC/Lot/TF) +
  price columns, iterates body rows; for each scope row resolves the TF *code→label* via
  `tf_code_to_label` (lines 585–587 — the template carries TF01/TF02, legacy keys on TF1/TF2), looks
  up the R2 bid by `(sup, dc, lot, tf_label)` (588), counts unmatched (589–592), then writes ONLY
  strictly-positive All-In/FOB/weekly/total via `_as_positive` (597–611 — SHORTCUT 5), counts
  `filled` (612). Keys stay intact so ingest is key-validated. Returns `(bytes, FillStats)`. **WHY:**
  fills OUR template's price cells by display-label match while preserving embedded keys.
- **`read_golden_scenarios(path) -> list[GoldenScenario]`** (632–667). Reads the golden "Executive
  Summary" per-scenario table: finds the header row where col A == "Scenario" (640–645), then reads
  each row until blank/`TOTAL` (648–650), deriving `code` = first token if alpha (652), `total_spend`
  / `incumbent_baseline` / `yoy_savings` / `savings_pct` from cols C/D/E/F (653–664). Eager load (635
  note). **WHY:** the golden comparison basis — the legacy engine's published per-lens spend.
- **`main() -> int`** (677–805). Orchestration, 6 stages (see flow below). Returns 0 success / 1
  failure / 2 missing-input. Side-effects: writes the throwaway setup + filled template into a temp
  vault, ingests/analyses against the real DB, **rolls back** (797).
- **`_count_quarantine_note(paths) -> str`** (808–822). Best-effort: regex-counts
  `(\d+)\s+row\(s\) quarantined` in the service-written NOTES.md; else "0". **WHY:** re-derive the
  quarantine count for the report (the service surfaces quarantine in NOTES.md). NOTE: returns `"0"`
  string on any miss — the printed "quarantined ~= 0" may UNDERREPORT if NOTES.md path/format differs.
- **`_latest_run_id(session, cycle_id) -> str`** (825–836). Raw SQL: latest `eng.analysis_run` for the
  cycle by `run_started_at DESC`. **WHY:** find the sealed run the comparison reads.
- **`_print_comparison(ours, golden)`** (839–914). Prints a per-lens table (OURS vs GOLDEN spend, Δ%,
  savings%, OURS cells/suppliers) using `o.savings_vs_incumbent_pct`, `o.cell_count`,
  `o.supplier_count`, `o.total_spend` (verified these fields exist on `ScenarioComparisonRow` in
  `app/domain/eng/read.py:62–77` — NO drift). Prints PARITY NOTES (875–914): best/worst spend Δ across
  shared lenses, lenses only-in-ours / only-in-golden, and the hardcoded narrative (899–914)
  explaining the ~+27% uniform spend gap as a **gating/coverage SEMANTIC difference** (legacy books
  spend only on gated cells with an eligible winner — of 324 awarded cells only 183 carry volume,
  ~88 volume cells / ~207k cases booked at $0; OUR V3 books more volume-bearing cells). **WHY:** the
  side-by-side is the migration-fidelity signal; the narrative pre-explains the known absolute-dollar
  divergence so a reviewer reads it as directional + cell-price parity, not a dollar-exact total.

### Dataclasses
- `LegacyConfig` (160–169, frozen): commodity, cycle_label, premium_ceiling/coverage_floor (Decimal),
  max_sup_dc (int), weight_preset (str), timeframes (tuple of (label,start,end,weeks)).
- `LegacyData` (172–185): config + dcs/lots/suppliers/volumes/incumbents/r2_bids + counters
  (dropped_volume_rows, r1_rows, r2_rows). The r2_bids key is `(supplier, dc, lot_id, tf)`.
- `GoldenScenario` (622–630, frozen): code/strategy/total_spend/incumbent_baseline/yoy_savings/
  savings_pct.
- `FillStats` (545–550): filled, scope_rows, unmatched_keys, examples (sample unmatched keys).

### Dependencies (imports, lines 42–83)
stdlib: tempfile, traceback, collections.abc.Iterable, dataclasses, decimal.Decimal, io.BytesIO,
pathlib.Path. Third-party: openpyxl (`load_workbook`, `Worksheet`), sqlalchemy.orm.Session. App:
`app.core.db.session.unit_of_work`, `app.cycle.loader.load_cycle`,
`app.domain.bid.template_schema` (BODY_START_ROW, SHEET_BIDS, BidColumn, HEADER_ROW as
BID_HEADER_ROW), `app.domain.eng.read.scenario_comparison`, `app.pilot.service.PilotService`,
`app.pilot.setup_template` (EXAMPLE_START_ROW, REGIONS, TAB_* , build_setup_workbook, HEADER_ROW as
SETUP_HEADER_ROW), `app.pilot.vault.stage_filename`. **NOTE:** imports `app.*` but NOT `reference.*`
— honors the clean-room ADR-0001 boundary (CI reference-guard) even though it reads a `reference/`
*file path* at runtime (reading a data file ≠ importing the reference package).

### Layer-1 data-flow (value-level) — the legacy→OURS conversion, every hop

```mermaid
flowchart TD
  L[legacy potato_2026_rfp_input.xlsx<br/>14 tabs, hdr row4 data row5] --> P[parse_legacy]
  subgraph P[parse_legacy — every transformation]
    C[CONFIG sheet -> LegacyConfig<br/>premium 0.15 / coverage 0.8 / max_sup 2<br/>weight_preset HARDCODED balanced]
    D1[DIM_DCs -> region REMAP→Central + state[:2]  ⚠S3]
    D2[DIM_Lots -> lot_id, desc, category]
    D3[DIM_Suppliers -> names]
    V[IN_Volumes -> DROP blank-Weekly ~141  ⚠S2]
    I[IN_Incumbents -> Routing (not FOB); dedupe per DC×Lot]
    B[IN_Bids -> KEEP ONLY R2 Delivered priced  ⚠S1<br/>key=(sup,dc,lot,tf); all_in←fob if missing]
  end
  P --> S[build_setup_bytes<br/>Rounds=2 ⚠S1 · LotName=Lot_ID ⚠S4 · Region∈REGIONS else Central ⚠S3]
  S --> IS[PilotService.ingest_setup -> governed cyc.* cycle]
  IS --> T[generate_bid_template round1]
  T --> F[fill_bid_template<br/>TF code→label · _as_positive >0 only ⚠S5]
  F --> IB[PilotService.ingest_bids round1 -> bid.bid_line]
  IB --> R[run_round round1 -> sealed eng.analysis_run + A–G lenses]
  R --> SC[scenario_comparison]
  G[golden analysis_output.xlsx<br/>Executive Summary] --> RG[read_golden_scenarios]
  SC --> CMP[_print_comparison: OURS vs GOLDEN side-by-side<br/>~+27% spend gap = gating/coverage semantic]
  RG --> CMP
  CMP --> RB[(session.rollback — no governed residue)]
```

**Decimal/precision hops in this file:**
- `_to_decimal` strips `,`/`$` → `Decimal` (no rounding); `premium`/`coverage` kept as Decimal,
  written to setup as `float(...)` (lines 442–443) — Decimal→float lossy cast at the workbook boundary.
- `weekly`/`routing` parsed as Decimal, written as `float(...)` (lines 501, 522) — same lossy cast.
- `_as_positive` casts to `float` and gates `>0` (line 151–154) — values ≤0 become None (dropped).
- No FOB+freight→landed math happens here (the legacy All-In is taken as-is; FOB substitutes for a
  missing All-In at line 369). The landed math lives in the engine, downstream of this file.

### Process branches / edge cases enumerated
- Missing legacy input → return 2 (682–684); missing golden → return 2 (685–687).
- Parse failure → traceback + return 1 (691–696). Setup-build failure → return 1 (717–722).
- ingest_setup / ingest_bids / run_round failures → traceback + return 1 (738–743, 768–773, 779–784).
- IN_Bids R1 rows → counted, skipped (350–352); non-R1/non-R2 → skipped (353); R2 with missing
  sup/dc/lot/tf → skipped (360–361); R2 with both all_in & fob None → skipped as No-Bid (366–367).
- fill: scope row missing sup/dc/lot → skipped (582–583); no R2 bid for the cell → unmatched++,
  sampled (589–592); R2 bid present but no positive price → unmatched++ (599–600).
- Volumes: blank Weekly → dropped (321–323); weeks 0 → coerced to 1 (`weeks or 1`, line 324).
- Incumbents: missing sup/dc/lot → skip (334); no routing → skip (337–338); duplicate (DC,Lot) →
  deduped to first (514–516).
- End state: `session.rollback()` (797) — the dry run intentionally leaves NO governed cycle.

---

# ============================================================================
# FILE 3 — `backend/demo/__init__.py`  (EMPTY)
# ============================================================================

**Path:** `/home/user/KR_RFP/backend/demo/__init__.py` · `.py` · **0 bytes / 0 lines · EMPTY** ·
census row 163.

**WHY EMPTY (explained, not skipped):** it is a Python **package marker** that makes `backend/demo/`
an importable package so `run_cycle_demo` can do absolute `app.*` imports and be discovered as a
module. It carries no code because a demo package needs no package-level exports, constants, or
initialization — its only job is to exist. **What breaks without it:** `demo` would not be a package;
tooling (mypy `namespace_packages`/`explicit_package_bases`, byte-compilation) and any
`from demo import …` would be on shakier footing. It is the conventional zero-byte `__init__.py`.

---

# ============================================================================
# FILE 4 — `backend/demo/run_cycle_demo.py`
# ============================================================================

**Path:** `/home/user/KR_RFP/backend/demo/run_cycle_demo.py` · `.py` · **1169 lines / 51,784 bytes** ·
not empty · census row 168 (created 2026-06-19, modified 2026-06-20T21:32:40).

## WHAT
The end-to-end **"see it working" demo** (D19 prototype fidelity): runs the WHOLE decision-support
loop against a REAL local Postgres with **SYNTHETIC** data, then writes four client-openable output
files into `backend/demo/output/`: `RECOMMENDATION.md`, `BOOKING_GUIDE_INTERNAL.xlsx`,
`SUPPLIER_AWARD_GUIDES.xlsx`, `SCENARIO_WORKBOOK.xlsx`.

## DETAILED WHY
- **Why it exists:** to demonstrate the full capability — seed → generate owned bid template →
  simulate supplier returns → key-validated ingest → engine runner (sealed run + scores + scenarios +
  split awards) → render decision-support `RECOMMENDATION.md` → simulate human selecting Scenario B →
  promote to award → render the post-award booking outputs. It is the tangible proof for a layman
  sponsor that the loop produces real deliverables.
- **Why shaped this way:** it seeds via **raw SQL** for the FK-heavy governed `ref/cyc/norm/perf`
  spine (the seed is pragmatic; the *runner* it drives is the real service), but every entity carries
  a clearly-SYNTHETIC, READABLE name (D23 — "Green Valley Farms (DEMO)", "Atlanta DC (ATL)") so the
  outputs are legible and obviously fictional (NO real supplier names/prices). Outputs render RESOLVED
  NAMES, never key IDs (D23); a trailing key-ref column is kept for traceability.
- **Why it is NOT a D45 violation:** it is fully SYNTHETIC, internally consistent demo data — it
  doesn't drop/flatten/force-positive real source data to "make data appear." It maps real component
  decomposition (All-In = FOB + Delivery(by region) + VegCool, lines 562–564) and full coverage
  faithfully. Distinct from FILE 1, which converts REAL legacy data with shortcuts.
- **What breaks without it:** no runnable, file-producing demonstration of the end-to-end loop on real
  Postgres; the `demo/output/*` artifacts (FILES 7–10) could not be regenerated.

## Module constants (lines 88–131)
`OUTPUT_DIR` (88); scope sizes N_DCS=3, N_LOTS=4, N_TFS=2, N_ROUNDS=3, N_SUPPLIERS=6 (91–95);
`SUPPLIER_NAMES` (6, all "(DEMO)", 100–107); `ITEM_DESCRIPTIONS` (4 desc+pack, 109–114); `LOT_NAMES`
(4, 115–120); `TF_NAMES` (2 season windows, 122–125); `ROUND_NAMES` (3, final=last, 127–131). **WHY:**
fixed, obviously-synthetic, readable scope so outputs are legible and reproducible.

## Every function
- **`_id() -> str`** (134–135): `uuid4()` string. **WHY:** synthetic PK minting.
- **`seed_cycle(session) -> SeededCycle`** (141–446): inserts the synthetic cycle + full scope via raw
  SQL into ref.client/commodity/subcommodity, cyc.cycle (round_count=N_ROUNDS=3 — satisfies the
  2..6 CHECK honestly), ref.dc (×3, readable names + region codes), ref.supplier (×6), ref.item (×4,
  one per lot), cyc.cycle_timeframe (×2), cyc.cycle_round (×3, is_final on last), cyc.cycle_lot +
  cycle_item_scope + cycle_lot_item (one item per lot), cyc.cycle_invited_supplier (×6),
  cyc.cycle_projected_volume (DC×item×TF synthetic cases, lines 341–367), perf.normalization_run +
  perf.historical_award_assignment + **perf.historical_awarded_price_basis** (the governed iTrade
  routing baseline D11, lines 369–428; routing = incumbent's final-round bid ×1.07 quantized to 0.01,
  line 388 — so the cycle shows ~7% realistic savings). Side-effect: `session.flush()` (430). Returns
  a fully-populated `SeededCycle`. **WHY:** a complete governed cycle the real runner can analyse;
  routing persisted to the governed home so `load_cycle` reconstructs it identically (lines 413–417).
- **`build_scope(seeded, round_entity) -> CycleScope`** (452–484): builds the intake CycleScope
  (embedded keys + display labels) for ONE round across every DC×lot×TF×supplier cell. **WHY:** the
  owned template generator (D21) needs the scope with keys embedded.
- **`_synthetic_price(round_idx, dc_idx, lot_idx, sup_idx) -> Decimal`** (490–513): deterministic
  All-In $/case. base = 10.00 + lot×0.50 + dc×0.20 (499); spread = |sup−specialist|×0.30 (501–503);
  round drift = round_idx × drift_rate where incumbent (idx0) concedes 0.04/round and challengers
  0.16 + sup×0.02/round (507–511); `price = base + spread − round_drift`, **quantized to 0.01**
  (513). **WHY:** tuned so a genuine 2-supplier DC split emerges (V3 split semantic) and asymmetric
  round-over-round concession reads the negotiation/fairness lens (pillar 4).
- **`_lot_specialist(lot_idx) -> int`** (516–522): rotation `(0,1,0,1,2,1)` — the keenest supplier per
  lot, alternating so each DC's lots split across two suppliers. **WHY:** force the genuine
  2-supplier split in scenarios B/D.
- **`fill_template(template_bytes, scope, round_idx) -> bytes`** (525–577): opens the generated
  template, writes per-row synthetic All-In + decomposed FOB/Delivery/VegCool + weekly/total volume.
  Decomposition (562–564): delivery = `REGION_FREIGHT[_dc_region(di)]`, vegcool =
  `VEGCOOL_SURCHARGE_CASE`, `fob = (price − delivery − vegcool)` quantized 0.01. A couple suppliers
  decline a couple cells (No-Bid: SUP-06 declines the last lot, lines 553–555 → leaves price cells
  blank). weekly=600, total = weekly×WEEKS_PER_TF (566–567). All written as `float(...)`. **WHY:**
  simulate varied supplier returns with a real FOB-vs-All-In freight decomposition and a real No-Bid
  branch; no Lot Discount so `ck_bid_line_no_double_discount` is satisfied (560–561).
- **`ingest_and_persist(session, filled_bytes, scope, seeded, round_entity) -> int`** (583–673):
  ingests via the KEY-VALIDATED path (`ingest_template`, 594), surfaces quarantine count (595–597),
  writes one norm.source_artifact + bid.bid_submission per supplier (FK chain, 600–637), then writes
  bid.bid_line rows ONLY for `Completeness.BID` lines (640–671 — no_bid/incomplete skipped as
  non-scoreable). Side-effect: `session.flush()` (672). Returns persisted count. **WHY:** real
  key-validated ingest → governed bid_line rows, mirroring the production intake.
- **`_header_map(ws)`** (679–685), **`_cell_str(ws,row,col)`** (688–690): openpyxl header/cell helpers.
- **`write_recommendation_md(session, seeded, analysis_run_id, config) -> Path`** (696–909): renders
  `RECOMMENDATION.md` PURELY from the sealed `eng.*` records. Builds id→name display maps + id→code
  key-ref maps (709–728); reads AnalysisScenario rows ordered by code (730–737); computes B-vs-A
  delta% (754–758); writes Cycle / Strategy / Scenario-comparison table / per-DC×lot×TF Scenario-B
  split award table (with savings vs incumbent routing avg, flags) / DC-level volume-weighted supplier
  split / Scenario-D split highlight. Side-effect: `OUTPUT_DIR.mkdir` + `path.write_text` (704, 908).
  **WHY:** the pre-award decision-support deliverable, names-not-keys (D23), from the records only.
- **`_split_cells(awards)`** (912–920): cells (dc,lot,tf) with >1 supplier award (a real split).
- **`_dc_supplier_split(awards, period_cases_by_cell)`** (923–943): per DC, supplier →
  (volume-weighted cases = projected cases × volume_share, distinct lot count). **WHY:** the real V3
  DC-split decision-support figure a buyer reviews.
- **Dataclasses `AwardedCell`** (954–972, frozen) / **`SelectedAward`** (974–981, frozen): the
  in-memory stand-in for an `awd.award` row (the demo defers the `awd.*` spine), carrying JOIN keys +
  resolved names so both booking guides render off ONE award.
- **`select_award_from_scenario(session, seeded, analysis_run_id, selected_scenario_code="B")
  -> SelectedAward`** (983–1043): simulates the human selecting a scenario and promoting it to a
  (frozen) award assembled from `eng.analysis_scenario_award` rows, keys resolved to seeded item +
  routing baseline. The docstring (989–998) explicitly marks `>>> FREEZE + SIGN-OFF GATES WOULD SIT
  HERE <<<` (D22 / ADR-0006) — the demo NOTES the gate rather than enforcing it (the `awd.*` spine is
  a later phase). **WHY:** booking outputs are generated FROM AN AWARD, never straight off a scenario
  (D22) — even in the demo.
- **`main()`** (1049–1165): orchestrates [1/8]…[9/9] (the stage numbering is inconsistent — see
  drift). Builds `EngineConfig` (BALANCED preset, weights 0.35/0.25/0.20/0.10/0.10, max_sup_dc=2,
  conc 0.40, premium 0.12, coverage 0.80, lines 1051–1062); seeds; loops 3 rounds (generate→fill→
  ingest each); runs the engine runner on the FINAL round; writes RECOMMENDATION.md; selects award B;
  writes the two booking guides + the scenario workbook; prints the four output paths + sizes. All on
  ONE `unit_of_work` (1064) which **COMMITS** on clean exit (the demo persists its governed cycle —
  unlike FILE 1's rollback). **WHY:** the whole loop, end to end, producing real files.

## Dependencies
stdlib uuid/collections/dataclasses/datetime/decimal/io/pathlib; openpyxl; sqlalchemy. App:
`app.core.db.session.unit_of_work`, `app.domain.bid.*` (bid_ingester, models.BidLine,
template_generator, template_schema), `app.domain.eng.*` (models, runner.EngineRunner/IncumbentRow),
`app.engine.interface` (EngineConfig/WeightPreset), `app.output.*` (booking_guide, scenario_workbook,
synthetic constants `DC_NAMES`/`REGION_FREIGHT`/`VEGCOOL_SURCHARGE_CASE`/`WEEKS_PER_TF`/`_dc_region`,
types Entity/SeededCycle). The output *writers* live in `app/output/*` (other slice); this file is the
driver.

## Decimal/precision hops
- `_synthetic_price` → Decimal, quantized `0.01` (513). routing ×1.07 quantized `0.01` (388).
- `fob = (price − delivery − vegcool)` quantized `0.01` (564). All written to xlsx as `float(...)`
  (568–573) — Decimal→float at the workbook boundary (the engine re-reads from the governed Decimal
  columns, not the xlsx, so scoring stays Decimal-exact).
- RECOMMENDATION.md: savings% = `(baseline − awarded)/baseline×100` Decimal, formatted `+.1f` (851);
  volume share `×100` formatted `.0f` (850, 873); spend `$,.2f` (800).

## Process branches
- Quarantine surfaced but tolerated (595–597). No-Bid branch: SUP-06 last lot (553–555); only
  `Completeness.BID` lines persisted (641). delta% only when spend_a>0 (757). Scenario-D split
  highlight only when split cells exist (881). Award selection `.one()` (1002–1009) → raises if
  Scenario B absent (a hard invariant: the runner always writes A–G).

---

# ============================================================================
# FILES 7–10 — `backend/demo/output/*`  (generated demo artifacts)
# ============================================================================

These are the **emitted outputs** of FILE 4 (`run_cycle_demo.py`) — committed/checked-in artifacts
(census marks them tracked=`y` for the .md, the .xlsx are binary; mtime 2026-06-20). They are
**generated, not authored**: regenerating the demo overwrites them. They are kept in-repo so a
reviewer can open the deliverables without running the demo.

- **FILE 7 `RECOMMENDATION.md`** (7316 B, 80 lines, census 165). The pre-award decision-support
  deliverable rendered by `write_recommendation_md`. Content verified end-to-end: cycle
  `CYC-20260620-A80F`, engine `v3-cleanroom` sealed run `d3b8a1ff…`, sealed input/output sha256
  manifests, BALANCED weights 0.35/0.25/0.20/0.10/0.10, max 2/DC, premium 0.12 / coverage 0.80 /
  conc 0.40. Scenario table A=$1,697,893.60 (lowest) < B=C=D=E=F=G=$1,719,296.80; headline B is
  **1.26% above** A. Per-DC×lot×TF Scenario-B split table (24 rows, 3 DCs × 4 lots × 2 TFs) with
  resolved DEMO names, 100% volume shares, awarded $/case, savings vs baseline (+2.1%…+13.2%), and a
  `DC·lot·sup` key-ref column. DC-level split: each DC splits ~51/49–52/48 across Sunbelt Produce +
  Harvest Ridge (2 suppliers/DC) — the V3 split semantic demonstrated. **WHY this artifact:** tangible
  proof the decision-support view renders names-not-keys from sealed records (D23).
- **FILE 8 `BOOKING_GUIDE_INTERNAL.xlsx`** (8078 B, census 164). The buyers/pricing master rendered by
  `app.output.booking_guide.write_booking_guide_internal_xlsx` FROM THE AWARD (D22) — awarded supplier
  NAME per DC×lot×item×TF with FOB/landed $/case, volume, routing. Binary (not line-audited; generator
  is another slice). **WHY:** the post-award pricing-master deliverable, generated last (after award).
- **FILE 9 `SCENARIO_WORKBOOK.xlsx`** (108992 B, census 166 — the largest demo artifact). The
  ALIGNMENT/COMPARISON tool (D26/D27) rendered by `app.output.scenario_workbook` — Scenario Comparison
  (lenses side by side + LIVE Custom column + expandable scenario→DC→supplier drill), interactive
  Custom Scenario (D25), and a flat "Data (pivot me)" Excel Table (D27). Binary. **WHY:** the
  interactive analysis workbook the buyer aligns scenarios in.
- **FILE 10 `SUPPLIER_AWARD_GUIDES.xlsx`** (8292 B, census 167). One sheet per awarded supplier
  ("here is what you've been awarded") rendered by `write_supplier_award_guides_xlsx` FROM THE AWARD.
  Binary. **WHY:** the per-supplier award communication deliverable.

**NOTE on `.dockerignore`:** `demo/output` IS excluded from the backend image (FILE 13 line 25) — the
demo artifacts never ship in the container (they're a local dev/demo convenience, not a runtime need).

---

# ============================================================================
# FILE 11 — `backend/pyproject.toml`
# ============================================================================

**Path:** `/home/user/KR_RFP/backend/pyproject.toml` · `.toml` · 93 lines / 3335 B · census row 174.

## WHAT / WHY
The backend Python project + tooling config. **WHY:** single source for dependencies, the package
discovery, and the ruff/mypy/pytest tool config that CI (FILE 20) enforces — without it nothing
installs or lints consistently.

- **[project]** (1–19): name `kr-rfp-backend`, version 0.1.0, `requires-python >=3.12`. Runtime deps
  with per-line WHY comments: fastapi/uvicorn/sqlalchemy>=2.0/alembic/psycopg[binary]/pydantic/
  pydantic-settings (the API+DB spine); `openpyxl>=3.1` (bid intake xlsx, D20); `passlib[argon2]`
  (argon2 password hash); `pyotp` (TOTP 2FA); `pyjwt` (signed session JWT in the kr_session cookie);
  `python-multipart` (FastAPI file-upload routes). **WHY each is pinned with a reason:** every dep
  ties to a capability so nothing is unexplained (exhaustiveness bar).
- **[project.optional-dependencies] dev** (21–29): pytest, pytest-cov (CI `--cov=app`), `mcp>=1.0`
  (the MCP SDK — tests/mcp imports `mcp.server.fastmcp` for the rfp_mcp server), httpx (fastapi
  testclient), ruff, mypy.
- **[build-system]** (31–33): setuptools>=68. **[tool.setuptools.packages.find]** (35–36):
  `include = ["app*"]` — only the `app` package is installed (scripts/, tests/, demo/, alembic/ are
  NOT installed as packages; they're run in-tree). **NOTE:** this is why the Dockerfile `pip install .`
  ships only `app*` as an installed package and copies the rest of `backend/` in via `COPY`.
- **[tool.ruff]** (41–52): target py312, line-length 100, src app/tests; lint select
  E/F/I/UP/B/C4/SIM, ignore B008 (FastAPI `Depends(...)` default idiom); isort first-party `app`.
- **[tool.mypy]** (57–83): py312, pydantic plugin, **strict=true**, warn_unused_ignores/redundant_casts,
  disallow_untyped_defs, no_implicit_optional, namespace_packages, explicit_package_bases. Overrides:
  `alembic.*` ignore_errors (generated/migration code); `openpyxl.*`/`pyxlsb.*` ignore_missing_imports
  (no stubs — narrower than ignore_errors so our boundary code stays strict); `passlib.*`
  ignore_missing_imports (no stubs; wrappers cast results back). **WHY:** strict typing everywhere
  except the un-stubbed third-party boundaries, explicitly enumerated.
- **[tool.pytest.ini_options]** (88–93): testpaths tests, `test_*.py`, marker `integration` (real
  Postgres; deselect with `-m 'not integration'`). **WHY:** lets CI run pure vs integration tests.

---

# ============================================================================
# FILE 12 — `backend/Dockerfile`
# ============================================================================

**Path:** `/home/user/KR_RFP/backend/Dockerfile` · no ext · 54 lines / 3105 B · census row 20.

## WHAT / WHY
Builds the backend API image (FastAPI on uvicorn). **WHY shaped this way (the load-bearing
constraints, all in the header 1–17):**
- **Cloud Run contract:** must bind `0.0.0.0:$PORT` and be STATELESS (no disk persistence — ADR-0018);
  reaches Cloud SQL over the `/cloudsql` unix socket via DATABASE_URL (set by deploy.sh); locally
  reaches compose Postgres over the network.
- **BUILD CONTEXT = REPO ROOT** (not `backend/`): the alembic 0001 baseline migration reads
  `<repo-root>/db/baseline/schema.sql` (the real as-built schema). The image must carry BOTH trees in
  the same relative layout — `backend/ → /app` and `db/ → /db` — so
  `/app/alembic/versions/0001_baseline.py` resolves `/db/baseline/schema.sql`. Build with
  `docker build -f backend/Dockerfile -t kr-rfp-backend .` from the repo root. **What breaks otherwise:
  the baseline migration can't find the schema SQL.**
- **Migrations are NOT in the CMD** (header 13–17): the serving container only serves; `alembic upgrade
  head` is a SEPARATE step (a Cloud Run job in deploy.sh, a one-shot `migrate` service in compose) so
  N serving instances don't race to migrate and a migration failure doesn't crash-loop the service.

**Steps:** `FROM python:3.12-slim` (18); ENV PYTHONUNBUFFERED/DONTWRITEBYTECODE/PIP_NO_CACHE_DIR +
`PORT=8000` default (20–24); WORKDIR /app (26); `COPY backend/pyproject.toml ./` then `pip install .`
FIRST for layer caching (29–30 — only pyproject busts the dep layer); `COPY db /db` (33 — the
baseline SQL); `COPY backend/ /app/` (35–37 — app/, alembic/, alembic.ini, scripts/, **tests/ on
purpose** because seed.py reuses tests/pilot/ builders); `COPY deploy/gcp/seed.py /app/deploy/gcp/
seed.py` (40–41 — ship the seed so the seed job can invoke it); `COPY
reference/samples/potato_2026_rfp_input.xlsx /reference/samples/...` (43–47 — the ONE 0.4MB reference
sample the POTATO seed reads, NOT the 150MB reference/ tree; seed skips gracefully if absent);
EXPOSE 8000 (49); CMD `sh -c "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"` (54 — shell
form so $PORT expands at runtime; note it can become gunicorn+UvicornWorker without changing the
contract). **WHY tests/ and seed.py and the sample ship:** the same image runs the migrate job AND
the seed job; the seed needs the test builders + the legacy sample.

---

# ============================================================================
# FILE 13 — `backend/.dockerignore`
# ============================================================================

**Path:** `/home/user/KR_RFP/backend/.dockerignore` · dotfile · 25 lines / 556 B · census row 18.

## WHAT / WHY
Keeps the backend build context small + reproducible (deps install from pyproject inside the image,
so the local venv + caches are pure noise). Excludes: `.venv`/`venv`/`__pycache__`/`*.pyc`/`*.pyo`,
`.pytest_cache`/`.mypy_cache`/`.ruff_cache`/`.coverage`/`htmlcov`/`*.egg-info`, `.env`/`.env.*` (but
NOT `.env.example`, line 19), `.git`/`.gitignore`, `Dockerfile`/`.dockerignore`/`README.md`, and
`demo/output` (25 — the demo artifacts never ship). **WHY tests/ is INTENTIONALLY NOT excluded**
(header 4–5): `deploy/gcp/seed.py` reuses the TOMATO synthetic builders from
`tests/pilot/test_pilot_cycle_e2e.py`, and the seed runs inside this image — so tests/ must ship.
**What breaks if tests/ were excluded:** the seed's TOMATO path can't import its builders.

**NOTE (build-context subtlety):** this `.dockerignore` lives in `backend/`, but the image builds from
the REPO ROOT (FILE 12). Docker uses the `.dockerignore` at the *build context root* (the repo root),
not `backend/.dockerignore` — so this file's exclusions only apply when something builds with
`backend/` as the context. There is no repo-root `.dockerignore` in B9's scope (R1 owns root
dotfiles); whether one exists is R1's to confirm. This is a **potential drift** worth flagging: the
documented exclusions here may not be the ones Docker actually honors for the repo-root build.

---

# ============================================================================
# FILE 14 — `backend/README.md`
# ============================================================================

**Path:** `/home/user/KR_RFP/backend/README.md` · `.md` · 60 lines / 2450 B · census row 21.

## WHAT / WHY
The backend developer README. **WHY:** the on-ramp — layout, run/migrate/test commands, invariants.
Sections: Layout (core/domain/engine/api/alembic, 6–17); Run locally (venv + `pip install -e ".[dev]"`
+ `cp .env.example .env`, 19–34); Migrate (upgrade/downgrade/revision, 37–42); Test (pure vs full,
ruff/mypy, 44–53); **Invariants (do not regress)** (55–59): services add+flush never commit (the
request UoW owns commit); tenant context from the verified token only; `backend/` must never import
`reference/` (ADR-0001, CI-enforced); governed rows append-only (corrections insert superseding rows).

**⚠️ DOC DRIFT flagged (read-only — not fixed):**
1. **Line 13–16 describes a STALE state:** "the other seven [domain packages] are present-but-empty
   stubs" and "api … the rest are present-but-empty routers." This contradicts the as-built reality
   (the domain layers `bid`/`eng`/`cyc`/etc. are populated — FILE 1 and FILE 4 import real
   `app.domain.bid.*`, `app.domain.eng.*` symbols). The README predates the build-out and was never
   updated. **What this misleads:** a reader would think the system is a scaffold.
2. **Line 24** documents `cp .env.example .env`; `.env.example` is referenced but is a repo/backend
   dotfile (R1's scope to confirm it exists). Cross-check needed with R1.
3. **Line 34** "Or via Docker (migrates then serves): `docker run … kr-rfp-backend`" — but FILE 12's
   CMD **only serves** (migrations are a separate step by design). So the README's "migrates then
   serves" is **wrong** for the current Dockerfile (the migrate is out-of-band). Drift to flag.
4. **Line 4** references `architecture/SKELETON.md` and `project/squads/architecture/PLAN.md` — paths
   to verify in other slices.

---

# ============================================================================
# FILE 15 — `backend/alembic.ini`
# ============================================================================

**Path:** `/home/user/KR_RFP/backend/alembic.ini` · `.ini` · 41 lines / 756 B · census row 22.

## WHAT / WHY
Alembic config. The DB URL is deliberately **NOT** here (header 1–2) — `alembic/env.py` pulls it from
`app.core.config.settings` (single typed config surface; **no secrets in the repo**). `[alembic]`
(3–7): `script_location = alembic`, `prepend_sys_path = .` (so `app` imports resolve),
`path_separator = os`, `version_path_separator = os`. Logging config (9–40): root WARNING, sqlalchemy
WARNING, alembic INFO, console handler to stderr, generic formatter. **WHY:** standard alembic plumbing
with the one deliberate choice that the URL comes from typed settings, keeping secrets out of the repo
(supports ADR-0018 / no-secrets-in-repo). **What breaks without it:** alembic can't locate migrations
or import `app`.

---

# ============================================================================
# FILE 16 — `deploy/gcp/README.md`
# ============================================================================

**Path:** `/home/user/KR_RFP/deploy/gcp/README.md` · `.md` · 197 lines / 8497 B · census row 250.

## WHAT / WHY
The GCP deploy RUNBOOK for `deploy.sh` (FILE 17) + `seed.py` (FILE 18). **WHY:** a layman-operable,
step-by-step deploy guide so the sponsor (or CI SA) can stand up the whole stack with one command and
understand each step, cost, and teardown.

Sections, all verified consistent with deploy.sh unless noted:
1. **Prerequisites** (13–39): GCP project w/ billing, gcloud CLI, openssl, IAM roles table (run.admin,
   cloudsql.admin, artifactregistry.admin, secretmanager.admin, iam.serviceAccountUser,
   cloudbuild.builds.editor, serviceusage.serviceUsageAdmin). Notes Docker NOT needed locally (builds
   in Cloud Build). Notes the script auto-grants the runtime Compute-default SA secretAccessor +
   cloudsql.client.
2. **Two access paths** (42–58): operator `gcloud auth login` or SA key.
3. **Parameters** (62–82): table matching deploy.sh defaults — PROJECT_ID + SEED_ADMIN_PASSWORD
   required; REGION us-central1, APP_PREFIX kr-rfp, DB_EDITION ENTERPRISE (with the ENTERPRISE_PLUS
   rejection rationale), DB_TIER db-f1-micro, DB_NAME kr_rfp, DB_USER kr_rfp_app, MIN_INSTANCES 0,
   RUN_SEED 1. Secrets auto-generated into Secret Manager (never typed).
4. **One-command deploy** (86–120): the 12-step ordered list — matches deploy.sh `main()` (enable
   APIs → AR → secrets → Cloud SQL → IAM → build backend → deploy backend → migrate → build frontend
   (with backend URL) → deploy frontend → wire CORS → seed). `--print-urls` fast path documented.
5. **Seeding separately** (124–140): re-run the seed job; or locally with DATABASE_URL +
   SEED_ADMIN_PASSWORD; flags `--admin-only | --skip-tomato | --skip-potato | --admin-username`.
6. **Rough cost** (144–157): db-f1-micro ~$8–15/mo (24/7, the main cost), Cloud Run ~$0 idle, AR+SM
   <$1 → ~$10–20/mo pilot. MIN_INSTANCES=1 for always-warm.
7. **Local full-stack verification** (160–177): `docker compose up --build -d` + `docker compose run
   --rm seed`; backend /health + /ready, frontend :3000; `down -v`. Notes it differs from prod only in
   local DB password, `AUTH_COOKIE_SECURE=false`, http vs https.
8. **Teardown** (181–198): delete services/jobs/SQL/AR/secrets; warns Cloud SQL delete is irreversible.

**⚠️ MINOR DRIFT flagged:** §4 line 112 and §3 line 78 say pass `--no-seed` to skip seeding, and
deploy.sh's `main()` case-matches `--no-seed` (line 421) — **consistent**. BUT deploy.sh's own header
comment line 27 says "`SEED_ADMIN_PASSWORD (required for --seed)`" referencing a `--seed` flag that
does NOT exist (the only flags are `--no-seed` and `--print-urls`). The README does not repeat that
error — the drift is internal to deploy.sh's header (see FILE 17).

---

# ============================================================================
# FILE 17 — `deploy/gcp/deploy.sh`  (the deploy driver)
# ============================================================================

**Path:** `/home/user/KR_RFP/deploy/gcp/deploy.sh` · `.sh` · 449 lines / 21,596 B · census row 251
(modified 2026-06-22T17:28:34 — most-recently-touched file in the slice). Shebang
`#!/usr/bin/env bash`, `set -euo pipefail` (36).

## WHAT / WHY
One-command, **idempotent** (CREATE-IF-NOT-EXISTS) deploy of KR_RFP to GCP Cloud Run + Cloud SQL: two
Cloud Run services (backend FastAPI + frontend Next.js) backed by a Cloud SQL Postgres, secrets in
Secret Manager, images in Artifact Registry. **WHY shaped this way:** ADR-0017 (GCP Cloud Run + Cloud
SQL) / ADR-0018 (stateless, no server-side files). Every step reconciles (never duplicates) and echoes
what it does, so re-running is safe and a layman can follow it.

### Parameters (41–57)
PROJECT_ID (required), REGION (us-central1), APP_PREFIX (kr-rfp), DB_EDITION (ENTERPRISE — the cheap
shared-core tiers only exist on ENTERPRISE, line 44/129–130), DB_TIER (db-f1-micro), DB_NAME (kr_rfp),
DB_USER (kr_rfp_app), RUN_SEED (1), MIN_INSTANCES (0). Derived resource names all deterministic from
the prefix (52–57): AR_REPO, SQL_INSTANCE, BACKEND_SVC, FRONTEND_SVC, SECRET_DB_PASSWORD,
SECRET_APP_KEY. `SCRIPT_DIR`/`REPO_ROOT` = two parents up (60–61).

### EVERY STEP (function) + WHY
- **`say/info/die`** (66–68): colored logging helpers.
- **`require_tools`** (70–72): gcloud must be installed, else die. **WHY:** fail fast.
- **`require_project`** (74–76): PROJECT_ID must be set, else die.
- **`print_urls`** (79–85): `--print-urls` fast path — describe both services' status.url; print or
  `<not deployed>`. **WHY:** reprint URLs without redeploying.
- **`enable_apis`** (90–100): `gcloud services enable run sqladmin artifactregistry secretmanager
  cloudbuild`. **WHY:** all five APIs are needed; enabling an enabled API is a no-op (idempotent).
- **`ensure_artifact_registry`** (105–118): describe-or-create the `<prefix>-images` Docker repo.
  **WHY:** the image registry; idempotent describe-then-create.
- **`ensure_cloud_sql`** (123–167): describe-or-create the Postgres 16 instance (—edition pinned, the
  comment 129–130 explains gcloud now defaults to ENTERPRISE_PLUS which rejects db-f1-micro);
  describe-or-create the database; describe-or-create the user — **resetting its password to the
  stored secret if it already exists** (153–156, idempotent). Reads the DB password from Secret
  Manager (152). Captures `SQL_CONNECTION_NAME` = `project:region:instance` (164–166) — the /cloudsql
  socket path. **WHY:** the system-of-record DB; the connection name threads into every later
  DATABASE_URL. **Ordering note:** secrets are created BEFORE this (header 169–171 / main order) so the
  user password comes from the secret (single source of truth).
- **`ensure_secret(name, generate)`** (173–187): describe-or-create a secret; if `generate`, add an
  initial version = `openssl rand -base64 32` (a strong default the operator never types). **WHY:** no
  secret values in the repo; auto-generated.
- **`ensure_secrets`** (189–193): ensure `<prefix>-db-password` + `<prefix>-auth-secret-key`, both
  generated.
- **`grant_runtime_iam`** (199–217): resolve the Compute default SA
  (`<projectnumber>-compute@developer.gserviceaccount.com`), grant it `secretmanager.secretAccessor`
  on both secrets + `cloudsql.client` on the project. **WHY:** Cloud Run runs as that SA and must read
  the secrets + reach Cloud SQL; re-adding a binding is a no-op (idempotent).
- **`image_uri(name)`** (222): `<region>-docker.pkg.dev/<project>/<repo>/<name>:latest`.
- **`build_backend`** (224–242): builds + pushes the backend image via Cloud Build with an
  **explicit generated cloudbuild.yaml** (mktemp) that runs `docker build -f backend/Dockerfile -t
  <uri> .` with **REPO_ROOT as context** (231–240). **WHY:** the backend image needs backend/ AND
  db/baseline/schema.sql in their real relative layout (FILE 12); `gcloud builds submit <dir> --tag`
  assumes a Dockerfile at the context root, so an explicit config is required. Cleans up the temp
  (240).
- **`build_frontend(backend_url)`** (244–268): builds + pushes the frontend image, passing
  `--build-arg NEXT_PUBLIC_API_BASE_URL=<backend_url>` via a generated cloudbuild.yaml, context
  `frontend/`. **WHY:** `NEXT_PUBLIC_*` is inlined at BUILD time, so the frontend must be built AFTER
  the backend is deployed (needs its URL).
- **`deploy_backend`** (273–304): `gcloud run deploy <prefix>-backend` with the image,
  `--allow-unauthenticated`, `--port 8000`, `--add-cloudsql-instances <conn>`,
  `--min-instances <MIN_INSTANCES>`, env `ENV=production,DATABASE_URL=<url>,AUTH_COOKIE_SAMESITE=none`,
  secret `AUTH_SECRET_KEY=<secret>:latest`. The DATABASE_URL uses the **/cloudsql UNIX SOCKET**
  (`postgresql+psycopg://<user>:<pw>@/<db>?host=/cloudsql/<conn>`, line 279) with the password
  substituted from the secret at deploy time (285–287 — the URL lives only in the service config, not
  the repo). Captures `BACKEND_URL` (301–303). **WHY:** the backend service, wired to Cloud SQL over
  the socket; AUTH_COOKIE_SAMESITE=none because the frontend is a separate origin (cross-site cookie).
  **NOTE (comment cruft):** lines 281–284 are a stream-of-consciousness comment musing about
  alternative password-injection approaches before settling on the deploy-time substitution — harmless
  but messy; flag as a readability nit, not a bug.
- **`deploy_frontend`** (309–324): `gcloud run deploy <prefix>-frontend`, `--port 3000`,
  `--min-instances`. Captures `FRONTEND_URL`. **WHY:** the frontend service (image already baked with
  the backend URL).
- **`wire_cors`** (329–351): sets the backend's `CORS_ALLOW_ORIGINS` to the frontend URL(s). The long
  comment (332–344) explains Cloud Run serves each service under TWO interchangeable hostnames
  (project-number form + hashed form); status.url returns only one, but credentialed CORS matches the
  EXACT origin, so it allows BOTH the status.url and the deterministic project-number form. Uses
  `^@^` to switch gcloud's env delimiter to `@` so the comma stays INSIDE the value (347–349). **WHY:**
  credentialed CORS must match the exact browser origin or login breaks from the other URL.
- **`run_migrations`** (357–380): runs `alembic upgrade head` against Cloud SQL via a one-off **Cloud
  Run JOB** (`<prefix>-migrate`) — update-or-create the job with the backend image, the SQL socket,
  `ENV=production` + DATABASE_URL, `--command alembic --args "upgrade,head"`, then `execute … --wait`.
  **WHY:** migrations out-of-band from serving (no instance race, no crash-loop). The backend image
  carries alembic + migrations.
- **`run_seed`** (385–410): if RUN_SEED=1 and SEED_ADMIN_PASSWORD set (else die), runs the seed via a
  one-off Cloud Run JOB (`<prefix>-seed`) — update-or-create with the backend image, SQL socket,
  `ENV=production` + DATABASE_URL + SEED_ADMIN_PASSWORD, `--command python --args
  "/app/deploy/gcp/seed.py"`, then `execute … --wait`. **WHY:** seed admin + TOMATO + POTATO via the
  same image; the seed.py is shipped at /app/deploy/gcp/seed.py (FILE 12 line 41).
- **`main`** (415–449): require tools+project; arg case `--print-urls` (exit 0) / `--no-seed`
  (RUN_SEED=0); `gcloud config set project`; then the ordered pipeline (426–440): enable_apis →
  ensure_artifact_registry → **ensure_secrets** → **ensure_cloud_sql** → grant_runtime_iam →
  build_backend → deploy_backend → run_migrations → build_frontend(BACKEND_URL) → deploy_frontend →
  wire_cors → run_seed; prints backend+frontend URLs. **WHY this order:** secrets before Cloud SQL (DB
  user reads its password from the secret); backend deployed + migrated before the frontend builds
  (frontend bakes the backend URL); CORS wired after both exist; seed last.

### Branches / edge cases
- Idempotency throughout: every `ensure_*` does describe→(exists: info | create); the SQL user path
  RESETS the password if the user exists (155–156). `--print-urls` short-circuits before any mutation.
- `run_seed` hard-fails (die) if SEED_ADMIN_PASSWORD is unset while RUN_SEED=1 (387) — refuses a
  blank-admin seed.
- `set -euo pipefail` (36): any unset var or failed command aborts the whole deploy (fail-loud).

### ⚠️ DRIFT flagged (read-only)
- Header line 27 documents `SEED_ADMIN_PASSWORD (required for --seed)` and the usage block (32–35)
  lists `--no-seed` and `--print-urls` — there is **no `--seed` flag**; the seed runs by default
  (RUN_SEED=1). The `--seed` reference in the header comment is stale/incorrect. (Functionally
  harmless; doc-only.)

---

# ============================================================================
# FILE 18 — `deploy/gcp/seed.py`  (the COMMITTING console-path seed driver)
# ============================================================================

**Path:** `/home/user/KR_RFP/deploy/gcp/seed.py` · `.py` · 319 lines / 14,200 B · census row 252.
Shebang `#!/usr/bin/env python3`.

## WHAT / WHY
Seeds the deployed (or local-compose) DB so the console renders something real: (a) an `admin`
web-console user (password from `$SEED_ADMIN_PASSWORD`), (b) the TOMATO synthetic full cycle, (c) the
POTATO real-data cycle — **all COMMITTED**. Both cycles end FROZEN/finalized so the Awards screens
render. **WHY shaped this way:** the runs are created on the WEB-CONSOLE path
(`db_runs=True, persist_outputs=False`) — exactly how the live console makes runs — so they land as
`pilot.run` rows with a linked governed cycle and a frozen `awd.award` (what the runs list + Awards
screens resolve from). No files written server-side (ADR-0018). **This is the committing counterpart
to FILE 1** (the dry-run rolls back; the seed commits) — explicitly contrasted in the header and in
`_drive_console_cycle`'s docstring.

### import-path bootstrap (43–55)
`_THIS`/`_REPO_ROOT`(parents[2])/`_BACKEND`; inserts `backend` then repo-root into `sys.path` so
`app`/`tests`/`scripts` import whether invoked from the repo root (local) or `/app` inside the image
(cloud). **WHY:** the file lives at deploy/gcp/ but imports backend test/scripts modules; inside the
image cwd is /app and those are already importable (the loop is the local fallback). The header
(29–31) explains WHY it lives here but imports backend modules: it runs INSIDE the backend image
(Dockerfile copies tests/ + scripts/ in).

### Every function
- **`_log(msg)`** (58–59): print+flush.
- **`seed_admin(username="admin") -> str`** (65–83): upserts the console admin via
  `app.auth.create_user.upsert_user` (argon2, active, no 2FA) — the SAME path as
  `python -m app.auth.create_user`, so seed and ops agree byte-for-byte. **Refuses** a blank/default
  password: raises SystemExit if `$SEED_ADMIN_PASSWORD` is unset (76–80). Idempotent (re-run resets the
  password). **WHY:** you must be able to log in; never seed a blank-password admin.
- **`_latest_analysis_run_id(session, cycle_id) -> str`** (89–100): raw SQL latest eng.analysis_run by
  run_started_at DESC (same query as FILE 1's `_latest_run_id`). **WHY:** find the sealed run to freeze.
- **`_drive_console_cycle(*, commodity, label, setup_bytes, fill_template, award_code) -> str`**
  (103–171): THE shared committing driver. Creates a throwaway temp vault (the console path scaffolds
  no folder but PilotService needs a RunPaths shape, 126–127), builds
  `PilotService(tmp_root, isolate_db=False, db_runs=True, persist_outputs=False)` (128), then on ONE
  `unit_of_work` (130): (1) `start_run` (mints slug, writes pilot.run, 132–134); (2)
  `ingest_setup_bytes` from BYTES (no-disk) → governed cycle linked on the run (136–142); (3)
  `build_scope_from_cycle(cycle,1)` → `generate_template_bytes` → `fill_template(template_bytes,
  cycle)` → `ingest_bids_bytes` round 1 (145–152); (4) `run_round` round 1 → sealed analysis (155–157);
  (5) `freeze_award(... scenario_code="B", award_code=...)` → awd.award (160–167). **The
  `unit_of_work` COMMITS on clean exit (169)** — the run/cycle/analysis/award persist. **WHY:** drives
  the exact console lifecycle to a frozen award so the Awards screens have real data; commit (not
  rollback) is the whole difference from the dry-run.
- **`seed_tomato() -> str`** (177–196): drives the TOMATO synthetic cycle FROZEN using
  `app.pilot.synthetic.build_filled_setup` / `fill_bid_template` — the EXACT builders the
  `test_full_cycle_loop_e2e` test drives (2 DCs, 2 lots, 2 suppliers, 1 TF, 2 rounds), kept in
  lock-step with the test (and in the app package so the seed never imports pytest at runtime). award
  code `AWD-TOMATO-SEED`. **WHY:** a synthetic cycle that matches the e2e test exactly.
- **`seed_potato() -> str`** (202–248): drives the **real-data POTATO** cycle FROZEN by reusing FILE
  1's `parse_legacy` / `build_setup_bytes` / `fill_bid_template` (`from scripts.potato_legacy_dryrun
  import …`, 211–216) — but through the COMMITTING console path (the dry-run rolls back). SKIPS
  gracefully if the legacy sample is absent (220–225, returns ""). The inner `_fill` (231–240)
  resolves the TF code→label map from the loaded cycle (`{tf.code: tf.name …}`) — same resolution as
  FILE 1 — and logs the fill stats. award code `AWD-POTATO-SEED`. **⚠️ This is the live path by which
  the D45-violating converter's output is COMMITTED to the deployed DB** — i.e. the 5 shortcuts in
  FILE 1 are not confined to a throwaway dry-run; via `seed_potato` they materialize the POTATO cycle
  the console actually shows. Flag for D45 remediation: fixing FILE 1's converters fixes this path too.
- **`_report_counts()`** (254–272): prints the runbook-asserted headline counts (auth.app_user,
  pilot.run, cyc.cycle, awd.award) on a fresh unit_of_work. **WHY:** the runbook checks these.
- **`main(argv) -> int`** (278–315): argparse `--admin-only / --skip-tomato / --skip-potato /
  --admin-username`; echoes DATABASE_URL with **credentials redacted** (292–297); seeds admin, then
  (unless --admin-only) TOMATO (unless --skip-tomato) + POTATO (unless --skip-potato); re-raises
  SystemExit, catches other exceptions with full traceback + return 1 (306–311); `_report_counts`;
  return 0. **WHY:** controllable, fail-loud entrypoint that redacts secrets in its echo.

### Branches / edge cases
- Blank SEED_ADMIN_PASSWORD → SystemExit (76–80). Missing legacy sample → POTATO skipped, returns ""
  (220–225). Any seed exception → traceback + exit 1 (308–311). SystemExit re-raised (so the
  blank-password refusal propagates, 306–307). Flags gate which cycles run.

### Dependencies
stdlib argparse/os/sys/tempfile/traceback/pathlib; app: `app.auth.create_user.upsert_user`,
`app.core.db.session.unit_of_work`, `app.core.config.settings.get_settings`, `app.cycle.loader`,
`app.cycle.scope`, `app.domain.bid.template_generator`, `app.pilot.service.PilotService`,
`app.pilot.synthetic`; **scripts**: `scripts.potato_legacy_dryrun` (FILE 1). sqlalchemy.text.

---

# ============================================================================
# FILE 19 — `docker-compose.yml`  (repo root)
# ============================================================================

**Path:** `/home/user/KR_RFP/docker-compose.yml` · `.yml` · 133 lines / 5556 B · census row 253.
(Distinct from `infra/docker-compose.yml`, census row 334 — a different, smaller compose in another
slice.)

## WHAT / WHY
Full-stack LOCAL verification of the Cloud Run deployment shape — postgres + backend + frontend wired
exactly as the two Cloud Run services will be, on one machine. **WHY:** the de-risk harness for
`deploy/gcp/` — prove the container shape comes up green (postgres healthy → migrations applied →
backend /ready → frontend HTML → seed runs) before deploying. Header (1–11) documents the up/seed/down
commands and that it's a DEV convenience (well-known local DB password, AUTH_COOKIE_SECURE off — plain
http on localhost; Cloud Run uses Secret Manager + HTTPS). `name: kr-rfp` (12).

### Services
- **`db`** (16–31): `postgres:15`, env POSTGRES_USER/PASSWORD/DB (defaults kr_rfp), port 5432, volume
  `db_data`, healthcheck `pg_isready`. **WHY:** the governed system of record.
- **`migrate`** (36–49): builds the backend image (context `.` = repo root, dockerfile
  `backend/Dockerfile` — the repo-root context note 38–41 mirrors FILE 12), `command: ["alembic",
  "upgrade", "head"]`, DATABASE_URL/ENV env, `depends_on db service_healthy`, `restart: "no"`. **WHY:**
  one-shot migration decoupled from serving (Cloud Run runs migrations as a separate job too); the
  backend waits for it via `service_completed_successfully`.
- **`backend`** (52–83): builds the backend image (repo-root context), env DATABASE_URL/ENV/
  CORS_ALLOW_ORIGINS(default http://localhost:3000)/AUTH_COOKIE_SECURE(default false — the comment
  62–64 explains a Secure cookie is silently dropped over plain http, so login would "succeed" with no
  session)/AUTH_SECRET_KEY(throwaway local default)/PORT=8000; `depends_on` db healthy + migrate
  completed; port 8000; healthcheck hits `/api/v1/ready` over loopback via python urllib (no curl in
  the image, 76–79). **WHY:** the API service, gated on a healthy DB + completed migration.
- **`frontend`** (86–108): builds `./frontend` Dockerfile with build-arg
  `NEXT_PUBLIC_API_BASE_URL` (default http://localhost:8000 — the comment 91–93 notes the BROWSER
  talks to the backend on the HOST, not the compose-internal name, since it runs outside the compose
  network); env PORT=3000; `depends_on backend service_healthy`; port 3000; healthcheck hits
  `/login` via node http (102–104). **WHY:** the frontend service wired to the backend exactly as in
  the cloud.
- **`seed`** (112–130): builds the backend image, `command: ["python", "/app/deploy/gcp/seed.py"]`,
  env DATABASE_URL/ENV/SEED_ADMIN_PASSWORD(default admin-local-dev-pw); `depends_on` db healthy +
  migrate completed; `restart: "no"`; **`profiles: [seed]`** (127–130) so it's kept OUT of `up` (it's
  a job, not a long-running service) and started explicitly via `docker compose run --rm seed`.
  **WHY:** seed admin + TOMATO + POTATO on demand, same image/DB as backend, commits its work.
- **`volumes: db_data`** (132–133).

### Edge cases / WHY notes
- The migrate→backend ordering uses `service_completed_successfully` (the backend won't serve until
  the migration job exits 0). The seed shares that gate. AUTH_COOKIE_SECURE=false and the local DB
  password are the ONLY intentional differences from prod (also noted in the README §7). Everything
  has a healthcheck with retries so `up` blocks until green. Consistent with deploy.sh's cloud shape.

---

# ============================================================================
# FILE 20 — `.github/workflows/ci.yml`
# ============================================================================

**Path:** `/home/user/KR_RFP/.github/workflows/ci.yml` · `.yml` · 223 lines / 9071 B · census row 5.

## WHAT / WHY
The program's non-negotiables encoded as CI. ONE workflow; independent jobs run in parallel and fan
into a single required `ci-pass` status (the only check branch protection needs). **WHY:** enforce the
gates (lint, types, clean-room boundary, real-Postgres tests, migration round-trip, frontend) on every
PR so drift can't merge; the single fan-in status keeps branch protection simple.

### Triggers + env + concurrency (11–25)
`on: pull_request [main]` + `push [main]` (PR runs the full gate; push to main runs the gate plus —
when DEP-4 lands — image build-push + deploy-to-staging, see the bottom stanza). env PYTHON 3.12 /
NODE 20 (ADR-0002). concurrency group `ci-${{github.ref}}` cancel-in-progress (save minutes).

### Jobs (each with WHY)
1. **`lint`** (29–42): ruff check + ruff format --check on backend/. Fast, no DB.
2. **`types`** (45–59): mypy on the app package, **run from `backend/`** so it finds pyproject's
   pydantic plugin + import overrides (the comment 56–57 notes the repo-root config isn't picked up).
3. **`reference-guard`** (63–76): runs `tests/test_cleanroom_import.py` — FAILS the build if `backend/`
   imports `reference/` (ADR-0001 clean-room invariant, a program non-negotiable). **WHY:** this is the
   boundary FILE 1 respects (imports app.*, not reference.*).
4. **`test`** (79–112): real **postgres:15** service container; install backend[dev]; `alembic upgrade
   head` (executes db/baseline/schema.sql); `pytest -v -m "" --cov=app` — `-m ""` runs ALL markers incl.
   integration; NO SQLite anywhere (architecture §7). **WHY:** the full suite against a real Postgres.
5. **`migration-roundtrip`** (118–150): fresh postgres:15; upgrade head; then
   `tests/test_migrations_roundtrip.py` drives down→up and asserts the schema is clean/unchanged (the
   byte-identical dump compare + alembic-check drift + ≥46-composite-FK floor live inside that test).
   **WHY:** migrations must round-trip cleanly (WAYS-OF-WORKING §3).
6. **`frontend-build`** (155–180): **path-filtered** (dorny/paths-filter on `frontend/**`); if changed:
   setup-node, `npm install` (no lockfile yet — `npm ci` at Phase F), `npm run typecheck`. If frontend
   unchanged, every step is skipped (a no-op, green). **WHY:** lightweight this phase (ADR-0002).
7. **`ci-pass`** (183–209): `if: always()`, `needs` all six. Asserts each required job result ==
   `success`; a **skipped** frontend-build (path filter) is acceptable (205–208). **WHY:** the single
   required status; goes red if any needed job failed.

### Branches / edge cases
- `frontend-build` skipped when no frontend changes → `ci-pass` treats skipped as OK (only required
  jobs must be `success`). `concurrency cancel-in-progress` cancels superseded runs. `-m ""` (line 112)
  is the deliberate "run integration too" knob.

### Main-only continuation (211–223, COMMENTED OUT — not yet authored)
On push to main, gated on ci-pass, the pipeline would ALSO `build-push` (immutable image tagged :<sha>
+ :main) and `deploy-staging` (deploy digest, gated migrations, smoke), with prod a manual
workflow_dispatch promotion behind environment approval. **NOT authored** because the
cloud/registry/secret-store fork on **DEP-4** (sponsor). **⚠️ Flag:** this is a documented
"phase-later" deferral. It is a CI continuation gated on an external dependency (DEP-4), not a product
stub — but per CLAUDE.md §1 (NO phase-later shortcuts) it is worth surfacing that the build-push +
deploy-staging legs of CI are deferred-and-commented, even though `deploy/gcp/deploy.sh` (FILE 17)
already implements the equivalent manual deploy. The two are NOT yet wired together (manual deploy
exists; automated main→staging deploy does not).

---

## CROSS-SLICE / DECISION-POINT INDEX (Layer-2)

| Decision / ADR | Enforced where (this slice) | Status |
|---|---|---|
| **D45** (data fidelity = NO-MVP; the 5 named shortcuts) | FILE 1 lines 350–353 (S1), 321–323 (S2), 99–114/451 (S3), 460 (S4), 145–154/597–611 (S5); committed to prod via FILE 18 `seed_potato` | **VIOLATED — live** |
| D19 (NO MVP / full capability) | FILE 4 demonstrates full loop; FILE 1 violates via shortcuts | partial |
| D21 (key-validated owned bid template) | FILE 4 `ingest_and_persist`; FILE 1 `fill_bid_template` keeps keys | enforced |
| D22 / ADR-0006 (award→freeze→sign-off before booking output; decision-support recommends, doesn't assert) | FILE 4 `select_award_from_scenario` (gate NOTED, awd.* deferred); FILE 18 `freeze_award` (real freeze) | enforced (demo notes gate; seed freezes) |
| D23 (names display, keys join) | FILE 4 RECOMMENDATION.md render; FILE 7 output | enforced |
| D11 (iTrade routing baseline) | FILE 4 perf.historical_awarded_price_basis seed | enforced |
| D18 (strategy-agnostic config) | FILE 4 EngineConfig; FILE 1 LegacyConfig from CONFIG sheet | enforced |
| ADR-0001 (clean-room: backend ⊁ reference) | FILE 1 imports app.* not reference.* (reads a reference *file* only); CI reference-guard (FILE 20 job 3) | enforced |
| ADR-0017 (GCP Cloud Run + Cloud SQL) | FILES 16/17/19 | enforced |
| ADR-0018 / D40 / D41 (stateless, no server-side files) | FILE 12 header; FILE 17 socket DATABASE_URL; FILE 18 persist_outputs=False; FILE 19 | enforced |
| ADR-0002 (Python 3.12 / Node 20; frontend lightweight this phase) | FILE 11; FILE 20 env + frontend-build | enforced |
| Schema CHECKs forcing FILE 1's shortcuts | `ck_cycle_round_count_range BETWEEN 2 AND 6` (S1), `ck_bid_all_in_positive`/`ck_bid_fob_positive` (S5), `REGIONS` closed set (S3) — all verified in db/baseline/schema.sql + app/pilot/setup_template.py | confirmed |

---

## GAPS / DRIFT / OPEN ITEMS (read-only findings)

1. **D45 — FILE 1 is a live, unremediated data-fidelity violation** (all 5 shortcuts mapped above with
   file:line + faithful behavior). It is NOT confined to a throwaway dry-run: FILE 18 `seed_potato`
   commits its converter output to the deployed DB, so the shortcuts materialize the POTATO cycle the
   console shows.
2. **FILE 1 docstring drift:** line 39 claims it "leaves a (real) cycle in the DB" but `main()` rolls
   back (line 797). The rollback is the truth.
3. **FILE 1 `weight_preset` is HARDCODED** "balanced" (line 221), not parsed from CONFIG — a 6th,
   smaller assumption beyond the 5 named shortcuts (the CONFIG active weights are asserted to equal the
   Balanced preset, not verified at runtime).
4. **FILE 14 (backend/README.md) is stale** in three places: domain/api described as "present-but-empty
   stubs" (lines 13–16, contradicted by the populated app.domain.* this slice imports); "Docker
   (migrates then serves)" (line 34) is wrong — the Dockerfile CMD only serves, migrations are
   out-of-band; references `.env.example` (line 24) and `architecture/SKELETON.md` (line 4) to confirm
   in R1/other slices.
5. **FILE 17 (deploy.sh) header drift:** references a `--seed` flag (line 27) that doesn't exist (only
   `--no-seed`/`--print-urls`). Also lines 281–284 carry stream-of-consciousness comment cruft.
6. **FILE 13 (.dockerignore) build-context subtlety:** it lives in `backend/` but the image builds from
   the REPO ROOT, so Docker honors the *context-root* `.dockerignore` (repo root), not this one. Its
   exclusions only apply to a `backend/`-context build. Whether a repo-root `.dockerignore` exists is
   R1's scope to confirm — flag as potential drift (the documented exclusions may not be the ones
   actually honored).
7. **FILE 20 (ci.yml) deferred legs:** the main→build-push→deploy-staging continuation is commented out
   pending DEP-4. A documented phase-later deferral (gated on an external sponsor dependency); the
   manual equivalent exists in deploy.sh but is not wired into CI.
8. **FILES 7–10 are generated artifacts checked into the repo** (demo/output/*). They're excluded from
   the image (.dockerignore line 25) and regenerated by FILE 4; kept in-repo for reviewer convenience.
   Not a violation (synthetic), but worth noting they can go stale vs the current engine if not
   regenerated.
9. **The two `.pyc` files** (FILES 2, 5, 6) are byte-compiled caches in the census's `__pycache__`
   vendored/generated bulk (4671 files) — accounted for, not per-file audited (not authored source).
   Listed here so the slice has no silent skip.

— END SLICE B9 —
