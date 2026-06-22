---
doc: AS-BUILT EXHAUSTIVE AUDIT — master index + resumable tracker
id: ASBUILT-INDEX
status: IN PROGRESS (started 2026-06-22). Fresh, ground-up. Reuses NOTHING from the old `audit/`.
rule: nothing skipped · nothing assumed · every file (incl. empty) · detailed WHY for everything · not one char skipped
contract: see /CLAUDE.md (ABSOLUTE REQUIREMENTS + GUIDING PRINCIPLES). Every audit agent gets it injected.
---

# As-Built Exhaustive Audit — index & tracker

**⚠️ THE BAR IS `AUDIT_STANDARD.md` — read it first.** This file (the census + slice tracker) is the
SKELETON. `AUDIT_STANDARD.md` defines the SUBSTANCE: the 3 layers, flow charts, every transformation /
decimal mapped, every process edge case, per-file detailed WHY. A file list is NOT the audit.

**Scope:** every one of the **896 owned files** (see `FILE_CENSUS.md` — full metadata: name, ext,
bytes, empty-flag, created, modified). Vendored/generated trees (`.git`, `node_modules`, `.venv`,
caches) are counted in the census, not per-file audited (not ours).

**Three-layer report (synthesized AFTER the per-file slices land):**
- `LAYER1_ARCHITECTURE_DATA_DATAFLOWS.md` — architecture, data model, data flows.
- `LAYER2_CODE_PROCESS_DECISIONS.md` — code, process, decision points.
- `LAYER3_UX_UI.md` — screens, components, interactions, states.

**Per-file deep audit lives in `AS_BUILT/files/<slice>.md`.** Each file entry MUST carry: path · what
it is · **detailed WHY it exists / why it's shaped this way / what breaks without it** · key
functions/tables/exports · inputs→outputs · dependencies · gotchas · cross-ref to its census row.

## Resume protocol (after a context clear)
1. Read `/CLAUDE.md` then this file.
2. Find the first slice with status `PENDING` below.
3. Launch a constrained agent with the ABSOLUTE REQUIREMENTS injected + "read CLAUDE.md first",
   scoped to that slice's paths, told to WRITE its output to the slice's output file (exhaustive,
   detailed-why, nothing skipped).
4. On return: review, commit, flip the row to `DONE`, update the census cross-refs.
5. When all slices are DONE, synthesize the three LAYER reports from them.

## Slice tracker

| Slice | Scope (paths) | Output file | Status |
|-------|---------------|-------------|:------:|
| B1 | `backend/app/engine/**` (scoring, allocation, formulas, v3, runner, guards, stub, interface) | `files/B1_engine.md` | ✅ DONE (867 ln, 9 files) |
| B2 | `backend/app/pilot/**` (service, ingesters, deliverables, vault, status, models) | `files/B2_pilot.md` | PENDING |
| B3 | `backend/app/domain/{ref,cyc,bid}/**` | `files/B3_domain_ref_cyc_bid.md` | PENDING |
| B4 | `backend/app/domain/{eng,awd,norm,perf,audit}/**` | `files/B4_domain_eng_awd_norm_perf_audit.md` | PENDING |
| B5 | `backend/app/api/**` + `backend/app/core/**` | `files/B5_api_core.md` | PENDING |
| B6 | `backend/app/{auth,comms,output,fiscal,cycle}/**` + any remaining `app/**` | `files/B6_auth_comms_output_fiscal_cycle.md` | PENDING |
| B7 | `backend/alembic/**` (20 migrations) + `db/baseline/**` (schema.sql, NAMING_MAP, README) | `files/B7_migrations_schema.md` | PENDING |
| B8a | `backend/tests/**` part 1 (api, auth, pilot) | `files/B8a_tests_1.md` | PENDING |
| B8b | `backend/tests/**` part 2 (engine, output, domain, conftest) | `files/B8b_tests_2.md` | PENDING |
| B9 | `backend/scripts/**`, `backend/demo/**`, `backend/{pyproject.toml,Dockerfile,README,*.cfg,*.ini}` | `files/B9_scripts_demo_config.md` | PENDING |
| F1 | `frontend/app/**` (routes, layouts, globals) | `files/F1_app_routes.md` | PENDING |
| F2a | `frontend/components/{ui,shell,auth}/**` | `files/F2a_components_ui_shell_auth.md` | PENDING |
| F2b | `frontend/components/{alignment,awards}/**` | `files/F2b_components_alignment_awards.md` | PENDING |
| F2c | `frontend/components/{intake,runs}/**` | `files/F2c_components_intake_runs.md` | PENDING |
| F3 | `frontend/lib/**` + `frontend/{next.config.mjs,tailwind.config.ts,package.json,tsconfig,Dockerfile,*.css}` | `files/F3_lib_config.md` | PENDING |
| D1 | `project/0*_*.md` (charter→governance) + `project/{DATA_AND_PROCESS_MAP,DESIGN_BRIEF,NO_FILE_STORAGE_PLAN,PRE_TEST_READINESS,RECONCILIATION_SEAMS}.md` | `files/D1_project_governance.md` | PENDING |
| D2 | `project/squads/**` | `files/D2_squads.md` | PENDING |
| D3 | `project/design/**` (canonical; redesign3 uploads = note as snapshots) | `files/D3_design.md` | PENDING |
| D4 | `docs/adr/**` + `specs/**` | `files/D4_adr_specs.md` | PENDING |
| D5 | `project/triage/**`, `reference/**`, `mcp/**`, `deploy/**`, `infra/**`, root `*.md`, `*.json`, `.mcp.json` | `files/D5_triage_ref_mcp_deploy_root.md` | PENDING |
| D6 | `var/**` (design snapshots + run vault notes + demo outputs) | `files/D6_var_archives.md` | PENDING |
| R1 | root config/dotfiles (`.gitignore`, `.dockerignore`, `.gcloudignore`, `.editorconfig`, `.github/**`, `docker-compose*.yml`, `.claude/**`) | `files/R1_root_config.md` | PENDING |

(Slices may be split further if a single agent can't be exhaustive within one pass — record the split here.)

## Empty files (18) — must each be explained (why it exists empty)
Listed in `FILE_CENSUS.md` (grep `EMPTY`). Each gets an entry in its slice with the reason it is
intentionally empty (e.g. package marker, placeholder, `.gitkeep`) — never skipped.
