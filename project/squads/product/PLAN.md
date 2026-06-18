---
doc: Product / Business-Analysis Squad — Plan (the kickoff keystone, supplier field & RFI)
id: PROD-PLAN
squad: Product / BA (Squad 7)
status: Draft
created: 2026-06-18
owns: the kickoff keystone field model (cyc.*, E-14 / G5), the structured-vs-narrative
      governing rule, the supplier field + configurable RFI, acceptance criteria for E-14,
      and the sponsor open-questions backlog
relates: audit/02 G5 (kickoff under-modeled in both), specs/rfp-engine/BUILD_02 Layer 3 (cyc),
         specs/original-engine/BUILD_02 Layer 3 (rfp_cycle, thin), project/squads/architecture/PLAN.md
         §2 (cyc table list), SESSION-02 (prior extraction — validated here), E-14/E-16/E-17,
         ADR-0001 + Security PLAN (clean-room, sample handling)
deliverables: KICKOFF_KEYSTONE_SPEC.md (this squad), reference/SAMPLE_REGISTER.md (this squad)
---

# Product / BA Squad — Plan

We own the **kickoff keystone**: the field-level data model for the `cyc.*` layer. The kickoff
doc is the *setup file* of the whole system — "declare structure once at kickoff, store it,
render everything downstream from it." Both source specs under-model it (G5): the as-built
`rfp_cycle` carries commodity/objective/dates only; the brief's `cyc.cycle` adds a thin
`pricing_basis` and names the safeties without modeling them. The five real kickoff docs prove
the structure is **consistent across categories and years** and can be lifted into fields.

The deliverable is `KICKOFF_KEYSTONE_SPEC.md`: source corpus, field catalog, a proposed
`cyc.*` model (additive DDL proposal — we do **not** edit `db/baseline/schema.sql`; Platform &
Data owns it mid-build), a crosswalk, Session-2 validation, and sponsor open questions.

---

## 1. Scope

**In scope (now — E-14 / G5):**
- The kickoff keystone field catalog — every kickoff data element, classified
  structured-vs-narrative, with type, cardinality, and source feed.
- The proposed `cyc.*` table set (additive migration proposal, presented as DDL in the spec).
- The **supplier field + configurable RFI** (`cycle_invited_supplier`, `cycle_rfi_question`) —
  invited-supplier denominator and the per-cycle, category-specific question set.
- The structured-vs-narrative governing rule and the data-handling note.

**In scope (next):**
- Acceptance scenarios driving E-14 (a cycle declared from a real kickoff doc) and feeding
  E-16 (rail rendered from `cycle_timeline_event`) and E-17 (Stage-0 in-gate).
- RFI question-set governance (template library vs free authoring) — pending sponsor.

**Out of scope (other squads):**
- The physical schema / migrations / constraints — **Platform & Data** (`db/baseline/`).
- Pricing-safety *execution/visualization* — **Engine** (E-15 / G4). We model the *declaration*
  (parameters at kickoff); they make it fire.
- Scorecard/iTrade/KCMS *ingestion* — **Platform & Data** (E-08/09/10). We model the kickoff
  *snapshot pointers* and the field shape; they build the receipt-grain feeds.
- RBAC / Stage-0 approval object internals — **Security** (E-17). We supply the gate's data needs.

---

## 2. The governing rule (held throughout)

> **Structured fields drive the system; narrative blocks carry the *why* and stay prose.
> Never force the narrative into fields; never bury a decision in prose.**

Operationally, every kickoff element is classified **structured** or **narrative**:

- **Structured** — a value the engine, the rail, a feed, or a downstream artifact reads:
  objective, pricing basis/cadence, the safety parameters, scope codes, PBA thresholds, terms,
  timeline events, invited suppliers, RFI question set. These become typed columns/rows.
- **Narrative** — the reasoning a human authored and a human reads: background, data dive,
  industry insights, category strategy, sourcing strategy, general goals. These are stored as
  **versioned rich text** attached to the cycle (`cycle_narrative`), never field-ified.

The five docs validate the split exactly: their structured header/terms/timeline content is
uniform across categories; their prose sections vary freely and resist tabulation.

---

## 3. Backlog slices for E-14 (vertical, store-first)

| Slice | Deliverable | Tables touched (proposed) | Depends |
|---|---|---|---|
| E14-S1 | **Cycle identity + objective** declared from a kickoff doc | `cycle` (extend), `cycle_objective` | norm.lot, ref.subcommodity |
| E14-S2 | **Pricing structure + five safeties** declared at kickoff | `cycle_pricing`, `cycle_safety` | E15 (exec) reads these |
| E14-S3 | **Scope & baseline pointers** (subcommodity/GTIN scope flag, two scorecard snapshots, KCMS grain) | `cycle_scope_item` (+ scope flag), pointers to `perf.*` | E-08/09/10 feeds |
| E14-S4 | **Commercial terms** — PBA, working capital, KPM | `cycle_pba_term`, `cycle_commercial_term` | — |
| E14-S5 | **Supplier field + configurable RFI** | `cycle_invited_supplier`, `cycle_rfi_question` | ref.supplier |
| E14-S6 | **Timeline / rail** from Next Steps | `cycle_timeline_event` | feeds E-16 |
| E14-S7 | **Narrative blocks** (versioned rich text) | `cycle_narrative` | — |

Each slice is store-first: a real kickoff doc round-trips into the fields, structured drives,
prose stays prose. Slices land additively (no breaking change to `cyc`; the breaking changes in
the program are all in `eng`).

---

## 4. Acceptance criteria (E-14)

1. A full cycle can be **declared from one real kickoff doc** end-to-end: identity, objective(s)
   with a primary, pricing basis + cadence + baseline-then-negotiate, the safety parameters,
   subcommodity scope, the manual GTIN in-scope flag, PBA thresholds, working-capital + KPM
   terms, invited suppliers (incumbent/non-incumbent), the RFI question set, the timeline, and
   the narrative blocks.
2. **Structured drives, prose stays prose:** every structured element is queryable; every
   narrative block is stored as versioned rich text and is *not* parsed into columns.
3. **Two scorecard snapshots** (kickoff + sign-off) and **KCMS at two grains** (subcommodity +
   GTIN) are representable, confirmed by the `Scorecard`/`Scorecard (Signoff)` and
   `KCMS (subcomm)`/`KCMS (GTIN)` tab pairs.
4. The **timeline drives the rail** (feeds E-16): the rail renders from `cycle_timeline_event`,
   not hardcoded; round count is variable; both leadership gates anchor the ends.
5. The **RFI question set is configurable per cycle** (category-specific), not a fixed enum.
6. **Objective is multi-valued with a primary**, not a single savings amount.
7. No table change is made to `db/baseline/`; the DDL is a reviewed **proposal** for a later
   additive migration owned by Platform & Data.
8. **No sensitive commercial value** appears in any committed file (CI clean-room check + review).

---

## 5. Open questions for the sponsor

1. **One setup per RFP, or multiple structures inside one cycle?** Field Tomato declares a single
   pricing shape, but its sourcing strategy floats "quarterly/monthly/weekly" *and* per-timeframe
   negotiation. Is a cycle ever **heterogeneous** (e.g. different cadence per subcommodity/lot),
   which would force `cycle_pricing` to a per-scope grain rather than one-per-cycle? **(Top Q.)**
2. **RFI question-set governance** — a curated template library (versioned, reusable, with a
   stable code per question) vs free per-cycle authoring? The docs show the set *evolves each
   cycle* ("new RFI questions incorporated"), so it must be configurable; the open part is
   whether answers must be comparable across cycles (argues for stable question codes).
3. **Safety vocabulary** — the five named safeties (disaster trigger, inverse de-escalator,
   collar, rolling midpoint, tolerance band) come from the broader intake; these four kickoff
   docs surface only **baseline-then-negotiate** + cadence options explicitly. Confirm the full
   safety set is the intended configurable menu (we model all five as optional).
4. **Objective enum** — confirm the closed set {savings, supply assurance, quality,
   diversification, strategic} and that exactly one is flagged primary.
5. **Scorecard window definition** — who sets the kickoff vs sign-off windows, and is the
   sign-off snapshot always re-pulled (the workbook shows two distinct windows)?
6. **KPM treatment** — held separate vs negotiated into COGS is a per-cycle choice; confirm both
   are valid and the field is a flag, not a constant.

---

## 6. Data-handling note (binding — ADR-0001 + Security PLAN)

The five source files contain **real commercial values** (annual spend, supplier names,
performance metrics, payment terms, funding amounts). They are **quarantined** under
`reference/samples/*` (gitignored). Our committed output is **structural only**: field names,
types, structured-vs-narrative class, cardinality, source feed. Any example is a generic
placeholder (`$XXXM`, `<SupplierA>`, `<SubComm-1>`). We never copy file contents verbatim into a
tracked file. The sanitized record of what arrived is `reference/SAMPLE_REGISTER.md`; the
sanitized schema is `KICKOFF_KEYSTONE_SPEC.md`. This honors the reference-intake rule (schema +
digest only across the boundary) and the clean-room CI gate (`backend/` never imports
`reference/`).

## Changelog

| Version | Date | Author | Change |
|---|---|---|---|
| 0.1 | 2026-06-18 | Product/BA squad | Initial plan; scope, governing rule, E-14 slices, acceptance, sponsor questions, data-handling note. |
