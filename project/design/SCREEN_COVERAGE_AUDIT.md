---
doc: Design screen-coverage audit — what's designed vs. what we'll need
id: PM-007-DR-AUDIT
version: 1.0
status: Audit of record — `project/design/handoff/` (v2) vs. the full lifecycle (As-Built PM-007 v1.24)
created: 2026-06-22
---

# Design screen-coverage audit

Stacks the delivered design (`project/design/handoff/` — 6 screens + the Handoff design-system page)
against every surface the product actually needs across the RFP lifecycle + governance, and marks the
gaps so we can request the rest from the design team. Coverage verified against the `.dc.html` and the
As-Built lifecycle (§2/§3/§13). Legend: ✅ designed · ◐ partial / referenced-not-built-out · ⬜ missing.

## Delivered (strong — the core happy path)

| Surface | Screen | Notes |
|---|---|---|
| Auth (login + 2FA) | ✅ Login | username → TOTP → httpOnly session |
| Runs portfolio | ✅ Dashboard | list + "New run" |
| Run overview | ✅ Run Detail (= "Overview" nav) | lifecycle stepper · activity board (kanban) · audit trail · run facts |
| Bid intake | ✅ Bid Intake | setup-file upload → template → load bids · strict/flexible · exception queue |
| Alignment (the centerpiece) | ✅ Alignment Workspace | 7 lenses A–G · engine rec · capacity feasibility · freeze modal · decision notes · version picker · diligence tabs |
| Award + post-award | ✅ Awards | frozen v0 · append-only layers · version history · adjustment form |
| Finalize / close-out | ◐ Awards/Alignment (added v2) | "finalize / close run" + award/rejection notices are *referenced*; built as an action, not a full close-out surface |
| Downloads | ◐ Run Detail | "run folder (.zip)" + file list; no dedicated outputs/downloads view |
| Design system / handoff | ✅ Handoff | tokens · component states · non-happy-path · field reference · a11y/Lucide |

## Gaps — what we'll need (to request), tiered

### Tier 1 — needed to run a complete real cycle end-to-end
| Surface | Coverage | What to request |
|---|:--:|---|
| **Cycle setup / scope-review + strategy config** | ⬜ | Today setup is a blind file upload (Bid Intake step 1); the cycle scope (DCs/lots/suppliers/volumes/timeframes) is only shown read-only as chips on Alignment. We need a screen to **review the ingested cycle** and **set/confirm the strategy** — weight preset, the four safeties (premium ceiling, coverage floor, concentration threshold, max suppliers/DC), preferences/exclusions (ADR-0016 strategy-agnostic). This is the front of the funnel and is missing. |
| **Supplier comms (E-37, the 6 touchpoints)** | ◐ | Award/rejection notices are referenced at finalize, but the supplier-facing comms surface is otherwise absent: **invite · template-send · incomplete-bid notice · round feedback · award/rejection · PBA transmittal**, each with the review/edit/send (draft-only) pattern. Deliberately **parked** for now, but it's the single biggest functional gap for actually running an RFP with suppliers — request it as the next major surface. |

### Tier 2 — governance / multi-user (before production or a second operator)
| Surface | Coverage | What to request |
|---|:--:|---|
| **Sign-off / approver gate** (G-D) | ⬜ | A formal author≠approver sign-off step before an award becomes "official / SENT" — distinct from the freeze assertion. |
| **Settings / Admin / Users / Roles** (G-C, G-J) | ⬜ | User management + RBAC roles (the "Sr. Sourcing Mgr" label is cosmetic today; no enforcement, no admin surface) + the eventual tenant boundary. |
| **Supplier management / participant selection** (E-34) | ⬜ | A supplier master (import/upsert) + per-RFP selection of participating suppliers by category. |

### Tier 3 — analytics & contract (backlog; request when scheduled)
| Surface | Coverage | Epic |
|---|:--:|---|
| Multi-round navigation / round-over-round evolution | ◐ | E-36 (only "Round 1" is shown; R2…Rn flow + round-evolution view) |
| Version savepoints + compare-versions + ROUND/FINAL marker | ◐ | **E-43** (version picker partly designed; the savepoint/compare/marker/meeting-label is new) |
| PBA / contract builder (post-award final step) | ⬜ | E-33 |
| Price-movement / timeframe-discovery view | ⬜ | E-35 |
| In-app capacity dashboard | ⬜ | E-38c (feasibility now lives on Alignment; standalone deferred) |
| Portfolio kanban (RFP portfolio + RFP-by-supplier) | ◐ | E-30 (the per-run activity board exists; the portfolio boards don't) |
| Supplier-behavior (contracted-vs-effective) analytics | ⬜ | E-28 |

## Already-flagged on the EXISTING screens (auditor round 2 — `handoff/DESIGN_FEEDBACK_v2.md`)
Not new screens — three tweaks to send with the next request: (1) compact-width status-strip short
labels (no clipping), (2) refresh the stale Awards error screenshot (verified not a live defect),
(3) make "Hash-chain current" drill through to the latest audit event.

## Recommended ask to the design team (in order)
1. **Cycle setup / scope-review + strategy config** screen (Tier 1 — front of the funnel).
2. The **3 tweaks** on the existing screens (cheap, finishes the locked baseline).
3. **Supplier comms surface (E-37)** — the next major workstream when we un-park it.
4. Then Tier 2 (sign-off, admin/users, supplier mgmt) ahead of multi-user/production.

The six delivered screens are enough to drive a **single-operator live cycle end-to-end** (intake →
align → freeze → adjust → download); the Tier-1 setup/strategy screen is the one real hole in that
path, and comms is the first thing you'll feel the absence of once suppliers are in the loop.
