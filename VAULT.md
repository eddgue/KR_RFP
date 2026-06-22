---
doc: THE VAULT — map of every markdown doc in the system, wiki-linked
id: VAULT
updated: 2026-06-22
note: Obsidian-style [[links]] use full paths so duplicate filenames resolve uniquely.
      157 .md files total; ~30 are vendored (.venv) and excluded. Everything else is mapped below.
      The complete FILE census (all 896 owned files, code + docs + config) is [[AS_BUILT/FILE_CENSUS|FILE_CENSUS]].
---

# 🗺️ The Vault — document map

## ⭐ Operating spine (read these first)
- [[CLAUDE|CLAUDE.md]] — the operating contract: ABSOLUTE REQUIREMENTS + GUIDING PRINCIPLES.
- [[HANDOVER|HANDOVER.md]] — current state + how to resume after a context clear.
- [[AS_BUILT/00_INDEX|AS-BUILT audit index]] — exhaustive audit tracker.
- [[AS_BUILT/FILE_CENSUS|FILE_CENSUS]] — every owned file with metadata (name/ext/empty/dates).

## 🏛️ Governance & decisions (the single sources of truth)
- [[project/00_PROJECT_CHARTER]] · [[project/01_TEAM_STRUCTURE_AND_RACI]] · [[project/02_WAYS_OF_WORKING|02_WAYS_OF_WORKING (NOT-MVP)]]
- [[project/03_DECISION_LOG|03_DECISION_LOG]] — **every decision D1–D45** (D19 no-MVP, D42/43/44 grain/pricing/freeze, D45 contract).
- [[project/04_PROGRAM_BACKLOG|04_PROGRAM_BACKLOG]] — epics E-00…E-44.
- [[project/05_MILESTONE_ROADMAP]] · [[project/06_MOBILIZATION_REPORT]] · [[project/08_RELEASE_GOVERNANCE|08_RELEASE_GOVERNANCE (principles)]]
- [[project/07_AS_BUILT_PROCESS_AUDIT|07_AS_BUILT_PROCESS_AUDIT (old — superseded by AS_BUILT/)]]

## 🧱 Architecture, data & storage
- [[project/DATA_AND_PROCESS_MAP]] · [[project/RECONCILIATION_SEAMS]] · [[project/NO_FILE_STORAGE_PLAN]]
- [[db/baseline/README|db/baseline/README]] · [[db/baseline/NAMING_MAP|NAMING_MAP]] (schema.sql is code, in the census)
- ADRs: [[docs/adr/ADR-0001-clean-room-reconciliation|ADR-0001]] · [[docs/adr/ADR-0002-frontend-stack|0002]] · [[docs/adr/ADR-0003-execution-model|0003]] · [[docs/adr/ADR-0004-tenancy-model|0004]] · [[docs/adr/ADR-0006-engine-brain|0006]] · [[docs/adr/ADR-0013-pricing-storage-and-display|0013]] · [[docs/adr/ADR-0014-pricing-safeties|0014]] · [[docs/adr/ADR-0016-strategy-agnostic-platform|0016]] · [[docs/adr/ADR-0017-hosting-platform|0017]] · [[docs/adr/ADR-0018-storage-model|0018]]

## ⚙️ Engine (the brain)
- [[project/squads/engine-domain/V3_ENGINE_LOGIC|V3_ENGINE_LOGIC]] · [[project/squads/engine-domain/GOLDEN_MASTER|GOLDEN_MASTER]] · [[project/squads/engine-domain/PLAN|engine PLAN]] · [[project/squads/engine-domain/SPIKE_D2_engine|SPIKE_D2]] · [[project/squads/engine-domain/TOMATO_RUN|TOMATO_RUN]]
- [[backend/app/engine/README|backend/app/engine/README]]

## 🧩 Squad plans
- [[project/squads/architecture/PLAN|architecture PLAN]] · [[project/squads/architecture/SKELETON|SKELETON]]
- [[project/squads/platform-data/PLAN|platform-data PLAN]] · [[project/squads/platform-data/FEEDS_ITRADE|FEEDS_ITRADE]] · [[project/squads/platform-data/CYCLE_FIELDTOMATO_STRUCTURE|CYCLE_FIELDTOMATO_STRUCTURE]]
- [[project/squads/experience/PILOT_SYSTEM_DESIGN|PILOT_SYSTEM_DESIGN]] · [[project/squads/experience/INTAKE_TEMPLATE_DESIGN]] · [[project/squads/experience/EMAIL_STYLE_AND_MAILMERGE]] · [[project/squads/experience/HARNESS_REHEARSAL]] · [[project/squads/experience/PILOT_INPUT_DOCS_SPEC]] · [[project/squads/experience/SCENARIO_TOOL_DESIGN_STUDY]] · [[project/squads/experience/SKILL_HARNESS_DESIGN]]
- [[project/squads/product/PLAN|product PLAN]] · [[project/squads/product/KICKOFF_KEYSTONE_SPEC|KICKOFF_KEYSTONE_SPEC]]
- [[project/squads/platform-devops/PLAN|devops PLAN]] · [[project/squads/quality/PLAN|quality PLAN]] · [[project/squads/security/PLAN|security PLAN]]

## 🎨 Design
- [[project/design/DESIGN_REQUESTS|DESIGN_REQUESTS]] · [[project/design/DESIGN_PACKAGE|DESIGN_PACKAGE]] · [[project/design/DESIGNER_PROMPT]] · [[project/design/SCREEN_COVERAGE_AUDIT|SCREEN_COVERAGE_AUDIT]] · [[project/design/REDESIGN3_GAP_ANALYSIS|REDESIGN3_GAP_ANALYSIS]]
- First draft / handoff: [[project/design/first_draft/DESIGN_REVIEW]] · [[project/design/first_draft/DESIGN_FEEDBACK_v1]] · [[project/design/handoff/HANDOFF_NOTES]] · [[project/design/handoff/DESIGN_FEEDBACK_v2]]
- (redesign3 `.dc.html` mockups + uploads are files in the census; the upload `.md` are snapshots of the above.)

## 📐 Specs (original + rfp engine + intake sessions)
- [[specs/rfp-engine/BUILD_00_README|rfp-engine BUILD_00]] · [[specs/rfp-engine/BUILD_01_SYSTEM_OVERVIEW_AND_ADRS|BUILD_01]] · [[specs/rfp-engine/BUILD_02_DATA_MODEL|BUILD_02]] · [[specs/rfp-engine/BUILD_04_TECH_SPEC|BUILD_04]]
- Intake sessions: [[specs/rfp-engine/intake/00_INDEX|intake 00_INDEX]] · SESSION-01…06 (in census).
- [[specs/original-engine/BUILD_00_README|original-engine BUILD_00]] (+ 01/02/04, the forked legacy spec).

## 🚀 Deploy / infra / MCP / reference
- [[deploy/gcp/README|deploy/gcp/README]] · [[WEB_DEPLOYMENT|WEB_DEPLOYMENT]] · [[infra/README]] · [[README|root README]]
- [[mcp/README|mcp/README]] · [[mcp/agents/rfp-engine|rfp-engine agent]] · [[mcp/agents/rfp-secretary|rfp-secretary agent]] · [[mcp/skills/rfp-pilot/SKILL|rfp-pilot SKILL]]
- [[reference/README]] · [[reference/SAMPLE_REGISTER|SAMPLE_REGISTER]] · [[reference/incoming/README]]
- [[backend/README]] · [[frontend/README]]

## 🔎 Triage & findings
- [[project/triage/DRIFT_RECONCILIATION|DRIFT_RECONCILIATION]] — what's real vs not (the audit answer).
- [[project/triage/MANUAL_MODEL_FINDINGS|MANUAL_MODEL_FINDINGS]] · [[project/triage/BACKFILL_CANDIDATES|BACKFILL_CANDIDATES]]
- [[project/PRE_TEST_READINESS|PRE_TEST_READINESS]] · [[project/DESIGN_BRIEF]]

## 🗄️ Archives / snapshots (kept, lower priority)
- `var/design_deliverable/`, `var/design_review{,2,3}/uploads/…`, `project/design/redesign3/uploads/…`
  — point-in-time SNAPSHOTS of the design/audit docs above (duplicates). Audited as a group in
  slice **D6** / **D3**, flagged as snapshots, not canonical.
- `audit/00–04` — the OLD as-built/gap audit; superseded by `AS_BUILT/` (this fresh one). Audited in D5.
- `var/vault/runs/*/{RUN,NOTES,FEEDBACK}.md` — MCP harness run-vault notes (real run artifacts). Slice D6.
