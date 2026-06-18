# RFP Engine — Build Control Index

Living state for the session-by-session rebuild. This file is the canonical "where are we." Each session adds a dated record file. Open this first.

- **Owner:** Ed (Eduardo Guevara), Sourcing.
- **Studio role:** external intake / build partner.
- **Governing rule of this rebuild:** the old `SYSTEM_SPEC.md` is a claim, not truth. Every claim gets verified against the running code before it counts. The spec was already wrong in both directions (see Discrepancy Log).
- **Status as of Session 06 (corrected):** intake complete on the as-built artifacts, but the engine-only verdict was **revised** — the engine is one of ten scripts in `RFP_Workflow_Package_v1.4` (cycle init, bid templates, intake, reconcile, distance, scoring, feedback letters, award letters, booking-sheet generation, event log). Front, back, supplier comms, generated booking guide, and an event log **exist as code**, contrary to the earlier engine-only read. The narrowed open question: is there a durable governed **store** under the workflow (does the live Streamlit app persist state / solve "open last cycle"), or is it still file-in/file-out per run? Need the package source (esp. `_event_log.py`, `init_cycle.py`) and the app's persistence layer to resolve. The fork ("v3 brain on a new spine") is paused pending that. See SESSION-06 Addendum 3.

---

## Session log

| # | Date | Focus | Output |
|---|------|-------|--------|
| 01 | 2026-06-17 | Intake. Process end to end. Data foundation. First doc-vs-build gaps. | `SESSION-01_intake-recap.md` |
| 02 | 2026-06-17 | Real kickoff docs reviewed. Kickoff-file schema extracted. Spine validated against real artifacts. | `SESSION-02_kickoff-schema.md` |
| 03 | 2026-06-17 | iTrade feed, normalization engine, bid intake, analysis engine, booking guide, 3 allocation models. Full data+engine layer mapped. Solver correction confirmed. | `SESSION-03_data-and-engine-layer.md` |
| 04 | 2026-06-17 | Leadership sign-off deck. Split awards confirmed — the locked one-supplier-per-cell grain is wrong. Sign-off gate output specified. | `SESSION-04_signoff-gate-and-split-awards.md` |
| 05 | 2026-06-17 | v3 Python engine notebook. Ed is already building the parameterized consolidation (config-driven, weighted scoring, TFs as config). Two-codebases fork surfaced. | `SESSION-05_v3-engine-and-codebase-fork.md` |
| 06 | 2026-06-17 | Full v3 engine code read. Verdict: v3 is the brain, not the spine. 5-factor weighted scoring, eligibility gates, split-award allocation all verified. Fork resolved. A later iteration (md5 c73ffc5, 4,244 ln) was also reviewed — output-layer only (Custom Scenario refactor + Glossary); verdict unchanged. | `SESSION-06_engine-verdict-and-fork-resolution.md` |

---

## The frame

Two governance gates with an operational middle between them.

- **Kickoff gate** — business inputs enter. Buyers, merch, category, sourcing set the target and the structure before any supplier sees anything.
- **Operational middle** — rounds, bids, scenarios, negotiation. Mostly built. Strongest part of the existing code.
- **Sign-off gate** — the business decision exits. Leadership approves. Award and contract leave the building.

The middle is built. The two gates are thin. The gates are where the value and the complexity sit. That shape exists because Ed built outward from the analysis (the middle), which is where he landed in the role. He is now extending to both ends.

---

## Locked truths (the spine)

Corrected by Ed at every point where the old spec drifted.

1. **Period grain.** Every line = supplier × parent product × DC × period × price. Fixed repeats the price across periods. Index stores the components and the price resolves. Same table, different columns carry the weight.
2. **Parent product is the bid and award grain, not UPC.** Suppliers bid the parent. UPC is a child identity underneath. Anchor = SAP **Sub Commodity** code, which carries grouped specs and packing variants.
2a. **Awards are split, not single-winner.** The award grain is a **cell** (DC × lot × timeframe), but a cell is awarded as a **set of supplier shares**, each with its own volume and price, capacity-constrained, human-decided. This is why they are "Allocation" models. The old spec's locked "one supplier per cell" rule is **wrong** (confirmed by the sign-off deck, Session 4).
3. **Freeze and layer.** Awarded terms freeze. Live, changed, or repriced values layer on top, date-stamped with who, when, why. Raw is never overwritten.
4. **Nothing deleted.** Any RFP, live or historic, opens with its full story and the proof attached.
5. **Setup file drives the read.** The system renders each RFP from stored structure, not from a person's memory. Same render live or historic.
6. **Draft to sent is a governance gate, not a channel.** The old "never sends" rule was wrong. Sent means official, it left the building, recorded with approver and timestamp.
7. **Two origin concepts, kept separate.** Ship-from (SAP, loose) is not grow-origin (supplier-stated, per period). Never auto-derive one from the other.
8. **Process shape is per-cycle, not hardcoded.** Rounds vary (3 default, more if there is juice). RFI is optional. The setup file defines the rail; the app builds the rail from the file. The old spec hardcoded 10 stages; a second doc hardcoded 13. Both wrong.

---

## Process, end to end (Ed's corrected version)

| Phase | Name | Type | What happens |
|-------|------|------|--------------|
| -1 | Pre-setup / Prep | prep | Log in, create cycle shell (category; start and length as sourcing envisions; DCs default to all, national). Pull SAP/iTrade historical (PO + scan-out), upload. Walk into the meeting armed with last cycle and sell-through since. |
| 0 | Strategy Kickoff | **GATE (in)** | Set objective (savings / continuity / quality / diversification / strategic). Set structure: pricing basis, duration and cadence, volume split, safeties. Confirm products, volumes, DCs, timing, supplier situation, eval criteria, negotiation objectives. **Recorded nowhere today. Lives in heads. KEYSTONE.** |
| 1 | Supplier Refresh + Qualification | op | Refresh every cycle (contacts, sourcing locations, storage; date-stamped, history kept). Qualification (RFI) optional. |
| 2 | Build + Release | op | Create the event from the kickoff structure. Suppliers quote on the defined shape. |
| 3 | Round Loop | op | 3 rounds default, more if juice. Per round: bids in → scenario review vs benchmark → custom scenario build → team alignment call → back to suppliers. Later rounds: live negotiation, price input and saved, confirmation sent to supplier and team, original bid frozen, agreed price layered. **Strongest built part.** |
| 4 | Final Scenario Build | op | Last custom scenarios. The intended recommendation. |
| 5 | Internal Alignment | op | Category, buyers, sourcing, analysts converge. "What should we do." Recommendation forms. |
| 6 | Sign-Off | **GATE (out)** | Leadership enters. "Are we officially approving this." Outputs: final allocation, final rationale, final approvals. |
| 7 | Awards | op | Supplier communication. Draft to sent. |
| 8 | Contracting + Execution | op | Assemble contract, attach specs and legal, send. Generated from award and kickoff terms, not retyped. Draft to sent gate. |

---

## Data foundation (sourced against the real iTrade export)

**The pull (sources, now confirmed against real exports):**
- **iTrade / SAP** — by commodity, period-stamped to both the regular and Kroger fiscal calendar. Carries Sub Commodity (parent anchor), Case Size (pack variant), FOB price, ship-from state. Source for historical awarded cost (FOB).
- **KCMS** (Kroger Category Management System) — the scan-out / movement feed, distinct from iTrade. Provides Scanned Cost, Scanned Retail, Scanned Movement, Gross Margin $, GM%, FCB Unit Cost, current vs previous period, at SubCommodity and GTIN grain. This is the "scan-out historical" source.
- **Supplier scorecard** (PO / receiving) — Volume Cases, % volume, % cost, Fill Rate, Adjusted Fill Rate, On-Time (DLVD only), DC Rejection, Rejected Case Qty, Rejection Count, Cost/Case, Age at Receipt. Captured twice per cycle: kickoff snapshot and sign-off snapshot, both frozen.

**Upload model:** Ed pulls the latest from SAP each new cycle and uploads. Full through today, reaching back to last cycle (not all-time). The system is the long memory. Overlap between uploads is small, so dedupe risk is low. Conflict rule: keep both, date-stamp, newest pull wins the live view, old version stays underneath.

**Two data sets:**
- **PO historical** — awarded and purchased. Our side. Central to the existing design.
- **Scan-out historical** — sell-through. Demand reality. **New vs the spec.** Tells you whether last cycle's volumes matched the shelf.

**Fiscal calendar:** loaded through **2037** in the current build. (Spec claimed parked and not loaded. Wrong, undersold.)

**Normalization table (in progress):** Ed has the lot list ready. Needs a mapping screen: pull the unique SKU list with basic data → category-filtered lot dropdown → click to assign → assignment sticks (remembered next cycle). Only new or changed SKUs surface for a decision.

**Pack-size cleanup:** requires human reasoning (a 50lb bin gets entered as "1 bin," "each," or "1lb"). The system catches the dirty rows, surfaces conversion options anchored to the Sub Commodity code, stores the decision, and remembers it. Raw underneath, normalized on top.

**Identity safety:** unrecognized items go to a quarantine queue, never a silent guess. The SAP Sub Commodity code is a hard anchor, so fuzzy-match risk is low.

**Reference vs transactional core (Ed's architecture):**
- Reference, own homes: Clients. RFP setups. Suppliers (CRM / contacts).
- Transactional core, the spine: one bid line store (every RFP, any structure, same shape) → award table (who won what, which RFP). Pull an award = read the table, find the lines, render.

---

## Discrepancy log (doc vs build / reality)

| # | The doc says | Reality | Type |
|---|--------------|---------|------|
| 1 | Fiscal calendar parked, not loaded | Loaded through 2037 | doc undersold |
| 2 | Proud of no SENT state, "never sends" | Ed needs send + a draft-to-sent gate | doc wrong |
| 3 | 6 pricing models at the bid line | 3 axes decided at kickoff (basis / duration / volume split); model belongs at setup, not inferred at the line | wrong layer |
| 4 | 10 stages (second doc: 13) | Shape is per-cycle variable | both wrong |
| 5 | Grain `DC × lot/item × supplier` locked | Pricing grain adds period; parent product (not UPC) is the unit; fiscal-period correction pending | grain under question |
| 6 | Safeties stored as parameters, never fired | Safeties are the core governance of the deal | inert where it matters |
| 7 | 2.9E normalizes priced offers (BUILT) | Bid intake is PARKED, so it runs on fixtures only | calculator with no input |
| 8 | (absent) | Scan-out / sell-through history needed | gap |
| 9 | (absent) | Ship-from vs grow-origin must be two fields | gap |
| 10 | Synthetic data only, no real cycle run | Same. Biggest risk in the build. | unverified fit |
| 11 | Pricing model inferred at bid line | Real docs declare it at kickoff (disaster clause, de-escalator, period-by-period, baseline-then-negotiate). Confirms the wrong-layer finding with hard evidence. | confirmed |
| 12 | (absent) | Annual spend, objective field, PBA governance, working-capital terms, KPM funding, configurable RFI question set — all real kickoff fields missing from the model | gaps to add |
| 13 | (absent) | KCMS is a distinct scan feed from iTrade; scorecard captured at both gates | source model incomplete |
| 14 | "Exact minimum-cost solver" awards by lowest cost | Ed's real engine is decision-support: computes/compares all suppliers, surfaces the min as reference, human picks (cost + supply + quality + incumbent + risk). Spec automated the one thing he does by hand on purpose. | spec backwards — keystone correction |
| 15 | Scenario A as single benchmark | Real engine uses a set of lenses (baseline/incumbent, min, no-disc, supplier-excluded) compared vs STLY and Latest | model incomplete |
| 16 | Booking guide / Stage 8 NOT BUILT | Ed builds it by hand every cycle; it is the award table + execution logistics. System generates it from the award. | exists manually |
| 17 | (absent) | Match key is a string concat (product&DC); the normalized lot must replace it | engine fragility |
| 18 | (absent) | Timeframe pricing forks the entire engine per timeframe by hand (Colored Potato). System parameterizes timeframe as a dimension. Biggest efficiency win. | bespoke fork |
| 19 | "One supplier wins one DC × lot × timeframe cell" — locked, everything depends on it | Cells are split across multiple suppliers (allocation with volume shares). The locked grain is wrong. | spec foundational error |
| 20 | Sign-off / leadership gate not modeled | Real, portfolio-level: strategy recap + per-DC recommendation + savings vs STLY + sign-off scorecard. Hand-built deck; system generates it. | gate output to build |

---

## Open questions (carry forward)

Asked and still unanswered:
- Kickoff file: actual structure. One setup per RFP, or several structures inside one RFP?
- "Open last cycle": final awards only, or the full picture including losing bids and the reasoning?
- Look-back: do you need a supplier's sourcing location as it was at that time?
- Same messy pack entry: ever map different ways across cycles, or a standing rule once decided?
- One Sub Commodity code = one parent, or is a level needed between code and UPC?
- What "basic data" shows on the SKU mapping row so you pick the lot confidently?

Resolved across sessions:
- **Which codebase is the real line?** → v3 is the engine brain; the repo's persistence/governance instinct is the spine. Build v3's scoring/allocation engine on a real governed data layer. Neither alone is the product (Session 6).
- **Split awards: YES, routinely** (Session 4, sign-off deck). A cell is allocated across multiple suppliers. The single-winner grain is corrected.
- Confirmation email = official record, governed by draft-to-sent (Session 1).
- Contracting = assemble contract + specs + legal, send (Session 1).
- Pricing model is declared at kickoff, not inferred at bid line (Session 2).
- Attribute taxonomy = universal core (organic, color, size, pack) + per-category extensions (Session 3, pending one confirmation pass per category).
- Scenario engine = decision-support, not auto-award (Session 3). Inside the system, generated from the award.

---

## What the next session needs (real screen)

- One or two real **kickoff files**.
- One real **iTrade pull** (actual headers) uploaded into the working chat.
- One **finished cycle's step list**.
- **Repo access** by zip upload or a proper collaborator handoff. No credentials pasted in chat.

---

## Build sequence (priority)

1. **Setup / kickoff layer (keystone).** Captures objective, basis, duration and cadence, volume split, safeties, and the why. Drives the read for everything downstream.
2. **Normalization + mapping screen.** Parent product via Sub Commodity, sticky lot assignment, pack-size cleanup.
3. **Back-end governance.** Sign-off gate, awards, contracting, all on the draft-to-sent gate.
4. **Middle.** Already strong. Extend it, do not rebuild it.

Note: the historical payoff starts at cycle 2 and compounds. Cycle 1 produces the record; it does not consume one. Get one full cycle running on real data soon, because until one completes, the historical benefit is zero.
