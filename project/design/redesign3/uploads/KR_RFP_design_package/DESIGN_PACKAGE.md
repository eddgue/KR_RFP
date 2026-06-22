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

**The three big things (the spine of this package):** (1) **treat data like data** — every control is
a data operation, so define how data is treated on each state change (**§0**); (2) **full screen
gaps** — the missing lifecycle screens (**§3** here / **§A** in `DESIGN_REQUESTS.md`); (3) **design the
midpoints** — the in-between reconciliation steps no screen owns (**§4b** here / **§C** in
`DESIGN_REQUESTS.md`). Everything else (corrections, visuals, interaction rules) supports these three.

## 0. Guiding principle (read first) — data-driven: every control is a data operation

**This is a data-driven process. A "button" is never just a UI state — it is a DATA operation.** For
every control (toggle · filter · sort · lens selector · supplier picker · version picker · freeze ·
finalize · record-adjustment), the design must make explicit **how the data is treated when its state
changes** — what recomputes, from what source, what's sealed, and what's audited. Classify every
control:

- **View ops** (filter · sort · lens-inspect · drill) — **reshape the view, never mutate.** All derived
  values (totals, %, counts, rollups) **recompute against the visible set** (see B5); the data is untouched.
- **Live-edit ops** (Custom build / Scenario-F per-cell change) — **recompute live** (re-score, re-total,
  re-flag capacity/concentration) against the live working scenario; clearly marked **live / unsaved**.
- **Version switch** (the picker: live ↔ sealed snapshot) — swaps the **data source**: live = editable +
  recomputing; a sealed version = **read-only immutable snapshot.** Which one you're on must be unmistakable.
- **Governed ops** (import · freeze · record-adjustment · finalize/close) — **seal/mutate the system of
  record + write an audit event** (the human asserts); gated, confirmed, append-only / irreversible.

Two invariants under all of them: **the DB is the source of truth and outputs derive on request** (a
state change recomputes/derives — it never shows a cached/stale number), and **governed ops are
audit-evented + tamper-sealed** while view/edit ops are transient and never silently alter sealed data.
Design (and build) every control through this lens.

## 1. Verdict — the baseline is LOCKED. Extend it, don't redesign.

The v2 handoff is the **UI baseline** (you + the auditor agreed: *calm by default, gravity only at
exceptions and governed decisions*). The six screens (Login · Dashboard · Run Detail/Overview · Bid
Intake · Alignment Workspace · Awards) and the **Handoff** design-system page stand. Do **not** rework
the core experience — the asks below are **corrections + net-new screens + visuals + midpoints** that build on it.

> **The live test will run on THIS rebuilt design (Next.js + Tailwind), not the current frontend.** So
> completing this set — the missing screens *and* the midpoints — is on the path to go-live, not a
> later polish pass.

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
- **Interaction-correctness rules (B5, cross-cutting):** **totals/%, counts, and rollups always follow
  the filter/sort — never a stale full-table number** (sponsor's example); plus empty-filter states,
  selection-reflects-summary, drill consistency. A living list ("those sort of things").

## 4b. Midpoints — the in-between reconciliation steps (full list in `DESIGN_REQUESTS.md` §C)

The "middle steps" no lifecycle screen owns — where data is mapped/reconciled across grains & systems,
and where real data silently breaks. Each needs a human-facing **propose → confirm/correct → sticky**
surface (never guess):
- **M1** editable column mapper (= A3) · **M2** lot/item ↔ **SKU** sticky map (E-11 — the headline;
  prerequisite for real STLY, E-28, E-35) · **M3** supplier/DC identity resolution / dedup (E-34) ·
  **M4** unit / pack-size reconciliation · **M5** ingest quarantine resolution (setup + bids) ·
  **M6** date → timeframe/period confirm.

Grounded in `RECONCILIATION_SEAMS.md` + the seam nodes on `DATA_AND_PROCESS_MAP.md`.

## 5. Recommended order
**A1 (setup/strategy) + the 3 corrections** → **A2 (finalize UI)** → A3/A4 → Tier-2 (A5/A6/A7).
Design the **midpoints (§C)** alongside the screens they ride with (M1/M5 with intake, M6 with A1,
M2/M3/M4 with the iTrade feed but patterned now).

## 6. What's in this bundle
- **`DESIGN_PACKAGE.md`** (this cover).
- **`DESIGN_REQUESTS.md`** — the per-screen briefs + the visuals list (the actionable detail).
- **`SCREEN_COVERAGE_AUDIT.md`** — the delivered-vs-needed analysis the asks come from.
- **`DATA_AND_PROCESS_MAP.md`** — the data-relationship ERD + the process/data-flow flowchart
  (decision points, access points, the reconciliation "middle-step" seams) — grounds where each screen sits.
- **`RECONCILIATION_SEAMS.md`** — the standing register of the in-between mapping seams (the source for the §C midpoints).
- **`handoff/`** — the locked v2 baseline (the 6 screens + `Handoff.dc.html` + Kroger assets).
