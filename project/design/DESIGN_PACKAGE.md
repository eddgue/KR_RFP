---
doc: Design package — round 2 (the full deliverable to hand the design team)
id: PM-007-DR-PKG
version: 1.0
status: Send-ready — the consolidated design ask (cover + the included docs)
created: 2026-06-22
---

# Design package — round 2 (start here)

This is the **full design deliverable**: what to keep, what to fix, what to build next, and the
context to ground it. Read this cover, then the included docs.

## 1. Verdict — the baseline is LOCKED. Extend it, don't redesign.

The v2 handoff is the **UI baseline** (you + the auditor agreed: *calm by default, gravity only at
exceptions and governed decisions*). The six screens (Login · Dashboard · Run Detail/Overview · Bid
Intake · Alignment Workspace · Awards) and the **Handoff** design-system page stand. Do **not** rework
the core experience — the asks below are **corrections + net-new screens + visuals** that build on it.

**Rebuild target:** the `.dc.html` are the **visual source of truth to rebuild in Next.js + Tailwind —
not merged.** Point the developer at **`Handoff.dc.html` first** (tokens for `theme.extend`, component
states, non-happy-path, field reference, a11y, Lucide). View locally via a quick local server
(double-clicking `file://` can blank the `support.js` runtime).

## 2. Corrections to the existing screens (small — finishes the baseline)

1. **Compact-width status-strip** — at narrow widths the four states clip ("Live · Roun…",
   "Hash-chain curr…"). At the compact breakpoint use short labels, no clipping: **Live · Sealed v1 ·
   Not frozen · Current.**
2. **Audit-state drill-through** — make "Hash-chain current" **clickable** → the latest event (actor ·
   timestamp · type · affected artifact/version · prior-hash). Don't make users dig through Run Detail.
3. **Refresh the stale Awards screenshot** — the `Awards.renderVals … c.demand is undefined`
   screenshot is **stale (export lag), not a live defect** (the prototype renders fine). Just replace it.

*(Already done in v2: "Save vs STLY" carries the MODELED tag; the lenses are A–G/seven.)*

## 3. New screens to design — full briefs in `DESIGN_REQUESTS.md` (included)

In priority order (details, data bindings, decisions, access points + states are in `DESIGN_REQUESTS.md`):

- **A1 · Cycle Setup / Scope-review + Strategy config** — the front-of-funnel hole: review the
  ingested cycle + set the strategy (weights/preset, the 4 safeties, exclusions/preferred, lenses).
  Today setup is a blind file upload. **Top ask.**
- **A2 · Finalize / Close-out** — the backend is **already built**; design the AssertModal + the
  "Closed" run state. After a FROZEN award, lock the run and surface the award (won) + rejection
  (not-won) notices.
- **A3 · Editable column mapper** — make the messy-file mapping **correctable** (field dropdown per
  column + resolve ambiguities), not confirm-only. *(Only if you'll accept suppliers' own sheets.)*
- **A4 · Supplier comms (E-37)** — the 6 touchpoints' review/edit/send surface. *Parked; the next
  major workstream once un-parked.*
- **A5 sign-off (G-D) · A6 settings/admin/users/roles (G-C/G-J) · A7 supplier mgmt + participant
  selection (E-34)** — governance/multi-user, before a second operator/production.

## 4. Visuals to produce (beyond whole screens) — see `DESIGN_REQUESTS.md` §B

- The 3 corrections above (B1).
- Non-happy-path states (empty / loading / error / read-only) for the new screens (B2).
- Visualizations (B3): scenario capacity-feasibility, version-compare two-up + ROUND/FINAL marker +
  meeting/date labels (E-43), the deep-workbench diligence charts (E-41), price-movement (E-35, later).
- Closed/finalized iconography + the run-status states (B4).

## 5. Recommended order
**A1 (setup/strategy) + the 3 corrections** → **A2 (finalize UI)** → A3/A4 → Tier-2 (A5/A6/A7).

## 6. What's in this bundle
- **`DESIGN_PACKAGE.md`** (this cover).
- **`DESIGN_REQUESTS.md`** — the per-screen briefs + the visuals list (the actionable detail).
- **`SCREEN_COVERAGE_AUDIT.md`** — the delivered-vs-needed analysis the asks come from.
- **`DATA_AND_PROCESS_MAP.md`** — the data-relationship ERD + the process/data-flow flowchart
  (decision points, access points, the reconciliation "middle-step" seams) — grounds where each screen sits.
- **`handoff/`** — the locked v2 baseline (the 6 screens + `Handoff.dc.html` + Kroger assets).
