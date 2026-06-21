---
doc: No-server-side-file-storage refactor — implementation plan
id: PM-NFS-PLAN
version: 1.0
status: DONE — all 6 slices landed + reviewed (s0 15d957e · s1 847140b · s2 c4507a8 · s3 a73fa3a · s4 3c2074b · s5 e12e26a · s6 ed2d26a). 247 tests pass; migration 0019 round-trips; web console writes zero files; MCP harness unchanged (oracle).
relates: ADR-0018 (storage model), ADR-0017 (GCP/Cloud Run), ADR-0003 (two runtimes), D30, D41, E-39, E-42
created: 2026-06-21
---

# No-server-side-file-storage — implementation plan

**Hard requirement (sponsor):** the **web console** must store **no files server-side**. The database
is the single source of truth — uploads stream into ingest in memory (never written to disk), and
every deliverable is generated on request from the DB and streamed (never written, never read from
disk). Confirmed: live runs go through the **web console**, backed by a **durable managed Postgres**.
The **MCP harness keeps its file vault** (a separate dev runtime; ADR-0018).

## Verified ground truth

- **A "run" is NOT a DB entity** — it's a vault folder `<vault>/runs/<slug>/`; the run↔cycle link is
  only `cycle_id.txt`; run metadata (commodity/label/rehearsal) lives in `RUN.md`/`NOTES.md`/
  `.rehearsal`. This is the deepest "run = folder" assumption and the crux (Slices 2–3).
- **Generators are deterministic pure DB-renders** (E-39). Slice 0 gave each a bytes builder:
  `build_scenario_workbook_bytes`, `build_booking_guide_internal_bytes`,
  `build_supplier_award_guides_bytes`, `build_supplier_award_guide_bytes` (per-supplier),
  `build_post_award_adjustments_bytes`. The `write_*_xlsx(output_path=…)` disk wrappers (harness) call
  the builders and write the bytes — unchanged behavior.
- **Status/kanban reads the DB** (`app/pilot/status.py:_cycle_counts`); the only file-derived signal is
  `setup_present = (inputs/SETUP).exists()`.
- **Setup template** `build_setup_workbook() -> bytes` and **bid template**
  `generate_template_bytes(scope) -> bytes` are already byte-returning.
- Tests: 233 green. File-coupled web tests: `tests/api/test_bids.py`, `tests/api/test_alignment.py`,
  `tests/api/test_post_award.py`. The `tests/pilot/*` are the harness contract (keep file-based).

## Slices (ordered, lowest-risk first)

- **Slice 0 — generators → bytes. ✅ DONE (15d957e).** Pure addition; 233 green.
- **Slice 1 — deliverable registry.** New `app/pilot/deliverables.py`: `enumerate_deliverables(session,
  *, cycle_id, slug, rehearsal) -> list[Deliverable]` where `Deliverable(name, kind, render:
  Callable[[Session], bytes])`. Enumerates from DB state only: setup template (always); per
  `cyc.cycle_round` bid template; per sealed `eng.analysis_run` the alignment workbook at its version
  seq; if `awd.award` FROZEN the internal booking guide + combined supplier guides + one per-supplier
  guide per awarded supplier; per `awd.award_adjustment` version the post-award doc. Reuse
  `stage_filename`/`_stage` so names match today's. Built but NOT wired. Test: enumerated names == the
  filenames `run_round`/`freeze_award` write today. Risk: low (read-only new module).
- **Slice 2 — DB-backed run identity (the crux; the migration).** New `pilot` schema + `pilot.run`
  table (mirrors the `auth.app_user` precedent): `slug PK, commodity, label, rehearsal bool, cycle_id
  (nullable), created_at`. Migration `alembic/versions/0019_pilot_run.py` (additive; round-trips). ORM
  `app/pilot/models.py:Run` + repo (`create_run_record/get_run/list_run_records/set_run_cycle/
  delete_run_record`). **Dual-write:** `start_run` inserts the row; `ingest_setup` sets `cycle_id`
  (still writing files too). Backfill a row for every existing `runs/<slug>/` folder before Slice 3.
  Risk: medium (structural, but additive/reversible). Harness untouched.
- **Slice 3 — console resolves run identity from the DB, not files.** `pilot_common.resolve_paths`/
  `resolve_round_id` resolve via `pilot.run`; `runs.py` `_has_cycle`/`_label_from_notes`/`_summary`/
  `list_runs`/`get_run`/`create_run` read from the row; `bids.py:234` reads the row's `cycle_id`.
  Severs "run = folder" for the console. Test: a run with NO folder still resolves/lists. Harness
  untouched. Risk: medium.
- **Slice 4 — uploads stream to ingest (no disk).** `ingest_setup`/`import_bids` drop `write_to_run`;
  read `file.file.read()` → pass bytes to new `PilotService.ingest_setup_bytes`/`ingest_bids_bytes`/
  `ingest_any_bytes` (the Path methods today just `Path(uploaded).read_bytes()`). Quarantine/supersede
  NOTES → return counts in the API response (console) instead of writing NOTES.md. Open ADR-0018 §4
  sub-decision: raw flexible upload → object storage (GCS) for audit; pre-GCS, not retained (flag for
  go-live). Harness untouched. Risk: medium.
- **Slice 5 — downloads generate on request; remove `outputs/` writes (console).** `/files`,
  `/files/{name}`, `/archive` become projections of `enumerate_deliverables` (render bytes →
  `Response`/in-memory zip; no `FileResponse`/dir-scan/`build_run_zip`). Console `run_round`/
  `freeze_award`/`record_adjustment` do the governed DB writes only (engine seal, audit event,
  `awd_service.*`) and skip the workbook/guide/post-award `wb.save`, `_render_kanban` files,
  `export_run_data`, `feedback_file`, `git_commit_run` (gate via a `persist_outputs`/console flag).
  Tests compare on DATA not raw bytes (date-stamped provenance lines differ across days). Harness
  untouched. Risk: medium-high (touches analysis/freeze/adjust). Behavior-preserving by E-39.
- **Slice 6 — decommission console vault usage.** Console `create_run`/`start_run` no longer scaffold
  the folder / write RUN.md/NOTES.md/cycle_id.txt/run_data.json/.rehearsal / git-commit. Close-out
  deletes the `pilot.run` row (optionally a DB-rendered archive zip). `export_run_data`/`feedback_file`/
  `snapshot_run` become harness-only. Risk: low after 3–5.

## Biggest risk + mitigation

Severing run identity from the filesystem (Slice 2→3). Mitigation: the Slice-2 dual-write + a backfill
of `pilot.run` rows for existing folders before Slice 3 flips the read source. Second-order: byte-drift
between stored and on-request renders due to `date.today()` provenance stamps — tests compare on data,
not raw bytes, for timestamped outputs.

## MCP harness

Untouched under every slice (keeps `vault.py`, `run_db.py`, `cycle_id.txt`, git autopush, `rehydrate`).
It calls the `write_*`(disk) generators and the Path-taking ingest methods.
