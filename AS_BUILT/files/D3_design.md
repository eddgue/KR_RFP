---
doc: AS-BUILT AUDIT — SLICE D3 · project/design/**  (canonical design docs + the redesign3 deliverable)
id: ASBUILT-D3-DESIGN
status: COMPLETE — read-only audit; no design/frontend code changed.
scope: /home/user/KR_RFP/project/design/**  (129 files, FILE_CENSUS rows #356–#484)
contract: /CLAUDE.md ABSOLUTE REQUIREMENTS honored; bar = AS_BUILT/AUDIT_STANDARD.md ("nothing skipped, every file, detailed WHY").
method: `find project/design -type f` (129) cross-checked 1:1 against FILE_CENSUS.md #356–#484 (129 rows) — exact match.
        Every .md read end-to-end. Every .dc.html surface named + mapped to build status. Every .png/.svg/.xlsx/.pdf described.
        Build status cross-referenced to REDESIGN3_GAP_ANALYSIS.md (§1 coverage table, §2 deep checks, §4 punch-list, §5 entry-points)
        and DATA_AND_PROCESS_MAP.md (DRIFT/decision/seam register). Byte-duplicate claims verified by md5sum/diff (recorded inline).
---

# SLICE D3 — project/design/** — exhaustive as-built audit

## 0. What this directory IS (the WHY of the whole slice)

`project/design/` is the **design system of record** for the frontend rebuild (epic **E-26**). It is NOT shipped product
code — it is the **visual source of truth to rebuild in Next.js + Tailwind, not merged** (stated verbatim in
DESIGN_PACKAGE.md §1, DESIGNER_PROMPT ground rules, DESIGN_REVIEW artifact note). The `.dc.html` files are interactive
HTML prototypes produced by an external "Claude Design" session; `support.js` is their shared runtime; the Kroger SVGs are
brand assets. The directory captures **three design iterations** plus the docs that drove and reviewed them:

1. **`first_draft/`** (2026-06-21 ~21:47) — draft 1: 6 screens. Reviewed in `DESIGN_REVIEW.md`; feedback in `DESIGN_FEEDBACK_v1.md`.
2. **`handoff/`** (2026-06-21 ~22:33) — v2, "feedback incorporated", the **LOCKED UI baseline** that E-26 was built against.
   Adds the `Handoff.dc.html` design-system page + a `Finalize/Close-out`. Feedback in `DESIGN_FEEDBACK_v2.md`; notes in `HANDOFF_NOTES.md`.
3. **`redesign3/`** (2026-06-22 ~10:44) — round 3: extends the locked baseline with the **missing lifecycle screens**
   (Cycle Setup, Reconciliation, Sign-off, Settings, Suppliers) + the 6 carried-forward baseline screens, plus a self-contained
   `uploads/` copy of the design package + the audit/review bundle that was handed to the designer, plus exported `screenshots/`.

The top-level `.md` files (DESIGN_REQUESTS / DESIGN_PACKAGE / DESIGNER_PROMPT / SCREEN_COVERAGE_AUDIT / REDESIGN3_GAP_ANALYSIS)
are the **canonical, current** design-program docs (the request → package → prompt → coverage-audit → gap-analysis chain).

**Why it exists / what breaks without it:** without this tree there is no spec for what the frontend must look like or which
surfaces must exist; the gap analysis is the authoritative "designed vs built" map that the build slices (frontend) are graded
against. It is also the home of the **decision-to-design traceability** for D42/D43/D44, E-26, E-37, E-40, E-41, E-43, E-44, G-C/G-D/G-I.

**Headline build-status finding (from REDESIGN3_GAP_ANALYSIS.md, corroborated by DATA_AND_PROCESS_MAP.md):**
- The **6 baseline screens are BUILT** in the Next.js console (E-26): Login · Dashboard · Run Detail · Bid Intake · Alignment · Awards.
- Redesign3's **net-new lifecycle/governance screens are DESIGNED but NOT BUILT** (no routes, no nav): Cycle Setup, Reconciliation,
  Sign-off, Settings, Suppliers — all "no route, no nav" in the shipped `AppShell.tsx` (which has exactly one nav item: "Runs").
- The **two D43/D42 (E-44) pricing items are NOT DESIGNED** (the #1 and #2 gaps): A1 pricing-basis (modality picker + cost-line
  manager) and B6 mixed-grain breakdown. Per **D44** these are enhancements outside the first live test, and per the SPONSOR
  DECISION banner atop REDESIGN3_GAP_ANALYSIS.md (2026-06-22) **E-44 design stays PARKED** — do not send those two gaps now.
- **A4 Supplier comms (E-37) is NOT DESIGNED anywhere** — deliberately PARKED.

---

## 1. File census reconciliation

`find project/design -type f` → **129 files**. FILE_CENSUS.md rows **#356–#484 = 129 rows**, all flagged `owned=y` except the
18 screenshot rows #418–#434 (17 redesign3 screenshots flagged `n` — counted, non-owned exports). 1:1 match, **zero unaccounted files**.
**Empty files: NONE** in this slice (every file in census has size > 0). Directory tree (18 dirs):

```
project/design/                                   (5 canonical .md at root)
├── first_draft/            (6 .dc.html + 2 .md + support.js)  └── assets/ (4 svg)
├── handoff/                (7 .dc.html + 3 .md + support.js)  └── assets/ (4 svg)
└── redesign3/              (12 .dc.html + .thumbnail + support.js)  ├── assets/ (4 svg)
    ├── drafts/             (1 .dc.html)  └── draft 2/ (12 .dc.html)
    ├── screenshots/        (17 .png)
    └── uploads/            (4 svg + 5 png + 1 pdf)
        ├── KR_RFP_design_package/  (5 .md)  └── handoff/ (7 .dc.html + 2 .md + support.js)  └── assets/ (4 svg)
        └── KR_RFP_review_bundle/   (README.txt)
            ├── 01_audit/   (4 .md)   ├── 02_screens/ (7 png)   └── 03_output_files/ (8 xlsx)
```

**Verified duplicate/identity facts (md5sum/diff):**
- `support.js` is **byte-identical** across all 4 copies (first_draft, handoff, redesign3, redesign3/uploads/.../handoff).
- The 4 Kroger SVG assets are **byte-identical** across first_draft / handoff / redesign3 / uploads-handoff assets folders.
- `redesign3/uploads/KR_RFP_design_package/handoff/*` is a **byte-identical snapshot** of the canonical `handoff/*` (all .dc.html + 2 .md + support.js + assets).
- `redesign3/*.dc.html` == `redesign3/drafts/draft 2/*.dc.html` (**byte-identical** — "draft 2" is the same files as the redesign3 root; spot-checked Alignment/Awards/Cycle Setup/Reconciliation, all identical).
- `redesign3/drafts/Alignment Workspace - draft 1.dc.html` == `first_draft/Alignment Workspace.dc.html` (**byte-identical** — "draft 1" is the first-draft Alignment, 93,575 b).
- redesign3 carries `Dashboard/Login/Handoff.dc.html` **byte-identical** to handoff (unchanged baseline screens).
- Screenshot byte-dupes: `01-adj.png`==`02-adj.png`==`03-adj.png` (identical); `01-top2.png`==`02-top2.png`; `drill.png`==`drill2.png`==`drill3.png`.

---

## 2. ROOT canonical design docs (5 files) — read end-to-end

### #358 · `project/design/DESIGN_REQUESTS.md` · md · 15,310 b · NOT empty · created 2026-06-22T02:36 · modified 03:52
**What:** The actionable "request the rest" — per-screen designer briefs derived from SCREEN_COVERAGE_AUDIT. **id PM-007-DR-REQ v1.0.**
Sections: **§A Missing screens** (A1 Cycle Setup/Strategy+pricing-basis · A2 Finalize/Close-out · A3 Editable column mapper · A4 Supplier comms E-37 [parked] · A5 Sign-off G-D · A6 Settings/Admin/Users/Roles G-C/G-J · A7 Supplier mgmt/participant selection E-34); **§B visuals** (B1 the 3 baseline tweaks · B2 non-happy-path · B3 visualizations [capacity feasibility, E-43 version-compare, E-41 deep-workbench charts, E-35 price-movement] · B4 iconography · B5 interaction-correctness "totals follow the filter" rules · B6 grain-by-surface D42/D43 mixed-grain); **§C midpoints** (M1 editable mapper · M2 lot↔SKU sticky map · M3 supplier/DC identity · M4 unit/pack reconciliation · M5 quarantine resolution · M6 date→timeframe). Each §A brief carries purpose · key elements · user decision · access point · binds-to · states.
**DETAILED WHY:** This is the spec that the designer's redesign3 deliverable is graded against in REDESIGN3_GAP_ANALYSIS.md. It is the **most detailed** version of the requests — crucially it embeds the **D43 pricing-basis** language in A1 (modality picker FOB/DELIVERED/XDOC + cost-line manager with sign/grain/$%/per-line %-base) and the **B6 mixed-grain** layout spec (horizontal/chronological, period columns + per-period total-landed + toggleable timeframe-total). Those two are exactly the gaps the gap-analysis flags as missing. Without this file the gap analysis has no "requested" baseline to diff against. The "every control is a data operation" guiding principle (view/live-edit/version-switch/governed ops) is the doctrine that ties UI to the DB-is-source-of-truth invariant (NO_FILE_STORAGE / D19 fidelity).
**Build mapping:** A1 strategy-half BUILT-pending (designed, on-baseline) / A1 pricing-half NOT designed (E-44 parked); A2 designed (built backend); A3/M1, M5 designed; A5/A6/A7 designed-not-built; A4 not designed (parked). See gap analysis §1.

### #357 · `project/design/DESIGN_PACKAGE.md` · md · 9,942 b · NOT empty · created 2026-06-22T02:42 · modified 04:29
**What:** The round-2 cover deliverable. **id PM-007-DR-PKG v1.0.** "Three big things": (1) treat data like data (§0); (2) full screen gaps (§3/§A); (3) design the midpoints (§4b/§C). Carries the **STATUS box**: ✅ REBUILT-in-code = the six baseline screens (Login·Dashboard·Run Detail·Bid Intake·Alignment·Awards) incl. navy shell + run-status strip + AssertModal; 🎨 still-to-design = the missing screens + midpoints + grain-by-surface. §2 lists the 3 corrections; §6 enumerates the bundle contents.
**DETAILED WHY:** The "start here" cover that orders the asks and **records which screens are built vs to-design**. It is the canonical statement that the live test runs on the rebuilt design, that the baseline is LOCKED (extend, don't redesign), and points the developer at `Handoff.dc.html` first. It names D42/D43/D44 as the decisions behind the new asks. Without it there's no top-level framing of the round-2 ask. **NOTE — duplicate relationship:** an OLDER/shorter version (8,239 b) lives at `redesign3/uploads/KR_RFP_design_package/DESIGN_PACKAGE.md` — the upload snapshot predates the D43 additions (see §5 flag).

### #356 · `project/design/DESIGNER_PROMPT.md` · md · 4,897 b · NOT empty · created 2026-06-22T03:00 · modified 03:45
**What:** The paste-ready prompt for the Claude Design session. **id PM-007-DR-PROMPT.** Ground rules (baseline LOCKED, Next.js+Tailwind target, view via local server) · the data-driven governing principle · a 3-phase priority order (Phase 1 critical path: 3 corrections → A1 Cycle Setup+pricing-basis+M6 → A2 Finalize → M1/M5 intake midpoints; Phase 2: M2/M3/M4 reconciliation; Phase 3: A4 comms + A5/A6/A7 governance) · the cross-cutting grain-by-surface §B6 rule · "flag back rather than guess."
**DETAILED WHY:** The instruction that actually produced redesign3. It is the operational compression of DESIGN_REQUESTS + DESIGN_PACKAGE into a sequenced brief, and it is why redesign3 contains exactly the Phase-1/Phase-2 screens (Cycle Setup, Finalize-on-Awards, Reconciliation, Sign-off, Settings, Suppliers) and NOT A4 comms (Phase-3, parked). The phase order is the audit trail for why some surfaces exist in redesign3 and others don't.

### #360 · `project/design/SCREEN_COVERAGE_AUDIT.md` · md · 6,314 b · NOT empty · created 2026-06-22T01:45 · modified 01:54
**What:** The delivered-vs-needed analysis. **id PM-007-DR-AUDIT.** "Delivered (strong)" table (the 6 screens + Handoff, with ◐ partials for finalize/downloads) and a **tiered gap register**: Tier 1 (Cycle setup/strategy ⬜; comms E-37 ◐; editable mapper ◐), Tier 2 (sign-off G-D ⬜; settings/admin G-C/G-J ⬜; supplier mgmt E-34 ⬜), Tier 3 analytics backlog (multi-round E-36, version-compare E-43, PBA E-33, price-movement E-35, capacity dashboard E-38c, portfolio kanban E-30, contracted-vs-effective E-28). Legend ✅/◐/⬜.
**DETAILED WHY:** The **source** the DESIGN_REQUESTS briefs are derived from (it says so in DESIGN_REQUESTS frontmatter). It is the earliest of the round-2 chain (created 01:45, before requests/package/prompt) and establishes the tiering. Without it there is no justification for which gaps are Tier-1 (live-path) vs Tier-2/3 (governance/backlog). **NOTE — duplicate:** byte-identical copy at `redesign3/uploads/KR_RFP_design_package/SCREEN_COVERAGE_AUDIT.md` (verified IDENTICAL).

### #359 · `project/design/REDESIGN3_GAP_ANALYSIS.md` · md · 28,352 b · NOT empty · created 2026-06-22T10:54 · modified 11:04
**What:** **The authoritative "designed vs built" map for the redesign3 deliverable** — read-and-assess, no frontend code changed. **id PM-007-DR-GAP v1.0.** Opens with the **SPONSOR DECISION banner (E-44 design stays PARKED)**. §1 coverage table (screens A1–A7, midpoints M1–M6, visuals B1/B5/B6 — each "In Redesign3? / matches spec?"); §2 deep checks on the two headline gaps (A1 D43 pricing basis missing; B6 mixed-grain not built to spec) + Reconciliation/B1/B5; §3 missing vs added-beyond-spec; §4 prioritized punch-list (1 add D43 pricing basis, 2 rebuild Landed view to B6, 3 B1 cleanup/delete stale screenshots, 4 keep A4 parked, 5 minor) + "Ready to build" list; **§5 entry-points pass** (the IA/navigation audit — the run-scoped tab rail, the orphaned surfaces Cycle Setup/Sign-off/Reconciliation, the BUILT-vs-DESIGNED nav gap vs `AppShell.tsx` which has one nav item).
**DETAILED WHY:** This is the **cross-reference spine** of this entire D3 slice — the single doc that maps every designed surface to its build status. It is the most recent file in the slice (modified 11:04, latest). It states the build facts this audit relies on: the 6 baseline screens BUILT; Settings/Suppliers/Setup/Reconciliation/Sign-off "no route, no nav"; the two E-44 pricing items not designed (and parked); A4 comms absent (parked); the stale `01/02/03-adj.png` error screenshots still shipped. §5 is the navigation-reachability evidence (orphaned surfaces). Without this file the build status of every redesign3 surface would be unverifiable from inside the design tree.

---

## 3. `first_draft/` — DRAFT 1 (2026-06-21 ~21:47) — 13 files

The first design iteration: 6 interactive screens + 2 review .md + support.js + 4 assets. Superseded by handoff/ (v2). Kept for history.

**The 6 `.dc.html` screens (draft 1):** each is a self-contained interactive HTML prototype using the shared `support.js` runtime (a tiny Vue-like reactive framework — `{{ }}` bindings, click handlers, popovers/modals). No `<title>` tags; surface identity is in the H1.

| Census | File · ext · bytes · empty? | Designed surface | DETAILED WHY / build status |
|---|---|---|---|
| #361 | `Alignment Workspace.dc.html` · html · 93,575 · n | **Alignment workbench** — 7 lenses A–G, engine-recommendation card, editable per-cell award matrix, cell drill-down (5-factor scoring + diligence tabs), per-cell decision-note popover, freeze modal w/ freeze-note. | The centerpiece. DESIGN_REVIEW §"mostly" flags the divergences: deep in-app workbench = **new capability G-I → E-41**; per-cell + freeze decision-rationale = **new → E-40**; "Save vs STLY" shown as hard metric but is a **synthetic ×1.04 proxy** (must carry MODELED tag). Built (Alignment) in E-26. **Byte-identical to `redesign3/drafts/Alignment Workspace - draft 1.dc.html`.** |
| #362 | `Awards.dc.html` · html · 25,291 · n | **Awards** — frozen v0 immutable baseline, append-only post-award layers, version history, record-adjustment form (CREATED event). | "Exact" map to as-built (DESIGN_REVIEW). Draft-1 had **no finalize/close-out step** — flagged as the missing lifecycle step (added in v2). Built in E-26. |
| #363 | `Bid Intake.dc.html` · html · 23,130 · n | **Bid Intake** — 3 gated steps (Setup→Template→Load bids), strict vs flexible, mapping-confidence review, exception/quarantine ("never guessed"), bid template's 3 sheets incl. Capacity (E-38). | "Exact" map. Confirm-only mapper (no editable override) — the gap that A3/M1 later requests. Built in E-26. |
| #366 | `Dashboard.dc.html` · html · 15,184 · n | **Dashboard / runs list** — runs table (Commodity/Cycle/Owner/Stage/Updated) + "New run". | "Exact" map to the runs list. Built in E-26. Byte-identical through handoff & redesign3 (unchanged). |
| #367 | `Login.dc.html` · html · 7,849 · n | **Login** — username → 6-digit TOTP → httpOnly session; decision-support tagline. | "Exact" map to auth+2FA. Built. Byte-identical through handoff & redesign3 (unchanged). |
| #368 | `Run Detail.dc.html` · html · 19,576 · n | **Run Detail / Overview** — lifecycle stepper, activity board (kanban), run facts, hash-chained audit trail, run-folder .zip. | "Exact" map. Built (= the Overview/Run Detail route). |

**The 2 review docs (the WHY layer of draft 1):**

- **#365 · `first_draft/DESIGN_REVIEW.md` · md · 12,691 b · n · created 21:51 · mod 21:59** — **The review of record** (id PM-007-DR1). Verdict: ship-worthy direction, B-class restyle of existing capabilities. **Captures the WHY:** decision-rationale layer (per-cell note + freeze note) → **E-40**; the 3 "where it breaks" decisions (STLY synthetic; deep workbench = new module G-I → **E-41**; missing finalize/close-out step); role-label cosmetic (G-C); the auditor design feedback verified (7 lenses A–G not 6; calm-by-default principle; net-new capacity-feasibility / run-status-strip / intake-exception-queue additions). **WHY it exists:** it is the audit trail for how draft 1 was graded and which items became backlog epics. Build status: feeds E-26 (restyle) + E-40/E-41 (new modules).
- **#364 · `first_draft/DESIGN_FEEDBACK_v1.md` · md · 6,461 b · n · created 22:01** — **The feedback-to-designer letter** (id PM-007-DR1-FB). "Great first draft." §A corrections (STLY = modeled; 7 lenses A–G); §B additions (scenario-level capacity feasibility, persistent run-status strip, intake exception queue, **add finalize/lock-&-close step**, modal polish); §C keep-doing; §D handoff asks (token sheet, component inventory w/ states, non-happy-path screens, real field names, responsive intent, a11y/WCAG-AA, name the icon set). **WHY:** this letter is what produced the v2 handoff — every §B/§D item shows up as ✅ in HANDOFF_NOTES' incorporation table. Email-drafter UI explicitly parked here.

**#373 · `first_draft/support.js` · js · 53,975 b · n** — The shared client runtime for all `.dc.html` prototypes (reactive bindings/handlers). Vendored-style support file, identical across all 3 iterations. **WHY:** the `.dc.html` are inert without it; DESIGN_PACKAGE warns that opening via `file://` can blank `support.js` (serve via local server). Not product code.

**`first_draft/assets/` — 4 Kroger brand SVGs (#369–#372):** `kroger-k-blue.svg` (1,323 b), `kroger-k-white.svg` (1,323 b), `kroger-wordmark-blue.svg` (3,803 b), `kroger-wordmark-white.svg` (3,803 b). The K-logo + wordmark in blue/white. **WHY:** brand identity for the navy shell; byte-identical across first_draft/handoff/redesign3. Sourced from the Kroger Brand Guidelines PDF in uploads.

---

## 4. `handoff/` — V2, the LOCKED UI BASELINE (2026-06-21 ~22:33) — 15 files

"Feedback incorporated" — supersedes first_draft. **This is the design E-26 was built against.** Adds `Handoff.dc.html` (design system) and a `Finalize/Close-out` lifecycle step. Screens carry the auditor-additive surfaces (run-status strip, capacity-as-control, intake exception queue).

**The 7 `.dc.html` screens (v2):**

| Census | File · ext · bytes · empty? | Designed surface | DETAILED WHY / build status |
|---|---|---|---|
| #374 | `Alignment Workspace.dc.html` · html · 100,303 · n | Alignment workbench (v2) — adds `capStatus` text+detail capacity feasibility in freeze modal + cell drill-down; run-status strip; sortable columns. | Grew +6.7 KB over draft 1 (added capacity-as-control + run-status strip + AssertModal polish). Built in E-26. |
| #375 | `Awards.dc.html` · html · 36,956 · n | Awards (v2) — **adds the Finalize / "lock & close run"** action writing a `CLOSED · run finalize` event; AssertModal pattern. | Grew +11.7 KB (the finalize step is the big add). HANDOFF_NOTES flags the fidelity gap: `CLOSED` is **not** in the `EventType` enum yet. Built in E-26 (Awards). |
| #376 | `Bid Intake.dc.html` · html · 28,753 · n | Bid Intake (v2) — adds the exception queue surfaced only on exception (old/wrong template, missing Capacity tab, duplicate, rejected line, low-confidence mapping, partial import). | +5.6 KB. Built in E-26. |
| #378 | `Dashboard.dc.html` · html · 15,184 · n | Dashboard — unchanged from draft 1 (byte-identical). | Carried forward; built. |
| #380 | `Handoff.dc.html` · html · 32,983 · n | **Design system & handoff page** — color tokens (named for Tailwind theme.extend), typography (Montserrat display/numerics + Nunito body, tabular-nums), spacing/radius/elevation (4px grid), component inventory w/ states (Button/Card/StatChip/.../the **AssertModal** governed-action pattern + **DataTable**), **non-happy-path** states (empty/loading/error/read-only), real **field reference** (names/units/formats — no placeholders), responsive/a11y(WCAG AA)/Lucide icons. | **NEW in v2.** "Point the developer at Handoff.dc.html FIRST" (DESIGN_PACKAGE §1). It is the token/component source for the Tailwind config. The single most load-bearing file for a faithful rebuild. Built-from in E-26. |
| #381 | `Login.dc.html` · html · 7,849 · n | Login — unchanged from draft 1 (byte-identical). | Carried forward; built. |
| #382 | `Run Detail.dc.html` · html · 21,565 · n | Run Detail (v2) — adds the run-status strip + audit refinements. | +2.0 KB. Built. |

**The 3 v2 docs (the WHY layer of the handoff):**

- **#379 · `handoff/HANDOFF_NOTES.md` · md · 3,472 b · n** — **id PM-007-DR2 v2.0.** "Current source of truth for the frontend rebuild (E-26). Supersedes first_draft/." Carries the **incorporation table** (every v1 feedback item → ✅ v2 status: STLY MODELED badge, 7 lenses, capacity feasibility, run-status strip, intake exception queue, finalize/close step, AssertModal, Handoff page; ⏸ email-drafter correctly not built). **The one fidelity note:** finalize writes a `CLOSED` event but the `EventType` enum (CREATED/SEALED/FROZEN/SUPERSEDED/SIGNED_OFF/SENT/GATE_APPROVED/IMPORTED) has **no `CLOSED`** — must add `CLOSED` or map to SIGNED_OFF/SENT when built. **WHY:** the contract that says "this is what gets built." The CLOSED-enum note is a real DRIFT flag (design asserts an event type that does not exist in code).
- **#377 · `handoff/DESIGN_FEEDBACK_v2.md` · md · 2,796 b · n** — **id PM-007-DR2-FB.** Round-2 auditor feedback, verified. Verdict: "this is now the UI baseline — lock it." Only **3 items** remain: (1) compact-width status-strip truncation fix (short labels Live/Sealed v1/Not frozen/Current); (2) Awards "runtime error" = **VERIFIED STALE SCREENSHOT**, no code fix — just refresh (`Awards.dc.html` CELLS() defines `demand:5200`, no undefined path); (3) audit-state drill-through (make "Hash-chain current" clickable). **WHY:** these 3 become the **B1 corrections** carried into redesign3; item 2 is the origin of the "delete the stale `01/02/03-adj.png`" punch-list item.
- **(also in handoff) — none beyond the 2 above + the screens.**

**#387 · `handoff/support.js` · js · 53,975 b · n** — identical runtime (see §3). **assets/ #383–#386** — the same 4 Kroger SVGs, byte-identical.

---

## 5. `redesign3/` — ROUND 3 DELIVERABLE (2026-06-22 ~10:44)

The designer's round-3 output: extends the locked baseline with the missing lifecycle/governance screens, plus a self-contained `uploads/` mirror of the package + audit/review bundle it was handed, plus exported `screenshots/`, plus a folder `.thumbnail`.

### 5a. The 12 root `.dc.html` screens (#388 is .thumbnail; #389–#400 are screens)

| Census | File · ext · bytes · empty? | Designed surface (H1) + what it depicts | DETAILED WHY · spec-match · BUILD STATUS (per gap analysis §1/§5) |
|---|---|---|---|---|
| #389 | `Alignment Workspace.dc.html` · html · 113,943 · n | **Alignment workbench** — engine-rec card; 7 lens cards A–G; editable award matrix; filter popover (DC/lot/supplier) with `matrixFooter` flipping to "Subtotal · filtered" + "X of Y cells shown" recomputing over `visCells`; Custom (F) live recompute; DC-locked sort; cell drill-down; freeze AssertModal; 8 diligence tabs (Suppliers/Lowest-cost/Coverage/Scoring/Landed/Share/Incumbent/Negotiation); version-compare two-up scaffolding. | Largest file in slice (+13.6 KB over v2). **B5 totals-follow-the-filter = BEST-realized cross-cutting rule** (strong, concrete). **B6 mixed-grain = NOT to spec** — the "Landed & hidden costs" view (`view==='landed'`) is a **flat stacked single-grain build-up** (FOB+delivery+cooling→all-in), the exact layout B6 says to avoid; no period columns, no per-period total-landed, no toggleable timeframe-total, no RPC line, no per-component grain labels. Scored price/awards correctly stay timeframe-grain. Diligence-tab set + version-compare are **added beyond spec** (aligned to E-41/E-43). BUILT shell (Alignment route); B6 NOT designed-to-spec (E-44 parked). **Byte-identical to drafts/draft 2/Alignment Workspace.dc.html.** |
| #390 | `Awards.dc.html` · html · 43,751 · n | **Awards + Finalize/Close-out (A2)** — frozen award + append-only layers; close-out card; "Finalize & close run" → finalize/assert modal; `CLOSED` state; pre-close checklist gate; won + rejection **notices as drafts** (draft→SENT note); read-only-after-close. Also the **B1 "Hash-chain current" drill-through** → "Latest audit event" popover (Actor/Timestamp/Prior hash); compact status-strip short labels. | A2 **matches the brief, backend-aligned** (`POST /runs/{slug}/finalize`, `CLOSED` event). B1 hash-chain drill-through present (could add event-type+artifact). BUILT (Awards route); finalize action TBD in build (gap analysis §5.1 "partial"). **Byte-identical to drafts/draft 2/Awards.dc.html.** |
| #391 | `Bid Intake.dc.html` · html · 40,079 · n | **Bid Intake + A3/M1 editable mapper + M5 quarantine** — field `<select>` per column, ambiguous-flag amber dot, confidence column, resolve hint; exception queue with quarantined-row reasons (wrong template / missing capacity / Round-0 / missing Capacity-tab E-38), **fix-and-retry** resolution. | A3=M1 **matches**; M5 **matches** (richer exception taxonomy added beyond spec). BUILT (Intake route, reachable). |
| #392 | `Cycle Setup.dc.html` · html · 33,138 · n | **Cycle Setup / Strategy (A1)** — H1 "Cycle setup". Ingested **scope read-back** (DCs·lots·items·timeframes·invited suppliers·volumes, READ-BACK tag); **Strategy panel** (weight preset Balanced/Price/Coverage/Risk-averse/Custom + 5 live weights w/ running Σ; the 4 safeties premium-ceiling/coverage-floor/concentration-cap/max-suppliers-per-DC; supplier treatment preferred/exclude; lenses to run); **M6** timeframe-date confirm ("inferred until you confirm — no silent month-13 fallback"); pre-ingest empty state; quarantine surface; gated "Generate templates →". | **A1 strategy-half MATCHES and is good; the entire D43 pricing basis is MISSING** (grep modality/FOB/DELIVERED/XDOC/cost.line/RPC → zero matches): no modality picker, no cost-line manager, no discounts-as-subtract-lines, no template-column link, none of the pricing states. **The #1 gap.** Per D44/sponsor banner E-44 is PARKED → does not block the live test. **NOT BUILT** — no `/runs/[slug]/setup` route; orphaned from the hub (Setup tab absent from Run Detail/Dashboard). **Byte-identical to drafts/draft 2.** |
| #393 | `Dashboard.dc.html` · html · 15,184 · n | Dashboard — unchanged (byte-identical to handoff/first_draft). | Carried forward; BUILT. |
| #394 | `Handoff.dc.html` · html · 32,983 · n | Design system page — unchanged (byte-identical to handoff). | Carried forward; the token/component source. |
| #395 | `Login.dc.html` · html · 7,849 · n | Login — unchanged (byte-identical). | Carried forward; BUILT. |
| #396 | `Reconciliation.dc.html` · html · 29,280 · n | **Data reconciliation (M2/M3/M4)** — H1 "Data reconciliation". **Lot → iTrade-SKU map** (1→many, PROPOSED vs CONFIRMED chips, "Confirmed · sticky", add-SKU); **Supplier & DC identity** (match-to-existing/merge/create-new, dedup language, sticky binding); **Unit & pack-size normalization** (quoted-unit→conversion factor, "Normalized", unconverted line quarantined → feeds `construct_price_from_parts`). iTrade feed shown **dormant (E-08)**; open-seam counter in nav. | M2/M3/M4 all **match** the propose→confirm→sticky pattern (M2 = the headline midpoint, done well; "Nothing crosses a boundary by inference"). **NOT BUILT** — no route, no nav; orphaned from hub (Reconciliation tab only on Recon/Sign-off sidebars). **Byte-identical to drafts/draft 2.** |
| #397 | `Run Detail.dc.html` · html · 24,887 · n | Run Detail / Overview (v3) — lifecycle, activity board, audit trail, run facts. | Carried forward + refined (+3.3 KB over v2). BUILT (the landing hub). Gap analysis §5: its run-scoped tabs **omit Setup/Reconciliation/Sign-off** — the orphaning root cause. |
| #398 | `Settings.dc.html` · html · 19,046 · n | **Settings & Admin (A6)** — H1 "Settings & Admin". Users list + invite; role assignment; **permission matrix**; "roles are enforced, not cosmetic"; tenant section marked (later). | **Matches G-C/G-J.** **NOT BUILT** — no route, no nav (reachable in R3 global "Sourcing" group only on Suppliers/Settings sidebars). **Byte-identical to drafts/draft 2.** |
| #399 | `Sign-off.dc.html` · html · 23,919 · n | **Sign-off / approver gate (A5)** — H1 "Sign-off queue". Awaiting-sign-off queue; **author≠approver enforced** ("Author · can't self-sign"); approver assert modal → `SIGNED_OFF` event; approver note. | **Matches G-D.** E-22 portfolio savings roll-up not obviously surfaced (minor). **NOT BUILT and the WORST orphan** — no route, no nav; Awards has no Sign-off link; appears only in its own sidebar → a user who freezes has no in-product path to the approver gate. **Byte-identical to drafts/draft 2.** |
| #400 | `Suppliers.dc.html` · html · 33,257 · n | **Supplier mgmt / participant selection (A7)** — H1 "Supplier master". Supplier master (`ref.supplier`) + importer (upsert/identity-resolve); per-cycle participant picker by category ("Participants · Field Tomatoes"); supplier drill (`{{ drill.name }}`); "Import suppliers · resolve identities". | **Matches E-34.** **NOT BUILT** — no route, no nav (global slot in R3 only). The in-Cycle-Setup participant-pick entry is **unwired** (half-covered). **Byte-identical to drafts/draft 2.** |

**#388 · `redesign3/.thumbnail` · (dotfile) · 6,660 b · n** — A **WebP image, 320×230** (verified `file`). The folder-preview thumbnail auto-written by the design/export tool. **WHY:** non-semantic export artifact (a directory icon), counted not analyzed; not product code.

**#435 · `redesign3/support.js` · js · 53,975 b · n** — identical runtime (see §3).
**`redesign3/assets/` #401–#404** — the 4 Kroger SVGs, byte-identical to first_draft/handoff.

### 5b. `redesign3/drafts/` — intermediate captures (13 files, #405–#417)

- **#405 · `drafts/Alignment Workspace - draft 1.dc.html` · html · 93,575 · n** — **Byte-identical to `first_draft/Alignment Workspace.dc.html`** (verified). The first-draft Alignment, retained as "draft 1" of the round-3 Alignment iteration. **WHY:** shows the designer's starting point before the +20 KB of filter/diligence/version-compare work landed in the final redesign3 Alignment. Duplicate snapshot.
- **#406–#417 · `drafts/draft 2/` (12 .dc.html)** — **Byte-identical, file-for-file, to the 12 `redesign3/*.dc.html` root screens** (spot-verified Alignment/Awards/Cycle Setup/Reconciliation; sizes match exactly for all 12). **WHY:** "draft 2" == the final round-3 set; an intermediate-save copy the export kept. Pure duplicates — flag as snapshots, no independent design content.

### 5c. `redesign3/screenshots/` — 17 exported PNGs (#418–#434, all flagged owned=n in census)

Static renders exported from the `.dc.html` prototypes. Census marks these **non-owned (n)** — counted exports, not authored source. All are 1240-px-wide compact-breakpoint captures of the **navy-shell redesign3** screens (the new visual era). Visually inspected; grouped by content:

| Census | File(s) · bytes | Depicts | WHY it's here |
|---|---|---|---|
| #432 | `full.png` · 37,848 | **Alignment workbench** full view: engine-rec card ($218,400 spend / $62,400 save vs incumbent / 22.2%·25.2% vs STLY), 7 lens cards A–F+ visible, freeze-award button, RecScore tooltip popover open. | The hero shot of the centerpiece surface. |
| #418/#420/#422 | `01-adj.png`=`02-adj.png`=`03-adj.png` · 33,326 each (**byte-identical**) | **The STALE Awards ERROR screenshot** — red banner `Awards.renderVals(): can't access property "toLocaleString", c.demand is undefined` over the Awards run-status strip. | **THE punch-list defect image.** DESIGN_FEEDBACK_v2 §2 + gap analysis §3/§4 flag this as a **stale export-lag artifact, NOT a live defect**, and say **delete/replace it** so the deliverable doesn't ship the red error on the governed-record screen. Still present (3 identical copies) → unresolved cleanup. |
| #419/#421 | `01-top2.png`=`02-top2.png` · 29,708 (**byte-identical**) | Alignment top region (engine-rec + scope chips), compact width. | B1 compact-width render. |
| #424/#425/#426 | `drill.png`=`drill2.png`=`drill3.png` · 37,003 (**byte-identical**) | Alignment with the full scope-chip stack (2 DCs · 2 lots · 2 suppliers invited · 4 award cells · 13-week horizon · Balanced preset · Round 1) + engine-rec. | Scope read-back / drill state of Alignment. |
| #423 | `body.png` · 28,660 | Alignment body (scope chips + engine-rec), full-rail sidebar. | Layout capture. |
| #427 | `explain.png` · 29,174 | Alignment with collapsed-icon sidebar + engine-rec. | Sidebar-collapse state. |
| #428 | `exq.png` · 30,746 | **Bid Intake** — run-status strip (Live·Round 1 intake / Not yet sealed / Not frozen / Hash-chain current), step 1 Setup workbook "Complete", `01_setup_kickoff.xlsx` + `02_round1_bid_template.xlsx` download rows. | The intake happy path render. |
| #429 | `finalize.png` · 30,352 | **Awards (clean)** — frozen AWD-2026-TOMATO-1, "Record adjustment", award-cell table (Green Valley Farms / Sunbelt Produce, frozen vs effective $/case, +$0.40 delta). | The **clean Awards render** that should replace the stale `*-adj.png`. |
| #430 | `freeze-fixed.png` · 32,713 | Alignment compact width — the B1 status-strip short-labels target. | Gap analysis §3 caveat: this capture **still shows clipping** ("Live · Roun…", "Hash-chain curr…") though the HTML CSS fix is in place → **re-shoot** flagged. |
| #431 | `freeze2.png` · 35,204 | **Freeze AssertModal** — "Freeze award — governed action", asserting Scenario B from sealed analysis v1, totals ($218,400 / $62,400 / 4 cells · 2 suppliers), awarded-cell list (Atlanta/Dallas × Lot1/Lot2 → Green Valley/Sunbelt @ $10.50), "Capacity (stated): Feasible against stated capacity (E-38)". | The governed-action gravity render — proof the AssertModal pattern landed. |
| #433 | `nav.png` · 26,929 | Alignment with collapsed icon-rail nav. | Nav-collapse state. |
| #434 | `wide.png` · 28,198 | Alignment at wide viewport — scope chips inline + 4 lens cards + the diligence COMPARE rail (Supplier comparison / Lowest-cost / Coverage / ... / Negotiation dynamics) starting. | The wide-layout + diligence-rail render (E-41 direction). |

### 5d. `redesign3/uploads/` — the package + audit/review bundle handed TO the designer (#436–#484)

This subtree is **the input materials the designer was given** — bundled into the deliverable for self-containment. It is a mix of (a) **byte-identical snapshots** of canonical docs, (b) **older versions** of two canonical docs, (c) **upload-only canonical docs** not present at root, and (d) the brand/source assets + the review bundle (audit docs + v1 screens + output workbooks).

**Logo source SVGs (#436–#439)** — `KR.svg` (1,308), `KR.D.svg` (1,369), `KR_BIG.svg` (3,788), `KR_BIG.D.svg` (3,788). **Distinct** from the `assets/kroger-*.svg` (different md5s) — these are the raw uploaded Kroger K / big-wordmark source files (the `.D` variants = dark/duotone). **WHY:** the brand-asset inputs the designer derived the `assets/` set from.

**`uploads/KR_RFP_design_package/` (5 .md + a handoff/ mirror):**

| Census | File · bytes | Relationship to canonical | WHY / flag |
|---|---|---|---|
| #440 | `DATA_AND_PROCESS_MAP.md` · 24,181 · n | **UPLOAD-ONLY canonical doc** (no root copy in this slice). id PM-MAP. | The companion data/process map — Diagram 1 (ERD spine + reconciliation `((SEAM))` nodes), Diagram 2 (process flowchart w/ DECISION diamonds, ACCESS points SCR:/EP:, audit events A:, gap dashed nodes), enumerated DECISION points D1–D8 (D6 finalize/D7 sign-off/D8 round-close = ⬜ gaps), ACCESS points table, reconciliation-seams table, **gaps-flagged table**, and "relationships I was unsure of" (eng.* FKs logical-not-enforced; pilot.run↔cyc.cycle text-not-FK; CLOSED EventType absent). **A primary cross-ref for build status / DRIFT** — it independently confirms: no setup/strategy screen (workbook-only), confirm-only mapper, unit/pack unmodeled, sign-off/comms/PBA/close-out gaps, CLOSED-type drift. **Derived view, not source of truth (Postgres + 07 win).** |
| #441 | `DESIGN_PACKAGE.md` · 8,239 · n | **OLDER version** of root #357 (9,942 b) — DIFFERS. | The pre-D43 snapshot handed to the designer; lacks the later pricing-basis framing. **Flag: superseded duplicate.** |
| #442 | `DESIGN_REQUESTS.md` · 11,783 · n | **OLDER version** of root #358 (15,310 b) — DIFFERS. | Confirmed: this upload's **A1 brief has NO D43 pricing-basis text** (no modality picker / cost-line manager) and a shorter B6 — i.e. the designer was handed the **pre-pricing-basis** requests. This is *why* redesign3's Cycle Setup has the strategy half but not the pricing half. **Flag: superseded duplicate — and the root cause of the #1 gap.** |
| #443 | `RECONCILIATION_SEAMS.md` · 5,601 · n | **UPLOAD-ONLY canonical doc** (no root copy in this slice). id PM-SEAMS. | The living seams watch-list — the source for the §C midpoints M1–M6. Seam table (lot→SKU 1→many headline OPEN; unit/pack OPEN; messy-columns ◐; supplier/DC identity ◐; dates→periods ◐; STLY ×1.04 proxy; + the ✅ done seams G-A/E-38/E-39); newly-surfaced gaps; the **known-template deterministic adapter** plan (emit OUR key-stamped template → STRICT ingest, never direct-to-DB). Cross-ref for which seams are built vs open. |
| #444 | `SCREEN_COVERAGE_AUDIT.md` · 6,314 · n | **BYTE-IDENTICAL** to root #360 (verified). | Snapshot duplicate. |
| #445–#458 | `handoff/` (7 .dc.html + DESIGN_FEEDBACK_v2.md + HANDOFF_NOTES.md + support.js + 4 assets) | **BYTE-IDENTICAL** to the canonical `project/design/handoff/` (verified Alignment + the 2 .md + support.js + assets). | The locked-baseline mirror bundled as designer input. **Flag: snapshot duplicates of `handoff/` (§4).** |

**`uploads/KR_RFP_review_bundle/` — the AUDITOR + DESIGN input bundle (README + 01_audit + 02_screens + 03_output_files):**

- **#478 · `README.txt` · 1,546 b · n** — bundle manifest (generated 2026-06-21 19:29): contents map, the G-I core design question (alignment workbench is Excel-only), DATA NOTE (all synthetic tomato demo data), REVIEW SEQUENCE (audit → auditor → triage → design from same bundle). **WHY:** the index for the handed-over bundle.
- **`01_audit/` (4 .md):**
  - **#459 · `04_PROGRAM_BACKLOG.md` · 18,984 · n** — snapshot of the program backlog (the E-xx register the design epics reference). Input copy; the live one lives at `project/04_PROGRAM_BACKLOG.md` (other slice). **Flag: bundled snapshot.**
  - **#460 · `07_AS_BUILT_PROCESS_AUDIT.md` · 61,800 · n** — the As-Built Specification v1.19 (the "START HERE" ground-truth the design + audit were graded against). Largest doc in the slice. **Flag: bundled snapshot of the As-Built (a different-version copy of the project's canonical audit).**
  - **#461 · `08_RELEASE_GOVERNANCE.md` · 9,912 · n** — change-classification + phases + review cadence (the governing doc; CLAUDE.md cites the live one). **Flag: bundled snapshot.**
  - **#462 · `DESIGN_BRIEF.md` · 3,700 · n** — **the one-page design-session orientation** (read end-to-end): what we're building (single-operator Kroger produce RFP web app; AI-generated-not-AI-managed), form factor/stack (Next.js+React18+TS+Tailwind, FastAPI, 1440px desktop-first, Vercel), the single biggest design question **G-I** (bring the ~18-tab Excel alignment workbench on-screen), net-new surfaces (capacity E-38, comms E-37, sign-off, close-out, documents), constraints (decision-support framing, governed actions deliberate, names-not-keys, advisory-not-canonical). **WHY:** the orientation that seeded the whole design effort; the only place G-I is framed as "the core ask." Upload-only in this slice.
- **`02_screens/` (7 .png) #463–#469** — **The v1 (PRE-redesign) live console screenshots**, 1440px, on seeded demo data — the "what the web is today" baseline the designer reskinned FROM. Visually distinct plain-white console (no navy shell). `01-login.png` (plain Sign-in card, username/password, httpOnly note) · `02-runs-list.png` · `03-run-detail.png` · `04-run-intake.png` · `05-run-alignment.png` (the v1 Alignment: "Analysis runs" table + flat 7-lens A–G scenario-comparison table with SPEND/Δ/save-vs-incumbent/save-vs-STLY/suppliers/cells/breaches — the thin slice that G-I asks to deepen) · `06-run-awards.png` · `07-run-intake-setup-only.png` (the "bonus state"). **WHY:** the before-state evidence; proves the redesign is a reskin-and-extend of a real working v1, not greenfield.
- **`03_output_files/` (8 .xlsx) #470–#477** — **the generated Excel artifacts** (synthetic tomato demo) — the "richness to bring on-screen": `01_setup_kickoff.xlsx`, `02_round1_bid_template.xlsx`, **`04_round1_alignment_v1.xlsx`** (42,586 b — the ~18-tab ALIGNMENT WORKBENCH that lives only in Excel; **the G-I artifact**), `08_award_booking_guide.xlsx`, two per-supplier award guides (`08_award_guide_..._green_valley_farms_...xlsx`, `..._sunbelt_produce_...xlsx`), `08_award_supplier_guides.xlsx`, `09_post_award_v1.xlsx`. **WHY:** the output lifecycle the design must surface; #472 is the single most important input (the workbench G-I asks to bring on-screen → drove the 8 diligence tabs added in redesign3 Alignment, E-41). Binary; described by manifest, not opened.

**Loose uploads at `uploads/` root (#479–#484):**
- **#479 · `Kroger Brand Guidelines_4-8-25.pdf` · 16,738,537 b (~16 MB) · n** — the official Kroger brand guidelines (dated 4-8-25). **The largest file in the slice by far.** Source for the brand tokens/logos/colors. Binary; counted, not page-audited (brand reference, not product spec).
- **#480 · `Screenshot 2026-06-21 at 4.36.46 PM.png` · 361,772 · n** — an **annotated Alignment** capture: 4 lens cards + the diligence COMPARE rail (Supplier comparison / Lowest-cost / Coverage / Detailed scoring / Landed & hidden / Share & relationships / Incumbent retention / Negotiation dynamics) with a Supplier-comparison table (award cell · demand 5,200 ×4 · Total-B 20,800) and a **red "HERE" box** marking where the deep workbench should land. **WHY:** the visual articulation of the G-I ask — pasted into the design session to point at the workbench location.
- **#481 · `Screenshot 2026-06-21 at 5.13.02 PM.png` · 155,269 · n** — a crop of the **Engine Recommendation card** ($218,400 vs $280,800 incumbent / $62,400 save / 22.2%·25.2% vs STLY / 2 suppliers · 4 cells · No cautions / Freeze award). Component detail reference.
- **#482 · `Screenshot 2026-06-21 at 5.18.50 PM.png` · 13,392 · n** — a tiny crop of the **"Analysis sealed · v1" status pill** (green dot). The status-badge component reference.
- **#483 · `pasted-1782077933482-0.png` · 335,614 · n** — a full **Alignment workbench** screen capture (same surface as full.png), pasted into the session as reference.
- **#484 · `pasted-1782080027937-0.png` · 1,364,100 · n** — a **screen-capture of the Claude Design TOOL itself** (browser chrome "Produce Sourcing RFP", left "Plan 11/15" checklist of edits to Alignment Workspace.dc.html, the canvas showing the Freeze-award AssertModal mid-build). **WHY:** a working-session screenshot showing the design being built — process evidence, not a product surface.

---

## 6. DESIGNED-surface → BUILD-STATUS map (the cross-reference deliverable)

Synthesized from REDESIGN3_GAP_ANALYSIS.md (§1/§2/§4/§5) + DATA_AND_PROCESS_MAP.md (DECISION/gap tables) + HANDOFF_NOTES (CLOSED drift). Legend: **BUILT** = shipped in E-26 console (route + nav) · **DESIGNED-not-built** = in redesign3, no route/nav · **NOT-designed** = absent from redesign3 · **DRIFT** = design asserts something code doesn't have.

| Designed surface / item | Design home (file) | Decision/epic | Build status |
|---|---|---|---|
| Login | Login.dc.html (all 3 iters, identical) | E-26 | **BUILT** (route `/login`) |
| Dashboard / runs list | Dashboard.dc.html (identical) | E-26 / E-30 | **BUILT** (route `/`) |
| Run Detail / Overview | Run Detail.dc.html | E-26 | **BUILT** (route `/runs/[slug]`) |
| Bid Intake (3 steps, strict/flex, exception queue) | Bid Intake.dc.html | E-26 / E-38 | **BUILT** (route `/runs/[slug]/intake`) |
| Alignment workbench (7 lenses, freeze, drill) | Alignment Workspace.dc.html | E-26 | **BUILT** (route `/runs/[slug]/alignment`) |
| Awards (frozen + append-only adjust) | Awards.dc.html | E-26 | **BUILT** (route `/runs/[slug]/awards`) |
| **A1 Cycle Setup — strategy half** (preset/weights/safeties/suppliers/lenses) | Cycle Setup.dc.html | E-26-adj | **DESIGNED-not-built** (no `/setup` route; minimal `StrategyPanel` inline on Run Detail; orphaned from hub) |
| **A1 Cycle Setup — D43 pricing basis** (modality picker + cost-line manager) | — (absent) | **D43/E-44** | **NOT-designed** (#1 gap; E-44 PARKED per sponsor banner; not a live-test blocker per D44) |
| **A2 Finalize / Close-out** (AssertModal + CLOSED + notices) | Awards.dc.html | E-22/E-24/E-37 | **DESIGNED**, backend built (`POST …/finalize`); action wiring TBD. **DRIFT:** `CLOSED` not in EventType enum (HANDOFF_NOTES) |
| **A3 / M1 editable column mapper** | Bid Intake.dc.html | seam (new) | **DESIGNED**; reachable surface built (Intake); editable-mapper API change pending |
| **A4 Supplier comms (E-37, 6 touchpoints)** | — (absent) | **E-37** | **NOT-designed** (deliberately PARKED) |
| **A5 Sign-off / approver gate** (author≠approver, SIGNED_OFF) | Sign-off.dc.html | **G-D** | **DESIGNED-not-built** (no route/nav; WORST orphan — no Awards→Sign-off link) |
| **A6 Settings/Admin/Users/Roles** (permission matrix) | Settings.dc.html | **G-C/G-J** | **DESIGNED-not-built** (no route/nav; reachable in R3 global group only) |
| **A7 Suppliers (master + importer + participant pick)** | Suppliers.dc.html | **E-34** | **DESIGNED-not-built** (no route/nav; in-Setup participant entry unwired) |
| **M2 lot↔SKU sticky / M3 supplier-DC identity / M4 unit-pack** | Reconciliation.dc.html | E-11/E-08/E-34 | **DESIGNED-not-built** (no route/nav; orphaned from hub; M2 awaits dormant iTrade feed E-08) |
| **M5 quarantine resolution** | Bid Intake.dc.html | — | **DESIGNED** (on a built surface) |
| **M6 date→timeframe confirm** | Cycle Setup.dc.html | — | **DESIGNED-not-built** (rides on the unbuilt Setup surface) |
| **B1 compact status-strip short labels** | Awards + Alignment CSS | — | **DESIGNED** (CSS in place); caveat: re-shoot `freeze-fixed.png` (still clips) |
| **B1 hash-chain drill-through** | Awards.dc.html popover | — | **DESIGNED** (could add event-type+artifact) |
| **B1 refresh stale Awards screenshot** | screenshots/ | — | **UNRESOLVED** — `01/02/03-adj.png` error image still shipped (delete) |
| **B5 totals-follow-the-filter** | Alignment Workspace.dc.html | — | **DESIGNED** (best-realized cross-cutting rule) |
| **B6 mixed-grain analysis breakdown** | — (flat stacked placeholder only) | **D42/D43/E-44** | **NOT-designed-to-spec** (#2 gap; "Landed" view is the avoid-this stacked layout; E-44 PARKED) |
| Deep workbench / 8 diligence tabs (G-I) | Alignment Workspace.dc.html | **E-41 / G-I** | **DESIGNED beyond spec** (welcome; ahead of strict §A) |
| Version-compare two-up (E-43) | Alignment Workspace.dc.html | **E-43** | **DESIGNED** scaffolding (forward motion) |
| Run-scoped tab rail (Setup·Overview·Intake·Recon·Alignment·Awards·Sign-off) | implied across R3 sidebars (inconsistent) | E-26 nav | **NOT-built** — biggest single navigation build item (`AppShell.tsx` has 1 nav item "Runs"); no two R3 sidebars agree on the set |

---

## 7. Flags (snapshots/duplicates + DRIFT + open items)

**Snapshots / duplicates (per the task's explicit ask to flag the redesign3/uploads .md):**
1. `redesign3/uploads/KR_RFP_design_package/SCREEN_COVERAGE_AUDIT.md` = **byte-identical** snapshot of root `SCREEN_COVERAGE_AUDIT.md`.
2. `redesign3/uploads/KR_RFP_design_package/DESIGN_PACKAGE.md` (8,239 b) = **older/superseded** version of root `DESIGN_PACKAGE.md` (9,942 b).
3. `redesign3/uploads/KR_RFP_design_package/DESIGN_REQUESTS.md` (11,783 b) = **older/superseded** version of root `DESIGN_REQUESTS.md` (15,310 b) — lacks the D43 pricing-basis A1 text; **this older brief is the documented root cause of the #1 gap** (the designer wasn't handed the pricing-basis ask).
4. `redesign3/uploads/KR_RFP_design_package/handoff/*` (all 14 files) = **byte-identical** snapshot of canonical `handoff/*`.
5. `redesign3/uploads/KR_RFP_review_bundle/01_audit/*` (4 .md) = **bundled snapshots** of the project's backlog / As-Built v1.19 / governance + the upload-only DESIGN_BRIEF.
6. `redesign3/uploads/KR_RFP_design_package/DATA_AND_PROCESS_MAP.md` and `RECONCILIATION_SEAMS.md` = **upload-only canonical docs** (no root copy in this slice — they live only here within project/design/).
7. `redesign3/drafts/draft 2/*` (12 .dc.html) = **byte-identical** to `redesign3/*.dc.html` root (intermediate-save duplicates).
8. `redesign3/drafts/Alignment Workspace - draft 1.dc.html` = **byte-identical** to `first_draft/Alignment Workspace.dc.html`.
9. `support.js` (4 copies) and the 4 Kroger SVG `assets/` (4 folders) are byte-identical vendored support/brand files.
10. `redesign3/.thumbnail` = WebP folder-preview image (export artifact).
11. `screenshots/`: `01/02/03-adj.png` identical; `01/02-top2.png` identical; `drill/drill2/drill3.png` identical (export produced redundant copies).

**DRIFT (design asserts what code lacks):**
- **`CLOSED` event type** — the v2/redesign3 finalize step writes a `CLOSED` audit event, but `EventType` enum has none (HANDOFF_NOTES + DATA_AND_PROCESS_MAP D6). Open product call: add `CLOSED` or map to SIGNED_OFF/SENT.
- **Designed-not-routed surfaces** — Settings, Suppliers, Cycle Setup, Reconciliation, Sign-off all designed in redesign3 but **un-routed and un-navigated** in the shipped `AppShell.tsx` (1 nav item). The run-scoped tab rail the redesign assumes does not exist in the build.
- **Orphaned surfaces (designed but unreachable even within R3 IA):** Sign-off (no Awards→Sign-off link — true orphan), Cycle Setup (Setup tab absent from the landing hub), Reconciliation (no attention-entry from hub/Intake).

**Open items still on the punch-list (per gap analysis §4):**
- Delete/replace the stale `01/02/03-adj.png` error screenshots; re-shoot `freeze-fixed.png` at compact width.
- (E-44 PARKED) A1 pricing basis + B6 mixed-grain breakdown — revisit when E-44 is scheduled.
- A4 Comms stays parked.
- Minor: E-22 portfolio savings roll-up on Sign-off; spot-check B5 filtered %/denominators on supplier/coverage/share diligence tabs; add event-type+artifact to the hash-chain popover.

---

## 8. Audit completeness statement
All **129 files** in `project/design/**` are accounted for, 1:1 against FILE_CENSUS rows #356–#484 (verified). **Zero empty files** in this slice. Every `.md` was read end-to-end (5 root + DESIGN_REVIEW/FEEDBACK_v1/FEEDBACK_v2/HANDOFF_NOTES + DATA_AND_PROCESS_MAP/RECONCILIATION_SEAMS/DESIGN_BRIEF/README). Every `.dc.html` surface is named with its designed surface + purpose + spec-match + build status. Every `.png` (screenshots + review-bundle + loose uploads) is described by content (key ones visually inspected). Binary `.xlsx`/`.pdf`/`.svg`/`.thumbnail` are counted with their role + WHY. Every designed surface is mapped to BUILT / DESIGNED-not-built / NOT-designed / DRIFT against REDESIGN3_GAP_ANALYSIS.md + DATA_AND_PROCESS_MAP.md. Duplicate/identity claims are md5sum/diff-verified. Nothing skipped, nothing assumed.
