# Release Governance & Change Management — RFP Engine

> **Status:** ratified 2026-06-21. This document governs **what may be built and when**. It is paired
> with the **As-Built Specification** (`07_AS_BUILT_PROCESS_AUDIT.md` — the single source of truth for
> *what exists*) and the **Program Backlog** (`04_PROGRAM_BACKLOG.md` — the item register).

## Decision Doctrine (how every decision is made)

Ratified 2026-06-21. These seven principles govern *how* we decide; the rules below govern *what* gets built and *when*.

1. **Outcome over output — full functionality, least margin for error.** Every call optimizes for a system that runs live RFPs accurately, repeatably, and auditably — not feature count. This is the tiebreaker when options compete.
2. **Default to backlog, not build; classify before acting.** A (critical fix → now) / B (enhancement within existing architecture → live-run cycles) / C (new module/workflow/domain → deferred). When unsure → backlog. The goal is live-run readiness, not perpetual development.
3. **Truth from reality, never from documents or memory.** Verify claims against the code/schema. The As-Built Spec is the single source of truth and must reconcile to what actually runs; no sprint is done until it is updated; no tribal knowledge.
4. **AI-generated, not AI-managed — the human asserts.** The engine and the agent recommend and prepare; the load-bearing decisions (award, sign-off, send, **merge**) are human-asserted and audit-evented. The agent never auto-asserts a governed outcome.
5. **Reversible and in-scope → proceed; consequential or ambiguous → surface.** Act autonomously on routine, reversible work and **save as you go** (commit/push so nothing is lost). Stop at genuine forks — destructive, architecturally significant, scope-changing, or where intent is load-bearing — via explicit control points, not constant check-ins.
6. **Gate before you ship.** Deterministic review at control points, fix *every* confirmed finding, and never merge over an open issue or a knowingly-stale record. Verify, don't assume; if in doubt, surface quickly.
7. **Small, verified, behavior-preserving.** Prefer small reviewable changes; prove correctness (e.g., byte-identical tests for refactors); record the delta. Minimize the surface for error.

## Core principle

**Default to backlog, not build.** The objective is a production-ready engine that runs live sourcing
events with accurate, repeatable, auditable results — **not** continuous feature development. Every
requested change is **classified before any work begins**.

## Success is…

Accurate calculations · reliable execution · repeatable outcomes · complete auditability · reduced
manual effort · stable operation across multiple live cycles · clear documentation · sustainable
maintenance. **Not**: maximum feature count, continuous expansion, architectural complexity, constant
redesign.

## Change classification (assign before building)

| Cat | Meaning | Examples | Priority |
|---|---|---|---|
| **A — Critical fix** | Wrong results / blocked execution / integrity, audit, security, data-loss | calc error, incorrect output, crash, workflow blocker, auditability failure, corrupted/lost export | **Immediate** |
| **B — Operational enhancement** | Improves analysis/reporting/validation/workflow/efficiency **inside the existing architecture** | new scoring/scenario calc, better reports, enhanced validation, UX/automation within existing modules, template improvements, decision-support outputs | **Eligible during Live Run #1/#2 cycles** (not speculative Phase-1 work) |
| **C — Major feature** | New module / agent / workflow family / database / dashboard / app section / integration / domain / **architectural redesign** | — | **Backlog only** until the Phase-4 post-validation review |

**B constraints:** operate within existing modules; no architectural redesign; no new system domains;
no new core workflows. **Anything that fails these is C.**

## Decision rules (in order)

1. Produces incorrect results? → **A**, fix now.
2. Blocks execution? → **A**, fix now.
3. Improves analysis/reporting/validation/workflow/efficiency **within existing architecture**? → **B**.
4. Introduces a new module / workflow family / agent / integration / domain / architectural component? → **C**, backlog.
5. Has Production Lock occurred? If yes, all enhancements → backlog → future-release planning.

**Default action when unsure: backlog.**

## Phases

1. **Initial Build (current)** — build agreed V1; avoid speculative features / future-proofing beyond reasonable need.
2. **Live Run #1** — operational validation; fix A immediately; approved B via short cycles; log C. No architectural redesign.
3. **Live Run #2** — repeat validation; A + B only; C deferred.
4. **Feature Consolidation Review** — evaluate every C item → Approve / Defer / Reject.
5. **Final Audit** — production-readiness review (calcs, data integrity, auditability, reporting, agents, workflows, docs); resolve all critical findings.
6. **Production Lock** — V1 complete; freeze core architecture / data model / modules / workflows / agents / analysis framework / storage / export.
7. **Maintenance** — bug/security/regulatory/template/report-format/minor-UX only; everything else → backlog. Future major work only via a formal **Version 2** planning cycle.

## Current phase & standing rulings (2026-06-21)

- **Phase: 1 — Initial Build, pre–Live Run #1.**
- **As-Built rule:** *no sprint is complete until the As-Built Specification is updated* (single source of truth; current-state and roadmap never mixed).

### Classification of the live backlog (see `04_PROGRAM_BACKLOG.md`)

| Item | What | Class | Disposition (Phase 1) |
|---|---|---|---|
| **E-37** comms email drafts (award/feedback/non-selection) | shipped (PR #18) | B (within existing output/render) | ✅ delivered |
| **E-39** canonical formula registry | shipped/in-review (PR #19) | A-adjacent (systemic fix for a calc-divergence defect; behavior-preserving) | ✅ delivered |
| **E-38** supplier capacity | ingest + persist + engine/custom cap flag + workbook control tab | **B** | **BUILD now** (accuracy: never recommend an award beyond stated capacity). **Wires the EXISTING baseline tables `bid.capacity_statement` + `bid.capacity_constraint` (As-Built §16) — NOT a new store**; usage computed against the active `eng.analysis_scenario_award` (NOT `eng.scenario_capacity_usage`, which is keyed to the dormant solver spine). |
| **E-38** supplier capacity | the in-app allocation-vs-capacity **dashboard** | **C** (new app section) | **Backlog** → Phase-4 review |
| **G-C** RBAC enforcement | call `require_permission` on routes | B (within existing auth) | Backlog/Live-Run (not speculative now) |
| **G-D / E-24** sign-off + draft→SENT lifecycle | new transition/state/gate + `SIGNED_OFF`/`SENT` events | **C** (new workflow family) | Backlog |
| **E-33 / G-F** PBA / contract builder | new post-award builder | **C** (new module/domain) | Backlog |
| **E-34 / E-08/09** supplier importer / external feeds | new ingestion + integrations | **C** | Backlog |
| **E-35** discovery / price-movement view | new app view | **C** (new app section) | Backlog |
| **E-36** progressive timeframe commitment / continuation RFP | new workflow family | **C** | Backlog |
| **E-28** contracted-vs-effective analytics | new analytics domain over external feeds | **C** | Backlog |

This table is the operative gate: only **A** and the **E-38 B-core** are buildable in Phase 1; everything
marked **C** is recorded and deferred until the post–Live-Run consolidation review.

## Review cadence & control points

**Two review tiers:**

1. **Agent self-review (every PR, automatic-by-agent).** Before calling a checkpoint, the agent runs a **tightly-scoped, read-only review agent** that verifies the change against the actual code/schema (not the docs) and reports findings; the agent triages (classify A/B/C), fixes, and re-verifies. This replaces the retired push-basic Codex bot (Codex is no longer in the loop). *(Push-basic Codex review was used through PR #20; it is no longer available.)*
2. **Human full-suite auditor (manual).** A deeper external review the **human runs on request** and pastes back. It does **not** auto-run, so the agent **explicitly calls it at defined control points**; the agent then triages findings (A/B/C), fixes the actionable ones, calls a re-run if the change was material, and proceeds only when clean.

Each manual-auditor request is a standout, copy-pasteable block:

> 🔎 **REVIEW CHECKPOINT** — please run the **full detailed auditor** on **<PR # / branch / commit range>**. Scope: `<what changed>`. I'll hold the merge until the report is back.

**Control points (when the agent will call the manual detailed auditor):**

1. **Pre-merge — every PR (primary gate).** When a PR is green and ready, before merge. This is the recurring rhythm — in practice a review lands at **every PR**, which is the "periodic" cadence.
2. **Sprint close.** When a unit of work + its **As-Built Specification** update is complete (often coincides with #1; called out separately for spec-only or multi-commit sprints — the As-Built rule: *no sprint complete until the spec is updated*).
3. **Phase gates.** Entering/leaving Live Run #1, Live Run #2, Feature Consolidation, Final Audit, Production Lock — a deeper full review (per Phase 5).
4. **Backstop.** If work accumulates without hitting 1–3 (e.g., a long working session), the agent calls a checkpoint rather than let review debt build.

**Between control points** the agent keeps working and committing ("save as you go"), but **does not merge** a PR until its review checkpoint is satisfied. If the human says "skip the review on this one," the agent proceeds and records that in the PR.
