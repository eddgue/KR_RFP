# ADR-0014 — Pricing safeties are contractual execution-layer terms, not engine inputs

- **Status:** Accepted (sponsor-specified 2026-06-18); mechanics pending sponsor confirmation of this write-up
- **Deciders:** Sponsor (Ed), PM, Solution Architect, Engine lead, Product
- **Relates:** gap G4, D3 (pricing at kickoff), D12/ADR-0013 (storage vs display), E-28 (contracted-vs-effective), the award freeze-and-layer (G3)
- **Supersedes the framing of:** "make the safeties executable in the engine" — corrected below

## Context

The intake called the five pricing safeties "the real product," and the original specs stored them as inert parameters. The PM's prior framing assumed the *engine* would fire them. **The sponsor corrected this:** the safeties are **contractual terms, not bid terms.** They exist to **incentivize suppliers to participate** (shared risk), and **they do not affect the scoring/allocation math.** They govern how the awarded price **moves over the life of the contract** (execution), and price changes are recorded against the frozen award (freeze-and-layer).

## Decision

1. **Safeties are declared at kickoff** (the setup file) as **contract terms** on the cycle/award, with configurable parameters.
2. **The engine (scoring + allocation) does NOT consume them.** They are out of the solver entirely. (Keeps the engine clean; removes the old "fire the safeties in the engine" scope.)
3. **A contract/execution module** applies or records reprices when a safety triggers, post-award. Formulaic safeties can be computed/visualized; discretionary ones record a human reprice decision. Every move lands in `award_layer` (date-stamped, who/why), raw award never overwritten.
4. They feed **contracted-vs-effective** (E-28) and the savings baseline (D11): the contract terms say what *should* happen; iTrade actuals say what *did*.

## The five safeties (mechanics as specified — CONFIRM)

> Default windows/cadences below are the stated defaults; all are per-cycle configurable contract parameters.

### 1. Collar (cap / floor) — applies to BOTH fixed and market/index
- A tolerance band on price movement. **Cap** = how far **up** Kroger will let the price go in a market hike (Kroger's upside protection). **Floor** = the **supplier's** downside protection (Kroger is willing to go to 0; the floor exists for the supplier, not Kroger).
- Same dynamic regardless of pricing basis.
- Parameters: `cap`, `floor` (per cell/lot/cycle as declared).

### 2. Rolling midpoint — market/index deals
- Every **8 weeks**, take the **midpoint of the market price over the trailing 4 weeks**; that midpoint becomes the price for the **next 8 weeks**.
- Parameters: `lookback_weeks` (default 4), `reset_cadence_weeks` (default 8).

### 3. Tolerance band — anomaly reprice (works with the collar)
- Separate from the collar. Monitors market price for an **anomaly**: price moves **outside the band** and the move **persists ≥ 2 weeks** (sustained, not a blip).
- On trigger: **temporary reprice to the market midpoint, bounded below the collar cap, for 2 weeks**, then **review at 2 weeks**.
- Parameters: `band` (threshold), `min_duration_weeks` (default 2), `reprice_window_weeks` (default 2).

### 4. Disaster trigger (escalator) — discretionary
- A **generalized market disaster** causes a price spike → Kroger **evaluates and reprices up accordingly** (human judgment, not a pure formula).
- **Temporary:** price **reverts to the contracted price after the disaster period** ends.

### 5. Inverse disaster trigger (de-escalator) — discretionary
- The mirror: a **generalized market drop** → Kroger **reprices down accordingly**.
- Same invariant: **reverts to contract after the disaster period.**

**Formulaic vs discretionary:** #2 and #3 are computable/auto-visualizable; #1 is a bound applied to any move; #4 and #5 are **human-evaluated** events with a hard "revert to contract" rule. The system computes/proposes and records; a human approves discretionary moves (author≠approver, draft→sent gate).

## Consequences

- **Engine unaffected** — no safety logic in scoring/allocation; the pilot (engine reproduction) is independent of safeties.
- Safeties are a **Phase-E+ contract-execution feature** (post-award monitoring + reprice-and-layer), not a Phase-D engine feature. Re-sequenced accordingly.
- Data model: `cyc.cycle_safety` stores the declared terms + parameters; `awd.award_layer` records actual reprices; a future `execution`/monitoring surface computes formulaic moves and flags disaster events for human action.
- Strengthens E-28: "was this deal honored?" = compare contract terms (+ legitimate safety moves) vs iTrade effective.

## Open / to confirm
- The exact mechanics above (this ADR is the sponsor's words, structured — confirm before build).
- Where the market reference comes from (USDA market data is referenced in the kickoff docs; the rolling-midpoint/tolerance-band need a market price series feed). **Likely a new feed (market index), TBD.**
