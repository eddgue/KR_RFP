---
doc: Technical Specification
id: DOC-003
version: 1.0
status: Draft
created: 2026-06-17
last_updated: 2026-06-17
depends_on: DOC-001 (System Overview & ADRs), DOC-002 (Data Model)
---

# Technical Specification

The handoff document. It defines the components, how data moves, how the v3 engine plugs in, the service surface, and the order to build — backend before frontend. It should need no verbal explanation.

---

## Stack

| Layer | Choice | Rationale |
|---|---|---|
| Database | PostgreSQL 15+ | The original repo used SQLAlchemy/Alembic; the model needs real constraints, JSONB for run config, and immutability. |
| Backend | Python (FastAPI), SQLAlchemy 2.x, Alembic | Keeps the engine's language; lets the engine run in-process as a library. |
| Engine | `rfp_analysis_engine_v3` logic, refactored to a library | Lift the ~1/3 that is logic; drop the ~2/3 that is Excel formatting. |
| Ingestion | pandas + openpyxl importers | Same libraries the engine already uses. |
| Output rendering | Templated (xlsx via openpyxl, letters via the existing HTML templates) | Reuse the workflow package's templates. |
| Frontend | Deferred (ADR-001). A thin view over the API. | Built last. |

---

## Component Map

| Component | Type | Responsibility |
|---|---|---|
| **Schema / migrations** | DB | The store in `BUILD_03_schema.sql`, under Alembic. |
| **iTrade loader** | service | Land PO receipts into `perf.itrade_receipt`; flag-first validation; date-span sanity. |
| **KCMS loader** | service | Land scan movement into `perf.kcms_movement`. |
| **Normalizer** | service | Propose lot + attributes for each item; persist `norm.*`; expose a confirm action. |
| **Bid importer** | service | Map per-template bid files (tomato flat, onion 9-tab) to `bid.*`; auto-upsert suppliers. |
| **Distance calc** | service | Ship-from zip → DC distance via `ref.zip_centroid`. |
| **Scorecard builder** | service | Derive `perf.supplier_scorecard` snapshots from `perf.itrade_receipt`. |
| **Engine runner** | library | Read bids+config from the store, run scoring/allocation, write `analysis_run`/`bid_score`/`scenario`/`scenario_award`. |
| **Selection service** | service | Promote a chosen scenario to `awd.award`; apply per-cell human overrides. |
| **Freeze service** | service | Seal awards at sign-off; route later changes to `award_layer`. |
| **Document generator** | service | Render booking guide, sign-off deck, letters, confirmation email into `awd.generated_document`. |
| **Event logger** | cross-cutting | Append to `audit.event_log` on every state change. |
| **API** | service | The surface in this doc. |
| **UI** | frontend | Deferred. |

---

## Data Flow

1. **Reference load.** Commodities, subcommodities, DCs, fiscal calendar (to 2037), zip centroids → `ref.*`. One-time + incremental.
2. **History load.** iTrade receipts → `perf.itrade_receipt`. Powers the cost baseline and the scorecard. KCMS → `perf.kcms_movement`.
3. **Normalize.** New items → Normalizer proposes lot + attributes → human confirms → `norm.item_lot_map` (sticky).
4. **Cycle setup.** Kickoff declares the cycle → `cyc.cycle` + timeframes + rounds + scope + terms. Scorecard kickoff snapshot frozen.
5. **Bid round.** Generate templates → suppliers return files → Bid importer maps to `bid.*` (one grain), resolves items to lots, computes distance, flags completeness.
6. **Run.** Engine runner reads eligible bids + cycle config → writes a sealed `analysis_run`, per-bid `bid_score`, and `scenario` + `scenario_award` (split allocation) for lenses A–G.
7. **Review + select.** Human compares scenarios, overrides per cell → Selection service promotes the chosen scenario to `awd.award`.
8. **Loop.** Steps 5–7 repeat per round (variable count) until the final round.
9. **Sign-off.** Portfolio savings vs STLY computed → `awd.signoff`. On approval, Freeze service sets `award.frozen_at`; scorecard sign-off snapshot frozen.
10. **Generate.** Document generator renders booking guide, sign-off deck, award/no-award/feedback letters, confirmation email → `awd.generated_document`.
11. **Every step** appends to `audit.event_log`.

**Failure modes.** Bad bid template → importer quarantines the row with a reason, does not silently drop. Impossible iTrade dates → receipt flagged, excluded from age math. Unmapped item → bid lands but is held out of scoring until its lot is confirmed.

---

## Engine integration (how v3 plugs in)

The engine is lifted from the monolith into a library with a single entry point:

```
run(cycle_id, round_code, config) -> run_id
    reads:   bid.bid + bid.bid_price + volume_* for (cycle, round, active TFs),
             incumbent/historical cost from perf.itrade_receipt,
             config (weights, thresholds, max_sup_dc, conc_thresh) from the cycle/run
    computes: bid_score (5 banded factors -> rec_score), eligibility + gate_flags,
              scenarios A-G incl. max_two_per_dc split allocation
    writes:  eng.analysis_run (sealed, config_json), eng.bid_score,
             eng.scenario, eng.scenario_award
```

Required refactors (small, known): move the top-level `argparse` into the `run()` signature; replace file-read with store-read and workbook-write with table-write; keep the scoring math, the banding, and `max_two_per_dc` exactly as verified. The Excel output code is not ported; the Document generator replaces it.

---

## Governance model

- **Immutable runs.** `analysis_run.is_sealed` + `config_json`. No updates; re-run to correct.
- **Freeze-and-layer.** `award.frozen_at` seals; `award_layer` carries every later change, date-stamped.
- **No deletes.** Enforce at the app layer and with DB rules; supersede, never remove.
- **Event log.** Every create/seal/freeze/supersede/sign-off appends to `audit.event_log`.
- **Open last cycle.** A read over `cyc.cycle` joined through rounds → bids → runs → scenarios → awards, with the event trail. This is the capability the stateless engine cannot provide and the reason the store exists.

---

## API surface (representative, REST)

```
POST  /cycles                         create a cycle (setup file)
POST  /cycles/{id}/timeframes         add TF
POST  /cycles/{id}/rounds             add round
GET   /cycles/{id}                    full cycle view (open last cycle)
GET   /cycles?commodity=&status=      list / search cycles

POST  /itrade/import                  land receipts
POST  /kcms/import                    land scan movement

POST  /normalize/propose              propose lots for new items
POST  /normalize/confirm              confirm item->lot (sticky)

POST  /cycles/{id}/rounds/{r}/bids/import   import a bid file (template-aware)
GET   /cycles/{id}/rounds/{r}/bids           bids at one grain

POST  /cycles/{id}/rounds/{r}/run     run the engine -> run_id
GET   /runs/{id}/scenarios            scenarios + split awards
GET   /runs/{id}/scores               per-bid scores + gate flags

POST  /cycles/{id}/awards/select      promote a scenario (with overrides)
POST  /cycles/{id}/signoff            compute savings vs STLY, request approval
POST  /cycles/{id}/signoff/approve    seal awards (freeze)
POST  /cycles/{id}/documents/{type}   generate booking guide / deck / letters
```

---

## Build sequence (backend before frontend)

**Phase A — Data layer.** Stand up Postgres, apply `BUILD_03_schema.sql` under Alembic, wire the event logger. Load reference data + fiscal calendar + zip centroids. *Exit:* schema migrates clean; reference tables populated.

**Phase B — History + normalization.** iTrade loader + KCMS loader + Normalizer (propose/confirm) + Scorecard builder. *Exit:* a real iTrade pull lands; items propose lots; a human can confirm; scorecard snapshot computes.

**Phase C — Cycle + bids.** Cycle setup endpoints + Bid importer (both templates) + Distance calc. *Exit:* a cycle is created and a real round of bid files imports to one grain, items resolved to lots.

**Phase D — Engine.** Refactor v3 to `run()`; wire store-read/store-write; produce runs, scores, scenarios, split awards. *Exit:* a stored round runs and reproduces the verified scoring/allocation against a known input.

**Phase E — Awards + outputs.** Selection service + Freeze service + Document generator (booking guide, sign-off, letters). *Exit:* a chosen scenario becomes frozen awards; the booking guide and sign-off generate from records; savings vs STLY computes.

**Phase F — API hardening, then UI.** Finalize the API; only then build the frontend as a view onto it (ADR-001).

**Dependencies:** A → B → C → D → E → F. B and C can overlap once A is done. The UI does not start until E is proven.

---

## Open items carried from the intake

1. **Verify the live app's persistence before greenfield** (`_event_log.py`, `init_cycle.py`, the Streamlit data layer). If a store exists, reconcile to this schema instead of rebuilding.
2. **Attribute taxonomy** needs one confirmation pass per commodity (universal core + extensions) at onboarding.
3. **Prior-round price is lot-level** in the current engine (no DC). Fix at the source: capture DC-level prior pricing in `bid.*` so round-over-round deltas are DC-specific.
4. **Kickoff structure**: confirm one setup per RFP vs several structures inside one RFP.

---

## Changelog

| Version | Date | Author | Change Summary |
|---------|------|--------|----------------|
| 1.0 | 2026-06-17 | Session | Initial draft from intake sessions 1–6 |
