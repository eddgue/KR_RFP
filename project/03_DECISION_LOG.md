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

### D15 — Gate-closure backup export · **RATIFIED 2026-06-18**
**Requirement (sponsor).** Every gate that closes at a decision point must generate a **downloadable backup file** the sponsor can save to the drives for historic archival / **emergency recovery**. The system is authoritative, but a portable, point-in-time snapshot at each gate is required as DR + a trust bridge from the shared-drive era.
**Scope.** Gate closures = kickoff in-gate (G12), each round close, award freeze (G3), sign-off out-gate. Each already emits an `audit.event_log` entry + a frozen snapshot; D15 adds a **portable export** of the full cycle state at that point (+ generated docs). Implemented as E-31.
**Linked:** E-31, governance model (Ways of Working §3), `awd.generated_document`, freeze-and-layer (ADR-004/D-equivalent).

### D16 — AI assistant (read-only) · **WISH-LIST (lowest priority)** 2026-06-18
**Requirement (sponsor, wish-list).** An AI layer for **drafting** (emails/letters) and **quick data recall** (NL Q&A). **Read-only — it never writes to the database**; it reads and answers, or drafts. Lowest priority / post-MVP.
**Guardrails (binding when built).** Read-only; **RBAC/tenant-scoped** reads (only what the requesting user may see); **decision-support-only** (never auto-asserts an award; drafts pass the human + draft→sent gate G9); auditable (reads/answers logged); built on the **latest Claude models**. The governed store + event log make it a clean, trustworthy retrieval source. Implemented as E-32.
**Linked:** E-32, Security plan (RBAC/tenancy), gap G9 (draft→sent), ADR-0006 (decision-support-only).

### D17 — Reference cycle files are AS-IS evidence, not the target design · **RATIFIED 2026-06-18**
**Clarification (sponsor).** The uploaded Field Tomatoes corpus (engine input, ingestion sheets, booking guide, raw supplier bids, etc.) is **AS-IS reference** — it reflects how the work is done **today, manually, in Excel** — for understanding the logic/data and for **testing**, **not a layout or a workflow to replicate.** Rule: **KEEP the technical substance + the domain truths** (the engine I/O contract, the bid grain + cost components, scoring config/constraints, data semantics, and the captured requirements/decisions D1–D16); **BUILD our own** system — our own **strategies, process steps, presentation, generated outputs, and RFP/bid template.** We are **not** digitizing today's manual workflow one-for-one; we improve it (governed gates, automation, new capabilities like E-28/E-30/E-32), and the **process shape is per-cycle configurable** — the setup file defines the rail (intake locked-truth #8), not a hardcode of today's steps. The supplier-facing RFP/bid template stays **multi-sheet** as a concept, but it is our design. Generalizes ADR-0006 ("lift the logic, drop the Excel") to the whole reference corpus and to the process itself.
**Linked:** ADR-0006, ADR-0013, gap G10 (rail from cycle timeline), CYCLE_FIELDTOMATO_STRUCTURE.md, FEEDS_ITRADE.md.

### D18 — Strategy-agnostic platform: strategies are first-class, developed & run · **RATIFIED 2026-06-18** (ADR-0016)
**Principle (sponsor).** The reference files are **single-strategy molds** (one RFP's approach each). We build a **strategy-agnostic platform** where strategies are **developed** (composed, saved as reusable, versioned templates) and **run** (bound to a cycle and executed). **Nothing strategy-specific is hardcoded.** A *strategy* = objective(s) + pricing model/cadence/safeties + scoring weights/preset (or custom) + award constraints (max-sup-per-DC, single-supplier-per-lot, premium thresholds, coverage floor) + the scenario lenses to run + process rail/steps + preferences/exclusions. Generalizes the engine's commodity-agnostic/config-driven design and the per-cycle rail (locked-truth #8) into a first-class **Strategy**. **Commodity-agnostic ⊆ strategy-agnostic.** Every run records its strategy version → reproducibility + faithful historic render.
**Linked:** ADR-0016, ADR-0006, D9/D12/D13, scenario_config_version/metric_definition_version/engine_release, intake locked-truth #8.

### D19 — Build methodology: modular, full-fidelity prototype versions — **NOT MVP** · **RATIFIED 2026-06-18**
**Directive (sponsor).** "I don't work off MVPs. Once in dev I work prototype versions and modularized builds — never a boiled-down MVP." We build **well-bounded modules**, each delivered as a **functional prototype version of the FULL capability** (iterated v1→v2→…), not a thinnest-possible slice.
**Implications.** Definition of Done per module = a working prototype of the *whole* capability (not a stub/thin MVP cut). Aligns with the existing modular architecture (8 domain packages per schema, engine-as-a-library behind an interface, additive migrations). The engine's deterministic stub was a D2-deferral placeholder only — with D2 resolved (adopt v3), the engine module becomes the real v3 prototype. Roadmap phases/epics are **modules**, each built to prototype fidelity. **Supersedes any "MVP" framing** in prior docs.
**Linked:** ADR-0003, ADR-0006, ADR-0016, Ways of Working §1.

### D20 — Round-trip ingest: the system ingests the files it generates · **RATIFIED 2026-06-18**
**Principle (sponsor).** "The engine should be able to ingest the files it itself is creating." The system **owns both ends** of the bid round-trip: it **generates** the RFP/bid template (multi-sheet, our design — D17) and **ingests** the returned files. Generation + ingestion share **one owned, versioned template schema**; the importer reads back OUR format, not arbitrary legacy layouts.
**Implications.** (1) The **intake module is paired with template generation** — same schema, two ends. (2) Ingest is robust by design — **no universal-format guessing for the live product**; the messy reference formats (`.xlsb`, 14-tab legacy) are **test/reference inputs only** (prove resilience during migration), not the live contract. (3) **Round-trip test:** generate the template for a cycle scope → fill (synthetic) → ingest → assert the `bid.bid_line` grain round-trips exactly. (4) Generalizes — generated artifacts are structured and re-ingestable where useful (not dead-end Excel). (5) The template is generated **from the cycle setup/strategy** (scope: lots, DCs, items, TFs, rounds) — ties to kickoff + strategy (D9/D18); and it carries the engine's IN_Bids contract (supplier×DC×lot×item×TF×round + cost components).
**Linked:** D17, D18, E-15 (template release), CYCLE_FIELDTOMATO_STRUCTURE.md (the IN_Bids contract), ADR-0016.

### D21 — Explicit key IDs at every grain; key-based pulls, never guessing · **RATIFIED 2026-06-18**
**Principle (sponsor).** Build **stable surrogate key IDs at every level** — RFP/cycle, round, timeframe, lot, item, DC, supplier, bid submission, and **bid line** — with relationships as **cascading FK dependencies**. The engine and every consumer **pull via keys** (deterministic joins down the dependency chain), never guess or text-match. This permanently kills the old `product&DC` string-concat match-key fragility (ADR-002).
**Implications.** (1) Every grain has an explicit ID; composite-identity FKs (already a KEEP strength — 46 of them) extend down to bid-line level. (2) **The generated bid template (D20) embeds the relevant key IDs** (cycle/round/tf/lot/item/dc) in each row, so returned bids carry their identity → **ingestion is a key-validated load, not a text resolve**; rows whose keys don't match the cycle scope are quarantined, never guessed. (3) The engine reads cycle → rounds → bids → lines → scores by **traversing keys** (cascading dependencies). (4) "Open last cycle" and audit are key-joins. (5) Surrogate keys are system-owned (UUIDs); human/source codes (UPC, SAP subcommodity, supplier names) are *attributes* resolved to keys via the alias layer, not the join key.
**Linked:** D20, ADR-002 (lot grain replaces string-concat), as-built composite-identity FKs (keep list), engine (no string-concat match key), the intake module.

### D22 — Booking guide is the FINAL post-award output; two audiences · **RATIFIED 2026-06-19**
**Clarification (sponsor).** The booking guide is the **final step, after awards** — not generated directly from a scenario. Real sequence: scenario → **human selects** → `awd.award` → **freeze** → **sign-off** → **booking guide**. Two versions, both generated from the frozen award records: (a) **internal** — buyers + pricing use it to **update pricing in the system**; (b) **per-supplier** — each awarded supplier receives their own "here is what you've been awarded" guide. The demo generated the booking guide straight off the recommended scenario (a shortcut) — the real flow routes through award selection + freeze first.
**Linked:** G3, E-21/E-22 (award/freeze/sign-off), E-23 (generated docs: internal booking guide + per-supplier award guide), D9 (pricing update).

### D23 — Human-facing outputs render resolved NAMES, never key IDs · **RATIFIED 2026-06-19**
**Principle (sponsor).** Every generated/human-facing surface (booking guide, recommendation, letters, the web UI) must display **resolved human-readable names** — supplier name, lot/item description, DC name — **never the data keys** (UUIDs/codes). Keys are for *joining* (D21); names are for *reading*. Feedback that triggered this: the demo booking guide showed `SUP-*`/`LOT-*` keys — "I can't read data keys." Corollary of D21 (keys join, names display).
**Implication.** Output generators resolve keys → display attributes (via the ref/alias layer) before rendering; the synthetic seed must also carry readable names so demos are legible.
**Linked:** D21, E-23, the output layer, ref/alias.

### D24 — Generated outputs are presentation-quality, not data dumps · **RATIFIED 2026-06-19**
**Requirement (sponsor).** Every generated human-facing artifact (booking guide, sign-off deck, per-supplier award guides, letters) must be a **formatted, presentation-ready** document a buyer/team/leadership can present — titled header block, styled/bold column headers, sensible column widths, borders/grouping, `$`/`%` number formats, freeze panes, and a summary. **NOT a raw CSV-like dump** (the first demo booking guide was unformatted). Quality bar for the Output Factory (E-23); applies to every xlsx and rendered doc.
**Linked:** E-23, D22, D23.

### D25 — Live, interactive scenario the buyer can play on (not a flat render) · **RATIFIED 2026-06-19**
**Requirement (sponsor).** The buyer must see the scenario as **interactive data tables they can play on** — the scored bids, the scenario comparison, and the per-cell allocation as tables, AND the ability to **override the awarded supplier per cell and watch all-in price / spend / savings / cap-breach recompute live** (the v3 `CUSTOM_SCENARIO` capability). A flat read-only `RECOMMENDATION.md` is only a *verification render*, not the deliverable.
**Two homes.** (1) **Production = the web UI scenario-review screen** — live, on the governed store; the right home, and it avoids the Excel live-formula fragility D12/ADR-0013 warns about. (2) **Demo/interim = a generated interactive Scenario Workbook (xlsx)** — data tables (scored bids / scenario comparison / per-cell allocation) + a Custom Scenario tab with **per-cell supplier dropdowns and live formulas** (spend/savings/cap-breach), generated from our records so the buyer can play with it now.
**Linked:** E-23, web UI scenario-review (Phase F), v3 CUSTOM_SCENARIO, ADR-0013 (live-formula caveat), D22/D24.

### D26 — The scenario workbook is an ALIGNMENT / COMPARISON tool, not a summary · **RATIFIED 2026-06-19**
**Requirement (sponsor).** The scenario deliverable's purpose is the **team alignment tool** — what buyers/category/sourcing work through in the alignment call to *decide* — NOT a final summary. (Treat it as a first-class deliverable in its own right, independent of the eventual web app — "get the right deliverables first.") It must provide the **comparison surfaces** that make it an alignment tool, all the v3 FOB-comparison + scenario-tool capability:
- **Across suppliers, per cell:** for each DC×lot×item×TF, **every eligible supplier side by side** — all-in/FOB $/case, the 5 factor scores + RecScore, premium vs market-low, **cost impact vs baseline / vs incumbent**, min/best highlighted, incumbent + recommended flagged. The competitive picture the team debates.
- **Across scenarios (the lenses A–G + custom):** **side by side** — per DC and total: recommended supplier(s), spend, **savings vs baseline / vs STLY**, supplier count, cap-breaches, and the **deltas between scenarios**. So the team aligns on which lens.
- **Interactive custom build (D25):** override per cell with live spend/savings/cap-breach, grounded in the comparisons (show the picked price vs min / incumbent / baseline).
- **Reference points:** incumbent, baseline, STLY/Latest throughout.
**Homes.** Deliverable now = the standalone Excel **alignment workbook** (the engine's primary analytical output). Production interactive home = the web UI scenario-review (Phase F).
**Linked:** D25, v3 FOB-comparison/scenario-tools, intake Session 1 (alignment calls) + Session 3, E-23, ADR-0016 (strategy-agnostic).

### D27 — Data is manipulable; analytical surfaces are flexible, not fixed reports · **RATIFIED 2026-06-19**
**Principle (sponsor).** "Make the data manipulable, and the system should do the same." The analytical deliverables (scenario workbook now; the web scenario-review later) must let the user **manipulate the data** — pivot, **expand/drill (scenario → DC → supplier)**, filter, slice, rearrange — not read fixed tables. Current tools are "great but messy" (rich/flexible); ours must reach that richness while staying clean: **depth on demand** (drill to detail) rather than everything-at-once (messy) or too-little (light). The system must also present the data in multiple cuts from the same records.
**Concrete asks (this iteration).**
- **Live custom-vs-scenarios:** as the buyer builds the Custom scenario, its totals appear **live alongside A–G** in the comparison (a live Custom column that recomputes off the Custom-tab picks).
- **Expandable pivot in Scenario Comparison:** collapse/expand from scenario totals → per-DC → per-supplier (outline grouping; + a flat data table the buyer can natively pivot).
- **More detail + flexibility:** per-DC and per-supplier breakdowns, volumes, premiums — reachable by drilling, not dumped.
**Homes.** Excel deliverable now (outline grouping / Excel Tables / live formulas); web UI later (real pivot/filter/drill on the store).
**Ownership (sponsor 2026-06-19).** The **binding requirement is that the buyer can *play with the data to make decisions*.** The specific mechanics above are **illustrative direction, not spec** — the studio owns the design, grounded in these decisions and the actual schema (what the records can support). Iterate toward the decision-making goal, not a fixed layout.
**Linked:** D25, D26, web UI scenario-review (Phase F), ADR-0016, intake (Ed's allocation models = the "great but messy" reference).

### D28 — Explanatory text is the engine's computed reason, rendered from the sealed records — never a generic catch-all, never generated · **RATIFIED 2026-06-19**
**Principle (sponsor).** "This should be the governing principle in any place we see comments." Every human-readable **explanation / reason / rationale** in any output (the "why not lowest" reason, scenario rationale, flags, future letters/UI) must be the system's **authoritative computed reason**, **derived from the sealed records and rendered deterministically** — *specific to the row's actual data*. It must NOT be (a) a hardcoded catch-all phrase that reads the same regardless of what drove the result, nor (b) free-form text generated by an LLM at output time. Reproducible and auditable: same records in → same words out (corollary of ADR-0006 decision-support + immutable sealed runs).
**Single source of truth.** The reason is computed **once in the engine** and **sealed on the record**; outputs **render** it, they do not **re-derive** it (no duplicated logic that can drift). Presentation may map an engine label to a fuller sentence (rendering), but the *category/decision* is the engine's.
**First application (this iteration).** The engine's per-cell **RecType** (V3 §5: Lowest cost / Coverage advantage / Comparable premium / Defensible premium / Risk-adjusted) was computed-but-dead-code; now `V3Engine` computes it for the Scenario-B picks, the runner **seals it on `eng.analysis_scenario_award.rec_type`** (migration 0009), and the Lowest-Cost Check renders the specific reason per cell instead of one boilerplate clause. The prior generic phrase ("risk-adjusted for coverage/continuity" on every premium pick) is retired.
**Audit.** Other explanatory surfaces already comply — Negotiation Dynamics' per-supplier "read" and the fairness verdict are branched off each supplier's computed concession/premium/role; the relationship ledger states structural facts. New explanatory strings must be added under this principle.
**Linked:** ADR-0006 (decision-support, reproducible), D23/D24 (presentation), V3_ENGINE_LOGIC §5, migration 0009.

---

### D29 — The bid column set is a SUPERSET, always available; processes use a subset · **NOTE 2026-06-20**
**Principle (sponsor).** Every column the platform understands is part of the standard bid column SET and is **always available**; any given cycle/process uses only the columns it needs (e.g. `Transit Days` — migration 0011 — is a standard, optional, nullable column surfaced only when a submission supplies it; no synthetic proxy when absent). **Buyer-side:** the buyer composes a cycle's intake template by selecting columns naturally and grouping them, delivered as a template-builder walk-through; the selection+grouping is **saved as a preset** that remembers how to map a returned file back to the canonical schema (not re-inferred per upload). **Supplier-side:** the sent template behaves as a governed FORM — only entry-point cells editable, everything else hard-coded + sheet-password-protected (keys/names/structure locked, D21/D23) — with a per-row **readiness traffic light** (Not bid / Bid incomplete / Complete bid) mirroring the ingester's completeness classes.
**Status.** Captured for the REAL software (post-pilot), not the pilot. Full requirements in `project/squads/experience/INTAKE_TEMPLATE_DESIGN.md`. First realisation: `Transit Days` as an always-available optional column (migration 0011).
**Linked:** EXP-INTAKE-TEMPLATE, D20 (round-trip), D21 (keys), D23 (names), bid `template_schema`, `bid_ingester` Completeness.

---

### D30 — Per-run data isolation: each run starts BLANK, no demo data, no cross-run contamination · **NOTE 2026-06-20**
**Principle (sponsor).** Every session/run uses a **blank database** — **no demo/synthetic data anywhere** in a run store (reinforces ADR-0001 clean-room). When **multiple RFPs run concurrently**, one run's data must **never** be visible to another: each run is an isolated data store (database/schema-per-run, or a hard run-scoped boundary). This is the substrate the skill harness reads — the Engine agent grounds its commentary by reading the run store, so isolation at the data layer is the *precondition* for clean, uncontaminated data commentary (D28).
**Known gap.** The pilot currently shares ONE Postgres DB across runs with globally-unique reference codes (`ref.dc` DC01.., suppliers, items); a second run collides (`dc_code=DC01 already exists`, observed in testing) and would see the first run's reference rows. Closing this — per-run isolation — is required before multi-run.
**Linked:** ADR-0001 (clean-room), EXP-SKILL-HARNESS, D28 (engine-derived comments), the multi-RFP concurrency goal.

---

### D31 — The pilot skill is a 3-agent HARNESS (orchestrator / engine / secretary) with isolated contexts · **NOTE 2026-06-20**
**Principle (sponsor).** The skill is a small agent harness, not one agent: **Orchestrator** (the only one that talks to the user; routes + sequences), **Engine** (data-dedicated — takes inputs, runs, delivers outputs + comments; answers data questions by **reading the data**; context = sealed records only), **Secretary** (memory + memory-file side: NOTES.md, `memory/`, reminders, kanban, admin — "the noise"). Separation keeps **data commentary uncontaminated** by operational noise. **Communication discipline:** preferred **hub-and-spoke** — only the Orchestrator talks to the Engine and Secretary, under strict constraints; the Engine and Secretary do not share context directly (peer-to-peer only if essential, mediated). The aim is strict **context isolation** so the Engine's commentary is provably data-only.
**Status.** Design vision for the skill build (the step after the first RFP_MCP commit). Full design in `project/squads/experience/SKILL_HARNESS_DESIGN.md`. Depends on D30 (per-run data isolation).
**Linked:** EXP-SKILL-HARNESS, D28 (engine-derived comments), D30 (data isolation), PILOT_SYSTEM_DESIGN, RFP_MCP + RFP_PILOT_VAULT.

---

## Dependencies (logistics blockers)

| ID | Dependency | Blocks | Owner | Status |
|---|---|---|---|---|
| **DEP-1** | **Isolated, read-only** access to the existing repo (`models.py`, Alembic chain, tests, ECLS) — in the sponsor's GitHub; read via an isolated worktree agent per ADR-0001, never imported | ECLS/test verification, R6 | Sponsor | **OPEN — non-blocking** (we baseline from the as-built schema we already hold) |
| DEP-2 | One **complete RFP process** = **all rounds (R1..Rn) of a single category**, end to end — ideally a category we already hold matching data for (the Potato golden-v3 run, or a kickoff category + its iTrade pull) so kickoff→history→bids→engine→award join up. iTrade pull already provided. **Fast-follow:** a *second* category of the **other bid template** (tomato flat sheet ↔ onion 9-tab) to prove multi-template intake. | Phase B pilot (E-13), S2, R1 | Sponsor | OPEN — bid workbooks outstanding |
| DEP-3 | One or two **real kickoff docs** (for the keystone, G5) | Phase C | Sponsor | OPEN (4 referenced in intake) |
| DEP-4 | Target hosting/cloud + identity provider (for tenancy/RBAC/D6) | Phase A DevOps/Sec | Sponsor/IT | OPEN |
| DEP-5 | **Historical booking guides** + prior-cycle award/contract data (sponsor can locate many) | E-28 contracted-vs-effective backfill; prior-RFP baseline (D11) | Sponsor | OPEN — upload to `reference/samples/` when found |
| DEP-6 | **Market-price feed — USDA MARS API** (Market Analysis & Reporting Service; series `FVWTRDS-1662`). **Sponsor HAS an API key.** | E-29 formulaic safety reprices (rolling midpoint, tolerance band) | Sponsor/Security | **RESOLVED (access available)** — key goes to the secret store at build time, never chat/repo |
| DEP-7 | **Award files + round/negotiation analysis** (sponsor to pass later) | understanding the live-negotiation process (round loop, target-setting); E-28 backfill | Sponsor | OPEN — deferred, low urgency |

---

## Ratified

*(none yet — `D-gaps` interpretation confirmed by sponsor 2026-06-18: "gsps" = gaps.)*
