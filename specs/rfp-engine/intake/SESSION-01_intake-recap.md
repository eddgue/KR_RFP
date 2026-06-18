# Session 01 — Intake

**Date:** 2026-06-17
**Mode:** Customer intake interview, one question at a time.
**Input on hand:** `SYSTEM_SPEC.md` only. No repo (locked / private). iTrade export seen via a prior conversation, not opened live.

---

## Posture set at the top

The studio did not write the spec and does not trust it. Every claim is treated as a claim until the running code proves it. This is not doubt about Ed. It is the only way to avoid scoping against a system that behaves differently from its own document. Confirmed correct within the session: the spec was wrong in both directions (see the Discrepancy Log in `00_INDEX.md`).

A recurring pattern surfaced early: three times the answer to "where is the real thing" was "in the repo," and three times the repo did not reach the studio (private, no access, phone with no file). That is a small version of Ed's own number-one problem. The source of truth exists but sits behind a door, reachable only by the right person doing the right manual step.

---

## The three problems this system exists to kill

1. **Historical data blindness.** Stated by Ed. Two parts: he is new in the role, and "look back" today means hunting a directory of a billion folders with non-standard naming. Reframed by Ed: the fix is not to clean the past. It is to store future cycles in a clean schema so "look back" becomes an "open last cycle" button. The graveyard stays; you stop adding bodies.
2. **Non-standard process.** Everyone runs an RFP their own way. Nothing is recorded. It lives in heads.
3. **Over-dependence on admin and manual flows.**

All three converge on one fix: declare structure once at kickoff, store it, render from it.

---

## What we covered, in order

**Prep before the meeting (Phase -1).** Ed added a phase the spec never had. Before the strategy meeting he logs in, creates the cycle shell (category, start, length as sourcing envisions), and pulls historical so he walks in armed. He wants PO history and scan-out (sell-through). National sourcing means all DCs apply 99.9% of the time, so DCs default to all; local is the exception.

**The kickoff meeting (Phase 0).** The keystone. Ed decides three independent axes here: pricing basis (fixed or index), duration and cadence (full year, two months, period by period, seasonal, or the 13 Kroger periods), and volume split. Plus the objective (savings, continuity, quality, diversification, strategic), which is the target the cycle aims at. Today none of it is recorded.

**The safeties.** The real product, and the spec stores them inert. Five structures named:
- Disaster trigger (fixed deal, supplier reprices up when the market spikes).
- Inverse disaster trigger (fixed deal, Kroger forces price down, inside a collar with cap and floor).
- Rolling midpoint (index deal, pay the midpoint of the last X weeks, reevaluate every Y weeks).
- Tolerance band (index deal, price shifts only when it moves past a set percent and holds for a set number of weeks; a shorter re-review once it trips).
- Period-by-period for weakly-correlated commodities (colored potatoes): suppliers price all 13 periods and name the sourcing region per period, so risk premium is read per supplier per period, not category-wide.

The spec has the parameter columns (`reset_cadence`, `trigger_band_pct`, collar floor/cap, `derived_trailing_mid`, a market-proxy model) but explicitly does not fire them. Parameters stored, engine inert. Not built where it matters most.

**The grain.** Resolved to period grain. Fixed = one price repeated across periods. Index = store the components, the price resolves. Same table. Ed's line: you don't register the FOB on an index deal, you register the market reference minus discount or QDP plus the other costs, and FOB falls out.

**Freeze and layer.** Awarded terms freeze. Live and changed prices layer on top, date-stamped. Raw never overwritten. The system is the long memory, so any RFP opens with its full story.

**The setup file as keystone.** Ed: price and components are preset; the system knows from the setup file how to display them when calling an RFP, live or historic. This closed the loop. The unrecorded kickoff meeting becomes the setup file. The setup file cures all three problems at once.

**Architecture correction.** Not one big table. Separated reference data (clients, RFP setups, suppliers/CRM) plus a unified transactional core: one bid line store for every RFP regardless of structure, then one award table. Pull an award, read the table, find the lines, render.

**Live negotiation.** Ed negotiates live on calls, inputs the agreed price, saves it, and a confirmation goes to supplier and team. This breaks the spec's proud "never sends" rule. Resolved: draft to sent is a governance gate, not a channel. Email, telegraph, snail mail, all the same. Sent means official and recorded.

**Process shape is variable.** Rounds are 3 by default, more if there is juice. RFI is optional, but the contact / sourcing-location / storage refresh runs every time so the reference data stays current. So the rail cannot be hardcoded. The setup file defines it.

**Mid-round work.** Alignment calls, scenario reviews, custom scenario builds. This is the part the spec actually built well (Scenario A benchmark, custom grid, side-by-side). Confirms the shape: operational middle built, governance ends thin.

**Why the middle is strong.** Not because it was on fire. Because Ed landed in the role on the analysis and built what he was learning. He is now expanding to both ends, and the setup layer is the first piece.

**Contracting (Phase 8).** After award, assemble the contract, attach specs and legal, send. Generated from the award and kickoff terms, not retyped.

---

## Normalization (Ed already started this)

The same product shows up many times with different names, SKUs, UPCs. Suppliers bid the **parent product**, not the UPC. So a normalization table is foundational, and parent product is the bid and award grain.

The anchor: SAP assigns a **Sub Commodity code** to every product, which leads to the grouped specs and holds the packing variants. That is a hard key, not a fuzzy match. Load it as truth. Confirmed against the real iTrade export, where **Sub Commodity** and **Case Size** are present fields.

The mess: buyers enter pack sizes inconsistently (a 50lb bin as "1 bin," "each," or "1lb"). Two problems in one: unit of measure (convert everything to one basis) and free-text pollution (size jammed into the name field). The pre-upload clean needs human reasoning to pick the right path, so it stays manual, but the system does everything around the judgment: catches dirty rows, surfaces conversion options anchored to the code, stores the decision, remembers it next cycle.

What Ed has: the lot list is ready. What is needed: a mapping screen. Pull the unique SKU list with basic data, show a category-filtered lot dropdown, click to assign, make it stick. Only new SKUs surface next time.

---

## The iTrade export (seen via prior conversation)

- Comes **by commodity** with a **calendar**, stamped to both the regular and the **Kroger fiscal** calendar.
- Carries **Sub Commodity**, **Case Size**, **FOB price**, and a **ship-from state**.
- Critical caveat Ed raised before: **ship-from is not growing origin.** iTrade carries a vendor / ship-from state, directional only. So the per-period sourcing region (colored potatoes) must stay a supplier-stated field captured at bid, never auto-filled from the pull. Two origin fields, kept separate.

---

## Hard findings

- The spec is strongest exactly where Ed started (the analysis middle) and weakest exactly where he had not reached (the governance ends). Coherent, not random.
- The single biggest risk: nothing has touched real data. Every "BUILT" means "passes tests its own author designed."
- The fiscal calendar discrepancy (parked in the doc, loaded through 2037 in the build) is the first hard proof that verifying against code beats trusting the doc. If it is wrong in Ed's favor here, it is wrong the other way somewhere else.

---

## Where we stopped

Process mapped end to end. Data foundation mapped and partly sourced against the real export. Next session needs a real screen: the kickoff file, one iTrade pull with real headers, one finished cycle, and repo access by zip or proper handoff.
