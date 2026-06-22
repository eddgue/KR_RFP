---
doc: AS-BUILT AUDIT — SLICE F2b — components/alignment + components/awards (Layer-3 UX/UI, exhaustive)
id: ASBUILT-F2b
status: DONE
scope: frontend/components/alignment/** (7 files) + frontend/components/awards/** (3 files) = 10 owned files
standard: /home/user/KR_RFP/AS_BUILT/AUDIT_STANDARD.md (Layer 3 — every component, every state, every data binding with format + precision)
contract: /CLAUDE.md ABSOLUTE REQUIREMENTS honored (no MVP / data fidelity / verify-before-asserting). READ-ONLY audit; nothing changed.
census: FILE_CENSUS.md rows 278–284 (alignment), 287–289 (awards). Sizes verified equal to on-disk bytes 2026-06-22.
---

# SLICE F2b — Alignment & Awards components (Layer-3, pixel-level)

This is the **analysis UI** — the surface where the buyer reads sealed engine output and makes the
governed award decision. Per the audit standard ("if a decimal moves one pixel, it gets mapped"),
every money/%/count/price binding below is traced from its backend field, through its TypeScript
type, through the shared formatter, to the rendered pixel — with the **exact rounding and decimal
precision** the formatter applies. None skipped.

## 0. Shared formatter contract (the decimal's journey — read this first; every binding cites it)

Source: `frontend/lib/format.ts`. All numeric bindings in this slice route through ONE of these four
formatters (plus inline `.toFixed`). The format/precision is determined HERE, not in the components,
so it is documented once and referenced per binding.

| Formatter | Signature | Null handling | Rounding / precision | Example |
|---|---|---|---|---|
| `formatMoney(value, opts?)` | `number\|null` → string | `null` → `"—"` (em-dash U+2014) | `Intl.NumberFormat` `style:"currency"`, `currency:"USD"`. **Default: 0 fraction digits** (`min=max=0`) → whole dollars, half-to-even/half-up per Intl (banker-ish; locale rounds half away from zero in V8). `{cents:true}` → `min=max=2`. Thousands separators from locale (`undefined` locale ⇒ runtime default, typically `en-US` comma groups). | `1234567.5` → `"$1,234,568"`; with `{cents:true}` → `"$1,234,567.50"` |
| `formatPercent(frac)` | `number\|null` → string | `null` → `"—"` | `style:"percent"`, `min=max=1` fraction digit. **Input is a FRACTION** (0.0524), multiplied ×100 by Intl. Rounds to 1 decimal. | `0.0524` → `"5.2%"` |
| `formatPrice(value)` | `number\|null` → string | `null` → `"—"` | `toLocaleString` `min=max=2` fraction digits. **No currency symbol** (bare number, "monetary-ish"). 2 decimals, locale thousands grouping. | `12.5` → `"12.50"`; `1234.5` → `"1,234.50"` |
| `formatCount(value)` | `number\|null` → string | `null` → `"—"` | `toLocaleString()` default (integer, locale grouping). No forced fraction digits — assumes integer input. | `12345` → `"12,345"` |
| `formatTimestamp(iso)` | `string` → string | `NaN` date → returns raw `iso` string verbatim (fallback) | `toLocaleString` with `year:numeric, month:short, day:numeric, hour:2-digit, minute:2-digit`. Locale-dependent; no seconds. | `"2026-06-22T11:17:56Z"` → e.g. `"Jun 22, 2026, 11:17 AM"` |

Inline (not via format.ts):
- `rec_score.toFixed(1)` — RecScore rendered to **1 decimal** (ScenarioDetailPanel SupplierGrid). `null` → `"—"`.
- `effective_price.toFixed(2)` — adjustment draft seed (RecordAdjustmentModal `toggle`), **2 decimals**, used as the editable input's initial string.
- `frozenAwardId.slice(0,8)` — frozen award id truncated to first **8 chars** for the chip.
- `Math.abs(l.delta)` then `formatPrice` — award-line Δ magnitude at 2 decimals, sign prepended manually (`+` / `−` U+2212 minus, NOT hyphen).

`tabular-nums` (CSS `font-variant-numeric: tabular-nums`) is applied to EVERY numeric cell in this
slice so digits align in columns — noted per binding where present. Em-dash placeholder `"—"` is used
uniformly for null/zero "nothing here".

StatusChip tones (`frontend/components/ui/StatusChip.tsx`): `neutral` (muted gray), `accent` (soft
accent), `amber`=`modeled` (warning bg/text), `green`=`frozen` (success bg/text), `slate`,
`sealed` (sealed bg/text), `gated` (danger bg/text). **Governed language is always colour + text,
never hue alone** (locked v2). All chips: pill, `text-2xs`, uppercase, tracking-wide, ring-inset.

---

# PART A — components/alignment/** (7 files)

================================================================================
## A1. AnalysisRunsPanel.tsx
================================================================================
- **Path:** `/home/user/KR_RFP/frontend/components/alignment/AnalysisRunsPanel.tsx`
- **Ext:** `.tsx` · **Empty?** No (3981 bytes, 119 lines) · **Census row:** 278 (size matches).
- **`"use client"`** — interactive (row clicks, button).
- **WHAT:** The table of **sealed analysis runs** for the cycle + the Run-analysis control in its
  header. Each row is one immutable engine seal (scores + seven scenarios) for a round. Latest =
  "Live"; older = "Read-only". Clicking a row drives the scenario comparison below.
- **DETAILED WHY:** The alignment screen is versioned — every "Run analysis" produces a new sealed,
  immutable `eng.analysis_run`. This panel is the **version selector / history ledger**: it lets the
  buyer pick which seal to inspect, names which is live vs historic (governed actions disable on
  historic — enforced in the parent page via `readOnly`), and offers the lightweight savepoint
  ("Save version"). Without it there is no way to navigate or name sealed builds; the freeze decision
  could be made against an ambiguous "current" state. Existence ties to D42/D43 (grain/pricing) +
  E-43 (savepoints).

### Props
| Prop | Type | Purpose |
|---|---|---|
| `analyses` | `AnalysisSummary[]` | All sealed runs (parent loads oldest-first via `listAnalyses`). |
| `selectedId` | `string \| null` | Currently inspected `analysis_run_id`; highlights the row. |
| `onSelect` | `(id:string)=>void` | Row click → parent re-loads comparison for that seal. |
| `onRun` | `(round:number)=>void` | Passed straight to `RunAnalysisControl`; fires the engine run. |
| `onSaveVersion` | `(a:AnalysisSummary)=>void` | Opens the SaveVersionModal for that run. |
| `running` | `boolean` | Loading flag → disables the run control while a seal is in flight. |

### State: NONE (pure presentational; all state lives in the parent page).

### Derived value
- `liveId` — computed: `analyses.reduce((a,b)=>b.version>a.version?b:a).analysis_run_id`, else `null`
  when list empty. **WHY:** the live seal = highest `version` (1-based ordinal, oldest=1). Drives the
  "Live" vs "Read-only" chip per row. Identical logic to the page's `liveAnalysis` (no disagreement).

### States
- **Empty** (`analyses.length===0`): centered muted text — *"No sealed analysis yet — run a round to
  score the bids and generate the seven scenarios."* (`px-5 py-10 text-center text-sm text-text-muted`).
- **Populated:** the table (below). No explicit loading/error state here — the parent owns those and
  only renders the panel once data exists (`running` only disables the control).

### PanelHeader
- Title: `<span class="font-display text-base font-bold text-text-strong">Sealed analyses</span>`.
- Description (static): *"Each seal is an immutable engine output (scores + seven scenarios) for a
  round. The latest is live; prior versions open read-only."*
- Actions slot: `<RunAnalysisControl onRun onRun running={running} />` (see A2).

### Table columns + DATA BINDINGS (5 columns; header row `Version·Round·Engine·Sealed·[Actions sr-only]`)
Per row over `analyses.map(a => …)`, key = `a.analysis_run_id`; `onClick={()=>onSelect(a.analysis_run_id)}`;
selected row gets `bg-accent-soft`.

| Col | Backend field (type) | Element / classes | FORMAT + PRECISION |
|---|---|---|---|
| Version | `a.version` (number, 1-based ordinal) | `TD font-semibold text-text-strong` → `v{a.version}` | Raw integer prefixed `v`. **No formatter** — small ordinal. Inline flex wraps the chips. |
| Version (chip 1) | derived `live` (`a.analysis_run_id===liveId`) | `StatusChip tone={live?"green":"sealed"}` → `Live` / `Read-only` | text label by liveness. |
| Version (chip 2) | `a.label` (`string\|null`) | `a.label && <StatusChip tone="accent">{a.label}</StatusChip>` | Shown only when a savepoint name exists. Raw string. |
| Version (chip 3) | derived `selected` | `selected && !a.label && <StatusChip tone="accent">Selected</StatusChip>` | "Selected" chip ONLY when selected AND no label (avoids double chip). |
| Round | `a.round_number` (number) | `TD text-text` → `Round {a.round_number}` | Raw integer, prefixed "Round ". No formatter. |
| Engine | `a.engine_version` (string) | `TD text-text-muted` | Raw string (e.g. engine semver). |
| Sealed | `a.sealed_at` (ISO string) | `TD text-text-muted` → `formatTimestamp(a.sealed_at)` | §0 formatTimestamp: localized `month short, day, year, hh:mm` (2-digit hour/min, no seconds). Bad ISO → raw string. |
| Actions | (no field) | `TD text-right` → ghost `Button` | Label = `a.label ? "Rename" : "Save version"`. `onClick` **stops propagation** then `onSaveVersion(a)` (so clicking the button does NOT also select the row). |

- **Navigation/reachability:** rendered by `app/(app)/runs/[slug]/alignment/page.tsx` (always, once
  run loads). Row click → `handleSelectAnalysis` (page) → re-loads comparison + clears selectedCode/detail.

================================================================================
## A2. RunAnalysisControl.tsx
================================================================================
- **Path:** `/home/user/KR_RFP/frontend/components/alignment/RunAnalysisControl.tsx`
- **Ext:** `.tsx` · **Empty?** No (1357 bytes, 50 lines) · **Census row:** 280.
- **`"use client"`** — local state + input.
- **WHAT:** A small round-number picker + "Run analysis" submit, mounted in the AnalysisRunsPanel
  header. Collects the round and fires `onRun(parsed)`; the actual POST + loading/error are owned by
  the page.
- **DETAILED WHY:** Sealing an analysis is per-round (a multi-round RFP seals each round separately —
  D-grain). This is the **only entry point to run the engine** from the UI. Kept tiny + stateless of
  the network call so the page can own the in-flight/error story and so it can sit inline in a header.
  Without it there is no way to trigger scoring/scenario generation.

### Props
| Prop | Type | Purpose |
|---|---|---|
| `onRun` | `(round:number)=>void` | Fires with the validated integer round. |
| `running` | `boolean` | Disables the input + shows the button's loading spinner. |

### State
- `round: string` — `useState("1")`. The raw text-input value (string so the field can be transiently
  empty/invalid without coercion). **WHY string:** lets the user clear the field; validation derives
  from it rather than fighting a coerced number.

### Derived
- `parsed = Number(round)`; `valid = Number.isInteger(parsed) && parsed>=1`. **WHY:** rounds are
  positive integers; reject `0`, negatives, decimals, blank, non-numeric.

### DATA BINDINGS / format
- Label "Round": `text-2xs font-bold uppercase tracking-wide text-text-subtle`, `htmlFor="analysis-round"`.
- `Input` (`id="analysis-round"`, `type="number"`, `min={1}`): `value={round}`, `onChange` sets raw
  string, `className="h-8 w-16"`, `disabled={running}`, **`invalid={round!=="" && !valid}`** — shows
  the error ring only when non-empty AND invalid (a cleared field is not flagged red).
- `Button size="sm"` "Run analysis": `loading={running}`, `disabled={!valid||running}`,
  `onClick={()=>valid && onRun(parsed)}` (double-guards validity before firing).

### States: default(valid "1") · invalid(red ring, button disabled) · running(input disabled, button spinner).
No empty/error/not-found here — purely an input control.

================================================================================
## A3. SaveVersionModal.tsx
================================================================================
- **Path:** `/home/user/KR_RFP/frontend/components/alignment/SaveVersionModal.tsx`
- **Ext:** `.tsx` · **Empty?** No (2487 bytes, 83 lines) · **Census row:** 281.
- **`"use client"`** — modal + local input.
- **WHAT:** A **lightweight savepoint** dialog — name (or rename) the current sealed alignment version
  so it can be found and compared later. Built on the generic `Modal` (NOT `AssertModal`).
- **DETAILED WHY (critical distinction):** This is **deliberately NOT the freeze flow.** Comment-stated:
  *"no governance copy, no audit event, no award."* It calls `PATCH /runs/{slug}/analysis/{id}` →
  `nameVersion` (E-43). A savepoint is a convenience label on an already-immutable seal; the actual
  immutable decision (freeze) is a separate governed step with the AssertModal gate. Conflating the
  two would let a buyer "save" and believe they had committed the award — a governance error. The
  copy at the bottom reinforces the split.

### Props
| Prop | Type | Purpose |
|---|---|---|
| `open` | `boolean` | Modal visibility. |
| `onClose` | `()=>void` | Dismiss. |
| `onConfirm` | `(label:string)=>void\|Promise<void>` | Fires trimmed label → page's `nameVersion`. |
| `submitting` | `boolean` | Loading → disables fields + spinner. |
| `error` | `string\|null` | Server/validation error → red line. |
| `version` | `number\|null` | The version ordinal, for the description copy. |
| `currentLabel` | `string\|null` | Existing savepoint name (rename pre-fill). |

### State
- `label: string` — `useState("")`. Re-seeded on open via `useEffect(()=>{ if(open) setLabel(currentLabel ?? "") },[open,currentLabel])`. **WHY:** opening to rename pre-fills the existing name; opening fresh clears.

### Derived
- `canSave = label.trim().length>0 && !submitting` — gates the Save button (non-empty trimmed label required).

### DATA BINDINGS / format
- Modal `title="Save this version"`.
- `description`: **conditional** — `version ? \`Name version v${version} so you can find it later and
  compare against it.\` : undefined`. Renders `v{version}` inline (raw integer).
- Input (`type="text"`, `maxLength={120}`, `autoFocus`): `value={label}`, `onChange` sets raw,
  `onKeyDown` Enter → `void onConfirm(label.trim())` when `canSave`. Placeholder *"e.g. Balanced
  baseline"*. Field label "Version name" (`text-2xs ... text-text-muted`).
- Footer: secondary "Cancel" (`disabled={submitting}`) + primary "Save version"
  (`loading={submitting}`, `disabled={!canSave}`, `onClick={()=>void onConfirm(label.trim())}`).
- Helper copy: *"A savepoint records the current sealed build under a name. It writes no audit event
  and does not freeze the award — freeze stays the separate, governed step."* (`text-xs text-text-subtle`).
- Error: `error && <p class="mt-2 text-sm text-danger">{error}</p>`.

### States: default · pre-filled(rename) · submitting(disabled+spinner) · error(red line). No length/precision on numbers (only the `v{version}` integer).

================================================================================
## A4. ScenarioComparePanel.tsx
================================================================================
- **Path:** `/home/user/KR_RFP/frontend/components/alignment/ScenarioComparePanel.tsx`
- **Ext:** `.tsx` · **Empty?** No (4801 bytes, 144 lines) · **Census row:** 282.
- **`"use client"`** — fetches on mount, local state.
- **WHAT:** Side-by-side **version comparison** of the seven lenses: the LIVE working build (left) vs a
  SAVED version (right), matched by lens `code`, with the **saved-minus-working spend Δ** per lens.
- **DETAILED WHY:** E-43. When several sealed builds exist, the buyer needs to see how a saved
  alternative shifts spend lens-by-lens before choosing. It **re-uses the sealed scenario reads**
  (`getScenarioComparison` for both run ids) so the numbers are byte-identical to each version's own
  comparison table — **no re-derivation, no drift** (data-fidelity contract). Without it, comparing
  versions means eyeballing two separate tables.

### Props
| Prop | Type | Purpose |
|---|---|---|
| `slug` | `string` | Run slug for the fetch. |
| `left` | `AnalysisSummary` | The working build (selected analysis). |
| `right` | `AnalysisSummary` | The saved version chosen in the page's `<select>`. |

### State
- `rows: { left: ScenarioComparisonRow[]; right: ScenarioComparisonRow[] } | null` — both fetched sets; `null` = loading.
- `error: string | null`.

### Effect (data load)
- `useEffect` keyed on `[slug, left.analysis_run_id, right.analysis_run_id]`. Sets `rows=null`,
  `error=null`, then `Promise.all([getScenarioComparison(slug,left.id), getScenarioComparison(slug,right.id)])`.
  Uses an `active` flag (not AbortController) to ignore late resolves after unmount/dep-change. On
  error: `err instanceof ApiError ? err.detail : "Could not load the comparison."`.

### Derived `merged`
- `rows ? rows.left.map(l => ({code,label,l, r: rows.right.find(x=>x.code===l.code) ?? null})) : []`.
  **WHY left-driven + match-by-code:** the seven lenses A–G are canonical; right is matched to left by
  lens code so columns always align even if a version differs. `r` is `null` if the saved version
  lacks that lens (defensive; renders "—").

### `title(a)` helper
- `a.label ? \`v${a.version} · ${a.label}\` : \`v${a.version}\`` — column header per version.

### States
- **error:** `px-5 py-8 text-center text-sm text-danger` → `{error}`.
- **loading** (`!rows`): `text-text-muted` → *"Loading comparison…"*.
- **loaded:** the table (`min-w-[820px]`, horizontal scroll under that width).

### PanelHeader
- Title "Compare versions". Description: *"The seven lenses for two versions side by side — your live
  working build vs a saved version. Δ is the saved version minus the working build (red = costs more)."*

### Table columns + DATA BINDINGS (5 cols)
Header: `Lens | {title(left)} · working | {title(right)} · saved | Δ spend | Save vs incumbent (work · saved)`.
Per `merged.map(({code,label,l,r}) => …)`, key=`code`. `delta = r ? r.total_spend - l.total_spend : null`.

| Col | Field (type) | Element / classes | FORMAT + PRECISION |
|---|---|---|---|
| Lens | `l.code` + `l.label` | `font-semibold text-text-strong` code, `text-text-muted` label; `l.is_recommended` → `StatusChip tone="green"` "REC" (ml-1.5) | code+label raw; REC chip when lens B. |
| working spend | `l.total_spend` (number) | `text-right font-display font-semibold tabular-nums text-text-strong` | **`formatMoney`** → whole-dollar USD `$1,234,568`, 0 decimals, comma groups, tabular-nums. |
| saved spend | `r?.total_spend` | `text-right tabular-nums text-text` | `r ? formatMoney(r.total_spend) : "—"`. Same whole-dollar format; `"—"` when lens missing in saved. |
| Δ spend | derived `delta` (saved − working) | `text-right font-semibold tabular-nums`, **colour = sign**: null/0 → `text-text-faint`; `>0` → `text-danger` (costs more); `<0` → `text-success` | `delta==null\|\|delta===0 ? "—" : \`${delta>0?"+":""}${formatMoney(delta)}\``. **`+` prefix on positive** (negative carries `formatMoney`'s own `-$…`? — note: `formatMoney` uses currency style which renders negatives as `-$X` in en-US; positive gets explicit `+`). Whole dollars. |
| Save vs incumbent (work·saved) | `l.savings_vs_incumbent_pct` + `r.savings_vs_incumbent_pct` (fractions) | `text-right tabular-nums text-text-muted` | `formatPercent(l.savings_vs_incumbent_pct)` ` · ` `r ? formatPercent(r.savings_vs_incumbent_pct) : "—"`. **§0 formatPercent: fraction ×100, 1 decimal, e.g. 5.2%.** Two values joined by " · ". |

================================================================================
## A5. ScenarioComparisonTable.tsx  (THE SEVEN-LENS TABLE)
================================================================================
- **Path:** `/home/user/KR_RFP/frontend/components/alignment/ScenarioComparisonTable.tsx`
- **Ext:** `.tsx` · **Empty?** No (5347 bytes, 144 lines) · **Census row:** 283.
- **`"use client"`**.
- **WHAT:** The **seven lenses A–G side by side** — the "which scenario" decision surface. Numbers are
  identical to the alignment workbook's Scenario Comparison tab (same gather). Selecting a lens drives
  the cell-by-cell ScenarioDetailPanel below.
- **DETAILED WHY:** This is the heart of the analysis. The engine produces seven award strategies
  (lenses); the buyer compares them on spend, savings, supplier count, cells, and capacity feasibility,
  then picks one to freeze. **B is flagged Recommended (default); A is the lowest-cost benchmark Δ is
  measured against** (per comment + types). Per comment, **below ~1100px the table scrolls horizontally
  (never reflows to cards)** so the lens-vs-lens read stays intact, and **DC stays the locked primary
  grouping** there — a deliberate "don't break the matrix" decision (D42 grain). Without it there is no
  comparison surface.

### Props
| Prop | Type | Purpose |
|---|---|---|
| `rows` | `ScenarioComparisonRow[]` | The seven lenses (from `getScenarioComparison`). |
| `selectedCode` | `string \| null` | The lens currently inspected (highlight + ring). |
| `onSelect` | `(code:string)=>void` | Row click → page sets `selectedCode` → loads detail. |

### State: NONE.

### Derived (§B5 — "every rollup reflects the set actually shown, never a stale full count")
- `shown = rows.length`.
- `capBreaches = rows.filter(r => r.cap_breach_count > 0).length` — # lenses over stated capacity.

### PanelHeader
- Title "Scenario lenses". Description: *"Each lens A–G reshapes the award below. Lens B is the
  recommended default; A is the lowest-cost benchmark. Select a lens to inspect it cell by cell."*
- Actions: `{shown} {shown===1?"lens":"lenses"}` and, when `capBreaches>0`, ` · ` +
  `text-danger` `{capBreaches} over stated capacity`. (Live count, never hardcoded 7.)

### Table (`min-w-[1100px]` → horizontal scroll under 1100px) — 8 columns
Header row: `Lens | Spend | Δ vs A | Save vs incumbent | Save vs STLY [modeled chip] | Suppliers | Cells | Capacity`.

Per `rows.map(r => …)`, key=`r.code`; `selected = r.code===selectedCode`; `overCap = r.cap_breach_count>0`;
`onClick={()=>onSelect(r.code)}`; selected row → `bg-accent-soft ring-1 ring-inset ring-brand-primary/30`.

| Col | Field (type, source) | Element / classes | FORMAT + PRECISION |
|---|---|---|---|
| Lens | `r.code`, `r.label`, `r.is_recommended` | a 6×6 rounded code badge (`h-6 w-6 font-display text-2xs font-extrabold`): selected→`bg-brand-primary text-white`; else recommended→`bg-success-bg text-success`; else `bg-surface-muted text-text-muted`. Then `font-semibold text-text-strong` label. `is_recommended` → `StatusChip tone="green"` "Recommended". | code raw (A–G); label raw. |
| Spend | `r.total_spend` (number) | `text-right font-display font-semibold tabular-nums text-text-strong` | **`formatMoney`** → whole-dollar USD, 0 dp, comma groups. |
| Δ vs A | `r.delta_vs_a` (number; spend Δ vs lens A) | `text-right tabular-nums text-text-muted` | `r.delta_vs_a===0 ? "—" : formatMoney(r.delta_vs_a)`. Whole dollars; lens A itself shows "—" (its own Δ is 0). Negatives via `formatMoney` currency `-$…`. |
| Save vs incumbent | `r.savings_vs_incumbent_pct` (fraction) | `text-right tabular-nums font-semibold text-success` | **`formatPercent`** → fraction×100, **1 decimal**, e.g. `5.2%`. Always green (savings framed positive). |
| Save vs STLY | `r.savings_vs_stly_pct` (fraction vs synthetic prior-year) | `text-right tabular-nums text-text-faint` | `formatPercent` 1 dp. Header carries a **`StatusChip tone="modeled"` "modeled"** chip (amber) — flags it as a modeled/synthetic proxy, not actuals (data-fidelity honesty). Faint text de-emphasizes. |
| Suppliers | `r.supplier_count` (number) | `text-right tabular-nums text-text` | **`formatCount`** → integer, locale grouping. |
| Cells | `r.cell_count` (number) | `text-right tabular-nums text-text` | `formatCount` integer. |
| Capacity | `r.cap_breach_count` (number) | `text-right tabular-nums` | `overCap ? <StatusChip tone="gated">{r.cap_breach_count} over</StatusChip> : <span text-text-faint>Feasible</span>`. Gated=danger chip with the breach count; else faint "Feasible". (Stated-capacity, E-38.) |

- **Navigation:** rendered by alignment page only when `comparison.length>0` and not loading/error. Row
  click → `setSelectedCode` → detail effect fires.

================================================================================
## A6. ScenarioDetailPanel.tsx  (THE CELL-BY-CELL MATRIX + FREEZE TRIGGER)
================================================================================
- **Path:** `/home/user/KR_RFP/frontend/components/alignment/ScenarioDetailPanel.tsx`
- **Ext:** `.tsx` · **Empty?** No (9651 bytes, 283 lines) · **Census row:** 284.
- **`"use client"`** — expand/collapse state.
- **WHAT:** **One lens inspected cell-by-cell — the workbench matrix.** Four headline stat tiles
  (spend + two savings + cell count), a scenario-level capacity-feasibility chip, the governed Freeze
  trigger, and a per-(DC × Lot × Item × TF) competitive grid. Each cell row **expands** to the full
  supplier picture (price, RecScore, share, flags). Contains 3 sub-components: `Stat`, `CellRows`,
  `SupplierGrid`.
- **DETAILED WHY:** After choosing a lens, the buyer audits *why* — which supplier won each cell, at
  what price, vs the baseline and the cheapest bid, with the engine's RecScore and the awarded share.
  This is the **evidence surface for the freeze decision.** Per comment: **DC is the locked primary
  grouping; the matrix scrolls horizontally below ~1100px and never reflows to cards** — preserving the
  competitive read. The footer states the governance stance (**"Engine output — decision support only.
  A human asserts the freeze; each assertion is audit-evented"** — ADR-0006). Without it the lens is a
  number with no provenance.

### Props
| Prop | Type | Default | Purpose |
|---|---|---|---|
| `detail` | `ScenarioDetail` | — | The lens: code, label, description, `savings`, `cells[]`. |
| `frozenAwardId` | `string \| null` | — | If set, this lens is already frozen → header shows the frozen chip instead of the Freeze button. |
| `onFreeze` | `()=>void` | — | Opens the page's FreezeAwardModal. |
| `readOnly` | `boolean` | `false` | Viewing a sealed/historic analysis → Freeze button **disabled**. |
| `capBreachCount` | `number \| null` | `null` | Stated-capacity breach count for THIS lens (from the comparison rollup, E-38). `null` ⇒ indicator hidden. |

### State
- `expanded: Set<number>` — `useState(new Set())`. The set of expanded cell-row indices.
- `toggle(i)` — immutably clones the set, adds/removes `i`. **WHY a Set of indices:** multiple rows can
  be open at once; keyed by positional index `i`.

### Derived
- `s = detail.savings` (the `ScenarioSavingsSummary`).
- `showCap = capBreachCount != null`; `capFeasible = (capBreachCount ?? 0) === 0`. **WHY sourced from
  the comparison rollup, not recomputed:** comment — "it can never disagree with the per-lens row above
  it (§B5)." (Stated-capacity, E-38 — distinct from concentration.)

### PanelHeader
- Title: `Lens {detail.code} — {detail.label}` (`font-display text-base font-bold`).
  - `detail.is_recommended` → `StatusChip tone="green"` "Recommended".
  - `showCap` → `StatusChip tone={capFeasible?"green":"gated"}`:
    - feasible → "Feasible vs stated capacity";
    - breached → `` `Over stated capacity · ${capBreachCount} ${capBreachCount===1?"cell":"cells"}` `` (singular/plural).
- `description = detail.description` (raw lens description).
- **Actions (the freeze gate trigger):**
  - If `frozenAwardId` → `StatusChip tone="frozen">Frozen · {frozenAwardId.slice(0,8)}</StatusChip>`
    (**first 8 chars of the award id**).
  - Else → primary `Button size="sm"` with a padlock SVG + "Freeze award", `onClick={onFreeze}`,
    **`disabled={readOnly}`** (historic view disables freezing).

### Stat tiles (4-up grid `grid-cols-2 sm:grid-cols-4`, `gap-px bg-border-hairline`) — DATA BINDINGS
Each via `<Stat label value sub? positive? modeled? />`. `Stat` renders: label (`text-2xs uppercase
text-text-subtle`, + "modeled" chip if `modeled`), value (`font-display text-base font-bold
tabular-nums text-text-strong`), optional `sub` (`text-xs font-semibold tabular-nums`,
`positive?text-success:text-text-muted`).

| Tile | Field | value FORMAT | sub FORMAT |
|---|---|---|---|
| Total spend | `s.total_spend` | `formatMoney` whole-dollar USD, 0 dp | — |
| Save vs incumbent | `s.savings_vs_incumbent` ($) / `s.savings_vs_incumbent_pct` (frac) | `formatMoney(s.savings_vs_incumbent)` whole-dollar | `sub=formatPercent(s.savings_vs_incumbent_pct)` 1 dp; `positive` → green |
| Save vs STLY | `s.savings_vs_stly` ($) / `s.savings_vs_stly_pct` (frac) | `formatMoney(s.savings_vs_stly)` whole-dollar | `sub=formatPercent(s.savings_vs_stly_pct)` 1 dp; **`modeled`** → amber "modeled" chip on label, sub is muted (not green) |
| Award cells | `detail.cells.length` | `String(detail.cells.length)` — **raw integer, no formatter** | — |

### Matrix table (`min-w-[1100px]`) — 6 columns, header `[expand] | Award cell · DC / Lot / Item / TF | Demand | Baseline | Min bid | Recommended`
Per `detail.cells.map((cell,i) => <CellRows … />)`, key = `` `${cell.dc}-${cell.lot}-${cell.item}-${cell.tf}` ``.

**`CellRows` summary row** (`onClick={onToggle}`):
| Col | Field (type) | Element | FORMAT + PRECISION |
|---|---|---|---|
| expand | `expanded` | `text-text-subtle` → `▾` (open) / `▸` (closed) | glyph only. |
| Award cell | `cell.dc`,`cell.lot`,`cell.item`,`cell.tf` (strings, D23 names) | `font-semibold text-text-strong` DC + ` · ` + `text-text-muted` `{lot} / {item} / {tf}` | raw names (NOT raw ids — D23 name resolution; data-fidelity rule "never rename entities to raw IDs"). |
| Demand | `cell.volume` (number) | `text-right tabular-nums text-text` | **`formatCount`** integer, locale grouping. |
| Baseline | `cell.baseline_price` (number; incumbent-routing baseline $/case) | `text-right tabular-nums text-text-faint` | **`formatPrice`** — bare number, **2 decimals**, no symbol. |
| Min bid | `cell.min_price` (number\|null) | `text-right tabular-nums text-text` | `formatPrice` 2 dp; `null` → "—". |
| Recommended | `cell.recommended` (`SupplierCellRef\|null`) | flex group | If set: `font-semibold` `supplier` name + `font-display tabular-nums text-text-muted` `formatPrice(cell.recommended.price)` (2 dp) + (if `rec_type`) `StatusChip tone="neutral">{rec_type}</StatusChip>` (the B-only reason label, "" for others). Else → `text-text-subtle "—"`. |

**Expanded sub-row** (`expanded` true): `TR > TD colSpan={6} bg-surface-subtle` → `SupplierGrid`.

**`SupplierGrid`** — inner `<table class="w-full text-sm">`, header `Supplier | $/case | RecScore | Share | Flags`.
- Empty: `cell.suppliers.length===0` → `td colSpan={5} text-text-subtle` *"No eligible bids in this cell."*
- Else per `cell.suppliers.map(sup => …)`, key=`sup.name`, row `border-t border-border-hairline`:

| Col | Field (type) | Element | FORMAT + PRECISION |
|---|---|---|---|
| Supplier | `sup.name` (string) | `text-text-strong` | raw name. |
| $/case | `sup.price_per_case` (number\|null) | `text-right font-display tabular-nums text-text` | **`formatPrice`** 2 dp; `null` → "—". |
| RecScore | `sup.rec_score` (number\|null, 0–100) | `text-right tabular-nums text-text-muted` | **`sup.rec_score == null ? "—" : sup.rec_score.toFixed(1)`** — **1 decimal** (inline, NOT formatPrice). |
| Share | `sup.volume_share` (fraction; 0 if not awarded) | `text-right tabular-nums text-text` | **`sup.volume_share > 0 ? formatPercent(sup.volume_share) : "—"`** — fraction×100, **1 decimal**; zero share → "—" (not "0.0%"). |
| Flags | `sup.is_recommended`,`is_min`,`is_incumbent` (bools) | flex chips | `is_recommended` → green "Awarded"; `is_min` → accent "Min"; `is_incumbent` → slate "Incumbent". Any combination. |

### Footer (governance note)
- Clock-ish SVG + `text-xs text-text-muted`: *"Engine output — decision support only. A human asserts
  the freeze; each assertion is audit-evented. DC is the locked primary grouping."* (`border-t
  bg-surface-subtle px-5 py-3`).

### States
- No internal loading/error (parent gates rendering on `detail && detail.code === selectedCode`).
- **frozen-already:** header chip replaces button. **read-only:** Freeze button disabled.
- **cell-collapsed / expanded:** toggle. **no-bids cell:** the "No eligible bids" sub-row.

================================================================================
## A7. FreezeAwardModal.tsx  (THE GOVERNED FREEZE ASSERT-GATE)
================================================================================
- **Path:** `/home/user/KR_RFP/frontend/components/alignment/FreezeAwardModal.tsx`
- **Ext:** `.tsx` · **Empty?** No (2795 bytes, 85 lines) · **Census row:** 279.
- **`"use client"`** — uses `useAuth`, local input.
- **WHAT:** Freeze a chosen lens into a **FROZEN award** — the governed, immutable decision (ADR-0006).
  Built on the shared `AssertModal`: summary of the lens being frozen → award-code field → **named
  assertion checkbox** → confirm. Collects the buyer's award code; `onConfirm(awardCode)` fires with
  the exact arg the page's `freezeAward` call uses.
- **DETAILED WHY:** Freezing is the single most consequential, irreversible governance action in the
  product — it promotes a lens to the official award and locks it (later changes become append-only
  layers, never edits). It MUST go through the AssertModal pattern so that: (1) the buyer sees exactly
  what they're freezing, (2) they tick a **named, personal assertion** recorded against their username,
  (3) the **`FROZEN` audit event** that will be written is shown up front. The POST + its loading/error
  are owned by the page (separation of concerns; the modal is reusable/testable). Without this gate the
  award could be set with no accountable assertion.

### Props
| Prop | Type | Purpose |
|---|---|---|
| `open`/`onClose` | bool/fn | Visibility. |
| `onConfirm` | `(awardCode:string)=>void` | Fires trimmed code → page `handleFreezeConfirm`. |
| `submitting` | `boolean` | Loading. |
| `error` | `string\|null` | Server error. |
| `scenarioCode` | `string` | The lens code being frozen (chip). |
| `scenarioLabel` | `string` | The lens label (summary). |
| `suggestedCode` | `string` | Pre-filled award code (page builds `AWD-{COMMODITY}-{lens}`). |

### Auth + State
- `const { user } = useAuth();` — `user?.username ?? "you"` woven into the assertion line by AssertModal.
- `code: string` — `useState(suggestedCode)`. Re-seeded on open: `useEffect(()=>{ if(open) setCode(suggestedCode) },[open,suggestedCode])`.
- `trimmed = code.trim()`.

### THE GATE (delegated to `AssertModal`, ui/AssertModal.tsx)
- `eventType="FROZEN"` (audit event chip), `actorName={user?.username ?? "you"}`, `confirmLabel="Freeze award"`, `loading={submitting}`.
- **`error={ trimmed ? error : (error ?? "Enter an award code to freeze.") }`** — if the code is blank,
  surface a guidance error even when the server error is null.
- `onConfirm={()=>{ if(trimmed) onConfirm(trimmed); }}` — only fires with a non-empty code.
- **AssertModal internals enforcing the gate** (`ui/AssertModal.tsx`):
  - Local `asserted` checkbox state (reset on open) + optional rationale (not used here — no `withRationale`).
  - `canConfirm = asserted && rationaleOk && !loading` → the **Confirm button is DISABLED until the
    named-assertion checkbox is ticked.** Checkbox label: *"I, **{username}**, assert this decision.
    Recorded against my name in the audit trail."*
  - Shows "Audit event: [FROZEN]" chip (`tone="sealed"`).
  - Cancel disabled while loading; Escape/backdrop close via base `Modal`.

### DATA BINDINGS (summary block)
- `StatusChip tone="sealed">Lens {scenarioCode}</StatusChip>` + `font-semibold text-text-strong` `{scenarioLabel}`.
- Copy: *"Freezing promotes this lens to the official award. It is **immutable** — later changes are
  recorded as append-only post-award layers, never edits."*
- `FormField label="Award code"` (required *) hint *"Names the frozen award, e.g. AWD-2026-TOMATO-1."*
  → `Input id="award-code" value={code}` placeholder *"AWD-2026-…"* `disabled={submitting}` `autoFocus`.

### States: default(prefilled code, assertion un-ticked → confirm disabled) · code-blank(guidance error) · asserted(confirm enabled) · submitting(spinner, cancel disabled) · error(server detail).
- **Page guards** (alignment/page.tsx): `scenarioLabel` passed only when `detail.code === selectedCode`
  (`detail?.code===selectedCode ? detail?.label ?? "" : ""`) — prevents a stale label showing lens A
  while freezing lens B. The page's `handleFreezeConfirm` records `frozen[{analysisId}:{code}]=award_id`.

---

# PART B — components/awards/** (3 files)

================================================================================
## B1. AwardsListPanel.tsx
================================================================================
- **Path:** `/home/user/KR_RFP/frontend/components/awards/AwardsListPanel.tsx`
- **Ext:** `.tsx` · **Empty?** No (2777 bytes, 89 lines) · **Census row:** 288.
- **`"use client"`**.
- **WHAT:** The cycle's **frozen awards** table. Each is an immutable baseline; post-award price moves
  are append-only versioned layers (latest version shown). Selecting one drives AwardDetailPanel.
- **DETAILED WHY:** Mirror of AnalysisRunsPanel but for the post-award world. A run can have one (or
  more) frozen awards; this is the selector/ledger. Shows the latest layer version per award so the
  buyer sees at a glance which awards have been repriced. Without it, the awards screen has no entry
  point to a specific award's detail.

### Props
| Prop | Type | Purpose |
|---|---|---|
| `awards` | `AwardSummary[]` | Frozen awards (parent `listAwards`, oldest-first). |
| `selectedId` | `string\|null` | Highlighted `award_id`. |
| `onSelect` | `(id:string)=>void` | Row click → load detail. |

### State: NONE.

### States
- **Empty** (`awards.length===0`): *"No frozen award yet — freeze a scenario on the alignment screen to
  create one."* (`px-5 py-10 text-center text-sm text-text-muted`).
- **Populated:** table.

### PanelHeader: "Frozen awards" + *"Each award is an immutable baseline; post-award price moves are append-only, versioned layers."*

### Table columns + DATA BINDINGS (5 cols) — header `Award | Scenario | Cells | Version | Frozen`
Per `awards.map(a => …)`, key=`a.award_id`, `selected = a.award_id===selectedId`; selected row `bg-accent-soft`.

| Col | Field (type) | Element / classes | FORMAT + PRECISION |
|---|---|---|---|
| Award | `a.award_code` (string) | `font-semibold text-text-strong` + `StatusChip tone="frozen">Frozen` + (if selected) `StatusChip tone="accent">Selected` | raw code + chips. |
| Scenario | `a.scenario_code` (string) | `text-text` → `Lens {a.scenario_code}` | raw lens code, prefixed "Lens ". |
| Cells | `a.line_count` (number) | `text-right tabular-nums text-text` | **raw integer** (`{a.line_count}`) — no formatter (small count). |
| Version | `a.latest_version` (number; 0=baseline only) | `TD` | `a.latest_version===0 ? <span text-text-muted>baseline</span> : <StatusChip tone="amber">v{a.latest_version}</StatusChip>` — baseline (gray text) vs amber `v{n}` chip. |
| Frozen | `a.frozen_at` (ISO) | `text-text-muted` | **`formatTimestamp`** localized date+time (no seconds); bad ISO → raw. |

================================================================================
## B2. AwardDetailPanel.tsx  (BASELINE → EFFECTIVE LINES + AUDIT TRAIL)
================================================================================
- **Path:** `/home/user/KR_RFP/frontend/components/awards/AwardDetailPanel.tsx`
- **Ext:** `.tsx` · **Empty?** No (8516 bytes, 212 lines) · **Census row:** 287.
- **`"use client"`**.
- **WHAT:** **One frozen award in a two-column post-award layout.** LEFT: the award card — awarded lines
  (frozen baseline → current effective price, per DC × Lot × TF) + adjustment/governance actions in the
  header + an explanatory footer. RIGHT: the chronological **audit trail** (v0 FROZEN → vN append-only
  layers). A **positive Δ = the effective price rose above the frozen baseline.**
- **DETAILED WHY:** The frozen award is the immutable baseline (v0); real-world price moves (market
  hikes, contract amendments) are recorded as append-only layers, never edits (ADR-0014). The buyer
  needs to see, per cell, the immutable frozen price next to the current effective price and the delta,
  AND the full append-only history with who/when/why. This panel is the **single authoritative view of
  the live contract state + its provenance**. The footer states the record (not any generated guide) is
  authoritative. Without it, post-award drift is invisible and unauditable.

### Props
| Prop | Type | Default | Purpose |
|---|---|---|---|
| `detail` | `AwardDetail` | — | award_code, scenario_code, frozen_at, frozen_by, latest_version, `lines[]`, `versions[]`. |
| `onAdjust` | `()=>void \| undefined` | — | Header "Record adjustment" button (rendered only if provided). |
| `onFinalize` | `()=>void \| undefined` | — | Header "Finalize & close run" button (rendered only if provided). |
| `canFinalize` | `boolean` | `false` | Enables Finalize only when a FROZEN award exists to close out against. |

### State: NONE.

### Derived (§B5)
- `adjustedLines = detail.lines.filter(l => l.delta !== 0).length` — count of repriced cells (for "N repriced" in the description).

### LEFT — Award card
**Header:** padlock badge + `font-display text-base font-bold` `{detail.award_code}` +
`StatusChip tone="frozen">Frozen · Lens {detail.scenario_code}` + (if `latest_version>0`)
`StatusChip tone="amber">v{detail.latest_version}`.
- **Description binding:** `Frozen {formatTimestamp(detail.frozen_at)} by <b text-text>{detail.frozen_by}</b>
  · immutable baseline · {detail.lines.length} {cell/cells}` + (if `adjustedLines>0`) ` · {adjustedLines} repriced`.
  - `formatTimestamp` localized; `frozen_by` raw username; line count raw int with singular/plural.
- **Actions:** if `onAdjust` → secondary "Record adjustment" (pencil SVG). If `onFinalize` → primary
  "Finalize & close run" (padlock SVG), **`disabled={!canFinalize}`**, `title` when disabled =
  *"A FROZEN award is required to close out the run."*

**Lines table** (`min-w-[760px]`) — 6 cols, header `Award cell | Supplier | Share | Frozen $/case | Effective $/case | Δ`.
Per `detail.lines.map(l => …)`, key = `` `${l.dc}-${l.lot}-${l.tf}-${l.supplier}` ``.

| Col | Field (type) | Element / classes | FORMAT + PRECISION |
|---|---|---|---|
| Award cell | `l.dc`,`l.lot`,`l.tf` (names, D23) | `font-semibold text-text-strong` DC; `text-2xs text-text-subtle` `{l.lot} · {l.tf}` | raw names (no item col here — award grain is DC×Lot×TF×Supplier). |
| Supplier | `l.supplier` (string) | `font-medium text-text` | raw name. |
| Share | `l.volume_share` (fraction 0–1) | `text-right tabular-nums text-text` | **`formatPercent`** fraction×100, **1 decimal** (e.g. `100.0%`, `40.0%`). |
| Frozen $/case | `l.frozen_price` (number) | `text-right tabular-nums text-text-faint` | **`formatPrice`** bare, **2 decimals**, faint (the immutable baseline, de-emphasized). |
| Effective $/case | `l.effective_price` (number; baseline overlaid by every layer) | `text-right font-display font-semibold tabular-nums text-text-strong` | `formatPrice` **2 dp**, strong (the live price, emphasized). |
| Δ | `l.delta` (number = effective − frozen) | `text-right font-semibold tabular-nums`, **colour by sign**: `>0`→`text-danger`; `<0`→`text-success`; `0`→`text-text-subtle` | `l.delta===0 ? "—" : \`${l.delta>0?"+":"−"}${formatPrice(Math.abs(l.delta))}\``. **Sign is MANUAL** — `+` for rises, `−` (U+2212 true minus, not hyphen) for drops — wrapping `formatPrice(Math.abs(delta))` at **2 dp**. Zero → "—". |

**Footer note:** info SVG + *"The **frozen** column is the immutable baseline (v0). The **effective**
column reflects all append-only post-award layers to date. The award record is authoritative —
generated guides are renders of it."*

### RIGHT — Audit trail panel
**Header:** "Audit trail" + *"v0 is the frozen baseline; each later version is an append-only,
date-stamped layer."*

**Versions table** — 6 cols, header `Version | Type | Effective | Reason | Cells | Recorded`.
Per `detail.versions.map(v => …)`, key=`v.version_no`.

| Col | Field (type) | Element | FORMAT + PRECISION |
|---|---|---|---|
| Version | `v.version_no` (number) | `v.version_no===0 ? <StatusChip tone="frozen">v0 · FROZEN</StatusChip> : <StatusChip tone="amber">v{v.version_no}</StatusChip>` | v0 = green FROZEN chip; later = amber `v{n}`. |
| Type | `v.adjustment_type` (string) | `text-text` | raw (data-derived, not a fixed enum — D28). |
| Effective | `v.effective_date` (ISO date `YYYY-MM-DD`) | `tabular-nums text-text-muted` | **raw date string** (NOT through formatTimestamp — it's a date, rendered as-is `YYYY-MM-DD`). |
| Reason | `v.reason` (string) | `text-text-muted` | raw rationale text. |
| Cells | `v.n_lines` (number) | `text-right tabular-nums text-text` | **raw integer**. |
| Recorded | `v.created_by` + `v.created_at` (ISO ts) | `text-text-muted` | `{v.created_by} · {formatTimestamp(v.created_at)}` — username raw + localized timestamp. |

### Layout / states
- Two-column grid `lg:grid-cols-[minmax(0,1.6fr)_minmax(280px,1fr)]` (left wider, right ≥280px); stacks
  to 1 col under lg. Left table scrolls horizontally under 760px.
- No internal loading/error (parent gates on `detail.award_id===selectedId`).
- **Δ states:** rose(red +), dropped(green −), unchanged(—). **baseline-only award:** `versions` has just
  v0; `lines` all delta 0; `latest_version` chip hidden.

================================================================================
## B3. RecordAdjustmentModal.tsx  (THE GOVERNED ADJUSTMENT ASSERT-GATE + CELL MATRIX)
================================================================================
- **Path:** `/home/user/KR_RFP/frontend/components/awards/RecordAdjustmentModal.tsx`
- **Ext:** `.tsx` · **Empty?** No (8881 bytes, 255 lines) · **Census row:** 289.
- **`"use client"`** — `useAuth`, drafts/type/date state.
- **WHAT:** Record a governed, **append-only post-award adjustment LAYER** (ADR-0014). Built on
  `AssertModal` with `withRationale` (the rationale IS the layer's reason). Summary = a checklist of
  award cells to reprice (each with a new-$/case input) + adjustment type + effective date. The frozen
  baseline is never edited; this writes a new version on top.
- **DETAILED WHY:** Post-award the contract price legitimately moves (market hikes/drops, tolerance
  bands, contract amendments). To stay auditable + immutable, every move is a **new versioned layer**
  with a named assertion + a captured reason, never an in-place edit. This modal is the **only way to
  create such a layer**: it forces cell selection, a positive new price per cell, a type, an effective
  date, a free-text reason (rationale, E-40), and the personal assertion. The `drafts` map is the single
  source of truth — *a cell is selected iff its key is present; the value is the new-price string.*
  Without it, post-award reality can't be recorded faithfully.

### Constants / helpers
- `TYPE_SUGGESTIONS = ["MARKET_HIKE","MARKET_DROP","TOLERANCE_BAND","CONTRACT_AMENDMENT"]` — datalist
  hints only; types are **free text / data-derived (D28)**, not an enforced enum.
- `cellKey(l) = \`${l.dc_id}|${l.lot_id}|${l.tf_id}|${l.supplier_id}\`` — the composite cell identity
  (uses IDs, not names, to be unambiguous when POSTing).
- `today() = new Date().toISOString().slice(0,10)` → `YYYY-MM-DD`.
- `isValidPrice(raw)` — true iff non-blank, `Number.isFinite`, **`> 0`** (strictly positive; rejects 0 and negatives).

### Props
| Prop | Type | Purpose |
|---|---|---|
| `open`/`onClose` | bool/fn | Visibility. |
| `onConfirm` | `(body:RecordAdjustmentBody)=>void` | Fires the full payload → page `handleAdjustConfirm`. |
| `submitting` | `boolean` | Loading → disables every field. |
| `error` | `string\|null` | Server error. |
| `awardCode` | `string` | For the description copy. |
| `lines` | `AwardLineView[]` | The award's cells (the checklist source). |

### State
- `drafts: Record<string,string>` — `useState({})`. **Selection + edited-price in one map**: key=`cellKey`, value=new-price string. Cleared on open.
- `adjustmentType: string` — `useState("")`. Cleared on open.
- `effectiveDate: string` — `useState(today())`. Reset to today on open.
- `useEffect(()=>{ if(!open) return; setDrafts({}); setAdjustmentType(""); setEffectiveDate(today()); },[open])` — full reset each open.

### Interactions / derived
- `toggle(line)` — if key in drafts → remove (deselect); else **seed the input with the cell's current
  effective price**: `{...prev, [key]: line.effective_price.toFixed(2)}` (**2 decimals** start value).
- `setPrice(key,value)` — overwrites the draft string on input change.
- `selectedKeys = Object.keys(drafts)`; `allPricesValid = selectedKeys.every(k=>isValidPrice(drafts[k]))`.
- **`formReady = selectedKeys.length>0 && allPricesValid && adjustmentType.trim()!=="" && effectiveDate!==""`**
  — gates the *local* form (cells+type+date). The **named assertion + rationale are gated by AssertModal**.
- `submit(rationale)` — guards `formReady`, then builds `changes: AdjustmentLineChange[]` from
  `lines.filter(l=>cellKey(l) in drafts).map(l => ({dc_id,lot_id,tf_id,supplier_id, new_price:Number(drafts[cellKey(l)])}))`
  and fires `onConfirm({ adjustment_type: adjustmentType.trim(), effective_date: effectiveDate, reason: rationale, changes })`.
  **WHY iterate `lines` (not `drafts`):** preserves the canonical cell identity fields; `new_price`
  parsed `Number(...)` at submit.
- **`effectiveError`** — `error ?? (!formReady && selectedKeys.length===0 ? "Select at least one cell to
  reprice." : !formReady ? "Complete the new price, type and effective date." : null)` — surfaces a
  staged guidance message if the human asserts before completing the form.

### THE GATE (`AssertModal`)
- `eventType="ADJUSTMENT"`, `actorName={user?.username ?? "you"}`, **`withRationale`**,
  `rationaleLabel="Reason"`, **`rationaleRequired`**, `confirmLabel="Record adjustment"`,
  `loading={submitting}`, `error={effectiveError}`, `onConfirm={submit}`.
- AssertModal enforces: `canConfirm = asserted && (rationale.trim().length>0) && !loading` — **Confirm
  disabled until BOTH the named-assertion checkbox is ticked AND a non-empty Reason is typed.** The
  Reason textarea = the layer's `reason`. Audit-event chip shows "ADJUSTMENT".

### DATA BINDINGS (summary block)
- Description: `` `Append a new versioned layer over ${awardCode} — the baseline never changes.` ``.
- Copy: *"This writes an **append-only layer** on top of the frozen baseline. Pick the cells to reprice
  and enter each new $/case."*
- **Cells-to-reprice list** (`max-h-56 overflow-y-auto`, divided): header *"Cells to reprice"* +
  `{selectedKeys.length} selected`. Per `lines.map(l => …)`, key=`cellKey(l)`, `checked = key in drafts`:
  - Checkbox (`accent-brand-primary`, `disabled={submitting}`) → `toggle(l)`.
  - Label: `text-text-strong` `{l.dc}` ` · ` `text-text-muted {l.lot} · {l.tf}` ` · ` `font-medium text-text {l.supplier}` (names, truncate).
  - Current effective price: `w-20 text-right tabular-nums text-text-faint` → **`formatPrice(l.effective_price)`** (2 dp).
  - If checked: `Input type="number" inputMode="decimal" step="0.01" min="0"` aria-label `New price for {supplier}`,
    `value={drafts[key]}`, `onChange={setPrice}`, **`invalid={!isValidPrice(drafts[key])}`** (red ring on ≤0/blank), `disabled={submitting}`.
    Else: `w-28 text-right text-text-subtle "—"`.
  - Helper: *"Current effective $/case shown; enter the new price (> 0)."*
- **Adjustment type** `FormField` (required): `Input list="adj-type-options"` placeholder "MARKET_HIKE"
  + `<datalist>` of the 4 suggestions. Hint *"A short label for the layer."*
- **Effective date** `FormField` (required): `Input type="date"` `value={effectiveDate}`. Hint *"When the new prices take effect."* → posts ISO `YYYY-MM-DD`.

### States
- default(nothing selected → "Select at least one cell" guidance) · cell-selected(input seeded w/ effective price)
  · invalid-price(red ring, guidance "Complete the new price…") · type/date-missing(guidance) ·
  asserted+reason(confirm enabled) · submitting(all disabled, spinner) · server-error(detail).
- Page wiring (awards/page.tsx): on success → success Alert "Recorded adjustment v{n}" + a **download
  link** for the regenerated post-award document (`downloadRunFile(slug, filename)`); bumps `reloadNonce`
  to re-fetch detail and re-lists awards (latest_version advances).

---

# CROSS-CUTTING NOTES (Layer-3)

### Parent-page wiring & state machine (alignment) — `app/(app)/runs/[slug]/alignment/page.tsx`
- Owns ALL network state for A1–A7. Loads `run`, `analyses`, then `comparison` (auto-selects the
  recommended lens B or `rows[0]`), then `detail`. **Race-safety:** both the comparison and detail
  effects use `AbortController`, and detail is cleared SYNCHRONOUSLY on selection change so a stale
  lens can never render/freeze (comment-documented; also a belt-and-suspenders render guard
  `detail.code===selectedCode`).
- **read-only / historic:** `readOnly = selectedAnalysis.version !== liveAnalysis.version` → disables
  Freeze (passed to ScenarioDetailPanel) + shows an amber "viewing a sealed, read-only analysis" banner
  with a "View live version" button.
- **suggestedAwardCode** = `AWD-{COMMODITY_SLUG}-{selectedCode ?? "B"}` (commodity upper-cased,
  non-alnum→`-`, capped 16 chars) → FreezeAwardModal default.
- **RunStatusStrip** cells bind: Run state (Historic/Live), Analysis (`Sealed · v{version}` / Not
  sealed), Award (Frozen / Not yet frozen), Audit ("Hash-chain current").
- **headerChips** (decision header) recomputed from the selected lens detail: #DCs, #lots, #suppliers,
  #award cells (all `Set`-deduped, singular/plural), + the TF horizon joined by " · " — reflect the lens
  actually shown (§B5).

### Parent-page wiring (awards) — `app/(app)/runs/[slug]/awards/page.tsx`
- Owns state for B1–B3 + the Finalize AssertModal (`eventType="CLOSED"`, `confirmLabel="Close run"`,
  with cautions "locks the run"). Finalize gated on `hasFrozenAward && !closed`. On close → success
  Alert "Run closed · {won} award + {not_won} rejection notice(s) · CLOSED event recorded."
  - **RecordAdjustment** success → re-fetch via `reloadNonce`, re-list awards, show download link.
  - **NOTE:** the Finalize `AssertModal` is rendered inline in the page (NOT a component in this slice's
    scope) — but it is the third governed assert-gate and shares the same pattern as B3/A7.

### The three governed AssertModal gates (the freeze / adjust / close pattern)
All three (FreezeAward `FROZEN`, RecordAdjustment `ADJUSTMENT`, page-level Finalize `CLOSED`) route
through `ui/AssertModal.tsx`: summary → (optional cautions) → (optional required rationale) → **named
assertion checkbox bound to `user.username`** → Confirm disabled until asserted (+ rationale if
required). The audit event that WILL be written is shown up front as a "sealed" chip. This is the
single, consistent governance UX for every irreversible action (ADR-0006 lineage).

### Precision summary (the analysis-UI decimals, at a glance)
- **Spend / savings $ totals:** `formatMoney` → **whole dollars** (0 dp), USD symbol, comma groups, tabular-nums. `{cents:true}` exists but is NOT used in this slice.
- **% (savings vs incumbent / STLY, volume share):** `formatPercent` → **1 decimal**, fraction input ×100. Zero share → "—" in SupplierGrid.
- **$/case prices (baseline, min, recommended, frozen, effective, draft seed):** `formatPrice` → **2 decimals**, NO symbol, tabular-nums.
- **RecScore:** `.toFixed(1)` → **1 decimal** (0–100 scale).
- **Counts (suppliers, cells, demand/volume, n_lines):** `formatCount` or raw integer, locale grouping, no decimals.
- **Δ signs:** spend Δ uses `+`/currency-`-`; price Δ uses manual `+`/`−`(U+2212) on `formatPrice(abs)`.
- **Timestamps:** `formatTimestamp` localized (no seconds); **effective_date kept raw `YYYY-MM-DD`** (it's a date, not a moment).

# VERIFICATION & GAPS
- **Verified (read-before-asserting, CLAUDE.md §5):** all 10 component files read end-to-end; the four
  formatters + inline `.toFixed` read from `lib/format.ts`; every TS field/type read from
  `lib/api/types.ts` (lines 171–359); `lib/api/alignment.ts` + `awards.ts` (endpoints); the shared
  `AssertModal`, `StatusChip`, `Modal`, `FormField` primitives; both parent pages for wiring/states.
  Census rows 278–284 / 287–289 confirmed; on-disk byte sizes equal census sizes.
- **GAP — capacity-feasibility semantics:** `cap_breach_count` is rendered as "over stated capacity" but
  the engine threshold/definition is backend-side (E-38); the UI only displays the count it's given. Not
  re-derivable from this slice. (Cross-ref: backend `app.domain.eng.*` / `awards.py` row 51 — out of F2b scope.)
- **GAP — `formatMoney` half-even vs half-up:** Intl rounding mode is engine/locale-dependent (V8 rounds
  half away from zero); at whole-dollar precision the last-cent direction on exact `.50` totals is not
  pinned in code. Noted, not a defect for display.
- **GAP — locale:** all formatters pass `undefined` locale → runtime default (no fixed `en-US`); thousands
  separators / month names follow the host. Intentional, but means rendered grouping is environment-dependent.
- **No stubs / placeholders / dropped data found** in any of the 10 files — all bind real sealed-engine /
  award fields; the "—" em-dash is a genuine null/zero placeholder, not mock content. Compliant with the
  ABSOLUTE REQUIREMENTS (no MVP, data fidelity).
