---
doc: Reconciliation seams — the "in-between spaces" register
id: PM-SEAMS
version: 1.0
status: Living watch-list — the mapping/reconciliation seams between grains & systems (sponsor, 2026-06-22)
relates: PM-004 (backlog), PM-007 (As-Built); E-08/E-09 (feeds), E-11 (lots), E-28 (analytics), E-34 (suppliers), E-35 (discovery), E-39 (formulas)
created: 2026-06-22
---

# Reconciliation seams — the "in-between spaces"

**Why this exists (sponsor):** the places where one representation must be reconciled/mapped to
another — across **grains** (lot ↔ item ↔ SKU ↔ period) and across **systems** (RFP ↔ iTrade ↔ KCMS ↔
supplier master) — are where real-data integration silently breaks, and they're easy to miss because
**no single screen owns them.** This is the watch-list: every seam, who owns it, and whether it's
handled. New seams get added here the moment they're spotted; nothing in an in-between space ships
"by inference" without a human-confirmable, sticky mapping.

## The seams

| Seam (from → to) | Cardinality | Status | Owner / epic | Note |
|---|---|:--:|---|---|
| Messy supplier columns → bid fields | n→1 | ◐ | **new** (editable mapper) | Infer + confirm exists; **no in-app override / ambiguity-resolution** (`confirm=true` re-applies the guess). Make the mapper editable; backend `apply_mapping` is already mapping-driven. Matters only if non-template sheets are accepted. |
| **RFP lot / item → unique iTrade SKU(s)** | **1→many** | ⬜ | **E-11 + E-08** | The headline seam. A lot ("Grape Tomatoes") spans many iTrade SKUs (pack/origin/size); must be **human-confirmed + sticky across cycles** (E-11) and depends on the iTrade receipt feed (E-08, dormant). **Prerequisite** for the real STLY baseline, contracted-vs-effective (E-28), and price-discovery (E-35). |
| Items → lots (the grouping itself) | many→1 | ◐ | E-11 | Today via the setup workbook (`cyc.cycle_lot_item`); no sticky/attribute-based propose-and-confirm regroup. |
| Supplier on a file → `ref.supplier` master | n→1 | ◐ | E-34 | Reused by natural key (D36 name match); **no dedup / fuzzy-identity / importer UI** — two like-named suppliers or name variants are a silent risk. |
| DC on a file → `ref.dc` master | n→1 | ◐ | E-34-adjacent | Natural-key reuse (D36); same name-variant risk as suppliers. |
| Setup dates → fiscal periods (timeframes) | 1→n | ◐ | deferred (#7) | The fabricated-date fallback breaks for >4 date-less timeframes (month-13). Product call: fabricate vs. require dates. |
| Prior award → current-cycle baseline (routing/STLY) | 1→1 | ◐ | E-08 / E-28 / D11 | Today a **synthetic STLY proxy** (incumbent × 1.04); swap for the real prior contracted/effective once iTrade lands. |
| **Units / pack-size** (cases ↔ weight ↔ pack) | — | ⬜ | **new** | **Likely unmodeled.** If iTrade or a supplier quotes a different unit/pack than the RFP, the numbers won't line up and nothing flags it. Needs an explicit unit/pack normalization at every cross-system join. |
| Currency | — | (watch) | — | Assumed single (USD); a seam the day a second currency appears. |
| Bid timeframe → flat-13 fiscal periods | 1→n | ✅ | G-A (done) | Fan-out wired; engine byte-identical. |
| Capacity statement → award cells | 1→1 | ✅ | E-38 (done) | Allocation vs stated ceiling, per dc×lot×tf. |
| Price basis (FOB / all-in / landed) → scored price | n→1 | ✅ | E-39 (done) | `construct_price_from_parts`, defined once, referenced everywhere. |
| **Routing modality (FOB / DELIVERED / XDOCK) → scored price** | n→1 | ◐ | **D43** | **Verified vs the manual potato model** (`MANUAL_MODEL_FINDINGS.md`): the manual's **"Routing"** = our modality; **XDOC = FOB + a supplier-stated VegCool XDOCK surcharge/case** (our `vegcool_surcharge`), via a named cross-dock — not a Kroger-second-leg split. Per lot/DC (D43). |
| **Discount unit: manual `%` ↔ our `$`** | 1→1 | ◐ | **D43 / E-44** | **✅ RESOLVED (2026-06-22):** a discount is a cost line (sign −) with a **buyer-selected base of one-or-many cost lines, set on setup**; unit `%` (preferred) or `$`. Engine: `−(pct × Σ selected base lines)`; adapter converts legacy `$`. `MANUAL_MODEL_FINDINGS.md` finding A. |
| **RPC cost impact (+/- $/case) → scored price** | 1→1 | ⬜ | **D43** | Real toggleable cost line in the manual (gated by "RPCs? Y/N"); **no distinct engine field** today (rides inside All-In). Add as a D43 cost line. `MANUAL_MODEL_FINDINGS.md` finding B. |

## Newly-surfaced gaps (not previously on any list)
1. **Editable column mapper** — override the inferred mapping + resolve ambiguities in-app (vs. confirm-only today). Contained backend change + an editable Bid Intake table.
2. **Unit / pack-size reconciliation** — an explicit normalization layer at every RFP↔external join; today a silent mismatch risk.

## Known-template adapter (planned — sponsor, 2026-06-22)

For the **manual-process templates the team controls**, the plan is a **deterministic Python parser**
that pulls from those templates and places the data onto **ours** — the right call (deterministic
parsing beats the flexible-ingest inference for known, stable formats; no guessing, no ambiguity).
The clean fit, to keep it governed:
- **Emit OUR key-stamped owned template** (the same `.xlsx` the app generates via
  `generate_template_bytes(scope)`), then **ingest via the existing STRICT key-validated path** — do
  NOT write to Postgres directly. This inherits key-validation, quarantine ("never guess"), and the
  `IMPORTED` audit events. A direct-to-DB parser bypasses all three.
- **Pure data-mover**: map cells/columns + **resolve identities to our keys** (lot/supplier/DC names
  → `ref.*` / cycle IDs). Let the engine/ingest compute; if the parser must build a price, call the
  canonical `construct_price_from_parts` (E-39) so it can't drift from the scorer.
- **Needs the cycle scope** (the keys) to stamp the template — flow: create run → setup ingested →
  pull scope → parser maps manual data onto the keyed template → strict ingest. It's a deterministic,
  hand-written `apply_mapping`.
- This adapter is the natural home for **two seams at once**: the column mapping (deterministic, for
  known templates) AND the lot/supplier/DC → our-keys identity mapping.

## Standing rule
When a new feature crosses a grain or a system boundary, add its seam here first and decide its
mapping (sticky? human-confirmed? unit-normalized?) **before** building — that's how the in-between
spaces stop being where it breaks.
