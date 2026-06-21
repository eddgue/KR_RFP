---
doc: UX/UI Design — handoff package (v2, feedback incorporated)
id: PM-007-DR2
version: 2.0
status: Current source of truth for the frontend rebuild (E-26). Supersedes project/design/first_draft/.
created: 2026-06-21
supersedes: project/design/first_draft/ (draft 1 + the review of record DESIGN_REVIEW.md)
---

# Design handoff (v2) — feedback incorporated

This is the **handoff-ready** design package: six screens + **`Handoff.dc.html`** (the design system
+ developer handoff page). It supersedes `project/design/first_draft/` (kept for history; the full
review of record is `first_draft/DESIGN_REVIEW.md`). The `.dc.html` are the **visual source of truth
to rebuild in Next.js + Tailwind — not merge**; to view locally, serve via a quick local server
(double-clicking `file://` can blank the `support.js` runtime).

**Point the developer at `Handoff.dc.html` first** — it carries: color tokens (named for Tailwind
`theme.extend`), typography (Montserrat display/numerics + Nunito body, `tabular-nums`), spacing /
radius / elevation (4px grid), the **component inventory with states** (buttons, inputs, status
badges, the **AssertModal** governed-action pattern, the **DataTable**), the **non-happy-path** states
(empty / loading / error / read-only), the **real field reference** (names, units, formats — no
placeholders), and responsive / accessibility (WCAG AA) / Lucide-icon notes.

## All prior feedback incorporated (verified against the `.dc.html`)

| Feedback (from `first_draft/DESIGN_FEEDBACK_v1.md`) | v2 status |
|---|---|
| STLY = synthetic/modeled | ✅ "Save vs STLY **MODELED**" badge |
| 7 lenses A–G (not 6) | ✅ all seven |
| Scenario-level capacity feasibility (not icon-only) | ✅ `capStatus` text+detail in the freeze modal + cell drill-down ("Capacity (stated): …") |
| Persistent run-status strip | ✅ Run · Analysis · Award · hash-chain states |
| Intake exception queue | ✅ quarantine / low-confidence / "imported with warnings" surfaced on exception |
| Finalize / "lock & close run" step | ✅ present — writes a **CLOSED · run finalize** event |
| Freeze-modal + adjustment polish | ✅ AssertModal pattern (summary → cautions → rationale → named assertion → audit event); sortable columns added |
| Developer handoff (tokens/components/states/fields) | ✅ `Handoff.dc.html` |
| Email-drafter UI | ⏸ correctly **not** built (parked, as instructed) |

## One fidelity note for implementation (capture, not a blocker)

The finalize/close-run step writes a **`CLOSED`** audit event. Our `EventType` enum
(`backend/app/core/audit/events.py`) has CREATED / SEALED / FROZEN / SUPERSEDED / SIGNED_OFF / SENT /
GATE_APPROVED / IMPORTED — **no `CLOSED`.** When the finalize step is built (the G-D/E-22 sign-off
out-gate → E-37 award/rejection comms → E-24 SENT chain), either add a `CLOSED` event type or map
finalize to `SIGNED_OFF`/`SENT`. Otherwise the design is faithful to the audit model.

## Build classification unchanged (PM-008)

- **B (restyle of existing screens)** → E-26: Login, Dashboard, Run Detail, Bid Intake, Awards, the
  Alignment shell + the new run-status strip + exception-queue + capacity-status surfaces.
- **C (new modules, Phase-4 review)** → **E-41** in-app deep workbench (closes G-I), **E-40**
  decision-rationale capture, and the **finalize/close-run** step (composes E-22/E-37/E-24).
- The `Handoff.dc.html` token sheet feeds the Tailwind config when E-26 starts.
