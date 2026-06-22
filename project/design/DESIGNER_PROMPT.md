---
doc: Designer prompt — round 2 (paste into the Claude Design session)
id: PM-007-DR-PROMPT
status: Send-ready prompt; priority order set by the team
created: 2026-06-22
---

# Designer prompt (paste this; attach KR_RFP_design_package.zip)

**Goal:** extend the locked RFP Console design with the missing screens and the in-between "midpoint"
steps, treating every control as a data operation. Work from the attached package — open
**`DESIGN_PACKAGE.md` first** (the cover); `DESIGN_REQUESTS.md` has the per-item briefs, the
`handoff/` folder is the locked baseline + design system.

## Ground rules
- The v2 baseline (the 6 screens + the **Handoff** design system) is **LOCKED — extend it, don't
  redesign.** Reuse the Handoff tokens / components / states; keep the calm-by-default,
  gravity-at-exceptions tone. Target a **Next.js + Tailwind** rebuild (the `.dc.html` are the visual
  source of truth, not merged; view via a local server).

## Governing principle — treat data like data (read first)
Every control (filter · sort · lens · supplier picker · version picker · freeze · finalize · adjust)
is a **data operation**. For each, make the data treatment explicit and legible to the user:
- **View ops** (filter / sort / drill): reshape the view — **all totals, %, counts, rollups recompute
  against the visible set, never a stale full-table number**; an empty filter shows an empty state.
- **Live-edit ops** (custom build): recompute live (scores, totals, capacity/concentration flags);
  mark **live / unsaved**.
- **Version switch** (the picker): swap **live ↔ a read-only sealed snapshot** — make which one you're
  on unmistakable; label each locked version with its **meeting + date + ROUND/FINAL** marker.
- **Governed ops** (import / freeze / adjust / finalize): an **AssertModal** (summary → cautions →
  rationale → named assertion → the audit event that will be written); gated, irreversible/append-only.
- Invariants: the **DB is the source of truth** (everything derives on request — no cached numbers);
  governed actions are **audit-evented + tamper-sealed**.

## Priority order (do in this sequence)

**Phase 1 — complete a single live cycle on the new design (critical path):**
1. **3 corrections to existing screens** — compact-width status-strip short labels (no clipping);
   make "Hash-chain current" drill through to the latest audit event; refresh the stale Awards screenshot.
2. **Cycle Setup / Scope-review + Strategy (A1)** — review the ingested cycle + set the strategy
   (weights/preset, the 4 safeties, exclusions/preferred, lenses) **+ the pricing basis (E-44/D43): the
   modality picker (FOB / DELIVERED / XDOC, per lot/DC) and the cost-line manager (a buyer-selected,
   toggleable, extensible catalog of cost lines — each with sign · grain · unit $/% · per-line %-base;
   the system never guesses)** + midpoint **M6** (date→timeframe confirm). See A1 + §B6 in `DESIGN_REQUESTS.md`.
3. **Finalize / Close-out (A2)** — the AssertModal + the "Closed" run state, surfacing the award (won)
   + rejection (not-won) notices (backend exists).
4. **Intake midpoints** — **M1** editable column mapper (correct/assign the inferred mapping, not
   confirm-only) and **M5** ingest quarantine resolution (fix-and-retry quarantined rows, setup + bids).

**Phase 2 — data-reconciliation midpoints (design the pattern now; wired when the iTrade feed lands):**
5. **M2** lot/item ↔ SKU sticky map (one lot → many SKUs; propose→confirm→sticky) · **M3** supplier/DC
   identity resolution (match / merge / create — dedup) · **M4** unit/pack-size reconciliation.

**Phase 3 — comms + governance/multi-user:**
6. **Supplier comms (A4)** — the 6 touchpoints' review/edit/send (draft-only).
7. **Sign-off (A5)** · **Settings/Admin/Users/Roles (A6)** · **Supplier management + participant
   selection (A7)**.

## Cross-cutting — grain by surface (§B6 / E-44)
Each cost component carries its own **grain** (per-period / timeframe / yearly). Show **per-period** in
collection + record-creation + the movement/discovery view; in **analysis**, show the **cost-component
breakdown at mixed grain** — each component as-is — in a **horizontal, chronological** layout (period
columns + a per-period **total-landed** column + a **toggleable timeframe-total** column; not stacked).
The **scored price / scenarios / awards stay timeframe-grain.** Apply wherever a price breakdown shows.

## For every screen / midpoint
Include the **non-happy-path states** (empty / loading / error / read-only) and apply the
**interaction rules (§B5)** and the **grain-by-surface rules (§B6)**. If a control's data treatment is
unclear (recompute vs derive vs seal vs audit), **flag it back rather than guess.**

## Deliver
Extend the `.dc.html` screen set + the Handoff design-system page, in the priority order above.
