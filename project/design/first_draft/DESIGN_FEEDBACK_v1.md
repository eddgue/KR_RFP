---
doc: Design feedback to the design team — after first draft
id: PM-007-DR1-FB
version: 1.0
status: To send — feedback on project/design/first_draft/, reconciled to the As-Built (PM-007 v1.22)
created: 2026-06-21
---

# Design feedback — first draft (what to adjust, and how to hand off)

**Verdict first: this is a great first draft.** You found the right product shape — a governed
decision console, not a spreadsheet in a browser — and the calm, card-based, easy-to-navigate feel
is exactly right. **Keep that.** The notes below are accuracy fixes + a few additions, plus a short
list of things that make the engineering rebuild clean. The guiding principle stays yours and the
auditor's: **calm by default, escalating gravity only at exceptions and governed decisions.**

## A. Corrections — match the real system

1. **"vs STLY" must be labelled synthetic / modeled.** There is no same-time-last-year data feed
   yet; the system *fabricates* STLY as a ~4% uplift over the incumbent baseline. Show it, but mark
   it clearly (e.g. a "modeled" tag/tooltip) and give it **less visual weight** than the real
   "Save vs incumbent." Don't present it as a hard, sourced number.
2. **There are SEVEN scenario lenses, A–G — not six.** The set is: A Lowest-cost reference ·
   B Risk-adjusted (recommended) · C Incumbent defense · D Max-N per DC · E Exclusion applied ·
   F Custom build (live) · **G Preferred supplier.** Make sure all seven appear everywhere lenses
   are shown (the current Alignment screen already has all seven — just keep them consistent).

## B. Additions — small, additive, "gravity at exceptions" (data already exists)

3. **Scenario-level capacity feasibility.** Today capacity is an icon. Make it a plain status on
   each scenario: **"Feasible against stated capacity"** or **"Exceeds stated capacity in X cells"**,
   with a click-through to the affected cells, and echo that status in the freeze modal. (Please do
   **not** design a full capacity dashboard — just the status line + the path to the cells.)
4. **One persistent run-status strip** across the run workspace: **Run state · Analysis state
   (sealed vN) · Award state (frozen?) · Audit state (hash-chain current).** Quiet/neutral when
   normal; stronger only when something is blocked or at risk. The system already knows all four.
5. **Intake — an exception queue that appears only when a file needs attention.** Surface the messy
   cases explicitly: old/wrong template, missing Capacity tab, duplicate supplier/file, rejected
   bid line, low-confidence column mapping, partial import, "imported with warnings." Keep the happy
   path as clean as it is now; show the queue only on exception.
6. **Add the finalize / "lock & close run" step** (currently missing — the flow stops at Freeze).
   This is the governed **close-out**: after the award is frozen, a deliberate "finalize & close the
   run" action that **generates the award notices (won) and rejection notices (not-won)** and marks
   the run complete. Treat it with the same gravity as Freeze.
7. **Minor polish on the two governed modals** (they're already strong — just round them out):
   - *Freeze modal:* add the **version being frozen** and a one-line **"a FROZEN audit event will be
     written"** preview, plus the capacity status from #3.
   - *Post-award adjustment:* show an explicit **before → after** value delta for each repriced cell.

## C. Keep doing (don't undo these)

- The **left-nav lifecycle** (Runs → Overview → Intake → Alignment → Awards). It's correct.
- The **Engine recommendation** card framed as decision-support ("a human asserts every governed
  action"). That framing is core to the product — keep it prominent.
- The **per-cell decision note + the freeze note** (decision rationale). Excellent — keep them; we'll
  wire them into the audit trail on our side.
- **Awards governance language**: Frozen / effective / append-only / version history / immutable
  baseline. Exactly right.
- The **calm, soft, card-based default**. Add density only at exceptions — never to the routine
  screens.

## D. Handoff — what makes the engineering rebuild clean

We rebuild this in **Next.js + Tailwind** (it won't be merged as-is — the `.dc.html` are the visual
source of truth). To make that fast and low-error, the most helpful things you can provide:

1. **A design-token sheet** (the single biggest win). Pull the inline colors/spacing/radius/shadows
   into **named, semantic tokens** — e.g. `brand/primary`, `text/strong`, `text/muted`, `border`,
   `surface`, `success` (savings), `warning` (caution/capacity), `danger` (over-capacity/blocked) —
   ideally as a small Tailwind-style config or a flat token list. Right now the values live inline
   per element; a token sheet lets us match it exactly, once.
2. **A component inventory with states.** Name the reusable pieces (Button primary/secondary, Card,
   StatChip, LensCard, ScenarioBadge, CautionFlag, StatusPill, Tab, DataTable, Modal, NavItem) and
   show each in its states: **hover / focus / disabled / loading (skeleton) / empty / error /
   read-only.** You already do read-only for sealed analyses — extend that discipline to the rest.
3. **The non-happy-path screens**, not just the populated ones: **empty** ("no runs yet", "no bids
   loaded"), **loading**, **error**, and **read-only/historic** (sealed prior version). These are
   where most build time goes if they're left to us to invent.
4. **Keep real field names, units, and formats** (DC, lot, timeframe, RecScore, $/case, cases, %,
   dates) — no lorem/placeholder. It keeps the data contract unambiguous.
5. **Responsive intent:** confirm desktop-first min width (we briefed ~1440px) and how the dense
   surfaces behave below it — the **Alignment award matrix** and the **diligence tables** especially
   (horizontal scroll vs. stack), and the **nav-collapse** breakpoint you already designed.
6. **Accessibility:** where color carries meaning (concentration / capacity flags, green savings),
   pair it with **text or an icon** so it doesn't rely on color alone, and keep text contrast at
   **WCAG AA** (watch the soft greys on white).
7. **Name the icon set** you used, so we pull from the same library (consistent stroke weight).

## Not this round

- **Email-drafter UI** — parked deliberately. Don't design it yet; we'll bring it back when the
  comms layer is scheduled.
