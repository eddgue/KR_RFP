# Slice D1 — Project Governance (As-Built per-file deep audit)

> **Slice:** D1 — `project/00_PROJECT_CHARTER.md` … `08_RELEASE_GOVERNANCE.md` (the full numbered range 00–08, i.e. 00/01/02/03/04/05/06/07/08), plus `project/{DATA_AND_PROCESS_MAP,DESIGN_BRIEF,NO_FILE_STORAGE_PLAN,PRE_TEST_READINESS,RECONCILIATION_SEAMS}.md`, plus the root operating docs `CLAUDE.md`, `HANDOVER.md`, `VAULT.md`, `README.md`, `WEB_DEPLOYMENT.md`.
> **Method:** `find` + the explicit list, cross-checked against `AS_BUILT/FILE_CENSUS.md`, each file read end-to-end. **READ-ONLY** — no source touched.
> **Contract honored:** `/CLAUDE.md` ABSOLUTE REQUIREMENTS + `AS_BUILT/AUDIT_STANDARD.md` (detailed WHY on every entry; nothing skipped/assumed; cross-references mapped).
> **Tracker note:** The `00_INDEX.md` slice tracker assigns the 5 root `*.md` files (CLAUDE/HANDOVER/VAULT/README/WEB_DEPLOYMENT) to slice **D5**; this task's explicit prompt pulls them into **D1**. They are audited here in full; D5 should reference this file for them rather than re-audit (overlap recorded so neither slice silently double-counts or drops them).

---

## Census cross-check (all 19 in-scope files accounted for)

All bytes match the filesystem (`wc -c`) exactly; **none are empty** (the 18 empty files in the census are elsewhere). Census rows: 9, 10, 11 (root) and 342–355 (`project/`).

| Census # | Path | Ext | Bytes | Lines | Empty? | Created (git author) | Modified (git author) | Trk |
|---:|---|---|---:|---:|:--:|---|---|:--:|
| 342 | `project/00_PROJECT_CHARTER.md` | md | 6208 | 79 | n | 2026-06-18T05:03:29Z | 2026-06-18T05:03:29Z | y |
| 343 | `project/01_TEAM_STRUCTURE_AND_RACI.md` | md | 6517 | 78 | n | 2026-06-18T05:03:29Z | 2026-06-18T05:03:29Z | y |
| 344 | `project/02_WAYS_OF_WORKING.md` | md | 7743 | 92 | n | 2026-06-18T05:03:29Z | 2026-06-21T07:34:55Z | y |
| 345 | `project/03_DECISION_LOG.md` | md | 77086 | 376 | n | 2026-06-18T05:03:29Z | 2026-06-22T18:36:07Z | y |
| 346 | `project/04_PROGRAM_BACKLOG.md` | md | 43116 | 90 | n | 2026-06-18T05:03:29Z | 2026-06-22T14:16:54Z | y |
| 347 | `project/05_MILESTONE_ROADMAP.md` | md | 3922 | 54 | n | 2026-06-18T05:03:29Z | 2026-06-18T05:03:29Z | y |
| 348 | `project/06_MOBILIZATION_REPORT.md` | md | 8454 | 82 | n | 2026-06-18T05:27:10Z | 2026-06-18T05:27:10Z | y |
| 349 | `project/07_AS_BUILT_PROCESS_AUDIT.md` | md | 86058 | 560 | n | 2026-06-21T04:30:57Z | 2026-06-22T02:32:02Z | y |
| 350 | `project/08_RELEASE_GOVERNANCE.md` | md | 9912 | 105 | n | 2026-06-21T16:38:21Z | 2026-06-21T17:43:43Z | y |
| 351 | `project/DATA_AND_PROCESS_MAP.md` | md | 24181 | 365 | n | 2026-06-22T02:11:15Z | 2026-06-22T02:11:15Z | y |
| 352 | `project/DESIGN_BRIEF.md` | md | 3700 | 51 | n | 2026-06-21T19:28:40Z | 2026-06-21T19:28:40Z | y |
| 353 | `project/NO_FILE_STORAGE_PLAN.md` | md | 6532 | 87 | n | 2026-06-21T22:55:59Z | 2026-06-21T23:59:48Z | y |
| 354 | `project/PRE_TEST_READINESS.md` | md | 7362 | 101 | n | 2026-06-22T04:29:41Z | 2026-06-22T14:16:54Z | y |
| 355 | `project/RECONCILIATION_SEAMS.md` | md | 6600 | 65 | n | 2026-06-22T01:54:00Z | 2026-06-22T03:52:08Z | y |
| 9 | `CLAUDE.md` | md | 6799 | 105 | n | 2026-06-22T18:36:07Z | 2026-06-22T18:36:07Z | y |
| 10 | `README.md` | md | 5202 | 63 | n | 2026-06-18T04:48:46Z | 2026-06-21T20:23:33Z | y |
| 11 | `WEB_DEPLOYMENT.md` | md | 9558 | 132 | n | 2026-06-20T22:27:25Z | 2026-06-21T02:19:43Z | y |
| — | `HANDOVER.md` | md | 4538 | 63 | n | fs mtime 2026-06-22 18:54 | 2026-06-22 18:54 | (not in census excerpt; counted) |
| — | `VAULT.md` | md | 6176 | 67 | n | fs mtime 2026-06-22 18:54 | 2026-06-22 18:54 | (not in census excerpt; counted) |

> **Census GAP flagged:** `HANDOVER.md` and `VAULT.md` are NOT present in `AS_BUILT/FILE_CENSUS.md` (the grep over the census returns no rows for them, and the root block lists only rows 9/10/11 = CLAUDE/README/WEB_DEPLOYMENT). Both files exist on disk (4538 / 6176 bytes, both referenced AS the resume spine inside HANDOVER and VAULT themselves and from `00_INDEX`-adjacent docs). The census header dates itself "Generated 2026-06-22T18:52Z" while both files carry mtime 18:54 — they were committed **after** the census was generated, so the census is two files stale. **Recommended action:** regenerate `FILE_CENSUS.md` so the "896 owned files" total includes these two; until then the audit-standard rule "every single file is listed" is technically violated for these two. (They are fully audited below regardless.)

---

# Part A — The numbered governance series (`project/00`–`08`)

These nine files are the **PM-owned program governance spine** (ids PM-000…PM-008). They were authored at program mobilization (00–06 on 2026-06-18), then 07/08 were added 2026-06-21 when the Release-Governance + As-Built frameworks were adopted. 02/03/04/07 are the *living* docs (recently modified); 00/01/05/06 are stable Phase-0 artifacts.

---

## D1.1 — `project/00_PROJECT_CHARTER.md`

- **Path:** `/home/user/KR_RFP/project/00_PROJECT_CHARTER.md` · **ext:** md · **bytes:** 6208 · **lines:** 79 · **empty:** no · **census:** #342.
- **What:** The Project Charter (id **PM-000**, v0.1, status "Draft — pending sponsor ratification"). The founding document that frames the entire program ("Project Spine").
- **DETAILED WHY (what it governs · who it binds · why it exists):** It is the **root authority** of the `project/` tree — every other PM doc declares `depends_on: PM-000`. It exists to convert the two pre-existing spec packages (the intake-derived BRIEF and the inherited AS-BUILT inventory) plus the `audit/` reconciliation into a **single sanctioned program direction**, so the build is not started from a contested premise. It binds the **sponsor (Ed/Sourcing)** as product authority and the **PM/Architect** as delivery owners. Without it there is no agreed scope boundary, no success-criteria contract (S1–S8), and no statement of the three problems being killed (historical blindness, non-standard process, manual dependence) — every downstream decision would lack a ratifiable "why." It encodes the program's **one-sentence vision**: "the brief's brain and outward-facing half, built on the as-built's governed spine, with pricing lifted to kickoff and the five safeties made executable … proven on one real cycle."
- **Structured outline (every section):**
  1. **Why we are here** — the reconciliation thesis ("neither is the product"); the three problems.
  2. **Vision (one sentence)** — the target.
  3. **Scope** — *In scope* (governed Postgres SoR reconciled from the 63-table store; the 5-factor + split + 7-lens engine as a library; full cycle lifecycle kickoff→sign-off→outputs; feeds iTrade/KCMS/scorecard; gaps G1–G12 + 7 keeps; net-new enterprise layer; the web front end built last per ADR-001). *Out of scope (this release)* — cleaning historical graveyard cycles; contract authoring/e-sign beyond assembly; real-time/high-throughput; non-produce categories.
  4. **Success criteria (S1–S8)** — table with measures: S1 open last cycle <2s; S2 real-data pilot passes (retires R1); S3 decision-support not auto-award; S4 split awards; S5 generated outputs; S6 governance (immutable runs, freeze-and-layer, no hard deletes, live audit, draft→sent); S7 enterprise NFRs; S8 savings vs STLY.
  5. **Governance** — sponsor/PM/architect roles; supersession rule (Target Spec v1.0 supersedes both packages; until then BRIEF=intent, AS-BUILT=what-exists, audit=reconciliation).
  6. **Key constraints & assumptions (A1–A5)** — existing 63-table/14-migration/796-test store; v3 engine verified; Postgres ample; nothing has touched real data (top risk); Python/FastAPI/SQLAlchemy stack.
  7. **Top risks** — R1 no real data (Critical) · R2 wrong-brain · R3 greenfield rebuild · R5 inert safeties · R7 no security/tenancy.
  8. **Milestones at a glance** — Phase 0 Reconcile → A → B → C → D → E → F.
  9. **Definition of done (program level)** — all 8 criteria; Target Spec current; pilot passed; NFR sign-off; web renders live+historic identically.
- **Cross-references:** depends_on `audit/00–04`, `specs/rfp-engine`, `specs/original-engine`; success criteria S1–S8 are referenced throughout 04/05; risk register lives in `audit/04_RISKS_DECISIONS_ROADMAP.md`; decisions D1–D7 referenced (sponsor ratifies). **Drift note:** still marked "Draft (pending sponsor ratification)" and references only D1–D7 / R-register, while the program has since ratified D1–D45 and shipped a live system — the charter is the least-updated of the living spine (frozen at 2026-06-18).

---

## D1.2 — `project/01_TEAM_STRUCTURE_AND_RACI.md`

- **Path:** `/home/user/KR_RFP/project/01_TEAM_STRUCTURE_AND_RACI.md` · **ext:** md · **bytes:** 6517 · **lines:** 78 · **empty:** no · **census:** #343.
- **What:** Team Structure & RACI (id **PM-001**, v0.1, Draft). Defines the program org, six delivery squads, leadership, and the responsibility matrix.
- **DETAILED WHY:** It exists to make ownership unambiguous and to **map agent-squads onto a human delivery org** — each squad lead is "instantiated as a specialist agent under the PM's orchestration," but the structure is written so it cleans onto people if staffed. It binds **who is Responsible/Accountable/Consulted/Informed** for every workstream and every gating decision (D1/D2/D3/D6), so no decision or build has a missing owner. Without it the "nitro mode" of constrained agents has no role contract and the RACI tiebreaks (esp. the sponsor being **Accountable** on D1/D2/D6) are undefined. It encodes the program's **Inheritance rule** (operating principle §6): take *shape/intent* from the BRIEF and *constraint discipline + the 7 KEEP capabilities* from the AS-BUILT — never regress to the brief's thinner schema, never carry the as-built's wrong brain.
- **Structured outline:**
  1. **Org at a glance** — ASCII tree: Sponsor → PM → {Architect, Product/BA} + 6 squads.
  2. **Leadership** — PM / Solution Architect (`architect` agent) / Product Owner-BA (`product` agent).
  3. **Delivery squads (1–6)** — Platform & Data; Engine & Domain; Experience (Web); Platform Eng/DevOps; Security & Compliance; Quality & Assurance — each with the gaps/capabilities it owns and lead staffing.
  4. **Squad outputs (first deliverable each on mobilization)** — 6 items (migration plan, engine/API spec, UX blueprint, CI/CD plan, security/NFR spec, test strategy + pilot plan).
  5. **RACI matrix** — workstreams/decisions × {PM, Architect, Product, Plat&Data, Engine, Exp, DevOps, Sec, QA, Sponsor}; sponsor is **A** on D1/D2/D6.
  6. **Operating principle** — the Inheritance rule; the Architect arbitrates each ruling as an ADR.
- **Cross-references:** depends_on PM-000; squads map to epics in 04 (e.g. Squad 1 → E-01/02/06/08–12; Squad 2 → E-18/19/20; Squad 5 → E-03/04/24); RACI rows reference D1/D2/D3/D6; the Inheritance rule generalizes ADR-0006 ("lift the logic, drop the Excel"). Squad plans live under `project/squads/` (slice D2).

---

## D1.3 — `project/02_WAYS_OF_WORKING.md`

- **Path:** `/home/user/KR_RFP/project/02_WAYS_OF_WORKING.md` · **ext:** md · **bytes:** 7743 · **lines:** 92 · **empty:** no · **census:** #344 · **modified 2026-06-21** (the As-Built §8 release-gate language was added).
- **What:** Ways of Working (id **PM-002**, v0.2, Draft). The operating model: delivery model, cadence/ceremonies, engineering standards, DoR/DoD, quality gates, documentation standard, and the As-Built-Audit-as-release-gate contract.
- **DETAILED WHY:** This is one of the **READ-BEFORE-ANY-NON-TRIVIAL-WORK** docs named in `CLAUDE.md`. It binds **every engineer/agent** to the **NOT-MVP delivery model (D19)**, the governance invariants enforced in code+DB, and the §8 audit-trigger discipline. It exists so "how we build" is not tribal: it codifies that each module ships as a **functional prototype of the full capability** (never a thin slice), that backend precedes frontend (ADR-001), that G1+G2 ship together, that migrations are roundtrip-tested, and that **no major version is complete until the As-Built Audit is updated (D37)**. Without it the no-MVP rule, the branch discipline, and the pre-merge audit-impact review (the DoD's load-bearing clause) have no canonical home.
- **STANDING RULES (this is one of the two "standing-rules" docs the prompt asks be enumerated):**
  - **§1 Delivery model (the binding rules):** Modular, prototype-fidelity — **NOT MVP** (D19); phased/gate-driven (Phases 0/A–F, gates = demonstrated outcomes not task counts); **backend before frontend** (ADR-001); **two changes ship together** (G1 split + G2 scoring in one engine increment); modules built end-to-end (schema→service→API→test→UI) at real fidelity, never stubbed.
  - **§2 Cadence & ceremonies:** program standup (per session) · backlog grooming (per phase entry) · architecture review (on each ADR) · decision review (on OPEN decision reaching due-by → escalate to sponsor) · phase gate review (end of each phase) · risk review (per phase).
  - **§3 Engineering standards (non-negotiable governance invariants, enforced in code + DB):** trunk-based + short-lived feature branches, PR review by owning squad lead, branch naming `squad/<area>/<short-desc>`, commits reference epic+gap, **no direct commits to default branch; current dev branch `claude/wizardly-pasteur-n4acb8`**; every schema change is an Alembic migration, **roundtrip-tested (upgrade→downgrade→upgrade) in CI**, additive-first (breaking G1/G2 isolated+flagged+sequenced), no SQLite idioms / real Postgres booleans + real enum constraints; Python/FastAPI/SQLAlchemy 2.x typed, **services never own a transaction (add+flush, never commit)**, engine is a library with a single `run()` entry point + no Excel-formatting ported, API contract-first (OpenAPI) + every endpoint authn/authz-guarded; **GOVERNANCE INVARIANTS:** immutable sealed runs (corrections are new runs) · freeze-and-layer of awards (raw never overwritten) · no hard deletes (supersede via new rows) · append-only **live** audit log · **decision-support only — the engine never auto-asserts an award** (`BANNED_DECISION_WORDS` guard).
  - **§4 Definition of Ready:** AC written · gap/epic linked · data-model impact identified · test approach noted · security/tenancy reviewed · dependencies resolved/flagged.
  - **§5 Definition of Done:** code+migration merged · unit/integration green · migration roundtrip passes · API contract updated · RBAC/tenancy honored · audit events emitted · docs/ADR updated · **pre-merge audit-impact review run + As-Built Audit & gap register updated in the same change if any audit trigger hit (§8, D37/D39)** · demoable vertical slice · no new hard-delete or live-formula fragility.
  - **§6 Quality gates (per phase):** CI green (lint/type/tests/migration roundtrip) · security review for new endpoint/entity · architecture review for any governance-invariant change · **Real-data check from Phase B onward** (slice works against the pilot dataset) · **As-Built Audit current** (a major version is not complete until updated, D37).
  - **§7 Documentation standard:** decisions → ADRs (`docs/adr/`) + the decision log; the Target Spec v1.0 is the living source of truth; originals/audit frozen under `specs/` and `audit/`; squad plans in `project/squads/<squad>/`.
  - **§8 As-Built Audit — living model of reality, event-triggered, a release gate:** the audit (PM-007) documents reality not intent (D39); refreshed on architecture events not calendar; headline rule **"No major version is complete until the As-Built Audit is updated" (D37)**; pre-merge audit-impact review (workflow · state transitions · persistence · runtime boundaries · permissions · governance · auditability · user-visible behavior · failure domains → if any "yes", audit + gap register updated in the same change before merge); re-audit triggers (per PM-007 §12.1); release-gate states **PASS / CONDITIONAL / FAIL**; each update records the **delta** (Added/Modified/Removed · Closed gaps · New gaps).
- **Cross-references:** D19 (NOT-MVP) · D37/D39 (audit gate) · ADR-001 (backend-first) · PM-007 §12–§13 (triggers/gates) · the DoD §5 clause is operationalized in 08 + 07. CLAUDE.md names this as a mandatory pre-work read.

---

## D1.4 — `project/03_DECISION_LOG.md`

- **Path:** `/home/user/KR_RFP/project/03_DECISION_LOG.md` · **ext:** md · **bytes:** 77086 · **lines:** 376 · **empty:** no · **census:** #345 · the **largest** governance doc; **modified 2026-06-22T18:36** (same timestamp as the CLAUDE.md commit — D45 was logged with the CLAUDE.md operationalization).
- **What:** The Decision Log (id **PM-003**, v0.1, status **Living**). The register of program-shaping decisions D1–D45 + dependencies DEP-1…DEP-7. Status vocabulary: **OPEN** (awaiting sponsor) · **RATIFIED** · **SUPERSEDED** (plus the informal sub-states **NOTE / WISH-LIST / NOTE-with-resolved-sub-decisions**).
- **DETAILED WHY:** This is the **single canonical place for every decided thing** (CLAUDE.md GUIDING PRINCIPLES: "decisions → `project/03_DECISION_LOG.md`"). It exists because the operating model assumes **context clears every 3rd prompt** — state must live on disk, not in memory; the log is how a fresh session/agent reconstructs *why the system is the way it is* without re-litigating. It binds every builder: each decision carries the PM/Architect recommendation so ratification is a confirmation not a research task; **D19 (no-MVP) and D45 (operating-contract operationalization) are the tiebreakers** referenced by CLAUDE.md. Without it the program drifts — exactly the failure D45 was raised to fix (rules lived only in unread docs). DEP-n are logistics blockers, not choices.

### EVERY decision D1–D45 enumerated (id · title · status)

| ID | Title | Status |
|---|---|---|
| **D1** | Build path → clean-room reconciliation (ADR-0001) | **RATIFIED 2026-06-18** |
| **D2** | The brain → adopt v3 (Option A) (ADR-0006) | **RATIFIED 2026-06-18** |
| **D3** | Pricing placement & safeties (lift to kickoff, make executable) | **OPEN** (needed by Phase C/D) |
| **D4** | Outward-facing sequence (award→freeze→sign-off→outputs; booking guide first) | **OPEN** (needed by Phase E entry) |
| **D5** | Net-new enterprise scope (tenancy/RBAC/PII/retention/NFRs from start) | **OPEN** (needed by Phase 0/A) |
| **D6** | Frontend / enterprise web app stack → React/Next.js + TypeScript SPA (ADR-0002) | **RATIFIED 2026-06-18** |
| **D7** | Execution mode for this engagement → plan then scaffold now (ADR-0003) | **RATIFIED 2026-06-18** |
| **D8** | Tenancy model → multi-tenant-capable, single-tenant-operated (ADR-0004) | **RATIFIED 2026-06-18** |
| **D9** | Cycle pricing grain → one model per RFP + item-level participation | **RATIFIED 2026-06-18** |
| **D10** | Split awards behavior → auto max-2 output + free manual per-cell selection (confirms G1) | **RATIFIED 2026-06-18** |
| **D11** | Incumbent & historical/baseline cost source → BOTH sources, display both (+ iTrade actual-paid savings baseline) | **RATIFIED 2026-06-18** |
| **D12** | Pricing storage vs display → period-grain storage, setup-file-driven display (ADR-0013) | **RATIFIED 2026-06-18** |
| **D13** | Pricing safeties = contractual execution terms, NOT engine inputs (ADR-0014) | **RATIFIED 2026-06-18** |
| **D14** | Attribute taxonomy → one shared catalog, sparsely populated | **RATIFIED 2026-06-18** |
| **D15** | Gate-closure backup export (DR/historic) | **RATIFIED 2026-06-18** |
| **D16** | AI assistant (read-only) — NL recall + drafting | **WISH-LIST (lowest priority) 2026-06-18** |
| **D17** | Reference cycle files are AS-IS evidence, not the target design | **RATIFIED 2026-06-18** |
| **D18** | Strategy-agnostic platform: strategies are first-class, developed & run (ADR-0016) | **RATIFIED 2026-06-18** |
| **D19** | Build methodology: modular, full-fidelity prototype versions — **NOT MVP** | **RATIFIED 2026-06-18** |
| **D20** | Round-trip ingest: the system ingests the files it generates | **RATIFIED 2026-06-18** |
| **D21** | Explicit key IDs at every grain; key-based pulls, never guessing | **RATIFIED 2026-06-18** |
| **D22** | Booking guide is the FINAL post-award output; two audiences (internal + per-supplier) | **RATIFIED 2026-06-19** |
| **D23** | Human-facing outputs render resolved NAMES, never key IDs | **RATIFIED 2026-06-19** |
| **D24** | Generated outputs are presentation-quality, not data dumps | **RATIFIED 2026-06-19** |
| **D25** | Live, interactive scenario the buyer can play on (not a flat render) | **RATIFIED 2026-06-19** |
| **D26** | The scenario workbook is an ALIGNMENT / COMPARISON tool, not a summary | **RATIFIED 2026-06-19** |
| **D27** | Data is manipulable; analytical surfaces are flexible, not fixed reports | **RATIFIED 2026-06-19** |
| **D28** | Explanatory text is the engine's computed reason from sealed records — never catch-all, never LLM-generated | **RATIFIED 2026-06-19** |
| **D29** | The bid column set is a SUPERSET, always available; processes use a subset | **NOTE 2026-06-20** |
| **D30** | Per-run data isolation: each run starts BLANK, no demo data, no cross-run contamination | **NOTE 2026-06-20** |
| **D31** | The pilot skill is a 3-agent HARNESS (orchestrator/engine/secretary) with isolated contexts | **NOTE 2026-06-20** |
| **D32** | Version isolation: a LIVE run is pinned to the MCP+Vault+platform version it started on | **NOTE 2026-06-20** |
| **D33** | Scenario B MAY breach max-suppliers-per-DC cap, FLAGGED; Scenario D is the hard-enforced lens | **NOTE 2026-06-20** |
| **D34** | A run's governed DB rides the Vault git as a SQL snapshot (resume on a fresh/ephemeral box) | **NOTE 2026-06-20** |
| **D35** | Kroger fiscal calendar stored AUTHORITATIVELY (data, not a date rule); 13 periods, 4-3-3-3 quarters, 53-week leap years | **NOTE 2026-06-20** |
| **D36** | Web app runs on ONE shared governed DB with strict per-run scoping; reference master shared, transactional per-run | **NOTE 2026-06-21** |
| **D37** | As-Built Audit is event-triggered (not calendar), tracked as deltas, and a release gate | **RATIFIED 2026-06-21** |
| **D38** | Flat-13 period storage: bids stored per-period; engine/awards stay timeframe-grain (Option B) | **RATIFIED 2026-06-21** |
| **D39** | As-Built Audit Governance contract: the audit is the living model of reality | **RATIFIED 2026-06-21** |
| **D40** | Hosting platform: GCP (Cloud Run + Cloud SQL for PostgreSQL) (ADR-0017) | **RATIFIED 2026-06-21** |
| **D41** | Storage model: DB is SoR; deliverables render on request, uploads not persisted (web/Cloud Run); NO storage change before live RFPs (ADR-0018) | **RATIFIED 2026-06-21** |
| **D42** | Price-component grain by surface (collection / storage / display / tables) | **RATIFIED 2026-06-22** |
| **D43** | Pricing modality (FOB/DELIVERED/XDOC) + configurable cost breakdown, set on SETUP (governs award); XDOC verified vs the manual potato model | **RATIFIED 2026-06-22** (sub-decisions resolved) |
| **D44** | Live-test SPEC FREEZE + change-control gate (default = backlog; DRY vs LIVE test tiers) | **RATIFIED 2026-06-22** |
| **D45** | Operating contract OPERATIONALIZED (CLAUDE.md + agent injection); data fidelity is part of NO-MVP | **RATIFIED 2026-06-22** |

### Dependencies (DEP-1…DEP-7 — logistics blockers, not choices)

| ID | Dependency | Status |
|---|---|---|
| **DEP-1** | Isolated read-only access to the existing repo (models, Alembic chain, tests, ECLS) | **OPEN — non-blocking** (baseline from the as-built schema already held) |
| **DEP-2** | One complete RFP process (all rounds of a single category) + fast-follow second template | OPEN — bid workbooks outstanding |
| **DEP-3** | One or two real kickoff docs (the keystone, G5) | OPEN |
| **DEP-4** | Target hosting/cloud + identity provider | **HOSTING RESOLVED (D40/ADR-0017)**; IdP half deferred (G-C/G-J) |
| **DEP-5** | Historical booking guides + prior-cycle award/contract data | OPEN |
| **DEP-6** | Market-price feed — USDA MARS API (series `FVWTRDS-1662`); sponsor HAS a key | **RESOLVED (access available)** |
| **DEP-7** | Award files + round/negotiation analysis | OPEN — deferred, low urgency |

- **"Ratified" footer:** D1–D39 are recorded with per-decision status (the old separate ratification queue is superseded by per-decision status). Note: "gsps" confirmed = "gaps" (sponsor 2026-06-18).
- **Structural note:** D1–D28 are presented as a continuous block; D29–D45 each sit under a `---` separator. The log is the canonical map from **behavior → decision** — AUDIT_STANDARD Layer-2 requires every coded behavior be tied to its D# and the file:line that enforces it (e.g. D33 → `V3Engine._breach_set`; D38 → `app/pilot/service.py::_persist_bid_lines` + `runner._assemble_bids`; D34 → `app/pilot/run_db.py` + `rfp_mcp/rehydrate.py`).
- **Cross-references:** virtually every other doc links here. ADRs 0001/0002/0003/0004/0006/0013/0014/0016/0017/0018 are the formal records for D1/D6/D7/D8/D2/D12/D13/D18/D40/D41. Epics in 04 carry their decisions (E-20←D10/D33, E-44←D42/D43, E-31←D15, E-32←D16, E-42←D41). CLAUDE.md pins D19/D42/D43/D44/D45.

---

## D1.5 — `project/04_PROGRAM_BACKLOG.md`

- **Path:** `/home/user/KR_RFP/project/04_PROGRAM_BACKLOG.md` · **ext:** md · **bytes:** 43116 · **lines:** 90 · **empty:** no · **census:** #346 · **modified 2026-06-22T14:16** (same as PRE_TEST_READINESS — updated together).
- **What:** Program Backlog — Epics (id **PM-004**, v1.0, status "Living — ratified working register, paired with PM-007 + PM-008"). The 12 gaps + 7 keeps + net-new layer converted into epics E-00…E-44, mapped to phases/squads, priority P0/P1/P2/P3.
- **DETAILED WHY:** The **operative item register** — the single place where scope is enumerated as buildable units, each linking its gap (`audit/02`), phase, owning squad, and a slice-done acceptance line. It binds the build sequence to the roadmap (05) and the build-authorization classification to 08. It is dense because many epics carry full sponsor-decision context inline (E-37 comms, E-38 capacity split, E-44 modality/cost). Without it there is no traceable map from "the twelve gaps" to "what is shipped/partial/missing" — the As-Built (07) reconciles *implemented reality* against this *intended register*.

### EVERY epic E-xx enumerated (id · title · status)

| Epic | Title | Status / Priority |
|---|---|---|
| **E-00** | Target Spec v1.0 supersedes both packages | P0 (Phase 0) |
| **E-01** | Validate as-built schema on real Postgres; kill SQLite-isms + no-op CHECK | P0 |
| **E-02** | Obtain & reconcile source-of-truth (repo, migrations, tests, ECLS) | P0 |
| **E-03** | Multi-tenant `client` + RBAC/actor model | P0 |
| **E-04** | Security & NFR specification (PII, retention, threat model, sizing) | P0 |
| **E-05** | Make the audit event log **live** (finish the hash-chain) | **✅ Closed v1.4 (G-B)** |
| **E-06** | KEEP-list hardening (identity FKs, calc-run spine, landed cost, eligibility, VSP) | P1 |
| **E-07** | "Open last cycle" query + read model | P0 |
| **E-08** | iTrade receipt-grain feed (`itrade_receipt`) | P0 (Phase B) |
| **E-09** | KCMS scan feed (`kcms_movement`) | P1 |
| **E-10** | Supplier scorecard — two frozen snapshots (derivation) | P1 |
| **E-11** | Persistent `norm.lot` + attribute taxonomy + sticky map | P0 |
| **E-12** | Two origins + `zip_centroid` distance | P1 |
| **E-13** | **REAL-DATA PILOT** (Phase B exit gate; retires R1) | P0 |
| **E-14** | Kickoff keystone — rich `cyc.*` | P0 (Phase C) |
| **E-15** | Pricing model + safety TERMS declared & stored at kickoff (engine does NOT consume) | P0 |
| **E-16** | Process rail generated from the cycle timeline | P1 (Phase C) |
| **E-17** | Stage-0 governance in-gate (G12) | P1 |
| **E-18** | v3 brain → `bid_score` 5-factor scoring + eligibility inputs | P0 (Phase D) |
| **E-19** | Scenarios A–G (lenses) | P1 |
| **E-20** | Split allocation — `scenario_award` + `volume_share` + cap-breach (ships with E-18) | **✅ Operational** |
| **E-21** | Award object → freeze → `award_layer` | P0 (Phase E) |
| **E-22** | Portfolio sign-off gate (`signoff`) + savings-vs-STLY | P0 |
| **E-23** | Generated outputs — booking guide → deck → letters → email | P0 |
| **E-24** | Draft→SENT governance gate | P1 |
| **E-25** | REST API hardening (contract-first, authn/authz) | P0 (Phase F) |
| **E-26** | Enterprise web app (stack D6) — the console | P0 (Phase F; on the live-test critical path) |
| **E-27** | Platform: environments, CI/CD, IaC, observability | P0 (Phase 0→F) |
| **E-28** | Supplier behavior — contracted-vs-effective analytics | P1 (Phase E / post-pilot) |
| **E-29** | Contract execution — safety reprice + market feed + reprice-and-layer | P1 (Phase E+) |
| **E-30** | Kanban views — RFP portfolio + RFP-by-supplier | P1 (Phase F) |
| **E-31** | Gate-closure backup export (DR / historic) | P1 (Phase E) |
| **E-32** | AI assistant (read-only) — NL data recall + drafting | **P3 (wish-list)** |
| **E-33** | PBA / Contract builder — the post-award final step | P0 (Phase E; spec now, build in parallel) |
| **E-34** | Supplier master list — importer + per-RFP participant selection | P1 (Phase B/C) |
| **E-35** | Per-period price-movement / timeframe-discovery view | P1 (Phase E/F) |
| **E-36** | Progressive timeframe commitment + partial/split award + continuation RFP | P1 (Phase E+) |
| **E-37** | Supplier communications — template-merge email drafts across the lifecycle (6 touchpoints; MECHANISM not AI) | P0 (Phase E/F) |
| **E-38** | Supplier capacity — ingest, allocation-vs-capacity dashboard, cap flag (split into a/b/c) | P0 |
| **E-38a** | Capacity ingest + persist (Capacity sheet → `bid.capacity_statement` + `capacity_constraint`) | **✅ DONE** |
| **E-38b** | Capacity-check evaluator + surface (workbook control tab / read endpoint) | **✅ DONE (workbook tab; G-G closed)** |
| **E-38c** | In-app capacity dashboard | **DEFERRED (Category C — Phase-4)** |
| **E-39** | Canonical formula registry — one "table of calcs", referenced everywhere | **✅ substantially delivered** (P0) |
| **E-40** | Decision-rationale capture — per-cell decision note + freeze note → audit trail | P1 (Phase E) |
| **E-41** | In-app alignment deep workbench (closes G-I) | P1 (Phase F; Category C) |
| **E-42** | Stateless storage — DB is SoR; deliverables render on request, uploads not persisted | **✅ DONE (ADR-0018, slices s0–s6)** |
| **E-43** | Version savepoints + version picker + compare-versions + ROUND/FINAL decision marker | P1; **✅ BUILT 2026-06-22** (migration 0020; residual deferred) |
| **E-44** | Pricing modality (Routing) + configurable cost breakdown + grain-by-surface (D42+D43) | P0 (Phase D/E; parked behind the live-test freeze) |

> **Enumeration note (ordering quirk, kept verbatim):** the table is authored out of strict numeric order — E-29/E-30/E-31/E-32 are inserted between E-15 and E-16; E-33/E-34/E-35/E-36/E-37/E-38(+a/b/c)/E-39/E-40/E-41/E-42/E-43/E-44 are appended after E-28. All 44 base epics (E-00…E-44) plus the 3 sub-epics (E-38a/b/c) are present — **47 rows total**. No epic id is missing in the 00–44 range.

- **Other sections:**
  - **Cross-references** — gaps→epics map (G1→E-20 · G2→E-18/E-19 · G3→E-21/22/23 · G4→E-15 · G5→E-14 · G6→E-08/09/10 · G7→E-12 · G8→E-11 · G9→E-24 · G10→E-16 · G11→E-05 · G12→E-17 · KEEP→E-06 · net-new→E-03/04/27); risk-retirement map (R1→E-13 · R2→E-18/20 · R3→E-01/02 · R5→E-15 · R7→E-03/04).
  - **Notes** — 13+ standing notes incl.: E-18+E-20 are one increment; E-28 is mostly derivation; the synthetic STLY proxy (`_STLY_UPLIFT = 1.04`) to be swapped for real iTrade; **live test runs on the NEW design E-26 (critical path)**; the **LIVE-TEST SPEC FREEZE (D44)**; the **reconciliation seams** watch-list pointer; the **D42 grain-by-surface** + **D43 modality/cost** sponsor notes (with the manual-potato verification + the 3 reconciliation findings A/B/C); the **MCP harness = live-run VERIFICATION ORACLE** note; the UX/UI design handoff pointer (`project/design/handoff/`); the **finalize/close-run** backend-built note (C5, As-Built v1.26); the E-37 email-drafter parking-lot.
- **Cross-references:** depends_on PM-000/PM-007/PM-008/`audit/02`/`audit/04`; classified by 08; reconciled by 07; epics carry their D# and gap; `MANUAL_MODEL_FINDINGS.md`, `RECONCILIATION_SEAMS.md`, `DESIGN_PACKAGE.md`, `REDESIGN3_GAP_ANALYSIS.md` referenced.

---

## D1.6 — `project/05_MILESTONE_ROADMAP.md`

- **Path:** `/home/user/KR_RFP/project/05_MILESTONE_ROADMAP.md` · **ext:** md · **bytes:** 3922 · **lines:** 54 · **empty:** no · **census:** #347 · stable (created==modified 2026-06-18).
- **What:** Milestone Roadmap (id **PM-005**, v0.1, Draft). Phase plan, gates, dependency graph, squad load.
- **DETAILED WHY:** It sequences the epics from 04 into **Phases 0/A–F**, each exiting on a **demonstrated outcome** (not a table count) — so progress is judged by proof, not activity. It binds the order of build (B and C overlap once A is done; D needs B's feeds + C's config; the UI in F does not start until E is proven) and records the **value-timing** truth (the historical payoff begins at cycle 2; Phase B's pilot is the inflection point). Without it the epics have no agreed dependency order and "when does value start" is unstated. **Calendar dates are intentionally omitted** until D1–D7 + DEP-1 land.
- **Structured outline:**
  1. **Phase plan** — table: Phase × Milestone × Epics × exit gate × lead squads (0 Reconcile · A Spine hardening · B History+Normalization+PILOT · C Kickoff keystone+rail · D The brain · E Outward-facing half · F API hardening then UI).
  2. **Dependency graph** — ASCII `0→A→B→D→E→F` with C overlapping B.
  3. **Squad load by phase (H/M/L)** — 6 squads × 7 phases.
  4. **Value-timing note** — payoff at cycle 2; Phase B is where value starts.
  5. **What gates the plan starting** — DEP-1 gates Phase 0 execution; D1/D2/D6/D7 gate detailed planning; sequence is firm regardless.
- **Cross-references:** depends_on PM-004 + `audit/04`; phases map to the epic phase-tags in 04; gates restate the success criteria S1/S2/S4/S5/S8 from 00. **Drift note:** this is the original 7-phase delivery roadmap (Phases 0/A–F); 08 introduces a *different, overlapping* 7-phase frame (Initial Build → Live Run #1/#2 → Consolidation → Final Audit → Production Lock → Maintenance). The two phase models coexist (build-sequence vs release-governance) — a reader must not conflate "Phase B" (roadmap) with "Phase 1" (governance).

---

## D1.7 — `project/06_MOBILIZATION_REPORT.md`

- **Path:** `/home/user/KR_RFP/project/06_MOBILIZATION_REPORT.md` · **ext:** md · **bytes:** 8454 · **lines:** 82 · **empty:** no · **census:** #348 · status **Final (Phase 0)**, stable 2026-06-18.
- **What:** Squad Mobilization Report (id **PM-006**, v1.0, Final). The PM's hand-off from *planning* to *scaffolding* — integrates all six squad plans + the D2 spike.
- **DETAILED WHY:** It is the **point-in-time integration record** proving the six plans are mutually consistent (no blocking conflicts) and that cross-squad forks were reconciled (tenancy enforcement, topology, audit-event sink, engine-interface-vs-D2, naming canonicalization, breaking-migration sequencing, clean-room boundary). It binds the **scaffold step** (ADR-0003 plan-then-scaffold): the exact Phase 0/A skeleton, the ADR backlog to write, and the consolidated sponsor asks. Without it the transition into building has no agreed baseline and the D2 spike recommendation (Option A) has no documented rationale ready for ratification. It is "Final" because it is a milestone artifact, not a living register.
- **Structured outline:**
  1. **Mobilization status** — 6-squad table (plan + headline outcome).
  2. **The D2 spike outcome (ready to ratify)** — Option A rationale (faithful to verified behavior; avoids R2 wrong-brain lock-in); the engine *interface* frozen regardless.
  3. **Cross-squad reconciliation** — 7-row table of dependencies/conflicts resolved.
  4. **ADR backlog** — 0004/0005/0006/0007/0008/0009/0010/0011/0012/0015 with owners.
  5. **Consolidated asks for the sponsor** — A (engine reproducibility pair: golden master + `rfp_analysis_engine_v3.py` md5 `c73ffc5…`) · B (real iTrade export, real bid round, real kickoff, KCMS) · C (zip centroids + fiscal calendar; sign-off deck + booking guide; DEP-4 cloud+IdP; data-classification/retention; role→person mapping).
  6. **Decisions now open for the sponsor** — D2 ratify; tenancy topology; DEP-4.
  7. **Next step: scaffold Phase 0/A** — the monorepo stand-up + exit gate (`docker-compose up` → healthy Postgres + 8 schemas; `alembic upgrade head`; `/health` green; CI passes).
- **Cross-references:** depends_on PM-000..PM-005 + all `project/squads/*/PLAN.md` + `docs/adr/*`; the topology fork resolves into D8/ADR-0004; the spike → D2/ADR-0006; the breaking-migrations plan → 02 §3 + Ways-of-Working; the consolidated asks map to DEP-2/3/4/5/6.

---

## D1.8 — `project/07_AS_BUILT_PROCESS_AUDIT.md`

- **Path:** `/home/user/KR_RFP/project/07_AS_BUILT_PROCESS_AUDIT.md` · **ext:** md · **bytes:** 86058 · **lines:** 560 · **empty:** no · **census:** #349 · the **largest file in the slice**; **modified 2026-06-22T02:32** (v1.26).
- **What:** The As-Built Specification incorporating the Process Audit (id **PM-007**, **v1.26**, status "Living — single source of truth; Phase 1 pre–Live Run #1"). A code-verified snapshot of the RFP lifecycle **as actually implemented** (every gate, loop, write-point, table, endpoint). `audited_commit: ed2d26a`.
- **DETAILED WHY:** This is the **single authoritative source of truth for what the system IS** — the codebase/prompts/workflows/other docs reconcile *to* it. It exists to kill documentation drift: per D37/D39 + 02 §8, "no sprint is complete until this is updated," and it is a **release gate** (PASS/CONDITIONAL/FAIL). It binds every developer (pre-merge audit-impact review) and every reviewer/operator (it must answer how-it-works / where-data-is / who-can-change-it / what-can-fail / what-changed **without reading source**). Without it the program ships on an aspirational picture; with it, "when did this capability appear / when did this control disappear" is answerable from the §Appendix delta history. **This D1 audit (the AS_BUILT/ tree) is the fresh, exhaustive successor that VAULT.md marks as superseding this 07 doc** — but 07 remains the current-state SoR until the new three-LAYER reports are synthesized.
- **STANDING RULES / structure (Part I narrative + UX; Part II reference catalog; Appendix delta log):**
  - **Executive summary** — Platform maturity snapshot (status vocab ✅/🟡/🟠/🔴/⬜ per D39) + the **Gap Register** (G-A…G-J with severity/impact/action/owner/status).
  - **Part I:** §1 end-to-end lifecycle flowchart (mermaid) · §2 stage-by-stage stacked (system + human layer; persists key V/S/A) · §3 data flow & write-points (mermaid + table) · §4 System-of-Record hierarchy · §5 Failure domains · §6 Gates (enforced/aspirational/missing) · §7 Loops · §8 Audit/event-log status (G-B detail; 9 EventTypes) · §9 Built/partial/missing · §10 Known issues queued · §11 Build authorization (→08) · §12 Governance (triggers/questions/release gate; §12.1 trigger table, §12.2 the 6 questions, §12.3 PASS/CONDITIONAL/FAIL, §12.4 pre-merge review) · §13 Runtime & trust boundaries.
  - **Part II:** §14 HTTP surface (29 live routes; 4 empty stub routers; RBAC never wired) · §15 Agent inventory (17 MCP tools; no autonomous runtime AI) · §16 Data model — every table (87 tables + 1 view; ACTIVE≈37, DORMANT≈50) · §17 Analysis-engine inventory (5 factors, gates, 7 lenses, 13 formulas, capacity check) · §18 Template & generated-output inventory · §19 Workflow maps · §20 Registries (backlog / tech-debt / audit-findings) · §21 Future roadmap.
  - **Appendix — version history v1.0 → v1.26** (the delta log).
  - **Current release-gate read (v1.24):** 🟡 **CONDITIONAL** (storage now solid+stateless; open gaps G-C RBAC / G-D sign-off / G-I deep-workbench / G-J tenancy documented + owner-assigned).
- **Gap register IDs (for cross-ref):** G-A flat-13 (✅ closed v1.6) · G-B audit hash-chain decisions (✅ closed v1.4) · G-C RBAC defined-not-enforced (open) · G-D sign-off decorative (open) · G-E `documents` router empty / draft→SENT (partial) · G-F PBA/contract + feeds + importer (open) · G-G capacity check surfaced (✅ closed v1.20 workbook) · G-H comms no-send/no-review-UI (open) · G-I web alignment ≠ alignment workbook (open) · G-J tenancy under-documented (open).
- **Cross-references:** depends_on PM-004 + PM-008 + 03; governs/gated-by 02 §5/§6/§8; D37/D39 are its charter; every epic's "shipped/partial/missing" status reconciles here; `db/baseline/schema.sql` + migrations 0001–0019 are its DDL basis; named in CLAUDE.md indirectly via Ways-of-Working. **Internal version drift to note:** front-matter says v1.26 and `audited_commit ed2d26a`, but the §12.3 release-gate line still reads "v1.24" and §16's prose says "86 tables" in one v1.19 correction line while the v1.24 body says 87 — minor internal-version lag typical of a living doc.

---

## D1.9 — `project/08_RELEASE_GOVERNANCE.md`

- **Path:** `/home/user/KR_RFP/project/08_RELEASE_GOVERNANCE.md` · **ext:** md · **bytes:** 9912 · **lines:** 105 · **empty:** no · **census:** #350 · ratified 2026-06-21.
- **What:** Release Governance & Change Management (id **PM-008**, ratified 2026-06-21). Governs **what may be built and when** — paired with 07 (what exists) and 04 (the item register).
- **DETAILED WHY:** It is the **build-authorization gate**. It exists to stop "perpetual development": the objective is a production-ready engine that runs live cycles accurately/repeatably/auditably, **not** feature count. It binds every change to a classification (A/B/C) assigned **before any work begins**, and pins the program to a phase (currently **Phase 1, pre–Live Run #1**). It encodes the **Decision Doctrine** (the 7 principles that govern *how* decisions are made — the tiebreaker is "outcome over output, least margin for error"). Without it, scope is unbounded and the live-run readiness goal is undefended. Named in CLAUDE.md as a mandatory pre-work read (ABSOLUTE REQUIREMENT #2 cites it).
- **STANDING RULES (this is the second "standing-rules" doc the prompt asks be enumerated):**
  - **Decision Doctrine (7 principles, ratified 2026-06-21):** (1) **Outcome over output — full functionality, least margin for error** (the tiebreaker); (2) **Default to backlog, not build; classify before acting** (A/B/C; when unsure→backlog); (3) **Truth from reality, never from documents or memory** (verify vs code/schema; the As-Built Spec is SoR; no sprint done until it's updated); (4) **AI-generated, not AI-managed — the human asserts** (award/sign-off/send/merge are human-asserted + audit-evented; the agent never auto-asserts); (5) **Reversible & in-scope → proceed; consequential/ambiguous → surface** (act on routine reversible work + save as you go; stop at genuine forks); (6) **Gate before you ship** (deterministic review at control points; fix every confirmed finding; never merge over an open issue or stale record); (7) **Small, verified, behavior-preserving** (prefer small reviewable changes; prove correctness — byte-identical tests for refactors).
  - **Core principle:** **Default to backlog, not build.**
  - **Change classification (assign before building):** **A — Critical fix** (wrong results / blocked execution / integrity/audit/security/data-loss → **Immediate**); **B — Operational enhancement** (improves analysis/reporting/validation/workflow/efficiency **inside existing architecture** → eligible during Live Run #1/#2 cycles, not speculative Phase-1 work); **C — Major feature** (new module/agent/workflow family/database/dashboard/app section/integration/domain/architectural redesign → **Backlog only** until the Phase-4 post-validation review). **B constraints:** within existing modules; no architectural redesign; no new system domains; no new core workflows — anything failing these is C.
  - **Decision rules (in order):** 1 incorrect results→A; 2 blocks execution→A; 3 improves within existing architecture→B; 4 new module/workflow/agent/integration/domain/architectural component→C backlog; 5 Production Lock occurred?→all enhancements backlog. **Default when unsure: backlog.**
  - **Phases (1–7):** 1 Initial Build (current) · 2 Live Run #1 · 3 Live Run #2 · 4 Feature Consolidation Review · 5 Final Audit · 6 Production Lock · 7 Maintenance.
  - **Current phase & standing rulings (2026-06-21):** Phase **1 — Initial Build, pre–Live Run #1**; **As-Built rule:** no sprint complete until the As-Built Spec is updated.
  - **Classification of the live backlog (the operative gate table):** E-37 ✅ delivered (B); E-39 ✅ delivered (A-adjacent); **E-38 capacity B-core = BUILD now** (wire existing `bid.capacity_statement`/`capacity_constraint`, NOT a new store), but the **in-app dashboard = C → backlog**; G-C RBAC = B (backlog/Live-Run); G-D/E-24 sign-off+SENT = C; E-33/G-F PBA = C; E-34/E-08/09 importer/feeds = C; E-35 discovery = C; E-36 continuation RFP = C; E-28 analytics = C. **Only A + the E-38 B-core are buildable in Phase 1.**
  - **Review cadence & control points:** two tiers — (1) **agent self-review** every PR (read-only review agent vs actual code/schema; replaces the retired push-basic Codex, used through PR #20); (2) **human full-suite auditor** (manual, on request, called at defined control points via the standout 🔎 REVIEW CHECKPOINT block). **Control points:** pre-merge every PR · sprint close · phase gates · backstop. Between control points: keep working+committing, but don't merge until the checkpoint is satisfied.
- **Cross-references:** paired with PM-007 (what exists) + PM-004 (register); operationalizes 02 §5/§6/§8 (the As-Built rule + DoD); the Decision Doctrine is the formal statement behind CLAUDE.md's decision-weighting rubric and ABSOLUTE REQUIREMENT #2; D37/D39 set the As-Built release gate it enforces; D44's "default = backlog" triage rule is the Phase-1 application of this doctrine.

---

# Part B — The five named project companion docs

These are topical specs/registers that hang off the numbered series — each created later (2026-06-21/22) for a specific concern (design handoff, storage refactor, reconciliation seams, pre-test readiness, the data/process middle).

---

## D1.10 — `project/DATA_AND_PROCESS_MAP.md`

- **Path:** `/home/user/KR_RFP/project/DATA_AND_PROCESS_MAP.md` · **ext:** md · **bytes:** 24181 · **lines:** 365 · **empty:** no · **census:** #351 · created 2026-06-22.
- **What:** Data & Process Map (id **PM-MAP**, v1.0, "Companion map (NEW)"). Surfaces the **middle** steps the other docs leave implicit: every user DECISION point, every ACCESS point (screen+endpoint), and the reconciliation seams. Explicitly a **DERIVED VIEW, not a source of truth** ("if it disagrees with 07, Postgres and 07 win").
- **DETAILED WHY:** The lifecycle's *ends* are well-documented but the *middle* (where a human asserts, where a user touches the system, and the in-between grain/system mappings no single screen owns) was implicit. This map makes those three visible so the build/audit can reason about break-points. It binds no one (derived), but it is the bridge between 07 (as-built), `RECONCILIATION_SEAMS.md`, the schema, and the 6 handoff screens — used to plan E-26/E-41 and to spot seam gaps. Without it the decision/access/seam topology is scattered across four docs.
- **Structured outline:**
  - Front-matter caveat + Purpose.
  - **Naming seam (read first)** — the ACTIVE ORM tables (`eng.analysis_*`, `awd.*`, `eng.bid_score` from migrations 0008/0010) vs the DORMANT baseline solver spine (`eng.calculation_run`, `eng.scenario`, `eng.scenario_award`, `eng.scenario_capacity_usage`); `awd.*`/`eng.bid_score` are net-new M7/M8 migrations not in `schema.sql`.
  - **Legend** (markers: rounded box/diamond/hexagon/dashed; SCR:/EP:/→DB:/A:).
  - **Diagram 1 — Data relationship map** (mermaid `erDiagram`): the spine pilot.run→cyc→bid→eng→awd + the `((SEAM))` nodes.
  - **Diagram 1 reading notes** — `pilot.run.cycle_id` is text not FK; `eng.*` FKs are logical (code-resolved, not DB-enforced); seams are not tables.
  - **Diagram 2 — Process & data-flow flowchart** (mermaid): each step with ACCESS/DB/audit; diamonds=decisions, hexagons=seams, dashed=gaps; the MCP harness mirrors the spine as the oracle.
  - **Enumerated DECISION points (D1–D8)** — D1 strict/flexible · D2 confirm mapping · D3 inspect/choose lens · D4 freeze award (ASSERT) · D5 record adjustment · D6 finalize/close-out · D7 sign-off · D8 in-gate/round-close. (5 wired+audit-evented: D1/D2/D4/D5 + the SEALED engine seal; D6–D8 gaps per this doc.)
  - **Enumerated ACCESS points** — 6 screens (Login/Dashboard/Run Detail/Bid Intake/Alignment/Awards) → endpoints (HTTP + MCP mirror).
  - **Reconciliation seams marked on the diagrams** — table mapping each seam to where it sits on the flow + status.
  - **Gaps flagged (dashed on Diagram 2)** — setup/strategy screen · editable column mapper · unit/pack · round-close/G12 · sign-off · comms review/send · PBA · close-out route · lot↔SKU feed.
  - **Relationships I was unsure of (left annotated)** — 6 items (eng.* logical FKs; award→analysis_run edge; capacity↔submission cardinality; pilot.run↔cycle soft link; the eng/awd naming collision; finalize/close-out semantics).
- **Cross-references:** relates PM-007 (§1/§2/§3/§13/§16) + PM-SEAMS + PM-004; uses `db/baseline/schema.sql` (+0019); the 6 handoff screens (`project/design/handoff/`). **STALENESS FLAG (cross-doc):** this map (v1.0, 2026-06-22T02:11) treats **D6 finalize / close-out + the `CLOSED` event as a GAP** ("CLOSED type absent; route is MCP-only; no close-out SCREEN"), but **07 v1.26 (2026-06-22T02:32, ~20 min later) records `finalize_run` + `POST /runs/{slug}/finalize` + the `CLOSED` EventType as BUILT** on the console. This map predates the v1.26 finalize entry by minutes and is now stale on exactly that point — consistent with its own "if it disagrees with 07, 07 wins" rule, so the contradiction is governed, not a defect, but should be refreshed.

---

## D1.11 — `project/DESIGN_BRIEF.md`

- **Path:** `/home/user/KR_RFP/project/DESIGN_BRIEF.md` · **ext:** md · **bytes:** 3700 · **lines:** 51 · **empty:** no · **census:** #352 · created 2026-06-21 · the **smallest** file in the slice.
- **What:** Design-Session Brief — a one-page orientation for an external UX/UI design session (e.g. Claude Design). Pairs with 07 (ground truth), the screenshots, and the Excel output files.
- **DETAILED WHY:** It exists to brief a **design vendor** in one page: what's being built (a single-operator governed RFP web console), the form factor/stack (desktop-first responsive Next.js + React 18 + TS + Tailwind; 1440px baseline), the hosting *shape* (managed PaaS + managed Postgres; Next.js on Vercel — note this predates/sits beside D40's GCP decision and frames hosting as "a standard responsive web app, host settled later"), and crucially **the single biggest design question (gap G-I):** the alignment/comparison workbench lives only in Excel (~18 tabs) and the web alignment screen surfaces only a thin slice — "design how that analytical workbench comes onto the screen." It binds the designer to the platform's design constraints (decision-support framing; governed actions are deliberate+audit-evented; names not keys). It is explicitly **advisory / not canonical** (feeds the Phase-4 consolidation review).
- **Structured outline:**
  1. What we're building (thesis: AI-generated not AI-managed).
  2. Form factor & stack (desktop-first responsive; Next.js/React/TS/Tailwind; FastAPI JSON API; Vercel export).
  3. Hosting platform (status) — not vendor-locked yet; doesn't change the UI.
  4. The screens today (6 + a bonus state) — Login/Dashboard/Run detail/Bid intake/Alignment/Awards.
  5. The single biggest design question (gap G-I) — the Excel workbench → screen.
  6. Surfaces that don't exist yet (design net-new) — capacity check (E-38), comms review/send (E-37), sign-off, close-out, documents.
  7. Design constraints to honor — decision-support framing; governed actions deliberate; names not keys; advisory/not-canonical.
- **Cross-references:** pairs with 07 (the gap register is the authoritative net-new list); G-I is the central ask (→E-41); D6/ADR-0002 (stack); D23 (names not keys); ADR-0006 (decision-support); the screenshots + Excel outputs are the inputs. **Hosting drift note:** says "Vercel … not Azure" while D40/ADR-0017 ratified GCP Cloud Run — the brief's hosting line is design-orientation only (it disclaims that hosting "does not change the UI/UX"), but a reader should treat D40 as the authoritative hosting decision.

---

## D1.12 — `project/NO_FILE_STORAGE_PLAN.md`

- **Path:** `/home/user/KR_RFP/project/NO_FILE_STORAGE_PLAN.md` · **ext:** md · **bytes:** 6532 · **lines:** 87 · **empty:** no · **census:** #353 · created 2026-06-21, modified 2026-06-21T23:59.
- **What:** No-server-side-file-storage refactor — implementation plan (id **PM-NFS-PLAN**, v1.0, status **DONE** — all 6 slices landed s0 `15d957e`→s6 `ed2d26a`; 247 tests pass; migration 0019 round-trips).
- **DETAILED WHY:** It is the executed implementation plan for ABSOLUTE REQUIREMENT #4 (no server-side file storage) — the contract CLAUDE.md cites by name. It exists to make the **web console write zero files** (DB is the single source of truth; uploads stream to ingest in memory; deliverables render on request) while the **MCP harness keeps its file vault** (the verification oracle). It binds the build to a slice order (lowest-risk first) and records the "verified ground truth" (the deepest assumption being severed: "a run is a vault folder, not a DB entity"). Without it the Cloud Run statelessness requirement (D41/ADR-0018) has no execution path, and the riskiest change (severing run identity from the filesystem) has no mitigation. Now historical/closed (DONE) but retained as the record of *how* E-42 was built.
- **Structured outline:**
  - Front-matter (status DONE with the 6 slice commit hashes).
  - **Hard requirement (sponsor)** — console stores no files server-side.
  - **Verified ground truth** — a "run" is a vault folder + `cycle_id.txt`; generators are deterministic pure DB-renders (E-39) with bytes builders; status/kanban reads the DB; setup/bid templates already byte-returning; 233 tests green pre-refactor.
  - **Slices (ordered, lowest-risk first)** — Slice 0 generators→bytes (✅ 15d957e) · 1 deliverable registry (`app/pilot/deliverables.py`) · 2 DB-backed run identity (new `pilot` schema + `pilot.run`, migration `0019_pilot_run`, dual-write) · 3 console resolves identity from DB · 4 uploads stream to ingest (`ingest_*_bytes`) · 5 downloads generate on request, remove `outputs/` writes (gated via `persist_outputs` flag) · 6 decommission console vault usage.
  - **Biggest risk + mitigation** — severing run identity (Slice 2→3): dual-write + backfill before flipping the read source; byte-drift from `date.today()` provenance → tests compare on data not raw bytes.
  - **MCP harness** — untouched under every slice (keeps `vault.py`, `run_db.py`, `cycle_id.txt`, git autopush, `rehydrate`).
- **Cross-references:** relates ADR-0018 (storage model), ADR-0017 (GCP/Cloud Run), ADR-0003 (two runtimes), D30, D41, E-39, E-42; the slice commits + migration 0019 + the `pilot.run` table are documented as built in 07 §16/§2/§3 and the v1.23/v1.24 appendix entries; the `persist_outputs`/`db_runs` flags it introduces are the console-vs-harness discriminator in 07 §13.

---

## D1.13 — `project/PRE_TEST_READINESS.md`

- **Path:** `/home/user/KR_RFP/project/PRE_TEST_READINESS.md` · **ext:** md · **bytes:** 7362 · **lines:** 101 · **empty:** no · **census:** #354 · created 2026-06-22T04:29, modified 2026-06-22T14:16 (same as 04).
- **What:** First pre-test readiness review (id **PM-PRETEST**, status "Review 2026-06-22 — gap analysis against the live-test critical path D44"). Asks "are we fully functional end-to-end?" for the **first DRY pre-test**.
- **DETAILED WHY:** It exists to answer, against the **D44 frozen live-test scope**, whether one real RFP can run end-to-end on the new design (E-26) and be compared to the MCP harness + the manual allocation model. It binds the *first pre-test* scope to **E-26 + the existing working pipeline** and records the three judgment calls (strategy config / where it runs / import path) with their resolutions. It contains the **dry-run log** — the load-bearing evidence that the lifecycle actually works (the TOMATO PASS + the POTATO converter run). Without it there's no readiness verdict and no record that the full lifecycle was exercised on real committed data. Critically, the POTATO dry-run log here is the **same converter HANDOVER.md flags as a 🔴 ACTIVE D45 VIOLATION** — this doc records the run as "✅ DONE" and reasons that the +27% spend gap is *not a bug* (human alignment decisions), while D45/HANDOVER say the converter cut corners that must be rebuilt faithfully first; the two readings are in tension (see Gaps below).
- **Structured outline:**
  - Front-matter + "What the first pre-test is (D44 scope)."
  - **Lifecycle readiness** — 12-step table (sign in → create run → setup → strategy → template → import bids → run analysis → inspect → freeze → finalize → downloads → audit trail), backend/frontend status, blocker-for-pre-test column. "Verified": frontend builds clean; the fixed price model matches the manual potato cost lines.
  - **The 3 judgment calls that decide "fully functional"** — A strategy config (✅ RESOLVED — minimal panel built; `GET/PUT /runs/{slug}/strategy`) · B where it runs (✅ LOCAL; GCP deploy parked) · C import path (✅ STRICT owned template; editable mapper deferred).
  - **Deferred (NOT blockers)** — E-44, full A1, A2 finalize-UI polish, A3/M1 editable mapper, A4 comms-send, A5–A7 governance/admin, M2–M6 reconciliation midpoints, the 3 design corrections, GCP deploy.
  - **Dry run log** — TOMATO dry run ✅ PASS (full lifecycle on the live app, real committed DB, all three new features exercised); POTATO dry run ✅ DONE via the legacy→owned converter (`backend/scripts/potato_legacy_dryrun.py`; 20 DCs / 27 lots / 17 suppliers / 2 TFs; 4,820 R2 Delivered bids; lens ordering matches the golden; +27% spend = full-coverage pre-alignment baseline vs the golden's post-alignment, ruled "not a bug").
  - **Verdict** — pre-test build scope COMPLETE; end-to-end lifecycle functional for a first pre-test + clean comparison.
  - **Test tiers — DRY vs LIVE (D44)** — dry test approved as-is on the fixed model; LIVE tests additionally require the fan-in/fan-out per-period granulation (D42/D38/E-35), built before the live tests not the dry one.
- **Cross-references:** relates 03 (D44 freeze) + 04 (E-26, E-44) + `DESIGN_PACKAGE.md` + `MANUAL_MODEL_FINDINGS.md`; the converter is `backend/scripts/potato_legacy_dryrun.py`; the strategy panel is the resolution of E-44's A1 minimal slice; the DRY/LIVE test-tier split is D44's; the POTATO converter is the subject of D45's "rebuild faithfully" order and HANDOVER's active-violation flag.

---

## D1.14 — `project/RECONCILIATION_SEAMS.md`

- **Path:** `/home/user/KR_RFP/project/RECONCILIATION_SEAMS.md` · **ext:** md · **bytes:** 6600 · **lines:** 65 · **empty:** no · **census:** #355 · created 2026-06-22T01:54, modified 2026-06-22T03:52.
- **What:** Reconciliation seams — the "in-between spaces" register (id **PM-SEAMS**, v1.0, "Living watch-list"). Every mapping/reconciliation seam between grains (lot↔item↔SKU↔period) and systems (RFP↔iTrade↔KCMS↔supplier master), who owns it, and whether it's handled.
- **DETAILED WHY:** Sponsor-driven: the places where one representation must be mapped to another are **where real-data integration silently breaks**, and they're easy to miss because **no single screen owns them**. This is the standing watch-list so nothing in an in-between space ships "by inference" without a human-confirmable, sticky mapping. It binds the build via a **standing rule** ("when a new feature crosses a grain or system boundary, add its seam here first and decide its mapping before building"). Without it, cross-system joins (lot→SKU, supplier/DC identity, units/pack) fail quietly on real data — exactly the failure mode the program's top risk (R1, real data) embodies.
- **STANDING RULE (verbatim intent):** add the seam here *first* and decide its mapping (sticky? human-confirmed? unit-normalized?) **before** building.
- **Structured outline:**
  - Front-matter + "Why this exists (sponsor)."
  - **The seams** — table (seam from→to · cardinality · status · owner/epic · note). Headline OPEN: **RFP lot/item → unique iTrade SKU(s)** (1→many; E-11+E-08; prerequisite for real STLY, contracted-vs-effective, discovery) and **units/pack-size** (unmodeled). Partial (◐): messy columns→bid fields, supplier/DC identity→ref.*, items→lots, setup dates→fiscal periods, prior award→STLY proxy (×1.04), routing modality (D43), discount unit %↔$ (✅ resolved 2026-06-22). Done (✅): bid timeframe→flat-13 (G-A), capacity→award cells (E-38), price basis→scored price (E-39). Open (⬜): RPC cost line (D43).
  - **Newly-surfaced gaps** — (1) editable column mapper; (2) unit/pack-size reconciliation.
  - **Known-template adapter (planned)** — a deterministic Python parser for the team's manual templates that **emits OUR key-stamped owned template then ingests via the existing STRICT key-validated path** (never direct-to-DB), reusing key-validation/quarantine/IMPORTED events; a pure data-mover that resolves identities to our keys and calls `construct_price_from_parts` (E-39) so it can't drift.
  - **Standing rule.**
- **Cross-references:** relates PM-004 + PM-007; E-08/E-09 (feeds), E-11 (lots), E-28 (analytics), E-34 (suppliers), E-35 (discovery), E-39 (formulas); the discount-unit and routing-modality seams cross-link D43/E-44 + `MANUAL_MODEL_FINDINGS.md`; the natural-key reuse is D36; the seams are placed on the flow in `DATA_AND_PROCESS_MAP.md` Diagram 2; the known-template adapter is the planned intake path noted in 04's reconciliation-seams note.

---

# Part C — The root operating docs (CLAUDE / HANDOVER / VAULT / README / WEB_DEPLOYMENT)

> These five are the repo-root spine. Per the `00_INDEX` tracker they belong to slice **D5**; the explicit D1 prompt audits them here (overlap recorded above). CLAUDE.md + AUDIT_STANDARD.md were the mandatory first reads for this slice.

---

## D1.15 — `CLAUDE.md`

- **Path:** `/home/user/KR_RFP/CLAUDE.md` · **ext:** md · **bytes:** 6799 · **lines:** 105 · **empty:** no · **census:** #9 · created==modified 2026-06-22T18:36 (the D45 commit).
- **What:** The OPERATING CONTRACT — "READ FIRST, EVERY SESSION, BEFORE ANY WORK." Claude Code auto-loads it. The non-negotiable contract for the repo; every sub-agent must receive the ABSOLUTE REQUIREMENTS verbatim.
- **DETAILED WHY:** This is the **mechanism that fixes the root-cause failure D45 names**: the standing rules previously lived only in `project/` docs that nothing auto-loads and were never injected into spawned agents, so every fresh session/agent started blind (causing the MVP-cut console + the shortcut-laden potato converter). CLAUDE.md is the one file Claude Code auto-loads every session, so it is where the **ABSOLUTE REQUIREMENTS** are pinned and the **AGENT PROTOCOL** is mandated. It binds *every* session and *every* sub-agent. Without it the no-MVP rule (D19, the *first* requirement and the tiebreaker) and the data-fidelity rule are not enforced where work actually happens.
- **STANDING RULES (the operative contract):**
  - **ABSOLUTE REQUIREMENTS (priority order):** (1) **NO MVP. NO STUBS. NO PLACEHOLDERS (D19)** — every module ships as a functional prototype of the FULL capability, fully wired to real data; the first requirement and the tiebreaker; (2) **Outcome over output — full functionality, least margin for error** (08); (3) **DATA FIDELITY is part of NO-MVP** — map every field through EVERY step (setup→template→bids→engine→analysis); forbidden: dropping rows, flattening dimensions, renaming entities to raw IDs, force-positiving, single-round collapse; bad data → quarantine, never fudge; reconcile to source/golden NUMBERS at each step; (4) **No server-side file storage** (DB is the single source of truth; `NO_FILE_STORAGE_PLAN.md`); (5) **Verify before actioning** (treat all claims with skepticism; the MCP harness is the live-run verification oracle); (6) **Save frequently; branch discipline** (develop on `claude/wizardly-pasteur-n4acb8`; `Co-Authored-By`/`Claude-Session` trailers; **never** put the model ID in any committed artifact).
  - **READ THESE BEFORE ANY NON-TRIVIAL WORK:** 02 (Ways of Working), 03 (Decision Log, esp. D19/D42/D43/D44), 08 (Release Governance), `NO_FILE_STORAGE_PLAN.md`, 04 (Program Backlog).
  - **AGENT PROTOCOL (mandatory):** paste the ABSOLUTE REQUIREMENTS into every sub-agent's prompt verbatim; tell it to read CLAUDE.md + Ways of Working + Decision Log first; **reject on arrival** any plan/output with a stub/placeholder/MVP-cut/phase-later shortcut/dropped-fudged data.
  - **DEFINITION OF DONE (every unit):** full capability wired to real data; data faithful + reconciled; verified vs tests + MCP harness; committed with proper trailers.
  - **GUIDING PRINCIPLES (sponsor, 2026-06-22):** Role contract (sponsor = layman client; assistant = studio owner who owns the work end-to-end, on disk not in memory); **Save constantly — ONE source of truth** (decisions→03; standing rules→CLAUDE.md; current state→HANDOVER.md; doc map→VAULT.md; **assume context cleared every 3rd prompt**); **Decision-weighting rubric (strict priority): (1) LONGEVITY → (2) FULL FUNCTIONALITY → (3) ERROR REDUCTION → (4) DRIFT REDUCTION** (earlier breaks the tie; record which drove the call); **Nitro mode** (constrained agents: set-up→prompt→execute→review→prompt; ABSOLUTE REQUIREMENTS injected; outputs reviewed; parallelize; durable output to disk); **The Vault** (all knowledge markdown, wiki-linked from VAULT.md; the as-built audit under `AS_BUILT/`, indexed from `AS_BUILT/00_INDEX.md`); **Exhaustiveness bar (audits/maps):** *nothing skipped/missed/assumed/unmapped — not one character*; every file listed incl. empty (name/ext/empty/created/modified/size); detailed WHY on everything; bulk-accounting allowed only for vendored/generated trees, and even then listed as a counted line — **never a silent skip**.
- **Cross-references:** sources D19 + 03 + 02 + 08 + `NO_FILE_STORAGE_PLAN.md`; D45 is the decision that created/operationalized it; HANDOVER/VAULT/03 are its named "one source of truth" targets; the Exhaustiveness bar is the charter `AUDIT_STANDARD.md` implements and this very audit honors. This is the file the AGENT PROTOCOL requires be injected into every sub-agent (including this audit agent — it was).

---

## D1.16 — `HANDOVER.md`

- **Path:** `/home/user/KR_RFP/HANDOVER.md` · **ext:** md · **bytes:** 4538 · **lines:** 63 · **empty:** no · **NOT in the census excerpt (census GAP — flagged above)** · fs mtime 2026-06-22 18:54.
- **What:** HANDOVER — "read this FIRST to resume after a context clear" (id **HANDOVER**, updated 2026-06-22). The current-state + resume-point doc.
- **DETAILED WHY:** Per CLAUDE.md's "save constantly — ONE source of truth," the **current state / resume point** lives here. It exists because context clears every 3rd prompt: a fresh session reconstructs *where the product is right now* (deployed URLs, login, branch), *what is actually built vs claimed* (from `DRIFT_RECONCILIATION.md`), the *work queue*, and *what's in progress*. It binds the next session's first moves. Without it, a resumed session has no truthful map of build state and would trust the optimistic record. It is the most operationally current of all the docs (mtime 18:54, the latest in the slice).
- **Structured outline:**
  - Front-matter + **Read order on resume** (CLAUDE.md → this → VAULT.md → 03 esp. D45 → `DRIFT_RECONCILIATION.md` → `AS_BUILT/00_INDEX.md`).
  - **Where the product is** — Live on GCP Cloud Run (frontend/backend URLs; login `admin`/`Eagv.3248!!`; project `krrfp-500214`; us-central1; Cloud SQL Postgres 16); deploy is one command (`deploy/gcp/deploy.sh`, `--no-seed`); branch `claude/wizardly-pasteur-n4acb8`.
  - **The truth about what's built** (from `DRIFT_RECONCILIATION.md`) — engine + governed-persistence spine is FULL-FIDELITY (not stubbed); console is ~half built + 4 MVP-cuts (built: dashboard/run hub/intake/alignment/awards; **not built**: full Cycle Setup/Strategy, Suppliers, Sign-off, Settings/RBAC, Reconciliation, run-scoped nav rail); **🔴 ACTIVE VIOLATION: the potato converter `backend/scripts/potato_legacy_dryrun.py` cuts corners D45 forbids** (single Delivered round, 141 demand rows dropped, regions flattened, lot names = raw IDs, values force-positived) and seeds the deployed image — **D45 ordered it rebuilt faithfully BEFORE more console build; still unmet**; backend perimeter not built (RBAC enforce, sign-off gate, iTrade importer/E-08 → STLY is a synthetic ×1.04 proxy, safety reprice/E-29, PBA/E-33, comms send 4/7; no RLS = D8 drift; setup/capacity ingest emit no audit event).
  - **The work queue (remediation order, per D45 + the rubric)** — (1) rebuild the potato converter faithfully + field-by-field mapping audit reconciled to golden NUMBERS (FIRST — it taints the data the client reviews); (2) build the full console to fidelity (no stubs); (3) build the backend perimeter; (4) delete/fill the dead empty routers.
  - **In progress right now** — the exhaustive AS-BUILT audit (896 owned files censused, 18 empty; per-file deep audit slice-by-slice into `AS_BUILT/files/` per `AS_BUILT/00_INDEX.md`).
  - **Operating model (CLAUDE.md)** — the layman-client/studio-owner recap + the decision rubric.
- **Cross-references:** points to CLAUDE.md, VAULT.md, 03 (D45), `project/triage/DRIFT_RECONCILIATION.md`, `AS_BUILT/00_INDEX.md`, `deploy/gcp/deploy.sh`. **Material finding:** HANDOVER is the only doc that **explicitly flags the potato converter as an unresolved 🔴 D45 violation**, directly contradicting `PRE_TEST_READINESS.md`'s "POTATO dry run ✅ DONE … not a bug" — the two are reconciled by reading: PRE_TEST treats the *run* as a successful lifecycle exercise; HANDOVER/D45 condemn the *converter's data fidelity*. Both are true of different things, but a reader must hold both. Also note HANDOVER says "console is ~half built + 4 MVP-cuts" — i.e. the program is *currently in violation* of CLAUDE.md ABSOLUTE REQUIREMENT #1 (no MVP), recorded honestly as remediation debt.

---

## D1.17 — `VAULT.md`

- **Path:** `/home/user/KR_RFP/VAULT.md` · **ext:** md · **bytes:** 6176 · **lines:** 67 · **empty:** no · **NOT in the census excerpt (census GAP — flagged above)** · fs mtime 2026-06-22 18:54.
- **What:** THE VAULT — map of every markdown doc in the system, wiki-linked (id **VAULT**, updated 2026-06-22). Obsidian-style `[[links]]` with full paths.
- **DETAILED WHY:** Per CLAUDE.md "The Vault," all knowledge is markdown, **mapped + wiki-linked from one map** so every decision/audit/spec/plan is reachable from a single index. It exists so no doc is orphaned and a reader can navigate the ~157 `.md` files (≈30 vendored/excluded) without grepping. It binds the doc-discovery surface and records which docs are canonical vs snapshots vs superseded. Without it the knowledge base is a flat pile with no entry point. It self-states the doc count and points at `FILE_CENSUS.md` for the full 896-file census.
- **Structured outline (the map's sections):**
  - Front-matter (157 .md total; ~30 vendored excluded; points to `[[AS_BUILT/FILE_CENSUS]]`).
  - ⭐ **Operating spine** — CLAUDE.md · HANDOVER.md · `AS_BUILT/00_INDEX` · `AS_BUILT/FILE_CENSUS`.
  - 🏛️ **Governance & decisions** — 00–08 (incl. note: **"every decision D1–D45"**, epics **E-00…E-44**); flags **07 as "old — superseded by AS_BUILT/"**.
  - 🧱 **Architecture, data & storage** — DATA_AND_PROCESS_MAP · RECONCILIATION_SEAMS · NO_FILE_STORAGE_PLAN · db/baseline · the 10 ADRs (0001/0002/0003/0004/0006/0013/0014/0016/0017/0018).
  - ⚙️ **Engine** · 🧩 **Squad plans** · 🎨 **Design** · 📐 **Specs** · 🚀 **Deploy/infra/MCP/reference** · 🔎 **Triage & findings** (DRIFT_RECONCILIATION, MANUAL_MODEL_FINDINGS, BACKFILL_CANDIDATES, PRE_TEST_READINESS, DESIGN_BRIEF) · 🗄️ **Archives/snapshots** (var/* + audit/00–04 OLD, superseded; audited in slices D6/D3/D5).
- **Cross-references:** links essentially the entire `.md` corpus; declares 07 superseded by the AS_BUILT/ tree; maps the slice assignments for archives (D3/D5/D6). **Census-coverage note:** VAULT.md claims "157 .md files total" and points to the 896-file census, but VAULT.md and HANDOVER.md themselves are missing from the census excerpt — the map references a census that does not list the map. Minor self-referential gap, same root cause (census generated 18:52, these two committed 18:54).

---

## D1.18 — `README.md` (root)

- **Path:** `/home/user/KR_RFP/README.md` · **ext:** md · **bytes:** 5202 · **lines:** 63 · **empty:** no · **census:** #10 · created 2026-06-18, modified 2026-06-21T20:23.
- **What:** The repository README — "KR_RFP — Kroger Produce RFP / Sourcing Engine." The orientation for anyone landing on the repo: what it is, the layout, the audit→build thesis, and the current operational state.
- **DETAILED WHY:** The conventional repo entry point. It exists to orient a *new* reader (human or tool) before they reach the deeper governance docs: it states the product in one paragraph, gives the directory **Layout** (specs/audit/project/docs/adr/backend/db/infra/frontend/reference/CI), records the **audit→build** move (D1/D6/D7 ratified, D2 ratified v3), and gives the **one-line conclusion** ("Neither package is the product"). It binds nothing (descriptive), but it routes the reader correctly ("Start at `audit/00_EXECUTIVE_SUMMARY.md`") and defers to 07 as the authoritative current-state SoR. Without it the repo has no front door.
- **Structured outline:**
  1. Title + product paragraph.
  2. "This repository starts with an audit" framing.
  3. **Layout** — `specs/` (rfp-engine BRIEF + original-engine AS-BUILT) · `audit/` (00–04) · `project/` (00–06 + squads) · `docs/adr/` · backend/ (FastAPI+SQLAlchemy+Alembic; ~28 routes; cycles/awards/documents/ingest stubs) · db/baseline · infra · frontend (Next.js, 6 screens) · reference (clean-room) · CI.
  4. Audit→build status paragraph (D1/D6/D7 + D2 ratified; v3 operational; ~28 routes; 6 screens; capacity persisted) → defers to 07.
  5. **The one-line conclusion** — neither package is the product; the target is the brief's brain + outward half on the as-built's spine, 12 gaps resolved by 5 sponsor decisions, proven on one real cycle.
  6. "Start at `audit/00_EXECUTIVE_SUMMARY.md`."
- **Cross-references:** routes to `audit/00`; defers current state to 07; lists D1/D2/D6/D7 + ADR-0001/0002/0003/0006; the gaps (audit/02) + decisions (audit/04). **Staleness note:** README still says "D1..D39" / "E-00..E-27" in the Layout descriptions and "~28 live routes" — the decision log now runs to **D45**, epics to **E-44**, and 07 §14 counts **29** live routes (after the finalize endpoint). README is a coarse front-door, intentionally not kept bleeding-edge current; 07 is the authority it points to.

---

## D1.19 — `WEB_DEPLOYMENT.md`

- **Path:** `/home/user/KR_RFP/WEB_DEPLOYMENT.md` · **ext:** md · **bytes:** 9558 · **lines:** 132 · **empty:** no · **census:** #11 · created 2026-06-20T22:27, modified 2026-06-21T02:19.
- **What:** "Running the RFP harness on Claude Code for the web" — the runbook for driving the produce-RFP **MCP harness** from Claude Code on the web (claude.ai/code) in an ephemeral container, rather than a terminal.
- **DETAILED WHY:** The harness must run **online** (Claude Code on the web), where the container + its Postgres are **ephemeral** — only what is committed to the cloned vault git survives. This runbook exists to make that work: what runs where, why HTTP (not stdio) MCP transport, how the 3-agent harness loads from `.claude/`, the one-time environment setup, how the vault gets into the container + pushed back, scheduled nudges (Routines), and exactly what is built+verified vs what still needs a real web session. It binds the operational deployment of the harness (the live-run verification oracle) and is the concrete realization of D34 (DB rides the vault as a SQL snapshot) + D31/D32 (3-agent harness, version pinning). Without it, the live RFPs (which run on the harness) have no documented way to survive the ephemeral web runtime. Referenced by name in D34 ("Running the harness on Claude Code for the web is documented in `WEB_DEPLOYMENT.md`").
- **Structured outline:**
  1. Intro (ephemeral container; only git-committed state survives; the DB rides the vault as a SQL snapshot, D34).
  2. **What runs where** — table (platform code+MCP server / Postgres+per-run DBs / the vault / the MCP transport).
  3. **Why HTTP, not stdio** — the web runtime doesn't spawn stdio servers; `RFP_MCP_TRANSPORT=streamable-http`; the repo-root `.mcp.json`.
  4. **The 3-agent harness (skill + subagents) on the web** — committed under `.claude/` (`.claude/skills/rfp-pilot/SKILL.md` + `.claude/agents/rfp-engine.md`/`rfp-secretary.md`); canonical copies under `mcp/` kept in sync; validation steps; the later marketplace-plugin option (preserves D31/D32 versioned-plugin design).
  5. **One-time environment setup (web console)** — setup script (`scripts/web_setup.sh`); env vars (`PILOT_VAULT_ROOT`, `RFP_PILOT_VAULT_REMOTE`, `DATABASE_URL`, `RFP_MCP_PORT`, `RFP_VAULT_AUTOPUSH`); network policy; SessionStart hook (`.claude/settings.web.json.sample` → `.claude/settings.json`; runs `scripts/web_session_start.sh` — starts Postgres, ensures role/DB, `python -m rfp_mcp.rehydrate`, starts HTTP MCP server).
  6. **The vault in the container** — `eddgue/RFP_PILOT_VAULT` (private); autopush BUILT; getting the vault in — option (a) attach as a second repo (recommended), option (b) clone from a URL.
  7. **Scheduled nudges (Routines).**
  8. **What is built and verified vs what needs a real web session** — built+tested locally (DB snapshot/restore round-trip; vault auto-push; HTTP transport; `web_session_start.sh` end-to-end; clean-JSON hook stdout); needs a real web session (hook-before-MCP ordering; subagent live-reload; the exact Postgres start command; the vault credential path).
- **Cross-references:** D34 (the DB-snapshot-rides-the-vault mechanism this operationalizes), D30 (per-run isolated DBs), D31/D32 (3-agent harness + version pinning); `rfp_mcp/rfp_pilot_server.py` (`main()` transport), `rfp_mcp/rehydrate.py`, `scripts/web_setup.sh` + `scripts/web_session_start.sh`, `.mcp.json`, `.claude/settings.web.json.sample`, `mcp/` canonical copies; the harness is the "live-run VERIFICATION ORACLE" per 04 + 07 §13. **Hosting note:** this runbook is for the **MCP-harness-on-the-web** path (claude.ai/code, ephemeral), which is *distinct from* the **GCP Cloud Run console deployment** (D40/ADR-0017, the path HANDOVER's "live on GCP" describes). The two runtimes (harness oracle vs console) are the ADR-0003 "two runtimes" — this doc covers only the harness one.

---

# Cross-document reference map (the wiring between the 19 docs)

- **CLAUDE.md** → 02 / 03 (D19, D42-45) / 08 / NO_FILE_STORAGE_PLAN / 04 (named pre-work reads); → HANDOVER / VAULT / 03 (the "one source of truth" targets). It is the auto-loaded operative version of 02 §3 + 08's doctrine + D45.
- **00 (Charter)** is depended-on by 01–06 (PM-000 root); supersession rule routes conflicts to BRIEF/AS-BUILT/audit until Target Spec v1.0.
- **01 (RACI)** maps squads → epics in 04 and decisions D1/D2/D3/D6.
- **02 (Ways of Working)** §5/§6/§8 are operationalized by **08** (release gate) and enforced/measured by **07** (the As-Built gate); D19/D37/D39 are its decisions.
- **03 (Decision Log)** is referenced by every other doc; ADRs are the formal twins of D1/D2/D6/D7/D8/D12/D13/D18/D40/D41.
- **04 (Backlog)** pairs with **07** (reconciles intended→implemented) + **08** (classifies A/B/C); carries each epic's D# + gap; embeds the D42/D43/D44 + seams + oracle notes.
- **05 (Roadmap)** sequences 04's epics; its 7-phase build model is distinct from **08**'s 7-phase release model (do not conflate).
- **06 (Mobilization)** integrates the squad plans (slice D2) + the D2 spike → D2/ADR-0006; sets up the scaffold (ADR-0003).
- **07 (As-Built)** is the current-state SoR; its gap register (G-A…G-J) + delta log are the audit spine; **VAULT.md marks 07 as superseded by the AS_BUILT/ tree** (this slice is part of that successor).
- **08 (Release Governance)** is the build-authorization gate; its Decision Doctrine is the formal statement behind CLAUDE.md's rubric; D37/D39 set its As-Built gate; D44 is its Phase-1 "default=backlog" application.
- **DATA_AND_PROCESS_MAP** is a derived view over 07 + SEAMS + schema + the handoff screens (07 wins on conflict).
- **DESIGN_BRIEF** pairs with 07 (gap register = the net-new list); G-I is its central ask (→E-41).
- **NO_FILE_STORAGE_PLAN** executes ABSOLUTE-REQ #4 / D41 / ADR-0018 / E-42; its `pilot.run` + slices appear in 07 §16/§2/§3 + the v1.23/24 appendix.
- **PRE_TEST_READINESS** measures against D44's frozen scope; its POTATO converter is D45's "rebuild faithfully" subject + HANDOVER's active violation.
- **RECONCILIATION_SEAMS** is the watch-list cited by 04; its seams are placed on the flow in DATA_AND_PROCESS_MAP; resolves into D43/E-44 + D36 + E-39.
- **HANDOVER** is the resume spine (CLAUDE.md "current state" target); flags the live D45 violation + the half-built console (a recorded standing violation of CLAUDE.md REQ #1).
- **VAULT** maps everything; declares 07 superseded; routes archives to slices D3/D5/D6.
- **README** is the repo front door (→`audit/00`, defers current state to 07).
- **WEB_DEPLOYMENT** operationalizes D34/D30/D31/D32 for the harness-on-the-web (the oracle runtime), distinct from the GCP console runtime (D40).

---

# GAPS, DRIFT & ANOMALIES found in this slice (for the synthesizers)

1. **Census omission (2 files):** `HANDOVER.md` and `VAULT.md` are NOT in `AS_BUILT/FILE_CENSUS.md` (census generated 18:52Z; both committed 18:54Z). Violates the audit-standard "every single file is listed." **Action:** regenerate the census; confirm the "896 owned files" total.
2. **Cross-doc staleness — finalize/CLOSED:** `DATA_AND_PROCESS_MAP.md` (v1.0, 02:11) calls finalize/close-out + the `CLOSED` event a GAP, but `07` (v1.26, 02:32, ~20 min later) records it as BUILT. Governed by the map's own "07 wins" disclaimer, but the map is stale on that point.
3. **Active governance violation, recorded:** HANDOVER flags `backend/scripts/potato_legacy_dryrun.py` as a 🔴 unresolved **D45 violation** (single round, 141 rows dropped, regions flattened, lot names = raw IDs, force-positived) seeding the deployed image; `PRE_TEST_READINESS.md` records the same converter run as "✅ DONE … not a bug." Tension between "the run exercised the lifecycle" (true) and "the converter's data fidelity is unacceptable" (also true; D45 orders a faithful rebuild first). Not yet remediated.
4. **Standing NO-MVP violation, recorded:** HANDOVER states the console is "~half built + 4 MVP-cuts" with several surfaces unbuilt — i.e. the program is *currently* short of CLAUDE.md ABSOLUTE REQUIREMENT #1 (no MVP), logged honestly as remediation debt, not hidden.
5. **Two distinct 7-phase models:** `05_MILESTONE_ROADMAP` (build phases 0/A–F) vs `08_RELEASE_GOVERNANCE` (release phases 1 Initial Build…7 Maintenance). Both valid, easy to conflate ("Phase B" ≠ "Phase 1").
6. **Hosting drift in DESIGN_BRIEF:** says Vercel + managed PaaS + "not Azure"; D40/ADR-0017 ratified **GCP Cloud Run + Cloud SQL**. The brief disclaims hosting affects the UI, but D40 is the authority.
7. **README staleness:** still cites "D1..D39", "E-00..E-27", "~28 live routes"; current = D45 / E-44 / 29 routes (07 §14). Coarse front-door, defers to 07.
8. **07 internal version lag:** front-matter v1.26 / `audited_commit ed2d26a`, but §12.3 release-gate line reads "v1.24" and a v1.19 correction line still says "86 tables" while the v1.24 body says 87. Typical living-doc lag.
9. **00 Charter frozen at Draft:** still "pending sponsor ratification," references only D1–D7 / the R-register, while D1–D45 are ratified and a system is live. Least-updated of the living spine.
10. **DORMANT-vs-ACTIVE naming collision (documented, not a defect):** the live `eng.analysis_*` / `awd.*` ORM spine (migrations 0008/0010) coexists with the dormant baseline `eng.calculation_run`/`eng.scenario`/`eng.scenario_award` solver spine in `schema.sql`; `eng.scenario_award` is ALTERed by 0005 yet dormant. Flagged in both 07 §16 and DATA_AND_PROCESS_MAP — a real grep-trap for future readers.
