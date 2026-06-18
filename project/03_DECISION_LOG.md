---
doc: Decision Log
id: PM-003
version: 0.1
status: Living
created: 2026-06-18
depends_on: PM-000
---

# Decision Log

The register of program-shaping decisions. **OPEN** decisions gate detailed squad planning and are escalated to the Sponsor. Each carries the PM/Architect recommendation so ratification can be a confirmation, not a research task. Dependencies (DEP-n) are logistics blockers, not choices.

Status: **OPEN** (awaiting sponsor) · **RATIFIED** · **SUPERSEDED**.

---

## Decisions

### D1 — Build path · **RATIFIED 2026-06-18 → clean-room reconciliation** (ADR-0001)
**Question.** Reconcile-and-extend the existing 63-table store, or greenfield the brief's 36-table schema?
**Resolution.** **Clean-room reconciliation.** New clean codebase; the AS-BUILT *schema* (re-expressed as clean PostgreSQL) is the migration baseline; the existing repo stays isolated in the sponsor's GitHub and is never imported (sponsor constraint: "i dont want it contaminating this build … keep it isolated"). The seven KEEP capabilities are re-modeled, not inherited; the wrong brain and SQLite-isms are dropped by construction. See ADR-0001 for the isolation protocol.
**Linked:** audit D1, DEP-1, ADR-0001.

### D2 — The brain · **RATIFIED 2026-06-18 → adopt v3 (Option A)** (ADR-0006)
**Resolution.** Sponsor ratified the spike ("D2 Spike ok!"). Adopt v3's five-factor banded scoring + `max_two_per_dc` split allocation as the engine library, behind the frozen `run()` interface; retire the as-built min-cost solver to "Scenario A = lowest-cost reference." Decision-support only — the engine never auto-asserts an award. **G1 (split) + G2 (scoring) ship together** in Phase D, after the Phase-B pilot, behind feature flags; validated by golden-master reproduction of v3.
**Linked:** spike SPIKE_D2_engine.md, gaps G1/G2, ADR-0006.

### D3 — Pricing placement & safeties · **OPEN** · needed by: Phase C/D
**Question.** Lift pricing + the five safeties to kickoff and make the safeties executable, keeping the as-built's commercial component storage?
**Recommendation.** **Yes.** Real kickoff docs declare pricing there (Discrepancy #3/#11); safeties are "the real product" and currently inert (R5).
**Impact if changed.** Pricing stays at the wrong layer; safeties stay decorative.
**Linked:** audit D3, gap G4.

### D4 — Outward-facing sequence · **OPEN** · needed by: Phase E entry
**Question.** Order of the `awd.*` build and which generated artifact ships first?
**Recommendation.** **award → freeze → sign-off → outputs; booking guide first** (most-used; v1.4 has `generate_booking_sheet`).
**Linked:** audit D4, gap G3.

### D5 — Net-new enterprise scope · **OPEN** · needed by: Phase 0/A
**Question.** Commit tenancy (`client`), RBAC, PII/retention, and NFRs from the start?
**Recommendation.** **Yes — design tenancy in now** (cheap before breadth, expensive after); author the security/NFR spec in parallel with Phase A; make the real-data pilot Phase B's exit gate.
**Linked:** audit D5, gaps net-new, R7.

### D6 — Frontend / "enterprise web app" stack · **RATIFIED 2026-06-18 → React/Next.js + TypeScript SPA** (ADR-0002)
**Resolution.** React + Next.js (App Router) + TypeScript, a pure client of the FastAPI backend, types generated from OpenAPI, built last (ADR-001). Streamlit is retired, not hardened.
**Linked:** ADR-0002.

### D7 — Execution mode for this engagement · **RATIFIED 2026-06-18 → plan then scaffold now** (ADR-0003)
**Resolution.** Finish detailed squad planning, then stand up Phase 0/A running ground this engagement (validated schema baseline, backend skeleton, tenancy/RBAC foundation, CI, infra), treating ratified decisions as binding and D2 as in-spike.
**Linked:** ADR-0003.

### D8 — Tenancy model · **RATIFIED 2026-06-18 → multi-tenant-capable, single-tenant-operated** (ADR-0004)
**Question (plain).** Who uses this system (one org vs many), and how physically separate must each group's data be?
**Resolution.** One logical tenant (Kroger Sourcing); keep `client_id` on every row as cheap insurance + shared-schema + Postgres RLS as the standard isolation pattern; **database-per-tenant deferred**, revisited only if divisions must be walled off, the system is offered externally (SaaS), or a compliance rule mandates physical separation. Resolves the Security/DevOps "topology" fork (mobilization report §6) with their default. Sponsor confirmed the "one org" framing.
**Linked:** ADR-0004, Security plan, DevOps plan.

### D9 — Cycle pricing grain · **RATIFIED 2026-06-18 → one model per RFP + item-level participation**
**Question.** Can one RFP carry different pricing setups per product group, or a single model?
**Resolution (sponsor).** **One pricing model per RFP** — the pricing *structure* (basis / cadence / safeties) is declared once at the cycle. Prices are captured at the **item level** (per line). Product heterogeneity is handled by **selecting which items participate** (scope in/out), not by mixing pricing structures. So `cyc.cycle_pricing` is one-per-cycle; the keystone needs a strong item-participation switch (`cyc.cycle_scope_item.participates`). Supersedes the PM lean toward per-scope pricing; resolves the kickoff-spec open question.
**Linked:** KICKOFF_KEYSTONE_SPEC.md (G5/E-14).

### D10 — Split awards behavior · **RATIFIED 2026-06-18 → auto max-2 output + free manual per-cell selection** (confirms G1)
**Question.** Splits everywhere, or gated by a flag?
**Resolution (sponsor).** Splitting a DC across suppliers is done occasionally but avoided. The **auto engine run outputs a maximum of two suppliers per DC** (`max_sup_dc` default 2, configurable). The human keeps full convenience to **hand-select lot-specific suppliers for any DC×lot**. Data model: `eng.scenario_award` / `awd.award` support N suppliers per cell with `volume_share`; the auto allocation caps at 2; `cap_breach_flag` surfaces when a manual selection exceeds the cap. **No separate per-DC "splittable" flag** — the cap is the default and human selection is unrestricted.
**Linked:** gap G1, ADR-0006, V3_ENGINE_LOGIC.md.

### D11 — Incumbent & historical/baseline cost source · **RATIFIED 2026-06-18 → BOTH sources, display both**
**Question.** Is DC-level prior pricing / incumbent-by-DC available, and from where?
**Resolution (sponsor).** From **both**, shown side by side:
- **Prior RFP bid/award data in the system** — used when a previous cycle exists for that lot×DC (the historical payoff that compounds from cycle 2 onward).
- **iTrade receipt history** (`perf.itrade_receipt`, DC No + Vendor + FOB per receipt, DC grain) — the actual purchase reality (e.g. min/max FOB per lot×DC); always available, the only source on cycle 1.
**Rule:** pull prior-RFP data when present, fall back to iTrade when absent, and **always display both**. Supplies the engine's **Historical** factor (delta vs baseline) and **Continuity** factor (incumbent). Ties to E-08 (iTrade importer) + the cross-cycle store.
**Savings baseline (sponsor-refined 2026-06-18 — supersedes prior default):** the yardstick for **actual savings** (and the engine's **Historical** scoring factor, and "Savings vs STLY") is the **iTrade volume-weighted average of what was ACTUALLY PAID over the full corresponding prior RFP period** — *not* the prior contracted/awarded rate. **Rationale:** a contracted rate may never have been effective (market swings, fired escalators/de-escalators, off-contract buys), so actual-paid is the honest baseline. The prior-RFP **contracted** price and iTrade **min/max** are still **displayed** for context (contracted-vs-paid is itself a story; min/max gives the range), but they are not the savings baseline. **Incumbent** identity = prior-RFP awarded supplier if present, else iTrade top shipper by volume for the DC×lot.
**Implication:** E-08 (iTrade importer) must derive a volume-weighted average actual-paid per lot×DC per fiscal period; this is a first-class baseline derivation, not just raw receipts.
**Linked:** gaps G6/G2, FEEDS_ITRADE.md (E-08), V3_ENGINE_LOGIC.md, ADR-0006.

### D12 — Pricing storage vs display · **RATIFIED 2026-06-18 → period-grain storage, setup-file-driven display** (ADR-0013)
**Principle (sponsor-raised, from the intake's locked truths).** Separate *how pricing is stored* from *how it is displayed*.
**Resolution.** **Storage:** period-grain component facts (supplier × lot/item × DC × **period** × price); fixed deals repeat the price across periods, index deals store components and resolve, period-by-period is native to the grain; one table, the basis decides which columns carry weight. **Display:** the **setup file** (`cyc.cycle` pricing declaration — basis, cadence, components shown, safeties) is the **render contract**; the system renders each RFP from stored facts + the setup file, so the **same data renders identically live or historic** (the mechanism behind "open last cycle"). Complements D3/G4 (pricing declared at kickoff) and D9 (one model per RFP).
**Linked:** ADR-0013, intake locked truths #1 (period grain) & #5 (setup drives the read), D3/D9.

### D13 — Pricing safeties = contractual execution terms, NOT engine inputs · **RATIFIED 2026-06-18** (ADR-0014)
**Reframe (sponsor).** The five safeties are **contract terms** (risk-sharing incentives to get suppliers to participate), declared at kickoff, governing **post-award price movement** during execution. **They do not affect the scoring/allocation math** — the engine stays clean.
**Objective + flexibility (sponsor 2026-06-18).** Their purpose is to let the price **move up when warranted and back down when warranted, within governed bounds** (controlled bidirectional flexibility, so a deal breathes without reopening). **All timelines/windows/bands are set individually per RFP** — not fixed defaults.
**Mechanics (confirm — see ADR-0014):** **Collar** = cap (Kroger upside protection on a hike) + floor (supplier downside protection; Kroger will go to 0), fixed + market. **Rolling midpoint** = every 8 wks, price = midpoint of trailing 4-wk market, for next 8 wks. **Tolerance band** = sustained anomaly (price outside band ≥2 wks) → temporary reprice to market midpoint below collar for 2 wks → review. **Disaster / inverse triggers** = discretionary; generalized spike/drop → human evaluates & reprices; **always reverts to contract after the disaster period**.
**Consequences.** Safeties move from "engine" to a **contract/execution module** (Phase E+): `cyc.cycle_safety` stores terms; `awd.award_layer` records reprices; feeds E-28 (contracted-vs-effective). The **pilot/engine work is independent of safeties.** Open: a **market-price feed** (USDA?) is needed for the formulaic ones.
**Linked:** gap G4, ADR-0014, D3, E-28.

### D14 — Attribute taxonomy: one shared catalog, sparsely populated · **RATIFIED 2026-06-18**
**Resolution (sponsor).** It is **one shared attribute taxonomy** — not separate per-commodity schemas. The *catalog* of attributes is common; **which fields are populated varies by item** ("not every item has data in every column"). So `norm.attribute_def` is one superset catalog and `norm.lot_attribute` is **sparse** (a lot carries only its applicable attributes). Simplifies G8: no per-commodity confirmation pass beyond extending the shared catalog when a genuinely new attribute appears.
**Linked:** gap G8, KICKOFF_KEYSTONE_SPEC.md, intake Session 3.

---

## Dependencies (logistics blockers)

| ID | Dependency | Blocks | Owner | Status |
|---|---|---|---|---|
| **DEP-1** | **Isolated, read-only** access to the existing repo (`models.py`, Alembic chain, tests, ECLS) — in the sponsor's GitHub; read via an isolated worktree agent per ADR-0001, never imported | ECLS/test verification, R6 | Sponsor | **OPEN — non-blocking** (we baseline from the as-built schema we already hold) |
| DEP-2 | One **real iTrade pull** + one **real bid round** (synthetic-only today) | Phase B pilot, S2, R1 | Sponsor | OPEN |
| DEP-3 | One or two **real kickoff docs** (for the keystone, G5) | Phase C | Sponsor | OPEN (4 referenced in intake) |
| DEP-4 | Target hosting/cloud + identity provider (for tenancy/RBAC/D6) | Phase A DevOps/Sec | Sponsor/IT | OPEN |
| DEP-5 | **Historical booking guides** + prior-cycle award/contract data (sponsor can locate many) | E-28 contracted-vs-effective backfill; prior-RFP baseline (D11) | Sponsor | OPEN — upload to `reference/samples/` when found |
| DEP-6 | **Market-price feed** (e.g. the USDA market data referenced in the kickoff docs) | E-29 formulaic safety reprices (rolling midpoint, tolerance band) | Sponsor/Data | OPEN |
| DEP-7 | **Award files + round/negotiation analysis** (sponsor to pass later) | understanding the live-negotiation process (round loop, target-setting); E-28 backfill | Sponsor | OPEN — deferred, low urgency |

---

## Ratified

*(none yet — `D-gaps` interpretation confirmed by sponsor 2026-06-18: "gsps" = gaps.)*
