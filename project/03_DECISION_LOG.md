---
doc: Decision Log
id: PM-003
version: 0.1
status: Living
created: 2026-06-18
depends_on: PM-000
---

# Decision Log

The register of program-shaping decisions. **OPEN** decisions gate detailed squad planning and are escalated to the Sponsor. Each carries the PM/Architect recommendation so ratification can be a confirmation, not a research task. Dependencies (DEP-n) are logistics blockers, not choices.

Status: **OPEN** (awaiting sponsor) · **RATIFIED** · **SUPERSEDED**.

---

## Decisions

### D1 — Build path · **RATIFIED 2026-06-18 → clean-room reconciliation** (ADR-0001)
**Question.** Reconcile-and-extend the existing 63-table store, or greenfield the brief's 36-table schema?
**Resolution.** **Clean-room reconciliation.** New clean codebase; the AS-BUILT *schema* (re-expressed as clean PostgreSQL) is the migration baseline; the existing repo stays isolated in the sponsor's GitHub and is never imported (sponsor constraint: "i dont want it contaminating this build … keep it isolated"). The seven KEEP capabilities are re-modeled, not inherited; the wrong brain and SQLite-isms are dropped by construction. See ADR-0001 for the isolation protocol.
**Linked:** audit D1, DEP-1, ADR-0001.

### D2 — The brain · **SPIKE COMPLETE → recommends Option A · awaiting sponsor ratification** · needed by: Phase D entry
**Question.** Adopt v3's 5-factor scoring + split allocation as the engine (retiring min-cost to a reference lens), or extend the as-built Scenario A?
**Spike result (2026-06-18).** `project/squads/engine-domain/SPIKE_D2_engine.md` recommends **Option A — adopt v3**: five-factor banded scoring + `max_two_per_dc` split as the engine library; the as-built min-cost solver becomes "Scenario A = lowest-cost reference." Strongest reason: only A is faithful to the verified real behavior (deck splits + cost-is-35% scoring, both confirmed in code); B installs a single-winner min-cost brain the evidence contradicts (R2). Ship G1+G2 together, after the Phase-B pilot.
**Status.** Ready for sponsor ratification → then ADR-0006. **Non-blocking:** the engine *interface* is frozen regardless (Architect), so store/contract/tests proceed against a deterministic stub.
**Linked:** audit D2, gaps G1/G2, SPIKE_D2_engine.md.

### D3 — Pricing placement & safeties · **OPEN** · needed by: Phase C/D
**Question.** Lift pricing + the five safeties to kickoff and make the safeties executable, keeping the as-built's commercial component storage?
**Recommendation.** **Yes.** Real kickoff docs declare pricing there (Discrepancy #3/#11); safeties are "the real product" and currently inert (R5).
**Impact if changed.** Pricing stays at the wrong layer; safeties stay decorative.
**Linked:** audit D3, gap G4.

### D4 — Outward-facing sequence · **OPEN** · needed by: Phase E entry
**Question.** Order of the `awd.*` build and which generated artifact ships first?
**Recommendation.** **award → freeze → sign-off → outputs; booking guide first** (most-used; v1.4 has `generate_booking_sheet`).
**Linked:** audit D4, gap G3.

### D5 — Net-new enterprise scope · **OPEN** · needed by: Phase 0/A
**Question.** Commit tenancy (`client`), RBAC, PII/retention, and NFRs from the start?
**Recommendation.** **Yes — design tenancy in now** (cheap before breadth, expensive after); author the security/NFR spec in parallel with Phase A; make the real-data pilot Phase B's exit gate.
**Linked:** audit D5, gaps net-new, R7.

### D6 — Frontend / "enterprise web app" stack · **RATIFIED 2026-06-18 → React/Next.js + TypeScript SPA** (ADR-0002)
**Resolution.** React + Next.js (App Router) + TypeScript, a pure client of the FastAPI backend, types generated from OpenAPI, built last (ADR-001). Streamlit is retired, not hardened.
**Linked:** ADR-0002.

### D7 — Execution mode for this engagement · **RATIFIED 2026-06-18 → plan then scaffold now** (ADR-0003)
**Resolution.** Finish detailed squad planning, then stand up Phase 0/A running ground this engagement (validated schema baseline, backend skeleton, tenancy/RBAC foundation, CI, infra), treating ratified decisions as binding and D2 as in-spike.
**Linked:** ADR-0003.

---

## Dependencies (logistics blockers)

| ID | Dependency | Blocks | Owner | Status |
|---|---|---|---|---|
| **DEP-1** | **Isolated, read-only** access to the existing repo (`models.py`, Alembic chain, tests, ECLS) — in the sponsor's GitHub; read via an isolated worktree agent per ADR-0001, never imported | ECLS/test verification, R6 | Sponsor | **OPEN — non-blocking** (we baseline from the as-built schema we already hold) |
| DEP-2 | One **real iTrade pull** + one **real bid round** (synthetic-only today) | Phase B pilot, S2, R1 | Sponsor | OPEN |
| DEP-3 | One or two **real kickoff docs** (for the keystone, G5) | Phase C | Sponsor | OPEN (4 referenced in intake) |
| DEP-4 | Target hosting/cloud + identity provider (for tenancy/RBAC/D6) | Phase A DevOps/Sec | Sponsor/IT | OPEN |

---

## Ratified

*(none yet — `D-gaps` interpretation confirmed by sponsor 2026-06-18: "gsps" = gaps.)*
