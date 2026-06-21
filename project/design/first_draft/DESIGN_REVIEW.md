---
doc: UX/UI Design Review — First Draft (Claude Design)
id: PM-007-DR1
version: 1.0
status: Review of record — the first-draft UX/UI package, reviewed against the As-Built (PM-007 v1.21)
created: 2026-06-21
depends_on: PM-007 (As-Built Spec), PM-004 (Program Backlog), DESIGN_BRIEF.md
source_package: project/design/first_draft/ (six .dc.html screens + assets + support.js, from Claude Design)
---

# UX/UI Design Review — First Draft

A fidelity review of the first-draft design package against the system as it actually is (PM-007
v1.21). The design team consumed the full review bundle (the audit docs, the current screens, the
output workbooks) plus the Kroger brand guidelines and logos. Method = the program's "stack and
compare where it breaks": every screen and every metric the design shows is checked against the
as-built, and the divergences are called out as decisions, not bugs.

> **Artifact note.** The package is six interactive HTML prototypes (`*.dc.html` + `support.js`
> runtime + Kroger SVGs). These are **design targets to rebuild** in our Next.js + Tailwind
> frontend — **not** drop-in production code. The `.dc.html` are the source of truth; the rendered
> `screenshots/` in the original export were stale (export lag) and were not used for this review.

## Verdict

Strong, coherent, **ship-worthy direction** and unusually faithful to what the system is — the
language, the governance framing, and the data model are right, not decorative. It is a
reskin-and-extend target. Three things genuinely extend or diverge from the as-built and need a
decision (below); everything else is a B-class restyle of capabilities we already serve.

## Screens reviewed (6)

| Screen | Maps to as-built? | Notes |
|---|---|---|
| **Login** | ✅ Exact | Username → 6-digit TOTP → "Sessions secured with httpOnly cookies." Mirrors our auth + 2FA. Tagline: "compare seven scenario lenses, freeze governed awards — recommended by the engine, asserted by a human · Decision-support, not auto-decided · Audit-evented, hash-chained." |
| **Dashboard** | ✅ Exact | Runs table (Commodity / Cycle / Owner / Stage / Updated) + "New run" = our runs list. |
| **Run Detail** | ✅ Exact | "Sourcing lifecycle" stepper; "Activity board — what's done, in progress, and waiting on you" = our kanban columns verbatim; "Run facts"; "Audit trail · Hash-chained" (type / text / who / when); run folder .zip. |
| **Bid Intake** | ✅ Exact | 3 gated steps (Setup → Template → Load bids); Strict vs Flexible; "keys validated, unrecognized rows quarantined — never guessed"; the bid template's three sheets incl. **Capacity (E-38)**; mapping-confidence review; "Round 1 bids imported · audit event recorded (IMPORTED)". |
| **Awards** | ✅ Exact | Frozen v0 immutable baseline + append-only post-award layers; "the award record in Postgres is authoritative — generated guides are renders of it"; version history; the record-adjustment form with "I, Dana Ellison, assert this adjustment … (CREATED event)". Already reflects #4 (actor = the authenticated user). |
| **Alignment Workspace** | ✅ mostly | 7 lenses A–G (B = REC); versioned sealed analyses (prior versions open read-only, "View live version"); scope chips (2 DCs · 2 lots · 4 award cells · 13-week horizon · Balanced preset · Round 1); engine-recommendation panel; the editable per-cell award matrix + cell drill-down (5-factor scoring + diligence tabs); decision notes (below); "Engine output — decision support only. A human asserts every governed action; each assertion is audit-evented." Divergences ↓ |

## Decision-rationale capture (sponsor-flagged — the WHY layer)

The design adds a **decision-rationale layer** that the as-built does not yet have. It pairs exactly
with the #4 actor-fidelity work just shipped: #4 captured **WHO** asserted a governed decision; this
captures **WHY**.

1. **Per-cell decision note** — a popover on every award cell in the Alignment matrix:
   *"Note your reasoning for this cell's supplier choice…"*, saved per cell; the cell's note icon
   fills blue once a note exists. (`Alignment Workspace.dc.html` — "DECISION NOTE POPOVER",
   `notes{}` / `openNote` / `setNote`.)
2. **Freeze note** — in the freeze-confirm modal, captured at the moment of assertion:
   *"Why this scenario over the alternatives? Any conditions, exceptions, or context for the audit
   trail…"*, alongside the *"I, Dana Ellison, assert this award decision … recorded against my name"*
   checkbox. (`freezeNote` / `setFreezeNote`.)

**As-built gap:** we persist no per-cell or per-freeze rationale today — only run-level `NOTES.md`
(`PilotService.remember` / `add_memory`). The decision events (`FROZEN`, `CREATED`, …) record
who/what/when but no free-text rationale. **Open governance question:** where the rationale lives —
a dedicated `decision_note` store keyed to the award line / freeze, vs. the `FROZEN`-event
`metadata`, and whether it is inside the hash-chain. (The audit envelope rule today is "no
commercial values in metadata"; a free-text rationale is not a commercial value but the placement
is a real call.) → captured as **backlog E-40**.

## Where it breaks (decisions, not bugs)

1. **"Save vs STLY" is shown as a hard metric — but in the as-built it is a *synthetic proxy.*** The
   engine has no same-time-last-year feed (deferred E-08/E-09). The workbook fabricates STLY as a
   clearly-labelled ~4% uplift over the incumbent baseline (`_STLY_UPLIFT = 1.04`,
   `scenario_workbook.py`). The design shows "$73,632 · 25.2% vs STLY" with the same visual weight as
   the real "vs incumbent" savings. **The UI must carry the same "synthetic / modeled" label the
   workbook does**, or it overstates savings against a number we cannot yet source. (Backlog note in
   PM-004 already anticipates swapping the proxy for the real iTrade baseline once E-08 lands.) Easy
   fix; flagged to the design team.
2. **The in-app deep alignment workbench is new capability, not a reskin (closes G-I).** The design
   proposes per-cell supplier override ("Editable — change supplier per cell"), live "Custom build
   (live)" Scenario-F building, the cell drill-down with 5-factor scoring + "Why this pick", and the
   eight diligence tabs (Suppliers / Lowest-cost / Coverage / Scoring / Landed / Share / Incumbent /
   Negotiation) — i.e. the in-app equivalent of the Excel alignment workbook. Today the web screen
   runs / compares / freezes; the deep per-cell workbench is Excel-only (gap **G-I**). Per the
   Decision Doctrine this is **Category-C (new module)**, not B. → captured as **backlog E-41**.
3. **Missing the finalize / "lock & close run" step (sponsor-flagged).** The design ends at **Freeze
   award** (FROZEN baseline). It has **no terminal "lock & close the run" action** — the governed
   close-out that finalizes the run and **generates the award notices (won) + rejection notices
   (not-won)** from the frozen result. This is a real lifecycle step missing from the design, not
   just a button: it maps to the **sign-off out-gate** (G-D / E-22), **draft→SENT** governance
   (E-24), and the **award/rejection comms** (E-37 touchpoint 5 = won / not-won per supplier). The
   next design pass should add this finalize step after Freeze. → captured as a PM-004 note against
   E-22 / E-24 / E-37.
4. **Role label is cosmetic.** "Sr. Sourcing Mgr" is shown but we do not enforce RBAC (gap G-C).
   Fine as long as no action is drawn as role-gated — and none is. Good restraint elsewhere too: the
   design did **not** draw a sign-off screen or a "Send to supplier" button (our unwired / draft-only
   features), so it is not promising vaporware.

## Parking lot (future design asks — do NOT spec yet)

- **Email-drafter UI (E-37 comms).** A later design ask: the screen where the buyer reviews / edits
  / sends the template-merged email drafts across the lifecycle. **Parked deliberately — not to be
  spec'd now.** Recorded here so it is not lost; raise with the design team when E-37's comms review
  UI is scheduled.

## Build classification (Decision Doctrine, PM-008)

- **B — restyle of existing screens** (within current architecture): Login, Dashboard, Run Detail,
  Bid Intake, Awards, and the Alignment *shell* (lens compare + freeze) reskinned to the
  Kroger-branded design. Eligible for Live-Run cycles. → folds into **E-26** (web console).
- **C — new modules** (Phase-4 review before build): the in-app deep alignment workbench (**E-41**,
  closes G-I) and the decision-rationale capture (**E-40**), which has a governance sub-decision.
- **Fix (now-ish):** STLY "synthetic" labelling wherever the UI shows vs-STLY.

## Next steps

1. Tell the design team the one real correction — **label "vs STLY" as synthetic / modeled** (and
   optionally soften its visual weight vs the real vs-incumbent savings).
2. Adopt this package as the frontend implementation target (E-26) and groom **E-40** + **E-41** at
   phase entry.
3. Resolve the E-40 governance sub-decision (where decision-rationale lives; whether it is
   hash-chained) before building it — it touches the audit envelope.
