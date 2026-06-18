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

### D1 — Build path · **OPEN** · needed by: Phase 0 exit
**Question.** Reconcile-and-extend the existing 63-table store, or greenfield the brief's 36-table schema?
**Recommendation.** **Reconcile-and-extend.** A real governed store exists; greenfield would discard 46 identity FKs, the calc-run spine, and proven landed-cost/eligibility/VSP work (R3).
**Impact if changed.** Flips the Platform & Data squad's entire migration plan; greenfield re-incurs the rigor the as-built already has.
**Linked:** audit D1, DEP-1.

### D2 — The brain · **OPEN** · needed by: Phase D entry
**Question.** Adopt v3's 5-factor scoring + split allocation as the engine (retiring min-cost to a reference lens), or extend the as-built Scenario A?
**Recommendation.** **Adopt v3.** It is the brief's ground truth; the min-cost solver becomes Scenario A = "lowest-cost reference." Ship G1+G2 together.
**Impact if changed.** Keeps a single-winner grain at the core (R2); contradicts the brief.
**Linked:** audit D2, gaps G1/G2.

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

### D6 — Frontend / "enterprise web app" stack · **OPEN (new — raised by the build mandate)** · needed by: Experience squad mobilization
**Question.** The user mandated an "enterprise-level web app." The as-built front end is **Streamlit**, which is not an enterprise SPA. Options: (a) **React/Next.js + TypeScript SPA on the FastAPI backend** (true enterprise web app); (b) keep & harden Streamlit (faster, weaker UX/governance); (c) other.
**Recommendation.** **(a) React/Next.js + TypeScript SPA.** Matches the "enterprise web app" mandate, gives a real auth/RBAC surface, and is a clean view onto the API. Streamlit was already flagged "structurally bad UI on a stateless engine" in the intake.
**Impact.** Shapes the Experience and DevOps squads (build pipeline, hosting, auth integration).

### D7 — Execution mode for this engagement · **OPEN (new)** · needed by: now
**Question.** What does "start the project / full deliverable" mean for *this* engagement? (a) **Plan & mobilize** — produce the full enterprise delivery plan (charter ✓, squads ✓, backlog, architecture, roadmap, estimates) and stand up the structure, then build on your go; (b) **Plan then start the foundation now** — also begin building Phase 0/A scaffolding (repo skeleton, validated schema, CI) with the agent squads this session; (c) **Build-first** — start implementing immediately against the recommended decisions.
**Recommendation.** **(b)** — finish planning with the squads, then immediately scaffold Phase 0/A so there is running ground, treating the recommended decisions as working assumptions until you ratify.

---

## Dependencies (logistics blockers)

| ID | Dependency | Blocks | Owner | Status |
|---|---|---|---|---|
| **DEP-1** | Access to the **actual codebase** (`models.py`, Alembic chain, tests) **and the ECLS** (`RFP_ENGINE_CONTROL_LAYER_SPEC_v1_0.md`, the as-built's stated source of truth) | D1 execution, Phase 0/A, R6 | Sponsor | **OPEN** — not in the audited packages |
| DEP-2 | One **real iTrade pull** + one **real bid round** (synthetic-only today) | Phase B pilot, S2, R1 | Sponsor | OPEN |
| DEP-3 | One or two **real kickoff docs** (for the keystone, G5) | Phase C | Sponsor | OPEN (4 referenced in intake) |
| DEP-4 | Target hosting/cloud + identity provider (for tenancy/RBAC/D6) | Phase A DevOps/Sec | Sponsor/IT | OPEN |

---

## Ratified

*(none yet — `D-gaps` interpretation confirmed by sponsor 2026-06-18: "gsps" = gaps.)*
