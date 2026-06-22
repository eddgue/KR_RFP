---
doc: BACKFILL TRIAGE — discussed-but-not-recorded candidates
id: TRIAGE-BACKFILL
status: ⚠️ NON-AUTHORITATIVE STAGING — NOT a live spec. Candidates only.
created: 2026-06-22
---

# ⚠️ Backfill triage — candidates, NOT the source of truth

**Read this first.** This file is a **holding pen** for things that were *discussed in our process but
never recorded* in the live specs. It is **deliberately stored apart** from the authoritative
documents (`04_PROGRAM_BACKLOG`, `07_AS_BUILT_PROCESS_AUDIT`, `03_DECISION_LOG`, the ADRs, the design
docs) so it **cannot corrupt the build plan or live specs**. Nothing here is ratified. The workflow is:
**verify each item → then promote it to its proper home (or discard it).** Until promoted, it has no
authority.

**Sweep scope (be honest about it):** combed THIS session's history + the pre-compaction summary.
Items discussed in *earlier* sessions that predate that record can't be reconstructed from here — name
them and I'll chase each down. Each candidate below was spot-checked against the current code/docs on
2026-06-22 (state noted), but the *decision* on each is yours.

## Candidates

### C1 — Auditor findings: the verification verdicts (pre-compaction)
~22 auditor notes were verified; ~18 confirmed TRUE and actioned (e.g. the capacity NOTE fix,
commits `3e4abfd`/`643fa74`). **4 were OVERSTATED and intentionally NOT actioned**, and that verdict
lives nowhere durable: **#1** engine input-hash (TRUE-partial → see C2), **#10** `WEB_DEPLOYMENT` (the
doc self-discloses its status), **#15** `gen:api` (honestly labelled), **#3** `all_lot_discount` (TRUE
but dead code → see C6). → **Home:** an As-Built audit-notes appendix / a verification log. **Verify:**
re-confirm the verdicts against current code before recording.

### C2 — Input-hash completeness (auditor #1, TRUE-partial)
`runner.py` seals a run with a hashed input manifest (`input_hash`, runner.py:90/150 via
`_inputs_manifest`). Finding: only the **config** is in the manifest — **components / exclusions /
thresholds are NOT** — so two runs differing only in those could share an `input_hash`. → **Home:**
backlog (B item / gap register). **Verify:** read `_inputs_manifest` for its exact contents; decide if
it matters for reproducibility/audit.

### C3 — CI hardening (now partly unblocked)
`frontend/package-lock.json` **is now committed**, but `.github/workflows/ci.yml` still runs
`npm install` (line 176) with a **stale comment** ("no lockfile committed yet … `npm ci` at Phase F").
`next build` + the generated-OpenAPI-client check are also not yet in CI. → **Home:** backlog (E-27
platform). **Verify:** flip to `npm ci`, add `next build`, refresh the stale comment; consider pinned
deps + a deeper migration test.

### C4 — Frontend "Breaches" rename + missing states (pre-redesign)
The "Breaches" column still ships in `frontend/components/alignment/ScenarioComparisonTable.tsx`; the
locked design renames it (capacity/concentration wording), shows names-not-keys, and adds
error-vs-empty states. **Applies only if the CURRENT frontend runs the live cycle** (the redesign
isn't built yet). → **Home:** E-26 (rebuild) or a "current-frontend fixes" note. **Verify:** are we
running the current frontend for the live RFPs?

### C5 — `delete_run` has no console close-out route
`PilotService.delete_run` exists (service.py:1309, added in the no-file-storage refactor) but **no HTTP
route calls it** (none existed). → **Home:** the finalize / close-out step (E-22 / E-43) or the screen
coverage audit. **Verify:** confirm route absence; decide where close-out lives.

### C6 — `all_lot_discount` dead code (auditor #3, TRUE-harmless)
A dead-code path; harmless but tech-debt. → **Home:** As-Built §20.2 tech-debt / backlog. **Verify:**
confirm it's still dead before recording/removing.

### C7 — Working-practice principles (meta)
Recurrent standing directives that may not be consolidated anywhere: **save as you go · verify before
actioning · least margin for error · full functionality with least margin for error · run
constrained, targeted agents (the harness loop) · MCP harness = verification oracle.** → **Home:**
`02_WAYS_OF_WORKING`. **Verify:** check what 02 already states before adding.

## Promotion log

Sponsor triage 2026-06-22 — filter: *does it affect the user process or analysis process?* If yes,
decided in layman terms; if not (internal / already covered), dropped.

| Candidate | Decision | Date |
|---|---|---|
| C1 — auditor verdicts | **Dropped** — internal record, no user/analysis impact | 2026-06-22 |
| C2 — input fingerprint completeness | **DONE** — sponsor approved; `_inputs_manifest` now seals the full `EngineConfig` (`model_dump`), tamper-evident over all inputs. 4 tests; As-Built v1.25 | 2026-06-22 |
| C3 — CI hardening | **Dropped** — dev/infra, no user/analysis impact | 2026-06-22 |
| C4 — "Breaches" label | **DONE** — renamed to "Over capacity" on the current comparison screen (`ScenarioComparisonTable.tsx`) | 2026-06-22 |
| C5 — in-app close-out | **APPROVED → build** — finalize/close-out action + route (governed close event, award/rejection notices render on request, gated on a frozen award); pairs with E-22/E-43 + the design's finalize step. Promote to backlog on build. | 2026-06-22 |
| C6 — `all_lot_discount` dead code | **Dropped** — internal, no user/analysis impact | 2026-06-22 |
| C7 — working-practice principles | **Dropped** — meta/process, no user/analysis impact | 2026-06-22 |
