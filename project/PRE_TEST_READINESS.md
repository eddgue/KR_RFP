---
doc: First pre-test readiness review — are we fully functional end-to-end?
id: PM-PRETEST
status: Review (2026-06-22) — gap analysis against the live-test critical path (D44)
relates: project/03_DECISION_LOG.md (D44 freeze), project/04_PROGRAM_BACKLOG.md (E-26, E-44),
         project/design/DESIGN_PACKAGE.md, project/triage/MANUAL_MODEL_FINDINGS.md
---

# First pre-test readiness review

**What the first pre-test is (D44 scope):** run **one real RFP end-to-end on the new design (E-26)** and
**compare the output to the MCP harness and the manual allocation model**. Live-test scope = **E-26 +
the existing working pipeline**; everything else (E-44 modality/cost, midpoints, comms-send, deploy) is
an enhancement unless flagged vital.

## Lifecycle readiness (the end-to-end path)

| # | Step | Backend | Frontend (E-26) | Blocker for pre-test? |
|---|------|:--:|:--:|---|
| 1 | Sign in (password + optional 2FA) | ✅ | ✅ Login | No |
| 2 | Create run | ✅ | ✅ Dashboard | No |
| 3 | Ingest setup/kickoff workbook → cycle | ✅ stream-ingest | ✅ Intake step 1 | No |
| 4 | Set strategy (weights / safeties) | ✅ get/set on cycle | ✅ **minimal strategy panel (Run Detail)** | No (built) |
| 5 | Generate round bid template | ✅ | ✅ Intake step 2 | No (fixed cost model = matches the manual) |
| 6 | Suppliers fill template → import bids | ✅ strict + flexible | ✅ Intake step 3 | No **if** strict owned template used (**call C**) |
| 7 | Run analysis → scenarios A–G | ✅ | ✅ Alignment | No |
| 8 | Inspect lenses / cells | ✅ | ✅ Alignment | No |
| 9 | Freeze award (governed) | ✅ | ✅ AssertModal | No |
| 10 | Finalize / close run + award & rejection notices | ✅ | ✅ AssertModal | No |
| 11 | Downloads (render-on-request, stateless) | ✅ | ✅ | No |
| 12 | Audit trail (hash-chained) | ✅ | ◐ (drill-through is a design correction, not built) | No |

**Verified:** the frontend builds clean (`next build`, all routes); all six screens preserve the existing
API wiring; the engine + generators are unchanged (the harness-oracle still produces identical analysis
from identical inputs). The current **fixed** price model (FOB · delivery · vegcool/XDOCK · lot/all-lot
discount) **matches the manual potato cost lines** (verified, `MANUAL_MODEL_FINDINGS.md`), so the
comparison is apples-to-apples.

## The 3 judgment calls that decide "fully functional"

These aren't bugs — they're scope choices for the *first* pre-test. Each has a low-risk default.

- **A — Strategy config — ✅ RESOLVED (built a minimal panel).** A weights-preset + four-safeties
  panel on Run Detail reads/sets the EFFECTIVE `EngineConfig` (persisted to the cycle; the next
  analysis uses it). Backend `GET/PUT /runs/{slug}/strategy` + tests; no engine change. The full A1
  (incl. the E-44 modality/cost manager) stays deferred.
- **B — Where it runs — ✅ RESOLVED: LOCAL.** The pre-test runs locally (backend + Postgres + `next
  dev`). GCP deploy prep (Cloud Run + Cloud SQL) is **parked** for a later, wider live test.
- **C — Import path — ✅ RESOLVED: STRICT owned template.** Deterministic import; the editable column
  mapper (M1) is **not** needed for the pre-test and stays deferred.

## Deferred (NOT blockers for the scoped first pre-test)

E-44 (modality/cost/grain configurability) · A1 full strategy screen · A2 finalize UI polish (the action
itself is built) · A3/M1 editable mapper · A4 comms **send** (drafts render fine) · A5–A7 governance/admin
· M2–M6 reconciliation midpoints · the 3 design corrections (status-strip labels, hash-chain
drill-through, refresh Awards screenshot) · GCP deployment.

## Verdict

**Pre-test build scope is COMPLETE** (sponsor's three calls: A — minimal strategy panel BUILT · B —
run LOCAL · C — STRICT owned template). The **end-to-end RFP lifecycle is functional on the new
design** for a first pre-test and a clean comparison to the harness + manual model. None of the
deferred items (E-44 modality/cost, full A1, M1 mapper, comms-send, GCP deploy, the 3 design
corrections) block *that* scoped run — but each is a real limitation to acknowledge before a *wider*
live test (esp. M1 messy-file import and deployment).

**Test tiers — DRY vs LIVE (sponsor, 2026-06-22).** The **dry test (this first pre-test) is approved as
is** — the fixed timeframe-grain model is fine. The **LIVE tests additionally require the fan-in /
fan-out per-period granulation** (D42 / D38 / E-35): collect **FOB by period + freight by period**
(fan-in), store flat-13, **roll up to timeframe** for the engine (fan-out), and the per-period display
surfaces (movement + the mixed-grain analysis breakdown). Build that **before the live tests, not the
dry one.** (Tracked on D44 + the backlog grain note.)
