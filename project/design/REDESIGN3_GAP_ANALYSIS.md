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

> **SPONSOR DECISION (2026-06-22): E-44 design stays PARKED.** Do **not** send the two E-44 gaps (the
> A1 modality picker + cost-line manager, and the B6 mixed-grain breakdown) to the designer now —
> revisit the design when E-44 is scheduled to build. Punch-list item 1 is therefore **deferred**; only
> the minor cleanup (items 3 / stale screenshots + freeze re-shoot) remains as designer feedback, low
> priority. A4 Comms stays parked. Redesign3's non-E-44 set is on-baseline and build-ready when needed.

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

---

## 5. Entry-points pass

> **Scope:** §1–§4 reviewed each screen's **content**. This pass reviews **navigation / access** — can a
> user actually *reach* each surface and action, and what entry points are **missing**? Read-and-assess
> only; no frontend code changed. Sources: the Redesign3 sidebars/breadcrumbs/in-screen links
> (`project/design/redesign3/*.dc.html`), the built `frontend/components/shell/AppShell.tsx`, the routes
> under `frontend/app/`, and the "Access point" line in each `DESIGN_REQUESTS.md` brief.

### How the Redesign3 IA is actually wired (the key finding)

The sidebar is **two stacked nav groups** — a top **"Sourcing"** group (global) and, below a divider, a
**run-scoped** group titled with the run name ("Field Tomatoes"). But the groups are **hard-coded per
screen and are NOT consistent** — a surface generally appears only in *its own* file's sidebar plus a few
neighbors:

| Screen file | "Sourcing" (top) group | Run-scoped group |
|---|---|---|
| `Dashboard` / `Run Detail` | **Runs** only | Overview · Intake · Alignment · Awards — *(no Setup, Sign-off, Reconciliation)* |
| `Cycle Setup` | Runs | **Setup** · Overview · Intake · Alignment · Awards |
| `Bid Intake` / `Awards` | Runs | Overview · Intake · Alignment · Awards |
| `Reconciliation` | Runs | Setup · Intake · **Reconciliation** · Alignment · Awards *(no Overview, no Sign-off)* |
| `Sign-off` | Runs | Setup · Intake · Reconciliation · Alignment · Awards · **Sign-off** *(no Overview)* |
| `Suppliers` / `Settings` | Runs · **Suppliers** · **Settings** | *(none — global screens)* |

So the IA the designer *intends* is: **global** = Runs / Suppliers / Settings; **run-scoped tabs** = Setup ·
Overview · Intake · Reconciliation · Alignment · Awards · Sign-off. But **no single sidebar shows that full
set** — each file only self-links plus partial neighbors. Critically, the **hub a user lands on (`Run Detail`)
omits Setup, Reconciliation, and Sign-off from its run-scoped tabs**, so in click-through those three are
reachable only by already being on a sibling page that happens to list them. Breadcrumb is uniform
(`Runs / <commodity> / <screen>`), but breadcrumbs only go *up*, never *across*.

### 5.1 Surface / action → access-point table

Legend: **R3 nav** = does a Redesign3 nav slot / run tab / per-row action reach it? · **Built** = present in
the shipped console (`AppShell` + `frontend/app/` routes)?

| Surface / action | Intended access point (DESIGN_REQUESTS) | In R3 nav/IA? | In BUILT console? | Verdict |
|---|---|---|---|---|
| **Cycle Setup** (A1) | "Overview" nav slot **or** a "Setup" tab on Run Detail | **partial** — a "Setup" run-tab exists, but **only on Cycle Setup / Recon / Sign-off**; **absent from Run Detail & Dashboard**, so unreachable from the landing hub | **no route** (`/runs/[slug]/setup` missing; minimal A1 lives inline as `StrategyPanel` on Run Detail) | **orphaned (from hub)** |
| **Bid Intake** (A3/M1/M5) | Bid Intake → flexible import → mapping step | yes — "Intake" run-tab on every run screen | yes — `/runs/[slug]/intake` + "Bid intake" Next-step | **reachable** |
| **Alignment** (B5/B6) | (workbench, run-scoped) | yes — "Alignment" run-tab everywhere | yes — `/runs/[slug]/alignment` | **reachable** |
| **Awards / Finalize** (A2) | Awards screen + run-status "Closed" | yes — "Awards" run-tab everywhere | yes — `/runs/[slug]/awards` | **reachable** |
| **Sign-off** (A5) | a "Sign-off" **step after Awards / before close-out** | **weak** — "Sign-off" tab appears **only in `Sign-off.dc.html`'s own sidebar**; **no Awards→Sign-off link**, not on Run Detail | **no route, no nav** | **orphaned** |
| **Settings / Admin** (A6) | top-level "Settings/Admin" area | yes — global "Settings" slot (on Suppliers/Settings sidebars) | **no route, no nav** | **reachable in R3 / missing in build** |
| **Suppliers** (A7) | a "Suppliers" area (master) **+ a step in Cycle Setup** | **partial** — global "Suppliers" slot exists; **the Cycle-Setup participant-pick step / link is not wired** | **no route, no nav** | **reachable (global) in R3 / missing in build** |
| **Reconciliation** (M2/M3/M4) | rides with iTrade feed / Cycle Setup (no own brief slot) | **weak** — "Reconciliation" run-tab appears only on Recon & Sign-off sidebars; **not on Run Detail/Intake/Awards** | **no route, no nav** | **orphaned (from hub)** |
| **finalize** (action) | "Finalize & close run" on Awards | yes — button on `Awards.dc.html` (`openFinalize`) | partial — Awards page exists; action TBD | **reachable** |
| **freeze** (action) | Freeze on Alignment | yes — "Freeze award" on `Alignment` (`openFreeze`) | yes (Alignment) | **reachable** |
| **record-adjustment** (action) | post-award on Awards | yes — "Record adjustment" on `Awards` (`openAdjust`) | partial (Awards) | **reachable** |
| **generate template** (action) | gated button on Cycle Setup | yes — "Generate templates →" on `Cycle Setup` | **no** (no Setup surface built) | **reachable in R3 only** |
| **run analysis** (action) | from Bid Intake | yes — "Run analysis →" link (Intake → Alignment) | n/a inline | **reachable** |
| **save-version / compare** (action) | within Alignment | yes — version toggle + "Compare two versions" on `Alignment`; sealed v0 via Freeze | partial | **reachable** |

> Note: all six **in-flow actions** are wired as **in-screen buttons** on the surface that owns them
> (freeze→Alignment, finalize/record-adjustment→Awards, generate-template→Cycle Setup, run-analysis→Intake,
> save-version→Alignment). None depends on a nav slot — so the action entry points are sound *as long as the
> owning surface itself is reachable.* The risk is entirely at the **surface** level, not the action level.

### 5.2 Orphaned surfaces (exist in R3, no reliable way in)

- **Cycle Setup (A1)** — *the front-of-funnel surface.* Has a "Setup" run-tab, but that tab is **missing from
  Run Detail and Dashboard** (the two screens a user actually lands on). There is **no per-row "Set up"
  action** on the Dashboard run list and **no "Setup" link in Run Detail's body** (Run Detail jumps straight
  to Intake/Alignment/Awards). Net: you can only reach Setup if you're *already* on Cycle Setup, Recon, or
  Sign-off. **Effectively orphaned from the entry hub.**
- **Sign-off (A5)** — **the worst case.** The brief says "a step *after Awards*," but **Awards has no
  Sign-off link** (Awards' run-tabs are Overview/Intake/Alignment/Awards). Sign-off appears **only in its own
  sidebar**. There is no governed hand-off from Awards/Freeze into the approver gate → a user who freezes an
  award has **no in-product path** to the sign-off queue. **True orphan.**
- **Reconciliation (M2/M3/M4)** — appears as a run-tab only on Recon's & Sign-off's own sidebars; **not on
  Run Detail, Intake, or Awards.** Since the seams *ride with* intake/iTrade, the natural entry is "attention
  needed → resolve," but **Run Detail's activity board and Intake do not surface a link into Reconciliation**
  (only Cycle Setup's quarantine row has a generic "Resolve" → Bid Intake, not → Reconciliation). **Orphaned
  from the hub.**
- **Settings / Suppliers** — **not orphaned within R3** (they live in the global "Sourcing" group on the
  Suppliers/Settings sidebars), but that group is only rendered on *those two* files — a user on a run screen
  doesn't see Suppliers/Settings in their sidebar at all, so cross-navigation to the global area from inside a
  run is **one-way-ish** (you can get to Runs, but the global Suppliers/Settings slots aren't present on
  run-scoped screens' top group). Minor IA inconsistency rather than a true orphan.
- **The Cycle-Setup participant-pick step (A7 half)** — the brief asks for Suppliers access **both** as a
  global area **and** as "a step in Cycle Setup." The global area exists; the **in-Setup participant-picker
  entry is not wired** (no link from Cycle Setup into the supplier picker). Half-covered.

### 5.3 BUILT vs DESIGNED nav gap (what the build must add)

The shipped `AppShell.tsx` has **exactly one nav item — "Runs"** (the `NAV` array has a single entry). Routes
that exist: `login`, `/` (dashboard/runs list), `/runs/[slug]`, `/runs/[slug]/intake`, `/runs/[slug]/alignment`,
`/runs/[slug]/awards`. Everything the redesign adds is **un-routed and un-navigated** today:

| New surface | Where it belongs | Build work needed |
|---|---|---|
| **Settings / Admin** (A6) | **top-level** nav slot (global) | add `Settings` to `AppShell` `NAV` + route `frontend/app/(app)/settings/` |
| **Suppliers** (A7) | **top-level** nav slot (global) | add `Suppliers` to `NAV` + route `frontend/app/(app)/suppliers/` |
| **Cycle Setup** (A1) | **run-scoped tab** (and/or per-run-row action on Dashboard) | route `frontend/app/(app)/runs/[slug]/setup/` + a run-scoped tab bar (none exists today — Run Detail uses ad-hoc "Next steps" buttons, not tabs) |
| **Reconciliation** (M2–M4) | **run-scoped tab** | route `frontend/app/(app)/runs/[slug]/reconciliation/` + tab + an "attention" entry from Intake/Run Detail |
| **Sign-off** (A5) | **run-scoped tab** *after* Awards + an Awards→Sign-off action | route `frontend/app/(app)/runs/[slug]/sign-off/` + tab + a hand-off button on Awards |
| (Comms A4) | run-scoped — **parked** | not now (D44 / parked) |

Structural note: the built console has **no run-scoped tab component at all** — it navigates run sub-pages via
the "Next steps" button stack and a back-breadcrumb on Run Detail. Redesign3 assumes a **persistent
run-scoped tab rail** (Setup·Overview·Intake·Recon·Alignment·Awards·Sign-off). That rail is the single
biggest *navigation* build item, separate from the per-surface page work.

### 5.4 Global IA — open questions / unclear

- **Is the run-scoped tab set canonical?** The designer's files imply a 7-tab run rail, but no two sidebars
  agree on it. The designer should pin **one** ordered run-tab set and render it identically on every
  run-scoped screen (incl. Run Detail), so Setup / Reconciliation / Sign-off aren't dependent on which sibling
  you came from.
- **Global Suppliers/Settings vs run scope:** Suppliers is meant to be **both** global (master) and a
  per-run step (participant pick). The global half is shown; the **per-run entry is unwired** — clarify the
  two access points and how they relate (does the Cycle-Setup picker deep-link into the global Suppliers area
  filtered to the cycle, or is it an embedded step?).
- **Reconciliation: run-scoped or global?** It's drawn as a run-tab (run-scoped), which fits the seams, but
  the brief frames the midpoints as "ride with intake / iTrade feed." Confirm it's run-scoped, and decide the
  **trigger**: how does a user *learn* a seam needs attention and get there — an attention badge on the
  Run Detail activity board / Intake ("N reconciliations need attention → Reconciliation") is the missing
  entry. Today only Cycle Setup's quarantine row has a "Resolve" link, and it points at **Bid Intake**, not
  Reconciliation.
- **How do you reach a midpoint (M1–M6) when a seam needs attention?** The §1 review confirmed M1/M5 live in
  Intake, M2/M3/M4 in Reconciliation, M6 in Cycle Setup — but there is **no global "attention" surface** that
  routes a user *to the right midpoint*. The nav has an "open-seam counter" badge concept (noted in §2) but
  it isn't wired to a destination on the hub screens.
- **Sign-off ordering:** if Sign-off is "after Awards / before close-out," the **finalize** action on Awards
  should arguably be **gated behind Sign-off** (author≠approver) — but the two surfaces have no link between
  them, so the governance sequence isn't expressed in the navigation.
