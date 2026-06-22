---
doc: Drift reconciliation — what the durable record CLAIMS vs what's actually in the repo
id: PM-DRIFT-RECON
status: Reconciliation (2026-06-22). Two read-only audits (backend/decisions + frontend/design),
        verified against code; folded with the data-fidelity findings. Grounded in opened files.
relates: CLAUDE.md, project/03_DECISION_LOG.md (D45), project/04_PROGRAM_BACKLOG.md,
         project/design/REDESIGN3_GAP_ANALYSIS.md
trigger: sponsor asked "how much has been lost?" after ~300 context compactions.
---

# How much has been lost? — reconciliation of the record vs the code

**Headline:** Across ~300 compactions, **almost nothing in the recorded core was lost** — because the
core lives on disk (schema, code, tests, decision log, backlog), not in context. The damage is
concentrated and enumerable: **one genuine data-fidelity violation, a handful of MVP-cuts I shipped
below the recorded bar, and a large but RECORDED backlog of not-yet-built perimeter.** "Lost" is the
wrong word for most of it; "not yet built (and recorded)" or "built below the bar (now enumerated)"
is accurate.

## The four categories

### A. TRULY LOST (knowledge/work gone) — ~0 (material)
The engine + governed-persistence spine is full-fidelity and tested: v3 5-factor banded scoring
(`engine/scoring.py`), 7 lenses A–G (`engine/allocation.py`), split allocation + cap-breach, sealed
reproducible runs with sha256 manifests (`runner.py:150-168`), freeze-and-layer immutability
(`awd/service.py`), the canonical formula registry (`engine/formulas.py`), flat-13 period storage
(migration 0014), key-validated ingest/quarantine, stateless render-on-request (`pilot/deliverables.py`),
savepoint/compare (E-43). Nothing of the core was silently dropped. The disk record held.

### B. BUILT BELOW THE RECORDED BAR — drift / violations (on me, fixable) — ~6
1. **🔴 Potato converter data-fidelity violation — `backend/scripts/potato_legacy_dryrun.py`.**
   The exact artifact D45 was written to condemn, still UNREPAIRED, and now wired into the Cloud
   Build seed (commits 32413af/dbbf071). Verbatim violations: single Delivered round only (drops the
   FOB/multi-round process, `:435`), 141 demand rows dropped (`:321-323`), regions flattened to a
   forced closed set unknown→"Central" (`:99-115`), Lot Name == raw Lot_ID (`:460`), values
   force-positived (`_as_positive`, `:145-154`). **This taints the very data the buyer reviews.** D45
   ordered it rebuilt faithfully BEFORE more console build; that order stands and is unmet.
2. **4 frontend MVP-cuts (violate D19/NO-MVP):** A1 Cycle Setup/Strategy (thin preset+4-safety panel,
   weights read-only, no scope read-back / lens select / supplier treatment / M6 confirm / generate
   gate; no `/setup` route); A3/M1 column mapper (confirm-only, not editable); M5 quarantine
   (surface-only, no fix-and-retry); Alignment depth (single matrix; missing the designed diligence
   tabs + B6 landed view + B5 filter-recompute on the workbench).
3. **Tenancy drift (D8):** decided "client_id on every row + RLS"; built as client_id on a couple of
   `ref` tables, **no RLS**. Single-operator-OK, real gap before multi-tenant/external use.
4. **2 write-points outside the audit hash-chain:** setup-ingest and capacity-ingest emit no event
   (the audit layer itself flags this).
5. (minor) `bid_line.fiscal_period_id` is `varchar(36)`, not `uuid`+FK (D38 acknowledged cleanup).
6. (minor) runner omits `all_lot_discount` when building `BidComponents` (`runner.py:300-306`) though
   the formula supports it — possible silent under-count on that leg; needs a check.

### C. RECORDED BUT NOT YET BUILT — deferred scope, NOT lost — ~13
Frontend (design surfaces with no route): **Sign-off (A5), Settings/Admin/RBAC UI (A6), Suppliers
(A7), Reconciliation M2/M3/M4, full Cycle Setup, Supplier-comms UI (A4 parked), run-scoped tab rail.**
Backend perimeter: **iTrade importer (E-08, table+view exist, nothing populates — so "vs STLY" runs on
a synthetic ×1.04 proxy), RBAC enforcement (rbac.py defined, zero routes call it), sign-off gate
(E-22, SIGNED_OFF enum never emitted), safety reprice + USDA market feed (E-29, 5 safety types stored,
never computed), PBA/contract builder (E-33, template only), KCMS (E-09), supplier scorecard (E-10),
comms SEND + 4/7 touchpoints unrouted (E-37).** All recorded in the backlog — deferred, not lost.

### D. LOOKS LOST BUT ISN'T — built-but-undocumented (recoverable by writing it down)
- Award / comms / freeze / savepoint capability lives in **`api/v1/runs.py` (23+ routes)**, NOT in the
  same-named domain routers. `awards.py`/`cycles.py`/`documents.py`/`ingest.py` are present-but-empty
  stub files — **dead files, not capability gaps** (except `ingest.py`, which genuinely has no feed).
- The two-runtime split (stateless console DB vs MCP harness file-vault) is real and deliberate.
- `construct_price_from_parts` unifies engine+ingester price math, fully tested.

## Tally
- Backend/engine/data (~30 decision/epic items reconciled): ~17 BUILT-faithful · ~6 PARTIAL · ~6
  NOT-BUILT · 1 DRIFTED (tenancy) · 3 in-tree stubs (off-path stub engine, 4 empty routers, the
  converter) · **1 active data-fidelity violation (converter)**.
- Frontend (18 designed surfaces): **7 faithful · 4 MVP-cut · 7 not built.** No mock/placeholder data
  anywhere in the built frontend — every number traces to a real backend call. The contract breach is
  SCOPE (MVP cuts), not faked data.

## Remediation order (per D45 + NO-MVP)
1. **Rebuild the potato converter faithfully** (all rounds, all volumes, real names/regions, no
   value-forcing, quarantine bad data) + a field-by-field mapping audit reconciled to the golden
   NUMBERS at each step. This is the one active violation and the data the buyer reviews. **First.**
2. Close the 4 frontend MVP-cuts to full fidelity and build the not-yet-built surfaces (full Setup,
   Suppliers, Sign-off, Settings/RBAC, Reconciliation) + the nav spine — each fully wired, no stubs.
3. Build the recorded backend perimeter to fidelity as scoped (RBAC enforcement, sign-off gate,
   iTrade importer, safety reprice+feed, PBA, comms send), and close the audit-write-point + tenancy
   drift.
4. Delete the dead empty routers (or fill them) so "looks lost" stops masquerading as a gap.

**Lesson (recorded, D45):** the 300 compactions did not cost the core because it was on disk. The cost
came where execution deviated from the disk record in real time (the converter, the MVP-cuts) — which
is exactly what the CLAUDE.md contract + agent-injection now guards against.
