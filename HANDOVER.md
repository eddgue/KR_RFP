---
doc: HANDOVER — read this FIRST to resume after a context clear
id: HANDOVER
updated: 2026-06-22
owner-model: sponsor = layman client; assistant = studio owner (see CLAUDE.md)
---

# HANDOVER — current state & how to resume

> **Read order on resume:** `CLAUDE.md` (the contract + guiding principles) → this file →
> `VAULT.md` (the doc map) → `project/03_DECISION_LOG.md` (esp. D45) →
> `project/triage/DRIFT_RECONCILIATION.md` (what's real vs not) → `AS_BUILT/00_INDEX.md` (audit tracker).

## Where the product is
- **Live on GCP Cloud Run.** Frontend: `https://kr-rfp-frontend-626832546924.us-central1.run.app`
  (also `…-5qcaubkbkq-uc.a.run.app`). Backend: `https://kr-rfp-backend-626832546924.us-central1.run.app`.
  Login: `admin` / `Eagv.3248!!`. Project `krrfp-500214`, region `us-central1`, Cloud SQL Postgres 16.
- **Deploy is one command** from GCP Cloud Shell: `deploy/gcp/deploy.sh` (idempotent). `--no-seed` to
  redeploy without duplicating demo runs. Cookie is `SameSite=None` (cross-site); CORS allows both
  frontend URL spellings. Seed loads TOMATO (synthetic) + POTATO (legacy-converted) runs.
- **Branch:** `claude/wizardly-pasteur-n4acb8`. Commit + push there only.

## The truth about what's built (from DRIFT_RECONCILIATION.md — verified vs the record)
- **Engine + governed-persistence spine is FULL-FIDELITY** (not stubbed): v3 5-factor scoring, 7
  lenses A–G, split allocation + cap-breach, sealed reproducible runs, freeze-and-layer immutability,
  canonical formula registry, flat-13 storage, key-validated ingest, stateless render-on-request,
  savepoint/compare. This is real and tested.
- **Console is ~half built + 4 MVP-cuts.** Built+real-data: dashboard, run hub, intake, alignment,
  awards. **Not built:** full Cycle Setup/Strategy, Suppliers, Sign-off, Settings/RBAC, Reconciliation,
  and the run-scoped nav rail (sidebar has one link). No mock data in the built screens.
- **🔴 ACTIVE VIOLATION (fix first): the potato converter** `backend/scripts/potato_legacy_dryrun.py`
  cuts corners D45 forbids — single Delivered round only, 141 demand rows dropped, regions flattened,
  lot names = raw IDs, values force-positived — and it seeds the deployed image. **D45 ordered it
  rebuilt faithfully BEFORE more console build. Still unmet.**
- **Backend perimeter not built (recorded, deferred):** RBAC enforcement (defined, 0 routes call it),
  sign-off gate (SIGNED_OFF enum never emitted), iTrade importer (E-08 dormant → "vs STLY" is a
  synthetic ×1.04 proxy), safety reprice + USDA feed (E-29), PBA builder (E-33), comms send (4/7
  touchpoints unrouted). Tenancy: no RLS (D8 drift). Setup/capacity ingest emit no audit event.

## The work queue (remediation order — per D45 + the decision-weighting rubric)
1. **Rebuild the potato converter faithfully** (all rounds, all volumes, real names/regions, no
   value-forcing, quarantine bad data) + a field-by-field mapping audit reconciled to the golden
   NUMBERS at each step. **First — it taints the data the client reviews.**
2. **Build the full console to fidelity** (no stubs): nav spine, full Setup/Strategy, Suppliers,
   Sign-off, Settings/RBAC, Reconciliation. (DB tables for Suppliers/DC/aliases/quarantine/invited
   already exist — no migration. Sign-off + RBAC + M2 need migrations. RBAC must default existing
   admin to full access — lock-out risk.)
3. **Build the backend perimeter** as scoped (RBAC enforce, sign-off gate, iTrade importer, safety
   reprice+feed, PBA, comms send); close audit-write-point + tenancy/RLS drift.
4. Delete the dead empty routers (`awards.py`/`cycles.py`/`documents.py`/`ingest.py`) or fill them.

## In progress right now
- **Exhaustive AS-BUILT audit.** 896 owned files censused (`AS_BUILT/FILE_CENSUS.md`, 18 empty).
  Per-file deep audit (detailed what + WHY) is being filled slice-by-slice into `AS_BUILT/files/` per
  the tracker in `AS_BUILT/00_INDEX.md`. **To continue: open the tracker, launch constrained agents
  on PENDING slices (contract injected), commit outputs, flip rows to DONE, then synthesize the 3
  LAYER reports.**

## Operating model (CLAUDE.md)
Layman-client / studio-owner. Save constantly; one source of truth. Decision rubric: **longevity →
full functionality → error reduction → drift reduction.** Nitro mode: constrained agents in a
set-up→prompt→execute→review→prompt loop. **Assume context clears every 3rd prompt — commit + note
that often.** No MVP/stubs/placeholders, ever. Data fidelity through every step.
