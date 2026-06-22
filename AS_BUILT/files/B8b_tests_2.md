---
doc: AS-BUILT AUDIT — SLICE B8b — backend/tests/** NOT covered by B8a
id: ASBUILT-B8b
layer: 2 (Code · Process · Decision-points) — applied to the test suite
contract: /CLAUDE.md (ABSOLUTE REQUIREMENTS injected); standard: /AS_BUILT/AUDIT_STANDARD.md
status: COMPLETE
scope: every backend/tests file outside tests/api/**, tests/pilot/**, and the root tests/conftest.py
  (those three are B8a). Together B8a ∪ B8b = ALL 65 test files (.py + .json), no overlap, no gap.
method: each file read end-to-end. Per file: path · ext · empty? · what · DETAILED WHY (the contract
  it guards) · EVERY test function with its assertions, setup, and the requirement/decision it protects.
  Engine/formula/capacity tests pin exact expected numbers verbatim.
---

# SLICE B8b — Tests outside B8a (engine, output, domain, core/audit, fiscal, comms, integration, mcp, ref)

## Scope boundary & union proof (B8a ∪ B8b = all files)

`find backend/tests -type f` (excluding `__pycache__/*.pyc`) yields **65 owned files** (63 `.py`,
1 `.json` golden-expectations, plus the per-package `__init__.py` markers). The split:

- **B8a owns** (NOT audited here): `tests/api/**` (12 files: `__init__.py`, `conftest.py`,
  `test_alignment.py`, `test_auth.py`, `test_bids.py`, `test_comms.py`, `test_cors.py`,
  `test_downloads.py`, `test_finalize.py`, `test_post_award.py`, `test_runs.py`, `test_strategy.py`,
  `test_version_save.py` — 13 entries incl. `__init__`), `tests/pilot/**` (8 files: `__init__.py`,
  `test_deliverables.py`, `test_pilot_cycle_e2e.py`, `test_pilot_setup.py`, `test_run_isolation.py`,
  `test_run_persistence.py`, `test_run_repo.py`, `test_vault_autopush.py`), and the **root
  `tests/conftest.py`**. (The "auth" scope named in the B8a brief is `tests/api/test_auth.py`; there
  is no separate `tests/auth/` directory.)
- **B8b owns** (this document): everything else —
  - root: `tests/__init__.py`, `test_cleanroom_import.py`, `test_health.py`,
    `test_migrations_roundtrip.py`, `test_tenant_isolation.py`
  - `tests/audit/**` — `__init__.py`, `test_commodity_client_backfill.py`, `test_decision_events.py`
  - `tests/awd/**` — `__init__.py`, `test_award_read.py`, `test_post_award_versioning.py`
  - `tests/bid/**` — `__init__.py`, `synthetic.py`, `test_capacity_persist.py`,
    `test_capacity_round_trip.py`, `test_completeness_and_guards.py`, `test_legacy_resilience.py`,
    `test_period_fanout.py`, `test_period_import.py`, `test_round_trip.py`
  - `tests/comms/**` — `__init__.py`, `test_formulas.py`, `test_merge.py`, `test_render.py`
  - `tests/engine/**` — `__init__.py`, `golden_expectations.json`, `golden_fixture.py`,
    `test_engine_golden.py`, `test_engine_invariants.py`, `test_engine_single_round.py`,
    `test_engine_stub.py`, `test_formulas.py`, `test_input_manifest.py`, `test_runner_incumbent.py`
  - `tests/fiscal/**` — `__init__.py`, `test_calendar.py`
  - `tests/mcp/**` — `__init__.py`, `test_server_imports.py`
  - `tests/output/**` — `__init__.py`, `test_capacity_check.py`, `test_capacity_tab.py`,
    `test_line_price.py`
  - `tests/ref/**` — `__init__.py`, `test_fiscal_period_table.py`

**Union check:** B8a (13 api entries + 8 pilot + 1 root conftest = 22) + B8b (43 entries enumerated
below) = **65**. No file appears in both; no file is unaccounted for. `__pycache__/*.pyc` are
vendored/generated build caches (counted, not per-file audited — same rule as the `FILE_CENSUS`).

---

## B8b file census (with dates/sizes)

| # | path (relative to backend/tests/) | ext | empty? | lines | bytes | created | modified |
|---|---|---|---|---|---|---|---|
| 1 | `__init__.py` | py | YES (0B) | 0 | 0 | 2026-06-18 | 2026-06-18 |
| 2 | `test_cleanroom_import.py` | py | no | 63 | 2321 | 2026-06-18 | 2026-06-18 |
| 3 | `test_health.py` | py | no | 32 | 900 | 2026-06-18 | 2026-06-18 |
| 4 | `test_migrations_roundtrip.py` | py | no | 56 | 1944 | 2026-06-21 | 2026-06-21 |
| 5 | `test_tenant_isolation.py` | py | no | 47 | 1761 | 2026-06-18 | 2026-06-18 |
| 6 | `audit/__init__.py` | py | YES (0B) | 0 | 0 | 2026-06-21 | 2026-06-21 |
| 7 | `audit/test_commodity_client_backfill.py` | py | no | 67 | 3024 | 2026-06-21 | 2026-06-21 |
| 8 | `audit/test_decision_events.py` | py | no | 286 | 12443 | 2026-06-21 | 2026-06-21 |
| 9 | `awd/__init__.py` | py | no (docstring) | 1 | 84 | 2026-06-19 | 2026-06-19 |
| 10 | `awd/test_award_read.py` | py | no | 110 | 5112 | 2026-06-21 | 2026-06-21 |
| 11 | `awd/test_post_award_versioning.py` | py | no | 383 | 14159 | 2026-06-21 | 2026-06-21 |
| 12 | `bid/__init__.py` | py | no (docstring) | 1 | 94 | 2026-06-19 | 2026-06-19 |
| 13 | `bid/synthetic.py` | py | no | 80 | 3136 | 2026-06-19 | 2026-06-19 |
| 14 | `bid/test_capacity_persist.py` | py | no | 234 | 9925 | 2026-06-21 | 2026-06-21 |
| 15 | `bid/test_capacity_round_trip.py` | py | no | 166 | 6505 | 2026-06-21 | 2026-06-21 |
| 16 | `bid/test_completeness_and_guards.py` | py | no | 130 | 5619 | 2026-06-19 | 2026-06-20 |
| 17 | `bid/test_legacy_resilience.py` | py | no | 172 | 5713 | 2026-06-19 | 2026-06-19 |
| 18 | `bid/test_period_fanout.py` | py | no | 109 | 3933 | 2026-06-20 | 2026-06-20 |
| 19 | `bid/test_period_import.py` | py | no | 504 | 25300 | 2026-06-21 | 2026-06-21 |
| 20 | `bid/test_round_trip.py` | py | no | 305 | 12456 | 2026-06-20 | 2026-06-20 |
| 21 | `comms/__init__.py` | py | YES (0B) | 0 | 0 | 2026-06-21 | 2026-06-21 |
| 22 | `comms/test_formulas.py` | py | no | 81 | 3082 | 2026-06-21 | 2026-06-21 |
| 23 | `comms/test_merge.py` | py | no | 70 | 2512 | 2026-06-21 | 2026-06-21 |
| 24 | `comms/test_render.py` | py | no | 117 | 4302 | 2026-06-21 | 2026-06-21 |
| 25 | `engine/__init__.py` | py | YES (0B) | 0 | 0 | 2026-06-18 | 2026-06-18 |
| 26 | `engine/golden_expectations.json` | json | no | 102 | 6520 | 2026-06-19 | 2026-06-19 |
| 27 | `engine/golden_fixture.py` | py | no | 283 | 11845 | 2026-06-19 | 2026-06-20 |
| 28 | `engine/test_engine_golden.py` | py | no | 295 | 12373 | 2026-06-20 | 2026-06-20 |
| 29 | `engine/test_engine_invariants.py` | py | no | 114 | 4301 | 2026-06-19 | 2026-06-19 |
| 30 | `engine/test_engine_single_round.py` | py | no | 58 | 2597 | 2026-06-19 | 2026-06-19 |
| 31 | `engine/test_engine_stub.py` | py | no | 115 | 4212 | 2026-06-19 | 2026-06-19 |
| 32 | `engine/test_formulas.py` | py | no | 85 | 2953 | 2026-06-21 | 2026-06-21 |
| 33 | `engine/test_input_manifest.py` | py | no | 45 | 1861 | 2026-06-22 | 2026-06-22 |
| 34 | `engine/test_runner_incumbent.py` | py | no | 61 | 2350 | 2026-06-20 | 2026-06-20 |
| 35 | `fiscal/__init__.py` | py | YES (0B) | 0 | 0 | 2026-06-20 | 2026-06-20 |
| 36 | `fiscal/test_calendar.py` | py | no | 116 | 4343 | 2026-06-20 | 2026-06-20 |
| 37 | `mcp/__init__.py` | py | YES (0B) | 0 | 0 | 2026-06-19 | 2026-06-19 |
| 38 | `mcp/test_server_imports.py` | py | no | 51 | 1491 | 2026-06-19 | 2026-06-19 |
| 39 | `output/__init__.py` | py | YES (0B) | 0 | 0 | 2026-06-21 | 2026-06-21 |
| 40 | `output/test_capacity_check.py` | py | no | 96 | 3692 | 2026-06-21 | 2026-06-21 |
| 41 | `output/test_capacity_tab.py` | py | no | 71 | 2400 | 2026-06-21 | 2026-06-21 |
| 42 | `output/test_line_price.py` | py | no | 40 | 1626 | 2026-06-21 | 2026-06-21 |
| 43 | `ref/__init__.py` | py | no (docstring) | 1 | 97 | 2026-06-20 | 2026-06-20 |
| 44 | `ref/test_fiscal_period_table.py` | py | no | 57 | 2348 | 2026-06-20 | 2026-06-20 |

**Empty files (8):** `__init__.py` (root), `audit/__init__.py`, `comms/__init__.py`,
`engine/__init__.py`, `fiscal/__init__.py`, `mcp/__init__.py`, `output/__init__.py` are all 0-byte
package markers. **WHY empty:** Python requires an `__init__.py` to make a directory an importable
package; pytest's import-mode and the `tests.<pkg>.<mod>` cross-imports (e.g.
`from tests.pilot.test_pilot_cycle_e2e import ...`) depend on these markers existing. They carry no
code because the test packages need no package-level setup; emptiness is correct, not a stub.
The non-empty `__init__.py` files (`awd`, `bid`, `ref`) hold only a one-line module docstring naming
the package's purpose (no executable code).

---

# ROOT-LEVEL TESTS

## 2. `test_cleanroom_import.py` · py · not empty · 63 lines

**WHAT:** A pure AST-walk guard (no DB, no app import — stdlib only) that proves `backend/` never
imports the `reference/` package.
**WHY (contract guarded):** ADR-0001 / security PLAN §5 / S14 — the clean-room boundary. `reference/`
is an INPUT-ONLY quarantine (the legacy v3 spreadsheet logic + real data); production `backend/` code
must never import it, or the clean-room separation that lets us commit synthetic-only artifacts
collapses. Runs in CI's lint stage (no Postgres), so it gates from day one.
Module constants: `BACKEND_ROOT = Path(__file__).parents[1]`, `SCAN_ROOTS = [app, alembic]`,
`FORBIDDEN_TOP = "reference"`. `_python_files()` rglobs `*.py` under the two roots. `_imports_reference(tree)`
walks the AST: an `ast.Import` whose alias name == `reference` or starts `reference.` → True; an
`ast.ImportFrom` at `level==0` (absolute) whose module == `reference`/`reference.*` → True (relative
imports `level>0` are explicitly exempted — they can never reach `reference`).

- **`test_backend_never_imports_reference()`** — parses every `app`/`alembic` Python file; collects
  any whose AST trips `_imports_reference` into `offenders`; asserts `not offenders` with a message
  naming the offending files. **Protects:** the clean-room import ban, file-by-file.
- **`test_scan_actually_found_files()`** — "guard the guard": asserts `_python_files()` is non-empty,
  so a broken `SCAN_ROOTS` can't make the ban vacuously pass. **Protects:** test integrity (no silent
  no-op).

## 3. `test_health.py` · py · not empty · 32 lines

**WHAT:** Boot smoke test via FastAPI `TestClient(app)`. `PREFIX = get_settings().api_v1_prefix`.
**WHY:** SKELETON liveness/readiness contract — proves the app process boots and the two ops probes
answer. Liveness must need no DB (so it's green from day one); readiness touches the store (integration).

- **`test_health_is_green()`** — GET `{PREFIX}/health` → status 200 and JSON exactly `{"status":"ok"}`.
  **Protects:** liveness probe contract; the app imports and routes without a database.
- **`test_ready_checks_the_store()`** (`@pytest.mark.integration`) — GET `{PREFIX}/ready` → 200 and
  `{"status":"ready"}`. **Protects:** readiness probe returns ready when the store is reachable.

## 4. `test_migrations_roundtrip.py` · py · not empty · 56 lines

**WHAT:** Alembic up→down→up round-trip against the real Postgres, driven programmatically via the
`command` API (`pytestmark = integration`). `_alembic_config(url)` builds a `Config("alembic.ini")`
with the test DB URL.
**WHY:** PLAN §7 / SKELETON R8 — every migration must be reversible (kills the SQLite-ism risk and any
non-reversible DDL). Imports `SCHEMAS` from `app.core.db.base` (the spine schemas) and hard-codes
`non_spine = {"auth", "pilot"}` (hand-written migrations: auth identity, ADR-0018 Slice 2 `pilot.run`).

- **`test_migrations_roundtrip(engine, database_url)`** — helper `schemas_present()` reads
  `information_schema.schemata`. Sequence: downgrade `base` (floor) → upgrade `head` → assert
  `SCHEMAS ⊆ present` AND `{auth,pilot} ⊆ present`; downgrade `base` → assert NONE of `SCHEMAS` and
  none of `{auth,pilot}` remain ("schemas should be gone after downgrade base"); upgrade `head` again
  → assert both sets present once more. **Protects:** full reversibility of all 20 migrations incl. the
  non-spine hand-written ones; idempotent re-upgrade.

## 5. `test_tenant_isolation.py` · py · not empty · 47 lines

**WHAT:** Application-layer tenant scoping via `CommodityRepository` (`pytestmark = integration`).
**WHY:** security PLAN §1 / S7 — defence-in-depth: a tenant-scoped repository must never return another
tenant's rows (the RLS DB backstop, Platform & Data M10, is tested separately). Uses `seed_tenants`
fixture (tenants "a"/"b") and `Commodity` ORM.

- **`test_scoped_read_returns_only_own_tenant(db_session, seed_tenants)`** — seeds Commodity rows:
  tenant A `APPLE`; tenant B `APPLE` + `ONION`. Builds `CommodityRepository(session, tenant_a/b)`.
  Asserts `repo_a.list()` codes == `{APPLE}`, `repo_b.list()` == `{APPLE, ONION}`. Cross-tenant:
  `repo_a.get_by_code("ONION") is None` (B's code invisible to A); `repo_a.get_by_code("APPLE")` returns
  A's row (`client_id == tenant_a`), NOT B's same-coded row. **Protects:** the scoped repository's WHERE
  client_id filter on `list` and `get_by_code` — no cross-tenant leak even on a shared code.

---

# tests/audit/ — the hash-chained decision-event ledger (Gap G-B)

## 6. `audit/__init__.py` · py · EMPTY (0B) — package marker (see empty-files note).

## 7. `audit/test_commodity_client_backfill.py` · py · not empty · 67 lines

**WHAT:** Migration-0018 backfill semantics, tested with raw SQL that **mirrors** the migration (the
test re-declares `_INSERT_LEGACY_CLIENTS` and `_ADOPT_ORPHANS` SQL because migrations can't be imported
as app code — the two are intentionally kept in sync).
**WHY:** Before G-B, setup ingest left `ref.commodity.client_id` NULL; the now-mandatory audit resolver
(`app/core/audit/recorder.py`, joining `cyc.cycle → ref.commodity.client_id`) strands such runs. 0018
adopts orphaned commodities into a per-row legacy tenant. The danger: two orphans sharing a
`commodity_code` are legal pre-migration (NULL client makes `uq_commodity_code_per_client` distinct),
but a single shared sentinel client on backfill would violate that unique and abort the upgrade — so
each orphan must get its OWN deterministic client (`md5('legacy-client:'||c.id)`).
Helper `_client_of(session, commodity_id)` reads `client_id` for a commodity.

- **`test_backfill_adopts_orphans_with_a_distinct_client_per_duplicate_code(db_session)`**
  (`@integration`) — inserts two commodities `com_a`, `com_b` with the SAME random `commodity_code` and
  `client_id NULL`; asserts `_client_of(com_a) is None` pre-backfill (orphaned). Runs the two backfill
  SQL statements; asserts both now have a non-NULL `client_id` (resolver's JOIN resolves) AND
  `client_a != client_b` (distinct per-row clients → the unique is never violated, upgrade can't abort).
  **Protects:** the 0018 backfill's per-orphan-client design; the audit resolver's tenant chain.

## 8. `audit/test_decision_events.py` · py · not empty · 286 lines

**WHAT:** Drives the REAL pilot loop (same path + synthetic builders as
`tests/pilot/test_pilot_cycle_e2e.py`, imported: `_build_filled_setup`, `_fill_bid_template`,
`_first_award_cell`, `_latest_run_id`) and asserts the hash-chained `audit.event_log`. All
DB-touching, `@integration`. Synthetic only (ADR-0001).
**WHY (contract guarded):** Gap G-B — every governed decision must append a tamper-evident
`audit.event_log` row IN THE SAME TRANSACTION as the decision (atomic, hash-chained, contiguous seq).
Imports `DomainEvent`, `EventType`, `client_id_for_cycle`, `AuditWriter`, `compute_event_hash`.
Helper `_events_for_client(session, client_id)` returns all event rows for a tenant in seq order as
dicts (seq, event_type, entity_type, entity_id, actor, occurred_at, before/after_state_hash,
prev_event_hash, event_hash). Helper `_drive_full_run(service, session, tmp_path)` runs the whole
synthetic loop: `start_run` → write setup → `ingest_setup` → `generate_bid_template` → `_fill_bid_template`
→ `ingest_bids` → `run_round` → `_latest_run_id` → `freeze_award(scenario_code="B", award_code="AWD-AUDIT-1")`
→ `_first_award_cell` → `record_adjustment(NEGOTIATED_REPRICE, frozen_price − Decimal("0.25"))`.

- **`test_full_run_emits_decision_events(tmp_path, db_session)`** — after a full run, buckets events
  by type. Asserts the four governed decisions each emitted: `IMPORTED` (ingest), `SEALED` (run_round),
  `FROZEN` (freeze), `CREATED` (adjustment). Asserts entity_types: every IMPORTED →
  `"bid.bid_submission"`; SEALED[0] → `"eng.analysis_run"`; FROZEN[0] → `"awd.award"`; CREATED[0] →
  `"awd.award_adjustment"`. **Pins:** exactly **2 IMPORTED events** (two suppliers ingested in the round).
  **Protects:** decision→event coverage + correct entity tagging.
- **`test_chain_is_contiguous_and_tamper_evident(tmp_path, db_session)`** — asserts ≥4 events; seq is
  exactly `1..N` contiguous; genesis `prev = "0"*64`; for each event `prev_event_hash == prev`, and
  **recomputing `compute_event_hash` from the stored fields reproduces the stored `event_hash`** (the
  test strips tz from `occurred_at` since the DB returns UTC-aware but the writer hashed naive). Walks
  `prev = event_hash` forward. **Protects:** hash-chain integrity / tamper-evidence — the cryptographic
  reproducibility guard on the audit ledger.
- **`test_resubmission_emits_superseded(tmp_path, db_session)`** — ingests bids twice for the same
  round; captures the first round's `bid_submission` ids; asserts SUPERSEDED events exist, their
  `entity_id`s are a subset of the FIRST submissions (point at the prior, not the new), and all carry
  entity_type `"bid.bid_submission"`. **Protects:** the supersession audit event on re-ingest (Option B).
- **`test_actor_threads_to_audit_events(tmp_path, db_session)`** — ingests + runs with
  `actor="alice@buyer.example"`; asserts every IMPORTED and the SEALED event records that actor (not the
  MCP "pilot"/"pilot-runner" fallback), AND `norm.source_artifact.created_by == {"alice@buyer.example"}`.
  **Protects:** the HTTP-authenticated user identity threading into the audit chain + source artifact.
- **`test_event_rides_caller_transaction_rollback(tmp_path, db_session)`** — appends a synthetic
  `DomainEvent(IMPORTED, ...)` onto a `begin_nested()` SAVEPOINT; flushes; asserts row count == before+1
  (visible); rolls the savepoint back; asserts count == before. **Protects:** atomicity — events ride the
  decision's unit of work, never auto-commit; a rolled-back decision drops its event.

---

# tests/awd/ — post-award freeze-and-layer versioning (ADR-0014)

## 9. `awd/__init__.py` · py · 1 line — docstring-only package marker
("Post-award (`awd`) tests — freeze-and-layer versioning + the versioned doc.")

## 10. `awd/test_award_read.py` · py · not empty · 110 lines (`@integration`)

**WHAT:** Drives the real PilotService pipeline (setup→bids→run_round→freeze_award), records an
adjustment layer, and asserts the post-award READ layer (`awd.read`) that the web console renders.
Imports `AwardLine`, `add_adjustment`; reuses `_fill_template_full_columns` (from
`tests/bid/test_period_import`) and `_build_filled_setup`.
**WHY:** The read views (`list_awards`, `award_detail`) must expose the frozen baseline, the effective
price + delta after layers, NAMES not keys (D23), the version history, and must be cross-run scoped.

- **`test_award_read_list_and_detail_reflect_layers(tmp_path, db_session)`** — runs a "Colored Potatoes"
  cycle, freezes scenario B as `AWD-READ-TEST`. Asserts `list_awards` returns exactly one summary with
  `award_id` match, `award_code == "AWD-READ-TEST"`, `scenario_code == "B"`, `line_count > 0`,
  `latest_version == 0` (baseline only). `award_detail`: all lines `delta == 0` and
  `effective_price == frozen_price`, all `line.dc` and `line.supplier` are names resolved (D23), versions
  == `[0]`, version 0 `adjustment_type == "FROZEN"`, `latest_version == 0`. Then records a +$5
  MARKET_HIKE on ONE cell via `add_adjustment(...)`; asserts `version_no == 1`. Re-reads: exactly one
  adjusted line with `delta ≈ +5.0` and `effective − frozen ≈ 5.0`, every other cell still 0; versions
  == `[0, 1]`, v1 `adjustment_type == "MARKET_HIKE"`, `latest_version == 1`, and `list_awards()[0]`
  advances to `latest_version == 1`. **Cross-run scoping:** a DIFFERENT run (own cycle) returns
  `list_awards == []` and `award_detail(other, award_id)` raises `ValueError` (clean 404, never a leak).
  **Protects:** the post-award read surface — baseline, layered effective price/delta, name resolution,
  history, and run isolation of award lookups.

## 11. `awd/test_post_award_versioning.py` · py · not empty · 383 lines (`@integration`)

**WHAT:** Synthetic-seeded freeze-and-layer test of `app.domain.awd.service` (`freeze_award`,
`add_adjustment`, `award_versions`, `effective_award`) + the versioned workbook
(`write_post_award_adjustments_xlsx`). `_seed_cycle_and_run(session)` inserts (by KEY, D21) a full
synthetic spine: `ref.client` + `ref.commodity` (the tenant chain the freeze/adjust audit resolves
through), `ref.dc` (Atlanta/Denver), `ref.supplier` (Fresh Valley Farms / Sunrise Produce Co),
`cyc.cycle` (subcommodity NULL so the composite FK is skipped), `cyc.cycle_round` (round 1, is_final),
`cyc.cycle_lot` (Strawberries Lot), `cyc.cycle_timeframe` (Spring Period, 13 weeks), a SEALED
`eng.analysis_run` (engine_version 'v3-test'), `eng.analysis_scenario` 'B', and two
`eng.analysis_scenario_award` cells: cell1 (Atlanta/sup1) share 0.6 @ **100.00**, cell2 (Denver/sup2)
share 0.4 @ **120.00**.
**WHY:** ADR-0014 — freeze produces an immutable baseline; adjustments are append-only versioned layers;
`version_no` increments; `effective_award` overlays layers (with `as_of_version` time-travel); freeze is
idempotent; the doc shows the explicit Version heading and resolved NAMES (D23).

- **`test_freeze_then_versioned_adjustments(db_session, tmp_path)`** — freezes scenario B → `award_id`
  (a str). **Idempotency:** re-freezing the same (cycle, run, scenario) returns the SAME `award_id`.
  Baseline `effective_award`: cell1 == `Decimal("100.000000")`, cell2 == `Decimal("120.000000")`.
  **v1** MARKET_HIKE on cell1 100→**108.00** → `version_no == 1`. **v2** TOLERANCE_BAND: cell1
  108→**112.00**, cell2 120→**118.00** → `version_no == 2`. `effective_award` (latest) overlays both:
  cell1 == `112.000000`, cell2 == `118.000000`. `effective_award(as_of_version=1)` reflects ONLY v1:
  cell1 == `108.000000`, cell2 still baseline `120.000000`. **Prior-price chaining:** the v2 cell1
  layer's `prior_price` is the v1 EFFECTIVE (`108.000000`) not the frozen baseline (100); `new_price`
  `112.000000`, `delta` `4.000000`. `award_versions` history == `[0, 1, 2]` with types
  `[FROZEN, MARKET_HIKE, TOLERANCE_BAND]` and `n_lines` `[2, 1, 2]`. **The doc (v2):** `Versions` sheet
  title cell == `"POST-AWARD ADJUSTMENTS — AWD-TEST-01"`, subtitle == `"Version 2 · as of 2026-05-01"`.
  `Current Effective Prices` tab contains the NAMES (Atlanta DC, Fresh Valley Farms, Strawberries Lot,
  Spring Period) and NOT the raw UUID keys (`dc1`/`sup1` absent). **The doc at as_of_version=1:**
  subtitle == `"Version 1 · as of 2026-04-01"`; `This Version's Changes` contains the dc1 name and the
  value `108.0`. **Protects:** the full ADR-0014 versioning math (overlay, time-travel, prior-price
  chaining), idempotent freeze, the version doc's heading + name resolution.
- **`test_deterministic_doc(db_session, tmp_path)`** — freezes `AWD-DET-01`, adds one MARKET_HIKE layer
  (cell1 → 105.00). `_body(path)` writes the doc and reads the `Current Effective Prices` content rows
  (cols 1–7, rows 6..end). Asserts two independent generations produce identical body rows. **Protects:**
  deterministic / byte-stable doc rendering (reproducibility of the post-award deliverable).

---

# tests/bid/ — bid intake (SYNTHETIC only; D20/D21 + fan-out + capacity)

## 12. `bid/__init__.py` · py · 1 line — docstring-only marker
("Bid intake module tests — SYNTHETIC data only (no real suppliers / prices / volumes).")

## 13. `bid/synthetic.py` · py · not empty · 80 lines — SHARED FIXTURE (no tests)

**WHAT:** The synthetic scope + resolver builders for the bid intake tests. 100% placeholder identity
tables: suppliers `SUP-1..3` (Acme/Bravo/Cresta), DCs `DC-1/2` (Atlanta/Memphis), lots `LOT-1/2`
(Grape/Roma), items `ITEM-1/2`, TFs `TF1/TF2`. `CYCLE_ID="cyc-syn-1"`, round `ROUND-R1`, tf `TFID-1`.
**WHY:** D21 — every grain carries a system-owned surrogate KEY ID; the generated template embeds the
keys and ingest validates them against the scope key set. The display labels are attributes used only
for the legacy name-resolver fallback + warn-only checks (ADR-0001 §4: no real data).
`build_resolver()` returns a `StubIdentityResolver` (label→id, normalized) — LEGACY-ONLY (used solely
by the legacy migration path; our template is key-validated, never name-resolved). `_scope_row(...)`
builds a `ScopeRow` (round_code R1, bid_type "Initial FOB", embedded ids + display labels).
`build_scope()` returns a `CycleScope`: 2 suppliers × 2 DCs × 2 lot/item pairs × 1 TF.

## 14. `bid/test_capacity_persist.py` · py · not empty · 234 lines (`@integration`)

**WHAT:** E-38 capacity PERSISTENCE — stands up a real cycle, generates the template, fills BOTH the
Bids and Capacity sheets, ingests, and asserts the stated ceilings land as CELL-scoped constraints under
a per-supplier statement that rides the supplier's own bid submission/artifact. Helpers: `_headers(ws)`,
`_fill(template, cap_fills)` (fills every Bids row All-In 20.0 / weekly 600 / total 7800 so each supplier
has a real submission; fills Capacity rows in `cap_fills` with `(max_weekly, max_total)`),
`_capacity_keys(template, offset)` (the embedded 6-tuple identity), `_distinct_cell_offsets(template, n)`
(picks n Capacity rows with DISTINCT supplier×dc×lot×tf cells), `_prepare_cycle(...)`.
**WHY:** A CELL constraint is per supplier×dc×lot×tf; a re-submission must SUPERSEDE the prior statement
so the cap check never reads stale data; the statement must ride the SAME submission/artifact chain.

- **`test_capacity_persisted_as_cell_constraints(tmp_path, db_session)`** — fills two DISTINCT cells:
  cell A `(weekly 500, total 6500)`, cell B `(total 7000 only)`. After ingest, reads
  `bid.capacity_constraint ⋈ bid.capacity_statement`: exactly **2** constraints. Cell A:
  `scope_type == "CELL"`, weekly `== 500.0`, period `== 6500.0`. Cell B: weekly `None`, period `7000.0`.
  Both statements `status == "SUBMITTED"`, non-NULL `submission_id` + `source_artifact_id`, and each
  statement rides the supplier's own `bid.bid_submission` (the shared FK chain — exactly 1 matching
  submission). **Protects:** capacity ceilings persist as CELL constraints on the supplier's submission.
- **`test_capacity_resubmit_supersedes_prior_statement(tmp_path, db_session)`** — first submission weekly
  500 on cell 0; re-submission weekly 900 on the same cell. Asserts the two statement statuses sorted ==
  `["SUBMITTED", "SUPERSEDED"]` (append-only, exactly one active). The ACTIVE statement's weekly ceiling
  `== 900.0`. **Protects:** supersession of capacity statements; the cap check filters superseded rows.
- **`test_load_active_capacity_reads_persisted_ceilings(tmp_path, db_session)`** — fills one cell
  `(500, 6500)`, ingests, calls `load_active_capacity(session, cycle_id)`; asserts the (supplier,dc,lot,tf)
  cell is present with `max_period_cases == 6500.0`, `max_weekly_cases == 500.0`. **Protects:** the reader
  the E-38b capacity tab depends on returns persisted CELL ceilings by cell.

## 15. `bid/test_capacity_round_trip.py` · py · not empty · 166 lines (PURE, no DB)

**WHAT:** E-38 capacity ROUND-TRIP — generate template → fill Capacity sheet → `ingest_capacity` by KEY.
Imports `QuarantineReason`, `ingest_capacity`, `generate_template_bytes`, capacity schema constants.
Uses `build_scope()`. Helper `_capacity_sheet(bytes)`, `_save(wb)`.
**WHY:** The Capacity sheet follows the same D21 discipline as Bids — embedded KEY IDs validated against
the scope, never name-resolved. Proves: generated sheet carries key+display+entry columns; filled cells
round-trip to the SAME identity with ceilings preserved; a blank max is NO statement (not a zero); a
tampered/missing/negative cell quarantines.

- **`test_generated_capacity_sheet_has_keys_and_entry_columns()`** — emitted headers == `CAPACITY_HEADERS`;
  every `CAPACITY_KEY_ID_COLUMNS` present; `MAX_WEEKLY_CASES` + `MAX_TOTAL_CASES` present; one capacity
  body row per distinct supplier×dc×lot×item×tf cell (round-independent). **Protects:** the capacity sheet
  shape + per-cell row count.
- **`test_capacity_round_trips_by_key_blank_is_not_zero()`** — fills row 1 `(weekly 500, total 6500,
  notes "firm")`, row 2 `(total 7000 only)`, rest blank. Asserts `quarantined == []`, exactly **2** lines
  (blanks are NOT zero ceilings). Line1 keys round-trip exactly to the captured `first_keys`,
  `cycle_id == scope.cycle_id`, the key-tuple ∈ `scope.capacity_key_set()`, `max_weekly == Decimal("500")`,
  `max_period == Decimal("6500")`, `notes == "firm"`. Line2: `max_weekly is None` (blank ≠ zero),
  `max_period == Decimal("7000")`. **Protects:** key round-trip + the blank-is-not-zero rule (data fidelity).
- **`test_tampered_capacity_key_quarantines_not_resolved()`** — fills total 6500, tampers ONLY the
  embedded `DC_ID` to `"DC-TAMPERED"` (the display DC Name stays valid + in scope). Asserts `lines == []`,
  one quarantine, reason `QuarantineReason.UNKNOWN_KEY`. **Protects:** D21 — tampered key fails, never
  silently re-resolved from the valid name.
- **`test_blank_capacity_key_quarantines_missing_key()`** — clears `SUPPLIER_ID` to `""`; asserts one
  quarantine, reason `MISSING_KEY`. **Protects:** missing key fails loud.
- **`test_negative_capacity_quarantines_bad_numeric()`** — sets `MAX_WEEKLY_CASES = -5`; asserts one
  quarantine, reason `BAD_NUMERIC`. **Protects:** negative ceilings quarantine (never load).

## 16. `bid/test_completeness_and_guards.py` · py · not empty · 130 lines (PURE)

**WHAT:** Completeness flags + the §7 double-subtract guard + quarantine-don't-guess. Imports
`Completeness`, `ParsedComponents`, `QuarantineReason`, `construct_price`, `ingest_template`. Helper
`_fill(template, filler)`.
**WHY:** A blank price is `no_bid` (placed in grain, flagged, NOT dropped); a partial price intent is
`incomplete`; All-In + a discount together is the double-subtract footgun → quarantine (never silently
recomputed); an attribute mismatch warns (D21).

- **`test_no_bid_and_incomplete_and_bid_flags()`** — row0 real All-In 100.00; row1 blank price/vol (keys
  intact) → `no_bid`; row2 volume 120 but no price → `incomplete`; rest All-In 100.00. Asserts
  `quarantined == []`, `no_bid_count == 1`, `incomplete_count == 1`, `bid_count == len(scope.rows) − 2`;
  the no_bid line is parsed but `landed_cost_per_case is None`. **Protects:** completeness classification
  (no_bid placed-not-dropped; incomplete flagged).
- **`test_double_subtract_blocked_and_quarantined()`** — row0 has BOTH All-In 95.00 AND Lot Discount 2.00.
  Asserts exactly one quarantine, reason `DOUBLE_SUBTRACT`; `bid_count == len(scope.rows) − 1`.
  **Protects:** §7 double-subtract guard — ambiguous row quarantined, the rest ingest cleanly.
- **`test_construct_price_guard_unit()`** — unit of `construct_price(ParsedComponents(...))`: All-In 95.00
  with no discount → `(95.00, "ALL_IN", None)`. All-In 95.00 + lot_discount 2.00 → `(None, None, err≠None)`
  (blocked). Fallback `(None, fob 90, +5 +3 −2)` → `(96.00, "COMPONENT_FALLBACK", None)`. **Protects:** the
  shared price-construction guard at the unit level — exact numbers `95.00`/`96.00`.
- **`test_unknown_supplier_name_warns_not_quarantined_d21()`** — overwrites one row's supplier display
  NAME to `"Unknown Vendor LLC"` (keys intact), prices all. Asserts `quarantined == []`,
  `len(lines) == len(scope.rows)`, exactly one `name_warning` on the `SUPPLIER` column with
  `found_name == "Unknown Vendor LLC"`. **Protects:** D21 — for OUR template an unknown NAME is a warn-only
  attribute mismatch (identity is the embedded key); the name-resolver quarantine survives only on legacy.

## 17. `bid/test_legacy_resilience.py` · py · not empty · 172 lines (PURE)

**WHAT:** Legacy-resilience proof. Builds OUR OWN synthetic legacy-shaped workbook (NOT the quarantined
real reference files) mimicking the reference reality: sheet `"6. Vol and Pricing Capability"`, header at
row 4 (NOT our row 2), reference column wording, a `No Bid` cell, an unmapped trailing column
("Distance (mi) to DC"). Runs `ingest_legacy(bytes, resolver, sheet_name, legacy_header_row)` with the
synthetic `build_resolver()`.
**WHY:** D20 — our owned template is the live contract; messy legacy shapes are migration-resilience proof
only. The adapter+ingester must map a legacy shape to the SAME `bid_line` grain or quarantine — never guess.

- **`test_legacy_shape_maps_to_same_grain_or_quarantines()`** — fixture rows: an All-In row (Acme/Atlanta/
  Grape, 100.00), a component-fallback row (Bravo/Memphis/Roma, FOB 90 + Del 5 + Veg 3 − LotDisc 2), a
  `No Bid` declined cell (Acme/Memphis/Roma), an unresolvable supplier ("Ghost Vendor Inc"). Asserts:
  exactly one quarantine, reason `UNRESOLVED_SUPPLIER`; **3** resolvable lines on the SAME grain as our
  owned template. The All-In row → `landed_cost_per_case == Decimal("100.00")`, `Completeness.BID`. The
  component row → `Decimal("96.00")` (90+5+3−2), `BID`. The `No Bid` cell → `Completeness.NO_BID`,
  `landed_cost_per_case is None` (NOT a zero price). **Protects:** the legacy adapter maps to the canonical
  grain, reconstructs the §7 sum from reference columns, flags No Bid, quarantines unresolvables — the
  data-fidelity/no-guess contract on the migration path.

## 18. `bid/test_period_fanout.py` · py · not empty · 109 lines (PURE)

**WHAT:** Pure tests for the intake fan-out (INTAKE §1a). Imports `FannedPrice`, `fan_out`, `fan_out_all`
from `app.domain.bid.period_fanout`, and `fiscal_quarters`/`fiscal_year_timeframe`/`group_periods` from
`app.fiscal.calendar`. Helper `_periods(records)`.
**WHY:** The flat-13 contract — a few timeframes priced once fan out to all 13 fiscal periods, each period
covered exactly once, payloads COPIED (not shared), overlaps rejected.

- **`test_full_year_fans_to_all_thirteen_periods_with_identical_payload()`** — a full-year timeframe with
  payload `{all_in_case: 12.34, volume: 1000}` fans to periods `1..13`, all `fiscal_year == 2026`, every
  record's payload `== payload`. **Protects:** full-year → 13 periods, payload preserved.
- **`test_buyer_example_grouping_maps_each_span_to_its_payload()`** — buyer grouping P1-2/P3-9/P10-13 (A/B/C)
  via `group_periods`; `fan_out_all` over `(tf, payload)` pairs. Asserts all 13 periods appear once;
  periods 1-2 carry A, 3-9 carry B, 10-13 carry C. **Protects:** per-span payload mapping with no gap/overlap.
- **`test_fiscal_quarters_fan_to_4_3_3_3()`** — fans the 4 fiscal quarters; asserts **4+3+3+3 = 13** fanned
  rows covering every period once, and per-period quarter membership: P1-4 → Q1, P5-7 → Q2, P8-10 → Q3,
  P11-13 → Q4, each with its quarter payload. **Protects:** the fixed 4-3-3-3 quarter split + payload routing.
- **`test_fan_out_all_rejects_overlapping_timeframes()`** — two timeframes both covering P5-7 → raises
  `ValueError` matching `"more than one timeframe"`. **Protects:** overlap rejection (no double-cover).
- **`test_payload_is_copied_not_shared()`** — mutates one fanned record's payload `price=999`; asserts the
  sibling stays `1` and the original `payload["price"]` stays `1`. **Protects:** payloads are deep-copied
  per period (no aliasing — a later edit to one period can't corrupt the others).

## 19. `bid/test_period_import.py` · py · not empty · 504 lines (`@integration`) — THE FLAT-13 STORAGE GUARD

**WHAT:** End-to-end proof on real Postgres that intake stores bids FLAT at the 13 fiscal periods while
the engine/awards stay at timeframe grain (INTAKE §1a). Uses the potato sample when present (real prices,
git-ignored) and falls back to synthetic prices otherwise (CI-safe). `_POTATO_SAMPLE` points at
`reference/samples/potato_2026_rfp_input.xlsx`. `_CARRIED_COLUMNS` = the 9 price/volume/meta columns that
must survive the fan-out verbatim. `_CELL_KEY_COLUMNS` = `(supplier_id, dc_id, lot_id, item_id, tf_id)`.
Helpers: `_potato_price_pool()` (≤64 (all_in, fob) pairs from `IN_Bids`), `_header_map(ws)`,
`_fill_template_full_columns(bytes, pool)` (alternates All-In basis even rows / component basis odd rows,
volume on every row), `_fill_all_in(bytes, all_in)` (constant All-In marker for the supersession scan),
`_expected_span(session, cycle_id)` (the period numbers each tf's stored dates cover via `period_for_date`).
**WHY (contract guarded):** The hard invariant — period-grain STORAGE must not change the engine's inputs,
scores, scenario awards, or the alignment workbook grain; the runner collapses period rows to ONE
representative per (dc, lot, tf, supplier) before building `BidInput`. Also: `ingest_bids` returns the
LOGICAL line count (not fanned rows); an unmappable timeframe gracefully falls back to tf-grain (NULL
period); a re-submission supersedes prior period rows in EVERY read (no stale price leak anywhere).

- **`test_intake_stores_bids_flat_at_fiscal_periods(tmp_path, db_session)`** — ingests a "Colored Potatoes"
  cycle filled across the full column set. (c) `n_lines = ingest_bids(...) > 0` is the LOGICAL count.
  Computes `span_by_tf` (exactly 1 timeframe, span > 1 period). (a) every `BidLine` row carries a non-NULL
  `fiscal_period_id` (period grain); `len(all_rows) == n_lines * n_periods`; distinct cell keys count
  `== n_lines` (fan-out hidden). (b) the SQL group-by `ref.fiscal_period` shows each period in the span
  covered exactly once per cell (`[(2026,p) for p in span]`, each count `== n_lines`). Every `_CARRIED_COLUMNS`
  value is identical across a cell's period rows (verbatim survival). Both `submitted_all_in_case` (Decimal)
  and `delivery_surcharge_case` columns were genuinely exercised. **Protects:** flat-13 period storage,
  exact per-period coverage, verbatim column carry, logical vs fanned counts.
- **`test_period_grain_storage_leaves_engine_output_unchanged(tmp_path, db_session)`** — THE HARD INVARIANT.
  Reads the real period-grain rows (`runner._read_bid_lines`), asserts `len(period_rows) > n_lines`
  (fanned). Collapses via `runner._representative_lines(period_rows)` → exactly `n_lines` (one row per
  logical cell). Assembles `BidInput`s from both period rows and the representative control;
  `_engine_facing(bids)` compares everything the engine scores on EXCEPT the surrogate bid_id (cell key,
  landed cost, eligibility, incumbency, components all_in/fob, volume) — asserts the two are IDENTICAL,
  and `len(period_bids) == n_lines`. **Determinism:** re-collapsing yields the SAME `bid_line_id` order.
  End-to-end: `run_round`, then `eng.bid_score` count `== n_lines` (no doubling), `eng.analysis_scenario`
  count `== 7` (the A–G lenses). The ALIGNMENT WORKBOOK grain: `_body_rows("Detailed Scoring")` `== n_lines`,
  `_body_rows("Coverage")` `== n_lines` (incl. component-basis FOB-only bids via the canonical price, E-39),
  and `# Bidders` (col 10) `max <= 2` (the true supplier count — a stats-dedupe miss would inflate it by
  `n_periods`). **Protects:** the period-grain change is invisible to the engine, the seal, and the
  workbook — the single most important reproducibility/safety invariant in intake.
- **`test_unmappable_timeframe_falls_back_to_tf_grain(tmp_path, db_session)`** — shoves the timeframe dates
  to 2099 (outside the seeded FY16–FY36 calendar), ingests; asserts `len(rows) == n_lines` and ALL
  `fiscal_period_id is None` (graceful tf-grain fallback, no fan-out, nothing breaks). **Protects:** the
  out-of-calendar fallback branch.
- **`test_resubmission_supersedes_prior_period_rows_in_every_read(tmp_path, db_session)`** — submits
  `old_price = 1311.07` then `new_price = 8742.93` (price-implausible distinct markers) for the same round;
  `n_lines2 == n_lines`. `_count(price, scoreable)`: old@scoreable==0 (no superseded row active),
  old@non-scoreable>0 (retained, ADR-0006 supersede-not-delete), new@scoreable>0 (active). (1) engine input
  `_read_bid_lines` returns ONLY rows with `submitted_all_in_case == Decimal(str(new_price))`. (2) workbook:
  after `run_round`, scans EVERY tab/cell — asserts the OLD price never appears (`> 0.01` away) in any tab
  and the NEW price IS present. (3) `export_run_data` snapshot: round-1 `bid_lines == n_lines` (active only,
  not doubled). **Protects:** supersession leak-detection across the engine, all three workbook gathers
  (price grid, Detailed Scoring stats, Coverage), and the run_data snapshot — no deduped read can surface a
  stale superseded price.

## 20. `bid/test_round_trip.py` · py · not empty · 305 lines (PURE)

**WHAT:** D20 round-trip proof — generate template → fill (synthetic) → ingest → grain round-trips. The
system owns BOTH ends of ONE owned schema. Imports `PRICE_BASIS_ALL_IN`, `PRICE_BASIS_FALLBACK`,
`Completeness`, `QuarantineReason`, `ingest_template`, `build_template_workbook`, `generate_template_bytes`,
the schema constants, and `build_scope()`. Helpers `_fill_bids(bytes)`, `_fill_all_in(bytes)`.
**WHY:** D20/D21 — a template generated for a scope, filled with synthetic bids, must ingest back to the
SAME supplier×DC×lot×item×TF×round grain with cost COMPONENTS preserved exactly; key validation, not
name resolution; tampered/missing keys quarantine; a name mismatch warns.

- **`test_generated_template_has_owned_sheets_and_grain()`** — `build_template_workbook(scope).sheetnames`
  == `[SHEET_INSTRUCTIONS, SHEET_BIDS, SHEET_CAPACITY]`; Bids headers == `BID_HEADERS`; one Bids body row
  per scope cell. **Protects:** the owned template's sheet set + header + per-cell row count.
- **`test_preset_reduces_columns_and_still_round_trips()`** — uses `ALL_IN_PRESET`: emitted headers include
  All-In but NOT FOB/Delivery (components not selected). Fills All-In 100.00 + total 200 on every row,
  ingests; `quarantined == []`, `len(lines) == len(scope.rows)`, every line `components.all_in == 100.00`
  and `components.fob is None` (column absent). **Protects:** column-selection presets don't break the
  D20/D21 round-trip.
- **`test_round_trip_grain_and_components_exact()`** — fills row0 All-In 100.00 (+ vol 500/50, comments
  "firm", transit 3), row1 component-fallback (FOB 90 + Del 5 + Veg 3 − LotDisc 2 = 96.00, vol 300), rest
  All-In 101.50. Asserts `quarantined == []`, `name_warnings == []`, `len(lines) == len(scope.rows)`.
  Transit days: `3` present where filled, `None` where blank (no proxy). The ingested IDENTITY grain
  `== scope_grain` EXACTLY (the D20 proof), and the EMBEDDED KEY 7-tuples `== scope.key_set()` (D21). Row0:
  `price_basis == ALL_IN`, `landed_cost_per_case == 100.00`, `components.all_in == 100.00`, `BID`,
  `total_vol_offered == 500`, `weekly_vol_offered == 50`, `pricing_comments == "firm"`. Row1:
  `price_basis == FALLBACK`, `landed == 96.00`, components fob/delivery/vegcool/lot_discount ==
  90/5/3/2 exactly, `BID`. Counts: `bid_count == len(scope.rows)`, `no_bid_count == 0`,
  `incomplete_count == 0`. **Protects:** exact grain + component round-trip — the data-fidelity core of intake.
- **`test_tampered_embedded_key_quarantines_not_resolved()`** — tampers row0's embedded `LOT_ID` to
  `"LOT-TAMPERED"` (names valid). One quarantine reason `UNKNOWN_KEY`; `len(lines) == len(scope.rows) − 1`
  (no name-based re-resolve). **Protects:** D21 fatal-on-tampered-key.
- **`test_blank_embedded_key_quarantines_missing_key()`** — clears `SUPPLIER_ID` to `""`; one quarantine
  reason `MISSING_KEY`; `len(lines) == len(scope.rows) − 1`. **Protects:** missing key quarantines.
- **`test_name_mismatch_warns_but_keys_still_resolve()`** — overwrites row0's SUPPLIER display name to
  `"Totally Wrong Name"` (keys intact). `quarantined == []`, `len(lines) == len(scope.rows)`, exactly one
  `name_warning` on the SUPPLIER column with `found_name == "Totally Wrong Name"`, and the warned line
  still carries the CORRECT embedded `supplier_id` (no re-resolve). **Protects:** D21 — name is an
  attribute, key is the join identity; mismatch warns, never re-resolves.

---

# tests/comms/ — supplier communications (E-37) — all PURE, no DB

## 21. `comms/__init__.py` · py · EMPTY (0B) — package marker.

## 22. `comms/test_formulas.py` · py · not empty · 81 lines

**WHAT:** Canonical formula reuse (E-37 / Codex PR #18) — comms computes prices/premia like the engine.
Imports `_constructed_price`, `_hard_ask_rows` from `app.comms.resolvers`, `construct_price`,
`premium_vs_low` from `app.engine.formulas`, `BidComponents`/`BidInput`, `GATE_COVERAGE`/`GATE_PREMIUM`.
**WHY:** Locks the two behaviours Codex flagged: a component-basis bid still yields a price via the
engine's §7 `construct_price`; an ineligible bid breaching BOTH hard gates produces a hard-ask row for EACH.

- **`test_constructed_price_primary_all_in()`** — `_constructed_price(11.50, 9.00, 1.00, 0.50, 0.25) == 11.50`
  (All-In verbatim, discounts not re-subtracted). **Protects:** All-In primacy in comms.
- **`test_constructed_price_fallback_from_components()`** — `_constructed_price(None, 9.00, 1.00, 0.50, 0.25)
  == 10.25` (FOB + delivery + vegcool − lot_discount). **Protects:** §7 fallback in comms.
- **`test_constructed_price_none_without_price()`** — no All-In and no FOB → `None`. **Protects:** no-price
  rows contribute nothing.
- **`test_constructed_price_matches_engine_construct_price()`** — builds a component-only `BidInput`,
  asserts `_constructed_price(...)` == the engine's `construct_price(BidInput(...))`. **Protects:** comms is
  the engine's canonical formula by construction (one source of truth).
- **`test_premium_vs_low()`** — `premium_vs_low(11.00, 10.00) == 0.1`; `premium_vs_low(10.00, 0) is None`
  (no benchmark → undefined). **Protects:** premium math + the no-benchmark guard.
- **`test_hard_ask_rows_reports_every_breached_gate()`** — `_hard_ask_rows("PREMIUM;COVERAGE", 0.18, 0.12,
  0.80)` → 2 rows, issues include "Price premium exceeds threshold" AND "Insufficient volume offered".
  **Protects:** one hard-ask row per breached gate.
- **`test_hard_ask_rows_single_and_fallback()`** — single gate → 1 row each; empty gate string → 1 fallback
  row `"Not eligible for award"`. **Protects:** single-gate + fallback hard-ask rows.

## 23. `comms/test_merge.py` · py · not empty · 70 lines

**WHAT:** The deterministic `[#Name]` template-merge engine (E-37). Imports `merge`, `placeholders` from
`app.comms.merge`.
**WHY:** A draft can't go out with an invisible gap — a missing placeholder must be left VISIBLE and
reported, never silently blanked. Only the exact `[#Name]` token shape merges.

- **`test_fills_known_placeholders()`** — `merge("Hi [#SupplierName], welcome.", {SupplierName:"Acme Produce"})`
  → text "Hi Acme Produce, welcome.", `used == ("SupplierName",)`, `missing == ()`.
- **`test_repeated_placeholder_filled_everywhere_listed_once()`** — `[#X] and [#X]` with X=Z → "Z and Z
  again", `used == ("X",)` (listed once). **Protects:** repeated token fills everywhere, listed once.
- **`test_missing_placeholder_is_left_in_place_and_reported()`** — `merge("Bids due [#DueDate].", {})` leaves
  `[#DueDate]` in place, `missing == ("DueDate",)`. **Protects:** visible hole, never silent blank.
- **`test_none_or_empty_value_counts_as_missing()`** — `{A:"", B:None}` → both left in place,
  `missing == {A,B}`. **Protects:** empty/None counts as missing.
- **`test_mixed_used_and_missing()`** — partial context fills SupplierName/RoundNumber, leaves `[#DueDate]`;
  `used == ("SupplierName","RoundNumber")`, `missing == ("DueDate",)`.
- **`test_plain_text_passes_through_unchanged()`** — no tokens → text unchanged, used/missing empty.
- **`test_non_token_brackets_are_left_untouched()`** — `[plain]`, `[#]`, `[# spaced]` are NOT tokens; only
  `[#Good]` merges. **Protects:** strict token shape.
- **`test_adjacent_tokens()`** — `[#A][#B]` with A=1,B=2 → "12". **Protects:** adjacency handling.
- **`test_placeholders_lists_distinct_names_in_first_seen_order()`** — `placeholders("[#B] [#A] [#B] [#C]")`
  == `["B","A","C"]`; `placeholders("no tokens") == []`. **Protects:** distinct-name extraction in order.

## 24. `comms/test_render.py` · py · not empty · 117 lines

**WHAT:** Table-aware render over the seven authored supplier-comms templates (E-37). Imports `render`,
`REGISTRY`, `EmailType`, `get_template`. `_INVITE_CTX` is the full scalar context for the invitation.
**WHY:** The render layer must keep machine tags in the subject, fill scalar bodies, expand table
placeholders to header+rows, report missing fields visibly, and cover all 7 touchpoints.

- **`test_subject_keeps_machine_tags_and_merges_inner_tokens()`** — invitation subject keeps `[RFP:...]` /
  `[SUP:...]` wrappers while merging inner tokens → `"[RFP:KR-2026-TOM] [SUP:DIVINE] Invitation – Tomato
  2026"`. **Protects:** subject machine-tag survival + inner merge.
- **`test_scalar_body_fills_and_reports_nothing_missing()`** — full context fills "Dear Acme Produce,",
  "Bid Submission Deadline: 2026-05-15", "Estimated Number of Rounds: 2", "J. Buyer"; `missing == ()`.
- **`test_missing_scalar_is_left_in_place_and_reported()`** — only SupplierName given → "Dear Acme,",
  `[#BidDueDate]` left visible, "BidDueDate" ∈ missing. **Protects:** visible-hole rule in rendered body.
- **`test_table_expands_to_header_plus_rows()`** — INCOMPLETE_BID with two IncompleteBidTable rows expands
  to the pipe-joined header `"DC | Lot | Item | Timeframe | Missing Fields"` plus both data rows; the
  `[#IncompleteBidTable]` placeholder is gone; `missing == ()`. **Protects:** table expansion.
- **`test_table_row_missing_field_is_reported()`** — a table row missing fields → "MissingFields" ∈ missing,
  `[#Item]` stays visible. **Protects:** per-row missing-cell reporting.
- **`test_empty_table_renders_none_placeholder_block()`** — empty IncompleteBidTable → body contains
  "(none)". **Protects:** empty-table rendering.
- **`test_registry_covers_all_seven_touchpoints()`** — `set(REGISTRY) == set(EmailType)`, `len(REGISTRY) == 7`.
  **Protects:** all 7 comms touchpoints registered.
- **`test_every_declared_table_placeholder_is_expanded()`** — for every template, rendering with empty
  data/tables leaves NO declared `[#XxxTable]` placeholder. **Protects:** no orphaned table placeholder.

---

# tests/engine/ — the V3 engine golden-master + numeric reproducibility CORE

## 25. `engine/__init__.py` · py · EMPTY (0B) — package marker.

## 26. `engine/golden_expectations.json` · json · not empty · 102 lines — THE GOLDEN MASTER

**WHAT:** Independently-derived golden expectations for the synthetic fixture (GOLDEN_MASTER.md §3).
Values traced BY HAND from `V3_ENGINE_LOGIC.md` band TABLES — NOT from our engine and NOT from the
quarantined v3 (clean-room, ADR-0001). Tolerance per the `_doc`: band scores exact; RecScore exact to 2dp.
No real data (placeholders only). **WHY (the contract it guards):** this file IS the numeric oracle for
the V3 engine — the lifted engine must reproduce these exact numbers or the Phase-D exit gate fails.
The pinned values (consumed by `test_engine_golden.py`):
- **weights_default:** price 0.35, coverage 0.25, historical 0.20, zrisk 0.10, continuity 0.10.
- **price_band** (edge bid: cov=100, hist=50, z=100, cont=0; `rec = price*.35 + 45`): LP01 price 100 /
  rec **80.00** / eligible; LP02 100 / 80.00; LP03 80 / **73.00**; LP04 80 / 73.00; LP05 50 / **62.50**;
  LP06 50 / 62.50; LP07 20 / **52.00** / **NOT eligible**, gate "Price premium exceeds threshold".
- **coverage_band** (`rec = 55 + cov*.25`): LC01 cov 0 / rec **55.00** / ineligible "Insufficient volume
  (<80%)"; LC02 40 / **65.00** / ineligible; LC03 40 / 65.00 / ineligible; LC04 70 / **72.50** / eligible;
  LC05 70 / 72.50; LC06 100 / **80.00**; LC07 100 / 80.00; LC08 95 / **78.75**; `b_cov_nan_e` 30 / **62.50**
  (NaN coverage); `b_cov_an_e` 70 / 72.50 (as-needed).
- **historical_band** (`rec = 70 + hist*.20`): LH01 hist 100 / rec **90.00**; LH02 100 / 90.00; LH03 85 /
  **87.00**; LH04 70 / **84.00**; LH05 45 / **79.00**; LH06 20 / **74.00**; `b_h_nobase` 50 / **80.00**.
- **zrisk_band:** `b_zl1` 100; `b_zlow` **60** gate "Low price outlier: validate sustainability"; `b_zhigh`
  **40** gate "High price outlier".
- **continuity:** `b_inc` 100 / rec **90.00** / incumbent; `b_inc_rival` 0 / rec **80.00** / not incumbent.
- **scenario_c_incumbent_defense** (DC60/LT01): A picks rival **S71**, B picks incumbent **S70**, C retains
  **S70** (proves A≠B + the incumbent-defense lens).
- **cost_construction:** `b_fallback` awarded **95.00** (FOB 90 + Del 5 + Veg 3 − Lot 2 − AllLot 1);
  `b_doublesub` awarded **95.00** (All-In 95 present WITH Lot_Discount 2 → NOT re-subtracted);
  `b_zeroprice` ineligible "No valid price".
- **scenario_d_split** (DC20/TF1, max_sup_dc=2): top-2 {S31, S33}; awards LT01→S31 (not fallback),
  LT02→S31, LT03→**S32 fallback=true** (coverable only by S32, outside top-2), LT04→S33.
- **scenario_a_lowest_cost** DC40/LT01 → **SX0 @ 100.00**; **b_recommended** DC40/LT01 → SX0;
  **e_exclusion** (SX0 excluded) DC40/LT01 → **SX1**; **f_custom** forces **S32** on DC20/LT01 (B picked
  S31); **g_preferred** forces **S32** on DC20/LT01 (a no-bid preferred rule on LT99 keeps B's pick).
- **concentration:** flagged supplier **["S50"]** (its B RecSpend 6000×100 ≥ 40% of total category B spend).
- **cap_breach:** breaching DC×TF **["DC11", "TF1"]**.
- **weight_renormalization:** raw 0.42/0.30/0.24/0.12/0.12 (sum 1.20) → normalized 0.35/0.25/0.20/0.10/0.10.

## 27. `engine/golden_fixture.py` · py · not empty · 283 lines — THE SYNTHETIC FIXTURE (no tests)

**WHAT:** The SYNTHETIC, committable golden fixture (GOLDEN_MASTER.md §4). 100% placeholder data —
suppliers S.., DCs DC.., lots LT.., TFs TF1/TF2; NO real prices/names/volumes/awards. Engineered so every
band edge + every branch of V3_ENGINE_LOGIC.md fires at least once (the Phase-D exit gate, ADR-0006 / S2).
`_bid(...)` builds a `BidInput`; `_config(single_round)` sets the BALANCED preset, the default weights,
`max_sup_dc=2`, `conc_thresh=0.40`, `global_premium_threshold=0.12`, `coverage_floor=0.80`, the 7 lenses,
exclusion `SX0`, a custom override (DC20/LT01/TF1→S32), and two preferred rules (DC20/LT01→S32; LT99/S_NONE
= the no-eligible-bid exception path). `final_round_code = "R1" if single_round else "R2"`,
`prior_round_code = None if single_round else "R1"`.
**WHY (band isolation design):** each band-edge bid sits in its own 2-bid group — an anchor that fixes the
group min/avg and the edge bid at the target premium. With exactly two bids, Z is ±1.0 (z-risk 100) and
coverage held at 100, so the edge bid's RecScore isolates the factor under test. `build_inputs(single_round)`
assembles: **PRICE edges** LP01..LP07 (anchor 100 + edge at 0/3/3.01/7/7.01/12/12.01% — LP07 also breaches
premium); **COVERAGE edges** LC01..LC08 (vol 49/50/79/80/99/100/120/121 vs 100) + a NaN-coverage cell
(no vol → 30) + an as-needed cell (→ 70); **HISTORICAL edges** LH01..LH06 vs incumbent baseline 100.00
(deltas −.11/−.10/−.03/+.03/+.07/+.08) + a no-baseline lot (→ 50); **Z-RISK** asymmetric clusters (8 @ 100
+ 1 deep-low 60 → Z≈−2.83 → 60; 8 @ 100 + 1 high 140 → Z≈+2.83 → 40); **SCENARIO D split** DC20 (S31 strong
LT01/LT02, S32 strong LT03, S33 only LT04, plus a weak S32 alt on LT01); **CONCENTRATION** S50 wins a 6000-case
lot (B RecSpend ≥ 40%); **EXCLUSION** SX0/SX1 on DC40/LT01; **CONTINUITY + Scenario C** incumbent S70 @ 100 vs
cheaper rival S71 @ 99 on DC60/LT01; **COST construction** fallback (FOB 90+Del 5+Veg 3−Lot 2−AllLot 1 = 95.00),
double-subtract guard (All-In 95 + Lot 2 → not re-subtracted), and a zero-price row (→ dropped). Returns an
`EngineInputs`. This is the fixture every `tests/engine` test (and several intake tests via the runner) drive.

## 28. `engine/test_engine_golden.py` · py · not empty · 295 lines (PURE) — GOLDEN-MASTER REPRODUCTION

**WHAT:** Asserts the lifted `V3Engine` reproduces `golden_expectations.json` exactly. `_EXPECT` loads the
JSON; `_scores_by_id()` / `_awards()` / `_award(code, dc, lot)` run `V3Engine().run(build_inputs())`.
**WHY:** S2 exit gate — band edges + eligibility gates + split allocation + scenarios A–G + cost
construction + weight renormalization + determinism, all pinned to the independent golden values.

- **`test_factor_band_edges(band)`** (parametrized `price_band`/`coverage_band`/`historical_band`) — for each
  expected bid, asserts the score field (Decimal) and the composite `rec_score` match, plus eligibility and
  the exact gate string where present. **Protects:** every price/coverage/historical band boundary +
  composite RecScore against the golden numbers above.
- **`test_zrisk_band_edges()`** — asserts `zrisk_score` for `b_zl1`=100, `b_zlow`=60 (+ "Low price
  outlier..." gate), `b_zhigh`=40 (+ "High price outlier" gate). **Protects:** z-risk scoring + outlier gates.
- **`test_continuity_incumbent_vs_rival()`** — `b_inc` continuity 100 / rec 90.00; `b_inc_rival` continuity
  0 / rec 80.00. **Protects:** the continuity factor + composite.
- **`test_eligibility_gates_and_reason_codes()`** — LP07 ineligible + "Price premium exceeds threshold";
  LC01 ineligible + "Insufficient volume (<80%)"; `b_zeroprice` ineligible + "No valid price"; `b_zlow`
  carries the advisory "Low price outlier..." gate but stays eligible (advisory ≠ hard gate). **Protects:**
  each hard gate flips eligibility with its exact reason code; advisory flags don't flip eligibility.
- **`test_low_bidder_count_flag()`** — `b_pe_LP01_e` carries "Low bidder count (<3): Z-score less reliable".
  **Protects:** the advisory low-bidder flag on 2-bid groups.
- **`test_scenario_d_split_and_fallback()`** — DC20 D awards match the expected (lot, supplier, is_fallback)
  set incl. LT03→S32 fallback=true. **Protects:** top-N split + fallback-flagged outside fill.
- **`test_concentration_flag()`** — `V3Engine().concentration_flagged_suppliers(build_inputs())` == `{"S50"}`.
  **Protects:** the concentration flag computed over all B cells.
- **`test_cap_breach_surfaces()`** — DC11/TF1 B awards all carry `cap_breach_flag is True`. **Protects:** the
  per-DC×TF supplier-count cap breach on Scenario B.
- **`test_cap_breach_consistent_across_scenarios()`** — regression: for every non-D `_mk`-built scenario, a
  (dc,tf) group seating > max_sup_dc distinct suppliers flags ALL its awards, within-cap groups flag none.
  **Protects:** cap-breach is a property of the AWARD not the lens (the rehearsal finding).
- **`test_scenario_a_lowest_cost()`** — A DC40/LT01 → exactly one award, supplier SX0, price 100.00.
- **`test_scenario_b_differs_from_a_when_risk_adjusted()`** — DC60/LT01: A→S71, B→S70, A≠B. **Protects:** B
  (risk-adjusted) can diverge from A (lowest cost) via the incumbent boost.
- **`test_scenario_c_incumbent_defense()`** — C DC60/LT01 → S70 (incumbent retained within comparable premium).
- **`test_scenario_e_exclusion()`** — E DC40/LT01 → SX1 (SX0 excluded, B re-runs).
- **`test_scenario_f_custom_override()`** — B DC20/LT01 → S31, F → S32 (override).
- **`test_scenario_g_preferred_with_noeligible_exception()`** — G DC20/LT01 → S32; the LT99/S_NONE rule has
  no eligible bid → no crash, no spurious award (`_award("G","DCxx","LT99")` empty).
- **`test_cost_fallback_and_double_subtract_guard()`** — A DC50/LT01 awarded 95.00 (fallback);
  A DC50/LT02 awarded 95.00 (All-In not re-discounted despite Lot_Discount 2). **Protects:** cost
  construction + the double-subtract guard at the award level.
- **`test_weight_renormalization()`** — raw weights (sum 1.20) → `resolve_weights` normalizes to
  0.35/0.25/0.20/0.10/0.10 summing to 1.00; the default config is unchanged (price 0.35). **Protects:** §2.6
  weight renormalization.
- **`test_engine_is_deterministic_and_versioned()`** — two runs are `==`; `engine_version == V3_VERSION ==
  "v3-cleanroom"` and `!= "stub"`. **Protects:** determinism + the real-engine version tag.

## 29. `engine/test_engine_invariants.py` · py · not empty · 114 lines (PURE)

**WHAT:** Decision-support invariants (ADR-0006). Imports `BANNED_DECISION_WORDS`,
`BannedDecisionWordError`, `assert_decision_support` from `app.engine.guards`.
**WHY:** The engine PROPOSES; a human decides. The engine must never emit an asserted award decision, never
name a single "winner" — it surfaces shares + the benchmark lens.

- **`test_banned_list_is_nonempty()`** — `BANNED_DECISION_WORDS` non-empty, all non-empty strings (S3).
- **`test_guard_raises_on_asserted_award(label)`** (parametrized: "...is awarded the contract", "Award to
  S01", "S01 is the winner", "S01 selected for the lot", "Final decision: S01") — each RAISES
  `BannedDecisionWordError`. **Protects:** asserted-award phrasing is blocked.
- **`test_guard_passes_decision_support_phrasing(label)`** (parametrized: "Risk-adjusted recommendation",
  "Lowest-cost reference", "Reward program note" [reward ≠ award], "Lawn maintenance lot" [benign substring],
  "Proposed split across two suppliers") — each returns the label unchanged. **Protects:** decision-support
  phrasing + benign substrings pass (no false positives on "reward"/"lawn").
- **`test_engine_scenario_labels_never_assert()`** — every emitted scenario `label` and `description` passes
  `assert_decision_support` unchanged. **Protects:** the engine never auto-asserts in its own labels.
- **`test_engine_never_auto_asserts_a_single_winner()`** — non-B awards have `is_recommended is False`; every
  award `0 <= volume_share <= 1` (a share, not a verdict); Scenario A is always present as the benchmark lens.
  **Protects:** awards are split shares + the lowest-cost context, never a winner verdict.
- **`test_b_awards_carry_the_engine_rec_type()`** — D28: every B award's `rec_type` ∈ {Lowest cost, Coverage
  advantage, Comparable premium, Defensible premium, Risk-adjusted}; every non-B award `rec_type is None`.
  **Protects:** the per-cell recommendation "why" is computed once in the engine, B-only.

## 30. `engine/test_engine_single_round.py` · py · not empty · 58 lines (PURE)

**WHAT:** The single-round guard (TOMATO_RUN.md). v3 crashed in step 6 on an R1-only cycle
(`prior_round['Round']` on `None`). Our engine must skip the prior-round lookup when
`config.prior_round_code is None`.
**WHY:** Regression — a one-round cycle must complete; scoring must be unaffected by the guard.

- **`test_single_round_cycle_completes_without_crash()`** — `build_inputs(single_round=True)` has
  `prior_round_code is None`; `V3Engine().run(inputs)` does NOT raise; produces scores/scenarios/awards;
  `engine_version == "v3-cleanroom"`. **Protects:** the no-crash single-round path (the exact v3 bug).
- **`test_single_round_prior_price_map_is_empty()`** — `V3Engine._prior_round_prices(inputs) == {}` (empty
  map, not None). **Protects:** the guarded prior-price lookup returns an empty dict.
- **`test_single_round_matches_multiround_scoring_for_same_bids()`** — per-bid `rec_score` is identical
  between single- and multi-round runs (historical uses the incumbent baseline, not the prior round).
  **Protects:** the guard doesn't perturb scoring.
- **`test_minimal_single_round_no_prior_no_incumbents_no_volumes()`** — a degenerate R1-only cycle (no
  bids/incumbents/volumes — the Tomato shape) completes; `engine_version == "v3-cleanroom"`, `awards == ()`.
  **Protects:** the degenerate-input single-round path.

## 31. `engine/test_engine_stub.py` · py · not empty · 115 lines (PURE)

**WHAT:** Engine library PURITY + version-tag guards (PLAN §3, ENG-PLAN §5). `ENGINE_DIR` = `app/engine`.
`FORBIDDEN_IMPORT_PREFIXES` = sqlalchemy, fastapi, starlette, requests, httpx, psycopg, random, reference,
app.core.db, app.core.security. `_sample_inputs()` builds a 3-bid `EngineInputs`.
**WHY:** Two invariants provable without a DB: (1) purity — no engine file imports db/http/nondeterminism
or the `reference/` quarantine (clean-room, ADR-0001); (2) version tagging — the stub tags `"stub"`, the
real engine `"v3-cleanroom"`, so a stubbed run is never mistaken for a validated v3 run.

- **`test_stub_is_deterministic_and_tagged()`** — two `DeterministicStubEngine().run(...)` are `==`;
  `engine_version == STUB_VERSION == "stub"`; scores cover {b1,b2,b3}; a Scenario A is present. **Protects:**
  stub determinism + tag.
- **`test_real_engine_tagged_distinctly_from_stub()`** — `V3Engine().run(...).engine_version ==
  V3_VERSION == "v3-cleanroom"` and `!= STUB_VERSION`. **Protects:** distinct real-engine tag.
- **`test_engine_package_is_pure_and_clean_room()`** — AST-walks every `app/engine/*.py`; any import in
  `FORBIDDEN_IMPORT_PREFIXES` (absolute imports only) is an offender; asserts `scanned > 0` (guard the guard)
  and `not offenders`. **Protects:** the engine library's purity + clean-room boundary, file by file.

## 32. `engine/test_formulas.py` · py · not empty · 85 lines (PURE)

**WHAT:** Canonical price-construction + math formulas (E-39) — `app.engine.formulas`. The §7 arithmetic the
engine scorer AND the bid ingester both route through (one place). Imports `awarded_cases`,
`construct_price_from_parts`, `coverage_ratio`, `delta_vs_historical`, `line_spend`, `premium_dollars`,
`price_delta`, `savings_dollars`, `savings_fraction`, `weekly_impact`, `z_score`.
**WHY:** Locks the canonical numeric definitions shared across engine + intake + output (no formula drift).

- **`test_all_in_taken_verbatim()`** — `construct_price_from_parts(11.50, 9.00, 1.00, 0.50, 0.25) == 11.50`
  (double-subtract guard). **Protects:** All-In primacy.
- **`test_fallback_sums_components_net_of_discounts()`** — `(None, 9.00, 1.00, 0.50, 0.25) == 10.25`; with
  all_lot_discount 0.10 → `10.15`. **Protects:** §7 fallback incl. all-lot discount.
- **`test_no_all_in_no_fob_is_none()`** — `(None, None) is None`. **Protects:** no-price → None.
- **`test_raw_result_is_not_clamped()`** — `(None, 1.00, lot_discount=3.00) == -2.00` (raw formula does NOT
  filter non-positive — that's caller policy). **Protects:** the raw formula's non-clamping contract.
- **`test_z_score()`** — `z_score(12, 10, 2) == 1`; `z_score(12, 10, 0) is None` (no spread). **Protects:**
  z-score + zero-std guard.
- **`test_coverage_ratio()`** — `(80, 100) == 0.8`; `(None,100)`/`(80,None)`/`(80,0)` all `None`. **Protects:**
  coverage ratio + its undefined cases.
- **`test_delta_vs_historical()`** — `(11, 10) == 0.1`; `(11, None)`/`(11, 0)` → None. **Protects:** historical
  delta + no-baseline guard.
- **`test_spend_and_savings()`** — `awarded_cases(600, 0.5) == 300.0`; `line_spend(11.50, 300) == 3450.00`;
  `savings_dollars(1000, 900) == 100`; `savings_fraction(1000, 900) == 0.1`; `savings_fraction(0, 900) == 0`
  (no baseline → 0, not a division error). **Protects:** spend/savings math + zero-baseline guard.
- **`test_premium_impact_and_price_delta()`** — `premium_dollars(11.50, 10.00) == 1.50`;
  `weekly_impact(1.50, 600) == 900.00`; `price_delta(9.75, 10.00) == -0.25`. **Protects:** premium-dollar,
  weekly-impact, price-delta math.

## 33. `engine/test_input_manifest.py` · py · not empty · 45 lines (PURE)

**WHAT:** C2 — the sealed-run input hash must be tamper-evident over the FULL config, not a subset. Imports
`_canonical_hash`, `_inputs_manifest` from `app.domain.eng.runner`. `_hash(config)` builds an `EngineInputs`
and hashes its manifest.
**WHY:** Previously `_inputs_manifest` hand-listed a few config fields, so a post-seal change to an un-hashed
field (per-lot thresholds, premium bands, exclusions, overrides, preferred rules, single-supplier-per-lot,
active TFs) would NOT change the input hash — undetectable tampering. Now the whole frozen config is sealed.

- **`test_identical_config_seals_identically()`** — `_hash(EngineConfig()) == _hash(EngineConfig())`.
  **Protects:** determinism (only a real change moves the hash).
- **`test_per_lot_threshold_change_changes_the_seal()`** — adding `lot_premium_thresholds` changes the hash.
  **Protects:** per-lot thresholds are in the manifest.
- **`test_premium_band_change_changes_the_seal()`** — changing `premium_band_max` changes the hash.
  **Protects:** premium bands are sealed (they change scores).
- **`test_single_supplier_per_lot_change_changes_the_seal()`** — toggling `single_supplier_per_lot` changes
  the hash. **Protects:** that flag is sealed.

## 34. `engine/test_runner_incumbent.py` · py · not empty · 61 lines (PURE)

**WHAT:** Regression for incumbent flagging in `EngineRunner._assemble_bids`. Drives the pure method with
`SimpleNamespace` stand-ins (no session — `EngineRunner.__new__`). Helper `_line(...)`.
**WHY:** The runner used to hardcode `is_incumbent=False` on every assembled bid, making the §2.5 continuity
factor inert. The fix: a bid whose (dc, lot, supplier) matches a cycle incumbent is flagged.

- **`test_assemble_bids_flags_only_the_incumbent_cell()`** — three lines (incumbent cell, challenger,
  same-supplier-different-DC); `incumbent_keys = {("DC1","LT1","SUP_INCUMBENT")}`. Asserts `b-inc.is_incumbent
  is True`, `b-chal` False, `b-other-dc` False (same supplier but not its incumbent cell). **Protects:**
  incumbent flag is per-cell, not per-supplier.
- **`test_assemble_bids_no_incumbents_flags_nothing()`** — empty `incumbent_keys` → the single bid
  `is_incumbent is False`. **Protects:** no-incumbents path flags nothing.

---

# tests/fiscal/ — the Kroger fiscal calendar

## 35. `fiscal/__init__.py` · py · EMPTY (0B) — package marker.

## 36. `fiscal/test_calendar.py` · py · not empty · 116 lines (PURE)

**WHAT:** Kroger fiscal calendar — period↔date, the 4-3-3-3 quarter split, leap weeks, timeframes. Asserts
the loaded reference table (`app/fiscal/data/kroger_fiscal_periods.csv`) against the sponsor's conversion
table, plus the timeframe grouping + intake fan-out the flat-13 model relies on (INTAKE_TEMPLATE_DESIGN §1a).
Imports the full calendar API. **WHY:** This is the authoritative time spine — every fan-out, deliverable
window, and the `ref.fiscal_period` seed derive from it; a calendar error corrupts all of intake.

- **`test_calendar_covers_fy16_to_fy36_with_13_periods_each()`** — `fiscal_years()[0]==2016`, `[-1]==2036`;
  each FY has periods `1..13`. **Protects:** the FY16–FY36 / 13-period coverage.
- **`test_every_period_is_contiguous_no_gaps()`** — each period's `begin == prev.end + 1 day`. **Protects:**
  no gaps in the date line.
- **`test_quarter_split_is_4_3_3_3_and_matches_the_data()`** — `QUARTER_OF_PERIOD` counts == `[4,3,3,3]`;
  every CSV row's `quarter` agrees. **Protects:** the fixed 4-3-3-3 split vs the data.
- **`test_today_resolves_to_fy26_period_5()`** — `period_for_date(2026-06-20)` → `(2026, 5, 2)`,
  `label == "P05-26"`, `begin 2026-05-24`, `end 2026-06-20`. **Protects:** date→period resolution + label.
- **`test_period_boundaries_are_inclusive()`** — `get_period(2026,1)` begin `2026-02-01`, end `2026-02-28`;
  begin/end both resolve to period 1; end+1 day → period 2. **Protects:** inclusive boundaries.
- **`test_leap_year_gives_period_13_a_fifth_week()`** — FY28 P13 has `weeks==5` / `days==35` (53-week year);
  FY26 P13 `weeks==4` / `days==28`. **Protects:** the leap-week (53-week year) handling.
- **`test_dates_outside_the_calendar_raise()`** — `period_for_date(2015-01-01)` and `get_period(2099,1)` both
  raise `ValueError`. **Protects:** out-of-range fails loud (the fallback branch's precondition).
- **`test_fiscal_quarter_timeframes_cover_the_year()`** — `fiscal_quarters(2026)` labels Q1..Q4 with
  period_numbers `(1,2,3,4)/(5,6,7)/(8,9,10)/(11,12,13)`; Q1 span begin/end match P1.begin / P4.end.
  **Protects:** quarter timeframe spans.
- **`test_halves_and_full_year_presets()`** — halves `(1..7)/(8..13)`; full year `(1..13)` single timeframe.
  **Protects:** half/full-year presets.
- **`test_group_periods_rejects_non_covering_spans()`** — a gap (1-2,4-13) and an overlap (1-13,5-7) each
  raise `ValueError`. **Protects:** grouping must fully cover with no gap/overlap.
- **`test_intake_fans_a_timeframe_out_to_its_flat_periods()`** — A/B/C grouping → `expand_to_periods` yields
  `{A:[1,2], B:[3..9], C:[10..13]}`; the union is exactly `1..13` each written once. **Protects:** the
  intake fan-out at the calendar level.

---

# tests/mcp/ — the RFP pilot MCP server surface

## 37. `mcp/__init__.py` · py · EMPTY (0B) — package marker.

## 38. `mcp/test_server_imports.py` · py · not empty · 51 lines (PURE)

**WHAT:** Smoke test for the RFP pilot MCP server (PART B). Imports `app` from
`rfp_mcp.rfp_pilot_server` and inspects registered tools WITHOUT running the stdio loop (stays pure).
`EXPECTED_TOOLS` = 17 tool names (run_start, run_list, run_status, setup_template, setup_ingest,
bid_template, ingest_bids, ingest_any, run_round, select_award, record_adjustment, history, feedback,
remember, add_memory, close_run, purge_run).
**WHY:** PILOT_SYSTEM_DESIGN §7 — guards against a tool being renamed/dropped or the module failing to
import (the MCP harness is the live-run verification oracle named in CLAUDE.md).

- **`test_app_is_fastmcp()`** — `isinstance(app, FastMCP)` and `app.name == "rfp-pilot"`. **Protects:** the
  app object identity + name.
- **`test_all_expected_tools_registered()`** — `app.list_tools()` registered names ⊇ `EXPECTED_TOOLS` (no
  tool missing). **Protects:** the full tool surface is registered.

---

# tests/output/ — the workbook/deliverable output surfaces

## 39. `output/__init__.py` · py · EMPTY (0B) — package marker.

## 40. `output/test_capacity_check.py` · py · not empty · 96 lines (PURE)

**WHAT:** E-38 capacity-check evaluator. Imports `StatedCapacity`, `evaluate_capacity` from
`app.output.capacity_check`. `_WEEKS = 13` (one timeframe = 13 weeks). `_Cell` dataclass + `_cell(...)`
(distinct dc/lot/tf per supplier so each cell has its own capacity key).
**WHY:** The accuracy core's "never recommend beyond stated capacity" flag — period + weekly over-capacity
verdicts, no DB.

- **`test_over_period_when_allocation_exceeds_total_ceiling()`** — allocated 6500 vs total 6000 → row
  `allocated_cases == 6500.0`, `has_statement True`, `over_period True`, `over_capacity True`,
  `status == "OVER CAPACITY"`. **Protects:** the period (total) over-capacity verdict.
- **`test_within_period_but_over_weekly()`** — 6500 total → 500/week vs weekly 400, total 7000 →
  `over_period False`, `allocated_weekly_cases == 500`, `over_weekly True`, `over_capacity True`.
  **Protects:** the weekly-dimension over-capacity verdict (within period).
- **`test_within_both_ceilings()`** — 6500 (500/week) vs weekly 600 / total 7000 → `over_capacity False`,
  `status == "Within capacity"`. **Protects:** the in-capacity verdict.
- **`test_volume_share_scales_allocation()`** — share 0.5 of 6500 → `allocated_cases == 3250.0`,
  `over_period False` vs total 4000. **Protects:** volume_share scales the allocation.
- **`test_no_statement_is_reported_not_flagged()`** — no capacity map → `has_statement False`,
  `over_capacity False`, `status == "No stated capacity"`, max_period/max_weekly None. **Protects:** absent
  statement is reported, never flagged as a breach.
- **`test_only_period_stated_ignores_weekly_dimension()`** — total only (no weekly) → `over_weekly False`,
  `over_period True`. **Protects:** weekly never flags without a weekly ceiling.
- **`test_nonpositive_weeks_fails_loud_not_open()`** — `weeks_per_tf` in {0, -1} raises `ValueError` matching
  "weeks_per_tf must be positive". **Protects:** a non-positive week count fails loud, never silently passes
  a weekly overage as in-capacity.

## 41. `output/test_capacity_tab.py` · py · not empty · 71 lines (PURE)

**WHAT:** E-38b capacity-check workbook TAB. Imports `CapacityCheckDisplayRow`, `_write_capacity_check_tab`
from `app.output.scenario_workbook`. `_row(...)` builds a display row.
**WHY:** The operator-facing safety surface in the alignment workbook — given resolved display rows, the
sheet writes with the right statuses and the OVER CAPACITY rows present.

- **`test_capacity_check_tab_renders_and_flags_over()`** — three rows (OVER CAPACITY / Within capacity / No
  stated capacity) written to a workbook; asserts "Capacity Check" sheet exists, the status column (col 9)
  contains all three statuses, and the period column (col 7) contains the "—" placeholder where no ceiling
  was stated. **Protects:** the tab renders statuses + the no-ceiling placeholder.
- **`test_capacity_check_tab_empty_is_safe()`** — empty rows → the sheet still writes ("Capacity Check"
  present), no crash. **Protects:** the empty-input branch.

## 42. `output/test_line_price.py` · py · not empty · 40 lines (PURE)

**WHAT:** Unit of `_line_price` — the scenario workbook's canonical price reader (#2 fix). Imports
`_line_price` from `app.output.scenario_workbook`.
**WHY:** The workbook must construct each bid's price the SAME way the engine scored it (E-39), so a
component-basis bid is no longer dropped from the price grids / market stats / coverage / FOB tabs.

- **`test_all_in_present_is_taken_verbatim()`** — `_line_price(11.50, 9.00, 1.00, 0.50, 0.25) == 11.50`
  (double-subtract guard). **Protects:** All-In primacy in the workbook reader.
- **`test_component_basis_is_constructed()`** — `(None, 9.00, 1.00, 0.50, 0.25) == 10.25`. **Protects:** §7
  fallback in the workbook reader.
- **`test_component_basis_none_surcharges_default_zero()`** — `(None, 9.00, None, None, None) == 9.00`.
  **Protects:** None surcharges default to 0.
- **`test_no_all_in_no_fob_is_none()`** — `(None, None, None, None, None) is None`. **Protects:** no-price → None.
- **`test_accepts_db_style_values()`** — DB-style Decimals: `(18.40, 0.85, 0.40, 0.25, 0) == 18.40` (All-In
  verbatim); `(None, 18.40, 0.85, 0.40, 0.25) == 19.40` (fallback). **Protects:** the Decimal/None coercion
  round-trips DB numeric columns.

---

# tests/ref/ — the governed reference dimensions

## 43. `ref/__init__.py` · py · 1 line — docstring-only marker
("Tests for the `ref` schema (governed reference dimensions) — real Postgres for DB paths.")

## 44. `ref/test_fiscal_period_table.py` · py · not empty · 57 lines (`@integration`)

**WHAT:** `ref.fiscal_period` seed fidelity — the governed period dimension mirrors the calendar library.
Migration 0014 creates `ref.fiscal_period` and seeds it from the SAME CSV `app.fiscal.calendar` loads.
Uses `provision_run_database(slug)` (fresh migrated isolated DB incl. 0014), `run_unit_of_work`,
`drop_run_database` (try/finally). Imports `get_period`.
**WHY:** The database dimension and the in-process library must NEVER diverge — the engine reads the typed
library, the deliverables read the DB table; both must be the identical calendar.

- **`test_ref_fiscal_period_seeded_from_calendar()`** — provisions a fresh DB; (a) `count(*) ==
  **273**` (full FY16..FY36 set); (b) `min/max(fiscal_year) == (2016, 2036)`; (c) a sampled row
  (fy 2026, period 5) → `quarter == 2`, `begin_date == 2026-05-24`, `end_date == 2026-06-20`, and matches
  the typed `get_period(2026, 5)` exactly (quarter, begin, end, weeks). Cleans up in `finally`. **Protects:**
  the migration-0014 seed reproduces the calendar exactly — DB ↔ library parity (no divergence).

---

# Cross-cutting observations (Layer-2 process / decision coverage)

- **Clean-room (ADR-0001)** is enforced from TWO angles in B8b: `test_cleanroom_import.py` (no
  `backend/` → `reference/` import) and `test_engine_stub.py::test_engine_package_is_pure_and_clean_room`
  (no `app/engine/` → forbidden/`reference/` import). Both "guard the guard" (assert the scan found files).
- **D21 (key-validated, never name-resolved)** is the dominant intake contract, covered at the bid level
  (`test_round_trip.py`, `test_completeness_and_guards.py`) and the capacity level (`test_capacity_round_trip.py`)
  — tampered/missing keys quarantine; a name mismatch warns. D20 (own both ends) is the round-trip itself.
- **The flat-13 fan-out (INTAKE §1a)** is proven at three altitudes: pure unit (`bid/test_period_fanout.py`,
  `fiscal/test_calendar.py`), end-to-end persistence + the engine-invariance guard (`bid/test_period_import.py`),
  and the DB-seed parity (`ref/test_fiscal_period_table.py`).
- **ADR-0006 supersede-not-delete** appears in `bid/test_period_import.py` (period rows flipped
  non-scoreable, leak-detected across engine + workbook + run_data), `bid/test_capacity_persist.py`
  (statement SUBMITTED/SUPERSEDED), and `audit/test_decision_events.py` (SUPERSEDED events).
- **The golden master** (`golden_expectations.json` + `golden_fixture.py` + `test_engine_golden.py`) is the
  numeric reproducibility oracle: band scores exact, RecScore to 2dp, all derived independently from the
  spec (clean-room), with determinism + version-tag guards. The exact pinned numbers are transcribed above.
- **Audit chain (G-B)** is hash-chained, contiguous, atomic (rides the decision txn), actor-threaded, and
  the chain hash is recomputed from stored fields (tamper-evidence) — `audit/test_decision_events.py`.

# Gaps / caveats (verified, not assumed)

- **No gap vs B8a.** B8b covers every `backend/tests` file outside `tests/api/**`, `tests/pilot/**`, and the
  root `tests/conftest.py`. Union = 65 files (counting `.py` + the one `.json`), no overlap.
- **`tests/api/conftest.py` and `tests/conftest.py`** are NOT audited here (B8a). B8b tests depend on
  fixtures defined in the root `tests/conftest.py` (`db_session`, `engine`, `database_url`, `seed_tenants`)
  — those fixtures' definitions are B8a's responsibility; here they are documented only as consumed inputs.
- **`reference/samples/potato_2026_rfp_input.xlsx`** is git-ignored (real data); `bid/test_period_import.py`
  is written CI-safe with a synthetic fallback when it is absent — so the test runs without the sample but
  exercises real prices when present.
- **Two non-empty `__init__.py`** (`awd`, `bid`, `ref`) carry only a docstring; the other 7 `__init__.py`
  are 0-byte markers. None contain executable test code (correct, not a stub).
- All `@pytest.mark.integration` tests require a live Postgres at head (provisioned via conftest / the
  `provision_run_database` helper); the pure tests need only the libraries (pydantic / openpyxl / stdlib).
