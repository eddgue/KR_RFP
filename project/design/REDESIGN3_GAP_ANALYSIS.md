---
doc: Redesign3 gap analysis — design review against the recorded requirements
id: PM-007-DR-GAP
version: 1.0
status: Design review — read-and-assess (no frontend code edited)
created: 2026-06-22
reviews: project/design/redesign3/ (the designer's Redesign3 deliverable)
against: project/design/DESIGN_REQUESTS.md (§A/§B/§C), project/design/DESIGN_PACKAGE.md, project/03_DECISION_LOG.md (D42/D43/D44)
---

# Redesign3 — gap analysis

Reviewing the designer's **Redesign3** deliverable (`project/design/redesign3/`) against the requested
screens (§A), visuals (§B), midpoints (§C), and decisions **D42 / D43 / D44**. Read-and-assess only —
no frontend code was changed.

**Headline:** the lifecycle screens are almost all here and on-baseline (A1 setup, A2 finalize, A5
sign-off, A6 settings, A7 suppliers, all six midpoints, the B1 corrections, the B5 filter rules). The
**two headline pricing items from D43/D42 are missing**: (1) Cycle Setup has **no pricing basis at all** —
no modality picker, no cost-line manager; (2) the Alignment "Landed" view is a **flat stacked cost
build-up**, not the mixed-grain horizontal/chronological breakdown B6 specifies. A4 Comms is absent
(parked, expected).

---

## 1. Coverage table

### Screens (A1–A7)

| Req | Screen | In Redesign3? | Matches spec? — notes |
|---|---|---|---|
| **A1** | Cycle Setup / Strategy | **partial** | `Cycle Setup.dc.html`. Scope read-back, M6 timeframe-confirm, **strategy panel** (weight preset + 5 weights live-sum, 4 safeties — ceiling/floor/conc cap/max-sup, supplier treatment, lenses), pre-ingest empty state, quarantine surface, gated "Generate templates" — all present and good. **MISSING the entire D43 pricing basis** — no FOB/DELIVERED/XDOC modality picker, no cost-line manager. See §2. |
| **A2** | Finalize / Close-out | **yes** | `Awards.dc.html` — close-out card, "Finalize & close run" → finalize/assert modal, `CLOSED` state, pre-close checklist gate, won + rejection **notices as drafts** (draft→SENT note), read-only-after-close. Matches the brief; backend-aligned. |
| **A3** | Editable column mapper | **yes** | `Bid Intake.dc.html` — field `<select>` per column, ambiguous flag (amber dot), confidence column, resolve hint. (= midpoint M1.) |
| **A4** | Supplier comms (E-37) | **no** | No comms/touchpoint surface anywhere (grep: no match). **Expected** — parked per the brief; flag as the standing functional gap once un-parked. |
| **A5** | Sign-off / approver gate | **yes** | `Sign-off.dc.html` — sign-off queue, **author≠approver enforced** ("Author · can't self-sign"), approver assert modal → `SIGNED_OFF` event, approver note. Matches G-D. (Portfolio savings roll-up E-22 not obviously surfaced — minor.) |
| **A6** | Settings / Admin / Users / Roles | **yes** | `Settings.dc.html` — users list + invite, role assignment, **permission matrix**, "roles are enforced, not cosmetic," tenant section marked (later). Matches G-C/G-J. |
| **A7** | Supplier mgmt / participant selection | **yes** | `Suppliers.dc.html` — supplier **master** (`ref.supplier`) + **importer** (upsert / identity-resolve), per-cycle **participant picker by category**. Matches E-34. |

### Midpoints (M1–M6) — pattern: propose → confirm → sticky

| Req | Midpoint | In Redesign3? | Where / notes |
|---|---|---|---|
| **M1** | Editable column mapper | **yes** | `Bid Intake.dc.html` — field dropdown + ambiguity + confidence (= A3). |
| **M2** | Lot/item ↔ SKU (sticky) | **yes** | `Reconciliation.dc.html` — lot → iTrade-SKU (1→many), PROPOSED vs CONFIRMED chips, "Confirmed · sticky," add-SKU. The headline midpoint, done well. |
| **M3** | Supplier / DC identity | **yes** | `Reconciliation.dc.html` — match-to-existing / merge / create-new, dedup language, sticky binding. |
| **M4** | Unit / pack-size | **yes** | `Reconciliation.dc.html` — quoted-unit → conversion factor, "Normalized," unconverted line quarantined (feeds `construct_price_from_parts`). |
| **M5** | Ingest exception / quarantine | **yes** | `Bid Intake.dc.html` — exception queue, quarantined-row reason (wrong template / missing capacity), **fix-and-retry** resolution. Also the setup-side quarantine surface on Cycle Setup. |
| **M6** | Date → timeframe/period | **yes** | `Cycle Setup.dc.html` — "Confirm timeframe dates · M6 — inferred until you confirm (no silent month-13 fallback)." Rides with A1 as recommended. |

> Note on **placement**: the dedicated `Reconciliation.dc.html` surface carries only **M2/M3/M4** (the iTrade-feed seams); **M1/M5** live in Bid Intake and **M6** lives in Cycle Setup. All six are covered — just distributed across the surfaces they ride with, which is consistent with the §C "design alongside the screen they ride with" guidance.

### Key visuals (B1 / B5 / B6)

| Req | Visual | In Redesign3? | Notes |
|---|---|---|---|
| **B1** | Compact status-strip short labels | **yes** | `.rs-full`/`.rs-min` + `@media (max-width:1240px)` short labels ("Sealed v1 · Not frozen · Current · Closed · Live") on Awards **and** Alignment, with `text-overflow:ellipsis` fallback. *Caveat:* the `freeze-fixed.png` screenshot still shows clipping ("Live · Roun…", "Hash-chain curr…") — a capture artifact / pre-fix render; the HTML fix is in place. Re-shoot the screenshot. |
| **B1** | "Hash-chain current" drill-through | **yes** | `Awards.dc.html` — clickable → "Latest audit event" popover (Actor / Timestamp / Prior hash). |
| **B1** | Refresh stale Awards screenshot | **partial** | The clean Awards renders are present (`finalize.png`, `exq.png`). **But the stale error screenshot is STILL in the folder** — `screenshots/01-adj.png` (and its byte-identical 02-/03-adj copies) shows `Awards.renderVals(): … c.demand is undefined`. Delete/replace those. |
| **B5** | Totals-follow-the-filter / selection-reflects-summary | **yes** | `Alignment Workspace.dc.html` — filter popover (DC/lot/supplier); `matrixFooter` flips to "Subtotal · filtered" + "X of Y cells shown" and recomputes spend/cases over `visCells` (the filtered set). Custom (F) lens recomputes spend/savings/cautions live off per-cell overrides (selection-reflects-summary). Sort keeps DC as the locked primary grouping. Strong. |
| **B6** | Mixed-grain analysis cost breakdown | **no** | The Alignment "Landed & hidden costs" view is a **flat, single-grain, stacked build-up** (FOB + delivery + cooling = all-in), explicitly placeholder. This is the layout B6/D43 say **not** to use. See §2. |

---

## 2. Deep checks on the headline items

### A1 — Cycle Setup: strategy config present, **D43 pricing basis entirely missing**

**Present (and good)** in `Cycle Setup.dc.html`:
- Ingested **scope read-back** (DCs · lots · items · timeframes · invited suppliers · volumes), READ-BACK tag.
- **Strategy panel** — weight **preset** (Balanced/Price/Coverage/Risk-averse/Custom) + **5 live weights** with a running Σ; **the 4 safeties** (Premium ceiling %, Coverage floor ×, Concentration cap %, Max suppliers/DC); supplier treatment (preferred/exclude); lenses to run.
- **M6** timeframe-date confirm; pre-ingest empty state; quarantined-rows surface; gated "Generate templates" with a readiness note.

**MISSING — the whole D43 pricing basis** (grep for `modality|FOB|DELIVERED|XDOC|cost.line|RPC|basis|pricing` in Cycle Setup → **zero matches**):
- ❌ **Modality picker (FOB / DELIVERED / XDOC)** — not present. D43 requires it **per lot / per DC** (a per-scope attribute, not one-per-cycle), with the consequence made legible ("awards decided on a DELIVERED basis") and the allocation-filter framing.
- ❌ **Cost-line manager** — not present. None of: toggle a line on/off (e.g. **RPCs**), add a line, per-line **sign** (add/subtract), per-line **grain** (period/timeframe/yearly per D42), per-line **unit ($/case vs %)**, the **per-line %-base** (a multi-select of one-or-many other lines + apply-order).
- ❌ **Discounts as subtract-lines** with a **buyer-selected base** of one-or-many cost lines.
- ❌ The **link to the template columns** ("changing the active set changes the columns suppliers fill").
- ❌ The pricing-basis states (modality-unset-blocks-templates; line-toggled-off greyed; percent-line-needs-base flag).

This is the **single biggest gap** — A1 was the "top ask," and the pricing basis is the half of A1 that D43 added. The strategy half landed; the pricing-basis half is absent.

> **Live-test note (D44):** D43/D42 are scoped as **E-44** and are explicitly **enhancements, NOT in the first live test** unless the sponsor rules a piece vital. So this gap **does not block the live test** (which runs on the current fixed price model that already matches the manual potato cost lines). It is the top **design** gap, not a live-path blocker. Worth confirming the designer was told E-44 is design-now / build-later, vs descoped.

### B6 / Alignment — mixed-grain breakdown: **not built to spec**

The B6 / D43 requirement: each cost component **at its own grain**, laid out **horizontally + chronologically** — period columns left→right, a **per-period "total landed"** column, and a **toggleable "timeframe-total"** column; per-period components fill the period columns, timeframe/yearly components show against the timeframe-total; **each component's grain labeled**; scored price/awards stay timeframe-grain.

What's in `Alignment Workspace.dc.html` "Landed & hidden costs" view (the `view === 'landed'` table):
- Columns: `Lot · DC · Region · Supplier · FOB · +Delivery · +Cooling · All-in · Freight% · Transit`.
- This is a **flat, stacked, single-grain cost build-up** (FOB + delivery + cooling → all-in) — the exact "stacked, one grain" layout B6 says to avoid.

Gaps vs spec:
- ❌ No **period columns** running chronologically left→right.
- ❌ No **per-period "total landed"** column; ❌ no **toggleable "timeframe-total"** column.
- ❌ No **mixed grain** — every component is shown at one undifferentiated grain; ❌ no per-component **grain labels** (e.g. RPC@timeframe, FOB@timeframe, delivery@period).
- ❌ No **RPC** line; delivery/cooling are explicitly "placeholders in this demo cycle."
- ✅ Scored price / scenarios / awards **do** stay timeframe-grain (13-week horizon) — that invariant is honored elsewhere.

Verdict: the *placeholder* of a landed-cost view exists, but the **defining mechanic of B6** (mixed grain, horizontal/chronological, the timeframe-total toggle) is absent.

### Reconciliation — midpoints & pattern

- **Coverage:** M2 + M3 + M4 on `Reconciliation.dc.html`; **M1 + M5** on Bid Intake; **M6** on Cycle Setup. All six covered.
- **Pattern:** the **propose → confirm → sticky** doctrine is explicit and consistent — PROPOSED vs CONFIRMED chips, "Confirmed · sticky," "Nothing crosses a boundary by inference," quarantine-not-guess on M4/M5. Open-seam counter in the nav badge. Calm-by-default, surfaces on attention. Matches the §C pattern well.
- **Minor:** the iTrade feed is shown **dormant (E-08)** — M2's lot↔SKU reads "pending" until the feed lands, which is correct framing.

### B1 — the 3 corrections

- ✅ **Compact short labels** — implemented in CSS on Awards + Alignment (see table). One caveat: re-shoot `freeze-fixed.png`, which still shows clipping.
- ✅ **Hash-chain drill-through** — Awards "Latest audit event" popover (Actor/Timestamp/Prior hash). Meets the ask (the brief also lists type/affected-artifact; popover shows actor/time/prior-hash — close, could add event-type + artifact for completeness).
- ⚠️ **Refresh stale Awards screenshot** — clean renders exist, but the **stale error PNG is still in the folder** (`screenshots/01-adj.png` + identical `02-adj`/`03-adj`). Remove them so the deliverable doesn't ship the defect image.

### B5 — interaction-correctness

Strong, concrete evidence in Alignment (`passCell`/`passSup` filters, `matrixFooter` filtered subtotal + "X of Y cells," live Custom recompute, DC-locked sort). This is the best-realized of the cross-cutting rules. (Whether the *other* tables — supplier comparison, diligence tabs, share/coverage — each re-derive their %/denominators over the filtered set should be spot-checked, but the spine is there.)

---

## 3. Missing / not-yet-designed · and ADDED beyond spec

**Missing or incomplete:**
- **D43 pricing basis on A1** — modality picker + cost-line manager (the #1 gap; §2).
- **B6 mixed-grain breakdown** — the horizontal/chronological, per-period + timeframe-total-toggle, per-component-grain table (the #2 gap; §2).
- **A4 Supplier comms (E-37)** — entirely absent. Expected (parked), but it remains the biggest functional hole once suppliers are in the loop.
- **Stale screenshot still shipped** — `01/02/03-adj.png` carry the old `c.demand is undefined` error.
- **Minor:** E-22 portfolio savings roll-up on Sign-off; audit popover could carry event-type + affected-artifact (B1 spec lists them).

**Added beyond what we spec'd (note, not necessarily wrong):**
- **Sign-off `Round 0 / wrong-template` and `missing Capacity tab (E-38)` exception types** in Bid Intake's M5 queue — a richer, sensible exception taxonomy.
- **A diligence-tab set on Alignment** beyond the asked views — supplier / lowest-cost / coverage / detailed scoring / landed / share / incumbent / negotiation (eight views). This is aligned with E-41 direction (B3) and welcome, though it's ahead of what §A strictly requested. The **column-group collapse toggle** (scoring/landed "show/hide cost build-up") is a nice manipulability touch (D27).
- **Version-compare two-up** scaffolding (E-43 / B3) appears in Alignment — good forward motion.

---

## 4. Prioritized punch-list

**Tell the designer to ADD / FIX (in priority order):**
1. **A1 — add the D43 pricing basis** (top): the **modality picker (FOB/DELIVERED/XDOC), per lot/DC**, with the legible "awards decided on X basis" consequence; and the **cost-line manager** — toggle/add lines, per-line sign · grain · unit ($/%) · the %-base multi-select + apply-order; **discounts** as subtract-lines with a buyer-selected one-or-many base; and the **template-column link** + the pricing-basis states. *(Confirm with the sponsor first whether E-44 is design-now-build-later or descoped under D44.)*
2. **B6 — rebuild the Alignment "Landed" view** as the **mixed-grain, horizontal/chronological** breakdown: period columns left→right, per-period **total-landed** column, **toggleable timeframe-total** column, per-component **grain labels**, and **RPC** as a first-class line. (Scored price/award stays timeframe-grain — already correct.)
3. **B1 cleanup** — delete/replace the stale `01/02/03-adj.png` error screenshots; re-shoot `freeze-fixed.png` at the compact width so it shows the short labels (the CSS fix is already in). Optionally add event-type + affected-artifact to the audit popover.
4. **A4 Comms** — keep parked; schedule as the next major surface when un-parked (do not build into the live path under D44).
5. **Minor** — surface E-22 portfolio savings roll-up on Sign-off; spot-check B5 (filtered %/denominators) on the supplier/coverage/share diligence tabs.

**Ready to build (matches spec, on-baseline):**
- **A2 Finalize/Close-out**, **A5 Sign-off**, **A6 Settings/Admin/Roles**, **A7 Suppliers (master + importer + participant picker)**.
- **All six midpoints M1–M6** (propose→confirm→sticky).
- **A1 strategy half** (preset/weights/safeties/suppliers/lenses) and **M6**.
- **B1 status-strip short labels + hash-chain drill-through**, **B5 totals-follow-the-filter** on Alignment.

**Net:** Redesign3 closes nearly the whole lifecycle/midpoint/governance set on-baseline and is largely build-ready; the two outstanding gaps are both **E-44 (D43/D42) pricing items** — the A1 pricing basis and the B6 mixed-grain breakdown — which per **D44** are enhancements outside the first live test. A4 Comms stays parked.
