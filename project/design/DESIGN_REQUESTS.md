---
doc: Design requests — missing screens & visuals (to hand to the designer)
id: PM-007-DR-REQ
version: 1.0
status: Request package — the actionable "request the rest" derived from SCREEN_COVERAGE_AUDIT.md
created: 2026-06-22
relates: project/design/SCREEN_COVERAGE_AUDIT.md, project/design/handoff/ (the locked v2 baseline), project/DATA_AND_PROCESS_MAP.md
---

# Design requests — missing screens & visuals

The "finish" of the coverage review: each missing surface as a **designer-ready brief** (purpose ·
key elements · the user DECISION(s) · access point in nav · the data it binds to · states), then the
**visuals/elements** to produce beyond whole screens. Built on the locked v2 baseline (do not redesign
the 6 shipped screens — extend them). Ordered by the audit's tiers.

> **Guiding principle (governs everything below):** this is a **data-driven** process — every control is
> a **data operation**, so each screen/control below must define **how the data is treated** on a state
> change: **view ops** (filter/sort/drill) reshape + recompute against the visible set, never mutate;
> **live-edit ops** (custom build) recompute live, marked unsaved; **version switch** swaps live ↔ a
> read-only sealed snapshot; **governed ops** (import/freeze/adjust/finalize) seal/mutate + write an
> audit event. DB is the source of truth; outputs derive on request (never a stale cached number).

---

## A. Missing SCREENS to request

### A1 · Cycle Setup / Scope-review + Strategy config  — Tier 1 (the front-of-funnel hole)
- **Purpose:** after the kickoff workbook is ingested, the buyer **reviews the cycle and sets the strategy** — today setup is a blind file upload with no review/config surface.
- **Key elements:** the ingested scope read-back (DCs · lots · items · timeframes · invited suppliers · projected volumes); the **strategy panel** — weight preset (Balanced / Price / Coverage / Risk-averse / Custom + the 5 weights), the 4 safeties (premium ceiling, coverage floor, concentration threshold, max suppliers/DC), exclusions / preferred suppliers, lenses to run.
- **User decision:** confirm scope · choose/tune the strategy before generating templates.
- **Access point:** the **"Overview"** nav slot (or a "Setup" tab on Run Detail). 
- **Binds to:** `cyc.*` (scope) + `EngineConfig` (strategy). ADR-0016 strategy-agnostic.
- **States:** pre-ingest (empty / "upload kickoff"), ingested (review), quarantined rows surfaced.

### A2 · Finalize / Close-out  — Tier 1 (backend is BUILT — C5)
- **Purpose:** the terminal governed step — lock the run **Closed** and surface the **award (won) + rejection (not-won)** notices. Backend ready: `POST /runs/{slug}/finalize`, `CLOSED` event.
- **Key elements:** an **AssertModal** (same governed-action pattern as Freeze): summary (award, won/not-won supplier counts, the notices that become available), the named "I, X, close this run" assertion, the audit event that will be written (`CLOSED`); afterward the **run-status strip flips to Closed** and Awards shows the notices.
- **User decision:** assert close-out (gated — only after a FROZEN award; refused otherwise).
- **Access point:** Awards screen (a "Finalize & close run" action) + the run-status strip "Closed" state.
- **Binds to:** the FROZEN `awd.award`, `award_email_drafts` / `rejection_email_drafts` (render-on-request), the `CLOSED` audit event.
- **States:** not-yet-frozen (disabled + "freeze first"), ready, closed (read-only).

### A3 · Editable column mapper (Bid Intake refinement)  — Tier 1 if messy files are accepted
- **Purpose:** let the buyer **correct/assign** the inferred column→field mapping for a supplier's own sheet — today it's confirm-only (accept the guess or cancel), with no way to fix a wrong/ambiguous mapping.
- **Key elements:** the existing mapping-review table made **editable** — a field dropdown per column, ambiguous columns flagged for assignment, confidence shown; "never guess" preserved.
- **User decision:** override the mapping / resolve ambiguities, then confirm.
- **Access point:** Bid Intake → flexible import → the mapping step.
- **Binds to:** the `MappingProposal` (the backend `apply_mapping` already accepts a mapping; the API would take the edited one).

### A4 · Supplier comms (E-37 — the 6 touchpoints)  — Tier 1, currently parked
- **Purpose:** the outward comms surface — **review / edit / send (draft-only)** at: invite · template-send · incomplete-bid notice · round feedback · award/rejection · PBA transmittal.
- **Key elements:** a draft list per touchpoint; a draft editor (merged fields from governed data, editable); a send action behind the draft→SENT gate (E-24); status per supplier.
- **User decision:** edit + send each draft (human-gated; the system never auto-sends).
- **Access point:** a "Comms" nav slot (per run).
- **Note:** **parked** — request as the next major workstream once un-parked; it's the biggest functional gap the moment suppliers are in the loop.

### A5 · Sign-off / approver gate (G-D)  — Tier 2
- **Purpose:** an author≠approver sign-off before an award/run is "official," distinct from the freeze assertion.
- **Key elements:** a sign-off queue, the approver's named assertion, a `SIGNED_OFF` event, the portfolio savings roll-up (E-22).
- **Access point:** a "Sign-off" step after Awards / before close-out.

### A6 · Settings / Admin / Users / Roles (G-C, G-J)  — Tier 2
- **Purpose:** user management + RBAC roles (today the role label is cosmetic, no enforcement) + the eventual tenant boundary.
- **Key elements:** users list, role assignment, the permission matrix; (later) tenant scoping.
- **Access point:** a top-level "Settings/Admin" area.

### A7 · Supplier management / participant selection (E-34)  — Tier 2
- **Purpose:** a shared supplier master (import/upsert) + per-RFP selection of participating suppliers by category.
- **Key elements:** supplier master list + importer (dedup / fuzzy-identity), per-cycle participant picker by category.
- **Access point:** a "Suppliers" area (master) + a step in Cycle Setup (participant pick).

---

## B. VISUALS / elements to produce (beyond whole screens)

### B1 · The 3 baseline tweaks (auditor round 2 — finishes the locked screens)
- Compact-width **status-strip** short labels (Live / Sealed v1 / Not frozen / Current — no clipping).
- **"Hash-chain current" drill-through** to the latest audit event (actor / time / type / artifact / prior-hash).
- **Refresh the stale Awards screenshot** (verified not a live defect — export lag).

### B2 · Non-happy-path states for the NEW screens
Empty / loading / error / read-only(historic) for A1–A7 — the handoff already sets the pattern for the
6 shipped screens; extend it to each new surface (esp. Setup's pre-ingest and Comms' per-supplier states).

### B3 · Visualizations
- **Scenario-level capacity feasibility** badge/treatment ("Feasible" / "Exceeds in X cells") — beyond the per-row "Over capacity" count.
- **Version compare (E-43)** — the two-up "same tables, version-selector per pane" + the ROUND/FINAL marker + the alignment-meeting + date label on each locked version.
- **Deep-workbench charts (E-41)** — the diligence-tab visuals (supplier comparison, lowest-cost, coverage, scoring, landed, share, incumbent, negotiation) for the in-app workbench.
- **Price-movement / timeframe-discovery (E-35)** — the per-period direction table + histogram (later).

### B4 · Iconography / status language
- The **Closed / finalized** run state (run-status strip + Awards).
- Consistent treatment for the run-status strip's four states and the `CLOSED`/`SIGNED_OFF` events in the audit trail.

### B5 · Interaction-correctness rules (cross-cutting — "those sort of things")
Apply to **every** data table / rollup (Alignment comparison, supplier comparison, the diligence
tabs, awards, post-award). A **living list** — add as more surface; the spirit is *what you see is
what's counted, never a stale full-table number.*
- **Totals follow the filter** — when a table is filtered (DC / lot / supplier / TF), the totals,
  subtotals, counts, %, and any rollup below reflect the **filtered set**, not the full table.
  *(Sponsor's example.)*
- **Percentages recompute against the filtered denominator** — supplier share, savings %, coverage %
  recompute over the visible scope, not the full-table base.
- **Sort preserves the locked grouping** — sorting orders rows *within* the DC primary grouping (per
  the Handoff DataTable note); it never breaks the grouping.
- **Empty filter → empty state, not a stale total** — a filter that yields no rows shows an empty
  state; totals read 0 / "—", never the last full-table number.
- **Selection reflects in the summary** — when cells are selected (e.g. the post-award reprice
  picker), the running summary/impact reflects the selection, not the whole award.
- **Drill / expand stays consistent** — counts and totals reconcile across grains (cell ↔ lot ↔ DC ↔
  portfolio) when expanding/collapsing.

### B6 · Grain by surface (per-period vs timeframe) — UX behaviors to establish (D42)
Prices are stored flat at 13 periods, but the engine/awards are **timeframe-grain** (D38/D42). The
grain you SHOW (and CREATE records at) depends on the surface — **per-period on three surfaces, timeframe
everywhere else:**
- **Collection (bid template / intake):** **FOB by period + freight by period** (the 13), **all other
  costs yearly** (one value). Fan-in at the period grain for FOB/freight only.
- **Record creation (per-period):** when records are **created/entered** — the bid template the supplier
  fills + any manual per-period data entry — the inputs are at **period grain** (the records are born at 13).
- **Period-movement / timeframe-discovery display** (E-35) + the **timeframe build / regroup** UX:
  **per-period** grain (the curves, ▲/▼ movement, histogram, the period→timeframe grouping).
- **Analysis data tables · scenarios · awards:** **timeframe-grain only** (the roll-up the engine
  reads) — **never per-period in these tables.**
- This tracks the ingestion **fan-in / fan-out**: collect + create + store per-period → roll up to
  timeframe for the tables/engine → expand to per-period only for collection, record creation, and movement.

---

## C. MIDPOINTS — reconciliation-step surfaces (the "middle steps" no screen owns)

These are the human-facing **resolution surfaces** for the in-between mappings between grains &
systems (see `DATA_AND_PROCESS_MAP.md` seams + `RECONCILIATION_SEAMS.md`). They're where real data
silently breaks, and no lifecycle screen owns them — so each needs a design. **One pattern for all:
propose → human confirms/corrects → sticky; never guess silently.** Calm by default; surface only when
a reconciliation needs attention.

- **M1 · Editable column mapper** (= A3) — messy-file column→field override + ambiguity resolution.
- **M2 · Lot/item ↔ SKU mapping (sticky)** — propose the item→lot grouping and the **lot→iTrade-SKU**
  links (one lot → *many* SKUs), human confirms, the map **sticks across cycles** (E-11). This is the
  headline midpoint: it's the prerequisite for real STLY, contracted-vs-effective (E-28), and
  price-discovery (E-35). Same confidence/propose treatment as the column mapper.
- **M3 · Supplier / DC identity resolution** — when an incoming supplier/DC name doesn't cleanly match
  the master: match-to-existing / merge / create-new (dedup), so identities don't silently fork (E-34).
- **M4 · Unit / pack-size reconciliation** — when a feed/file quotes a different unit or pack than the
  RFP ("/lb vs /case"), a normalization-confirm so the numbers line up (today an unflagged mismatch).
- **M5 · Ingest exception / quarantine resolution** — the fix-and-retry surface for quarantined rows
  (setup AND bids): the row, the reason (key mismatch / bad number / missing field), and a resolve
  action. Extend the Bid Intake exception queue into a resolution workflow, and add the setup side.
- **M6 · Date → timeframe/period reconciliation** — when timeframe dates are missing/ambiguous, a
  confirm step instead of silent fabrication (the month-13 fallback risk).

---

## Recommended request order
1. **A1 Cycle Setup / Strategy** (the live-path hole) + **B1** (the 3 tweaks — cheap, finishes the baseline).
2. **A2 Finalize / Close-out** (backend is built — design the UI to match).
3. **A3 editable mapper** (only if messy supplier sheets will be accepted).
4. **A4 Comms (E-37)** — the next major surface when un-parked.
5. **Tier 2 (A5/A6/A7)** before a second operator / production.
B2–B4 ride along with whichever screens they belong to.
**Midpoints (§C):** **M1** (editable mapper) + **M5** (quarantine resolution) ride with intake; **M2**
(lot↔SKU sticky map) + **M3/M4** land with the iTrade feed (E-08/E-11) but should be designed now so
the pattern is consistent; **M6** rides with A1 (Cycle Setup).
