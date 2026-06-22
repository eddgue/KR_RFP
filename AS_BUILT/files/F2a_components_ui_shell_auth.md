# SLICE F2a — As-Built Audit: `components/ui/**`, `components/shell/**`, `components/auth/**`

> Exhaustive, read-only as-built audit produced to `AS_BUILT/AUDIT_STANDARD.md`.
> Layer-2 (per-file: path · what · detailed WHY · every export/function · deps · census cross-ref)
> and Layer-3 (every component · every prop · every visual state/variant · design tokens · every
> data binding · bindings to backend) for the 14 files in this slice. Nothing skipped, nothing
> assumed; where a value is unverifiable it is stated as such with the reason.

## Slice scope & census reconciliation

Directories audited (all `*.tsx`/`*.ts`, none empty):
- `frontend/components/ui/**` — Button, Input, FormField, Panel, Table, StatusChip, Modal, AssertModal, FileInput, `index.ts` (barrel).
- `frontend/components/shell/**` — AppShell, RunStatusStrip.
- `frontend/components/auth/**` — AuthProvider, AuthGuard.

All 14 files are present in `AS_BUILT/FILE_CENSUS.md` (rows 285–313). Sizes on disk match the
census byte-for-byte; none are empty (`empty?` column blank → not empty). Census rows:

| Census # | Path | ext | bytes | created | modified |
|---|---|---|---|---|---|
| 285 | `./frontend/components/auth/AuthGuard.tsx` | tsx | 1035 | 2026-06-21T03:05:25Z | 2026-06-21T03:05:25Z |
| 286 | `./frontend/components/auth/AuthProvider.tsx` | tsx | 2288 | 2026-06-21T03:05:25Z | 2026-06-21T03:05:25Z |
| 302 | `./frontend/components/shell/AppShell.tsx` | tsx | 4237 | 2026-06-21T03:05:25Z | 2026-06-22T04:08:23Z |
| 303 | `./frontend/components/shell/RunStatusStrip.tsx` | tsx | 1389 | 2026-06-22T04:08:23Z | 2026-06-22T04:08:23Z |
| 304 | `./frontend/components/ui/AssertModal.tsx` | tsx | 4507 | 2026-06-22T04:08:23Z | 2026-06-22T04:08:23Z |
| 305 | `./frontend/components/ui/Button.tsx` | tsx | 1687 | 2026-06-21T03:05:25Z | 2026-06-21T03:05:25Z |
| 306 | `./frontend/components/ui/FileInput.tsx` | tsx | 3010 | 2026-06-21T04:12:26Z | 2026-06-21T04:12:26Z |
| 307 | `./frontend/components/ui/FormField.tsx` | tsx | 839 | 2026-06-21T03:05:25Z | 2026-06-21T03:05:25Z |
| 308 | `./frontend/components/ui/Input.tsx` | tsx | 799 | 2026-06-21T03:05:25Z | 2026-06-21T03:05:25Z |
| 309 | `./frontend/components/ui/Modal.tsx` | tsx | 2799 | 2026-06-21T03:05:25Z | 2026-06-22T04:08:23Z |
| 310 | `./frontend/components/ui/Panel.tsx` | tsx | 1168 | 2026-06-21T03:05:25Z | 2026-06-21T03:05:25Z |
| 311 | `./frontend/components/ui/StatusChip.tsx` | tsx | 1645 | 2026-06-21T03:05:25Z | 2026-06-22T04:08:23Z |
| 312 | `./frontend/components/ui/Table.tsx` | tsx | 1710 | 2026-06-21T03:05:25Z | 2026-06-21T03:05:25Z |
| 313 | `./frontend/components/ui/index.ts` | ts | 789 | 2026-06-21T03:05:25Z | 2026-06-22T04:08:23Z |

Note on dates: census `created` for all is the same harvest timestamp (2026-06-21T03:05:25Z);
several were re-touched 2026-06-22T04:08:23Z — the same mtime cluster that introduced the governed
`StatusChip` tones, `RunStatusStrip`, `AssertModal`, and the AppShell re-skin (the "locked v2"
token migration referenced in `tailwind.config.ts` header). Filesystem `birth` times differ slightly
(see below) because the census mtimes were normalized at harvest; the relative ordering is consistent.

### Shared dependencies pulled in by this slice (audited here for binding completeness)
- `frontend/lib/cn.ts` — `cn(...parts)`: a dependency-free classname joiner. Filters falsy
  (`false | null | undefined`) and `.join(" ")`. Every component in this slice composes classes
  through it. WHY: avoids a `clsx`/`classnames` dependency for a 3-line need (longevity / fewer
  deps); the falsy-filtering is what lets call sites write `cond && "class"` inline.
- `frontend/lib/api/*` — the typed FastAPI client (`auth.ts`, `client.ts`, `index.ts`, `types.ts`).
  AuthProvider/AuthGuard bind to `me`, `logout`, `ApiError`, and the `User` type from here. The
  client centralizes `credentials: "include"` and the typed `ApiError`. Audited in the AuthProvider
  section below (these are the Layer-3 backend bindings for this slice).
- `frontend/tailwind.config.ts` + `frontend/app/globals.css` — the locked-v2 design tokens that
  every className in this slice resolves against. Token table reproduced in the Design Tokens
  appendix so the per-file token references are concrete (exact hex).

---

# UI primitives — `frontend/components/ui/**`

## `ui/Button.tsx` — census #305 (1687 B, 55 lines)

**What.** The single button primitive for the whole console: an accessible `<button>` with four
visual variants, two sizes, and a built-in loading spinner. Forwards a ref.

**Detailed WHY.** Centralizes button look + a11y (focus ring, disabled semantics, spinner) so no
screen hand-rolls a button. It exists as the lowest-level interactive primitive; `AssertModal`,
`AppShell` header (Log out), and most pages consume it. Shaped as a `forwardRef` so it can be used
as a Radix/anchor trigger or be focus-managed; `loading` collapses two states (busy + disabled) into
one prop so callers never forget to also disable a button mid-request — the chief correctness reason
(error reduction): a submit can't be double-fired because `disabled={disabled || loading}` is
enforced inside the primitive, not at each call site. Without it, every page would re-implement
variant colors and the disabled/loading coupling, and they would drift.

**Exports.**
- `interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement>` — inherits the full native
  button surface (`onClick`, `type`, `name`, `form`, `aria-*`, etc.) plus:
  - `variant?: "primary" | "secondary" | "ghost" | "danger"` — default `"primary"`. WHY: enumerated
    union, not free string, so the variant map is exhaustive and typos fail at compile.
  - `size?: "sm" | "md"` — default `"md"`. (No `lg`; the console is data-dense — gravity comes from
    color/placement, not size.)
  - `loading?: boolean` — default `undefined` (falsy). When truthy: renders the spinner AND disables
    the button.
  - (inherited) `disabled?: boolean`, `className?: string`, `children`, `...rest`.
- `const Button = forwardRef<HTMLButtonElement, ButtonProps>(...)` — the component.

**Every visual state / variant (exact classes → tokens).**
- `base` (always applied): `inline-flex items-center justify-center gap-2 rounded-md font-medium
  transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/40
  focus-visible:ring-offset-1 disabled:cursor-not-allowed disabled:opacity-55 whitespace-nowrap`.
  - `rounded-md` = 6px (Tailwind default; NOT the custom `control`/`card` radii).
  - focus ring uses `ring-accent/40` → `accent.DEFAULT #084999` at 40% alpha. (Note: globals.css also
    sets a global `:focus-visible` outline `2px solid #2478ce` = `brand.sky`; both apply — the Tailwind
    ring is the inset colored ring, the global outline is the 2px offset outline.)
  - disabled state: `cursor-not-allowed` + `opacity-55`.
- `variants.primary`: `bg-accent text-white hover:bg-accent-hover` → bg `#084999`, hover `#0a5bbf`,
  white text. The default, highest-gravity action.
- `variants.secondary`: `bg-white text-ink border border-line-strong hover:bg-surface-muted` →
  white bg, text `ink.DEFAULT #16243d`, border `line.strong #cdd3dc`, hover bg `surface.muted #eef0f3`.
  The neutral/secondary action (used by AppShell "Log out", AssertModal "Cancel").
- `variants.ghost`: `bg-transparent text-ink-muted hover:bg-surface-muted` → transparent, muted text
  `ink.muted #5b6b82`, hover `surface.muted`. Lowest gravity (icon/tertiary).
- `variants.danger`: `bg-white text-red-700 border border-line-strong hover:bg-red-50` → white bg,
  Tailwind `red-700` text, `red-50` hover. NOTE: danger uses raw Tailwind `red-*`, NOT the locked
  `danger` token (`#b3261e`). This is a *token drift* point: the danger Button does not route through
  the v2 `danger`/`danger-bg` tokens. Recorded as a gap below.
- `sizes.sm`: `h-8 px-3 text-sm` (32px tall). `sizes.md`: `h-9 px-4 text-sm` (36px tall). Both
  `text-sm` (14px); size differs by height + horizontal padding only.
- **Loading state:** when `loading` truthy, prepends `<span aria-hidden className="h-3.5 w-3.5
  animate-spin rounded-full border-2 border-current border-t-transparent" />` — a 14px spinner that
  inherits `currentColor` (so it matches each variant's text color), with a transparent top border
  to create the rotating gap. Children still render after the spinner (label stays visible).
- **Disabled-vs-loading coupling:** `disabled={disabled || loading}` — the native button is disabled
  if either is set; `disabled:` utility classes then style it.

**Side effects / errors.** None (pure presentational). Click handling is delegated via `...rest`.

**Deps.** `react` (`forwardRef`), `ButtonHTMLAttributes` type, `@/lib/cn`.

**Consumed by (Layer-3 reachability).** `ui/index.ts` re-exports `Button` + `ButtonProps`; used by
`AssertModal` (Cancel/Confirm), `AppShell` Header (Log out), and most page/panel components.

---

## `ui/Input.tsx` — census #308 (799 B, 27 lines)

**What.** The text-input primitive: a styled native `<input>` with an `invalid` flag and forwarded ref.

**Detailed WHY.** One place owning input height, border, focus ring, disabled and invalid styling, so
forms look identical and the invalid affordance (red border) is consistent. `forwardRef` so form
libraries / `FormField`'s `htmlFor` and focus management work. Minimal by design — it intentionally
does NOT own the label/error (that's `FormField`'s job): separation keeps the input reusable inside
and outside `FormField`.

**Exports.**
- `interface InputProps extends InputHTMLAttributes<HTMLInputElement>` — full native input surface
  plus `invalid?: boolean` (default `undefined`/false). WHY a boolean not an error string: the input
  only renders the *border* affordance; the message lives in `FormField`.
- `const Input = forwardRef<HTMLInputElement, InputProps>(...)`.

**Every visual state (classes → tokens).**
- Base: `h-9 w-full rounded-md border bg-white px-3 text-sm text-ink` → 36px tall, full width,
  6px radius, white bg, text `ink.DEFAULT #16243d`.
- Placeholder: `placeholder:text-ink-subtle` → `#8a97a8`.
- Focus: `focus:outline-none focus:ring-2 focus:ring-accent/40 focus:border-accent` → 2px ring at
  `#084999`/40% + border becomes `accent #084999`.
- Disabled: `disabled:cursor-not-allowed disabled:bg-surface-muted disabled:opacity-70` →
  `surface.muted #eef0f3` bg, 70% opacity.
- **Valid vs invalid border (the one stateful branch):** `invalid ? "border-red-400" :
  "border-line-strong"`. Invalid → Tailwind `red-400`; valid → `line.strong #cdd3dc`. NOTE: like
  Button danger, the invalid border uses raw `red-400`, not the `danger` token — recorded as drift.

**Side effects / errors.** None. Value/onChange via `...rest` (uncontrolled or controlled by caller).

**Deps.** `react` (`forwardRef`), `InputHTMLAttributes`, `@/lib/cn`.

**Consumed by.** `ui/index.ts` exports `Input` + `InputProps`; used in forms (login page, modals).

---

## `ui/FormField.tsx` — census #307 (839 B, 39 lines)

**What.** The label + hint + error wrapper around a single control. Renders a `<label>`, the control
(`children`), and conditionally a hint or an error message.

**Detailed WHY.** Standardizes the vertical field layout (label, control, helper text) and the
required-marker and error treatment so every form field is identical and accessible (`htmlFor` ties
label→control). Splitting this from `Input` means it wraps *any* control (Input, FileInput, select,
textarea), and the error/hint precedence logic lives in exactly one place. The hint is suppressed
when an error is present (error wins) — a deliberate UX rule so the field never shows contradictory
helper + error text at once.

**Exports.**
- `interface FormFieldProps`:
  - `label: string` (required) — the field label text.
  - `htmlFor?: string` — associates the `<label>` to the control's `id`. WHY optional: some controls
    self-associate; when omitted the label still renders (clicking it just won't focus).
  - `hint?: ReactNode` — helper text, shown only when there's no error.
  - `error?: ReactNode` — error text; when present, hint is hidden and this shows in red.
  - `required?: boolean` — renders a red `*` after the label.
  - `className?: string` — extends the wrapper.
  - `children: ReactNode` (required) — the actual control.
- `function FormField(props)`.

**Every visual state (classes → tokens).**
- Wrapper: `flex flex-col gap-1.5` (+ caller `className`).
- Label: `text-sm font-medium text-ink` (`#16243d`). Required marker: `<span className="ml-0.5
  text-red-600">*</span>` (raw `red-600` — drift from `danger` token).
- Hint (only when `hint && !error`): `<p className="text-xs text-ink-subtle">` → `#8a97a8`.
- Error (when `error`): `<p className="text-xs text-red-600">` → raw `red-600`.
- **Branch precedence:** hint renders iff `hint && !error`; error renders iff `error`. So states are:
  (a) neither → just label+control; (b) hint only; (c) error only (hint suppressed even if passed).

**Side effects / errors.** None (pure layout).

**Deps.** `react` (`ReactNode` type), `@/lib/cn`.

**Consumed by.** `ui/index.ts` exports `FormField` + `FormFieldProps`.

---

## `ui/Panel.tsx` — census #310 (1168 B, 52 lines)

**What.** The base surface (`Panel`) for grouped content, plus a `PanelHeader` sub-component (title /
description / actions row with a bottom divider).

**Detailed WHY.** The card/section primitive that gives the console its calm, bordered, slightly
raised surfaces. Almost every screen groups content into Panels; centralizing the radius/border/
shadow means surfaces are visually consistent and a token change re-skins everything. `PanelHeader`
is split out so a Panel can have a header *or* be a bare surface (e.g. a table-only panel), and so the
header's title/description/actions layout (title left, actions right, divider under) is identical
everywhere.

**Exports.**
- `interface PanelProps { className?: string; children: ReactNode }`.
- `function Panel({ className, children })` — `<section>` with
  `rounded-panel border border-line bg-surface shadow-panel`:
  - `rounded-panel` = 12px (`borderRadius.panel`, legacy alias → `card` 12px).
  - `border-line` = `line.DEFAULT #e3e8ef`.
  - `bg-surface` = `surface.DEFAULT #ffffff`.
  - `shadow-panel` = `0 1px 3px rgba(16,42,76,.05)` (legacy alias → `card`).
- `interface PanelHeaderProps { title: ReactNode; description?: ReactNode; actions?: ReactNode;
  className?: string }`.
- `function PanelHeader({ title, description, actions, className })`:
  - Row: `flex items-start justify-between gap-4 border-b border-line px-5 py-4`.
  - Title: `<h2 className="text-sm font-semibold text-ink">` (`#16243d`). WHY `<h2>`: section heading
    semantics; renders in the display face per globals.css `h2` rule (Montserrat).
  - Description (optional): `<p className="mt-0.5 text-sm text-ink-muted">` (`#5b6b82`).
  - Actions (optional): `<div className="flex shrink-0 items-center gap-2">` on the right; only
    rendered when `actions` is passed.
  - Left block: `min-w-0` so long titles truncate rather than push actions off-row.

**Every visual state.** Static: there is no loading/error/disabled state — Panel/PanelHeader are pure
layout surfaces; states live in the content placed inside them.

**Side effects / errors.** None.

**Deps.** `react` (`ReactNode`), `@/lib/cn`.

**Consumed by.** `ui/index.ts` exports `Panel`, `PanelHeader`, `PanelProps`, `PanelHeaderProps`.

---

## `ui/Table.tsx` — census #312 (1710 B, 74 lines)

**What.** Six compact, data-first table primitives: `Table` (scroll wrapper + `<table>`), `THead`,
`TBody`, `TR`, `TH`, `TD`.

**Detailed WHY.** The console is fundamentally tabular (runs, bids, scenarios, awards). These wrap
the native table elements so every data grid shares the same dense styling (small caps headers,
hairline row dividers, hover affordance on clickable rows, horizontal overflow scroll) without each
page restyling `<th>`/`<td>`. Splitting into discrete components (rather than a config-driven
`<DataTable>`) keeps full control of cell content/colSpan per screen while still being consistent —
the longevity/flexibility tradeoff: pages own their columns, the primitives own the look.

**Exports (each is a function component).**
- `Table({ children, className })` — wraps in `<div className="w-full overflow-x-auto">` (horizontal
  scroll for wide tables on narrow viewports) then `<table className="w-full border-collapse
  text-sm" + className>`. WHY the wrapper div: prevents wide tables from breaking page layout.
- `THead({ children })` — `<thead className="bg-surface-subtle">` (`surface.subtle #f7f9fc` tint).
- `TBody({ children })` — `<tbody className="divide-y divide-line">` — horizontal hairline dividers
  between rows (`line.DEFAULT #e3e8ef`).
- `TR({ children, className, onClick, ...rest })` — props are
  `{ children; className?; onClick? } & React.HTMLAttributes<HTMLTableRowElement>`. **Stateful:** when
  `onClick` is provided, adds `cursor-pointer hover:bg-surface-subtle` (row becomes clickable with a
  hover tint); otherwise no hover. The `onClick` is also spread to the `<tr>`. WHY: master-detail
  tables (runs list, bids) navigate on row click; non-interactive tables stay flat.
- `TH({ children, className, ...rest })` — `& ThHTMLAttributes`. `<th scope="col" className="border-b
  border-line px-4 py-2.5 text-left text-2xs font-semibold uppercase tracking-wide text-ink-subtle">`.
  - `text-2xs` = custom `0.6875rem` (11px) / `lineHeight 1rem`. Small-caps column header.
  - `scope="col"` for a11y. Color `ink.subtle #8a97a8`.
- `TD({ children, className, ...rest })` — `& TdHTMLAttributes`. `<td className="px-4 py-2.5
  align-middle text-ink">` (`#16243d`).

**Every visual state.** (a) static header/body cells; (b) `TR` clickable vs non-clickable (the only
variant). No empty/loading state baked in — pages render their own empty rows inside `TBody`.

**Side effects / errors.** None; `onClick` delegated to caller.

**Deps.** `react` (`ReactNode`, `ThHTMLAttributes`, `TdHTMLAttributes`, and inline
`React.HTMLAttributes`), `@/lib/cn`.

**Consumed by.** `ui/index.ts` exports `Table, THead, TBody, TR, TH, TD` (no separate type exports —
props are inline). Used by every list/grid (runs table, bids, scenario comparison, awards).

---

## `ui/StatusChip.tsx` — census #311 (1645 B, 59 lines) — GOVERNED TONE MAPPING

**What.** A small pill/badge (`StatusChip`) with a tone→color map, plus a helper `stageTone(stage)`
that maps a free-form run-stage string to a tone. This is one of the two homes of the **governed
status language** (the other is `RunStatusStrip`).

**Detailed WHY.** Status is everywhere in this product and it is *governed* — the locked-v2 rule
(comment line 10) is **"always colour + text, never hue alone"** (WCAG AA; colorblind-safe). The
chip always renders the caller's text label inside the colored pill, so the meaning is never carried
by hue alone. The tone union is split into *generic* tones (neutral/accent/amber/green/slate) and the
**governed** tones (`frozen`/`sealed`/`modeled`/`gated`) that encode the product's four immutable
lifecycle/decision states. Centralizing the tone→token map means the governed colors can't drift
between screens — every "FROZEN"/"SEALED"/"GATED"/"MODELED" badge in the app resolves to the same
exact tokens.

**Exports.**
- `type Tone` (not exported, used by props): the union
  `"neutral" | "accent" | "amber" | "green" | "slate" | "frozen" | "sealed" | "modeled" | "gated"`.
- `interface StatusChipProps { children: ReactNode; tone?: Tone; className?: string }` — `tone`
  defaults to `"neutral"`.
- `function StatusChip({ children, tone="neutral", className })`.
- `function stageTone(stage: string): Tone` — exported helper.

**The governed tone → token map (EXACT values — `const tones: Record<Tone, string>`).**
Pill base class (always): `inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-2xs
font-medium uppercase tracking-wide ring-1 ring-inset` (`text-2xs` = 11px; `ring-1 ring-inset` =
1px inset ring as the border). Then per tone:

| tone | classes | bg token | text token | ring token | resolved hex |
|---|---|---|---|---|---|
| `neutral` | `bg-surface-muted text-text-muted ring-border` | `surface.muted` | `text.muted` | `border.DEFAULT` | bg `#eef0f3`, text `#5b6b82`, ring `#e3e8ef` |
| `accent` | `bg-accent-soft text-accent ring-accent/25` | `accent.soft` | `accent.DEFAULT` | `accent/25` | bg `#e8eff8`, text `#084999`, ring `#084999`@25% |
| `amber` | `bg-warning-bg text-warning ring-warning/30` | `warning.bg` | `warning.DEFAULT` | `warning/30` | bg `#fdf6e8`, text `#c98a1a`, ring `#c98a1a`@30% |
| `green` | `bg-success-bg text-success ring-success/30` | `success.bg` | `success.DEFAULT` | `success/30` | bg `#e7f3ea`, text `#1a7a4f`, ring `#1a7a4f`@30% |
| `slate` | `bg-slate-100 text-slate-600 ring-slate-300` | Tailwind `slate-100` | `slate-600` | `slate-300` | raw Tailwind slate (NOT a locked token) |
| **`frozen`** | `bg-success-bg text-success ring-success/30` | `success.bg` | `success.DEFAULT` | `success/30` | bg `#e7f3ea`, text `#1a7a4f`, ring `#1a7a4f`@30% |
| **`sealed`** | `bg-sealed-bg text-sealed ring-sealed/25` | `sealed.bg` | `sealed.DEFAULT` | `sealed/25` | bg `#eef4ff`, text `#1d4ed8`, ring `#1d4ed8`@25% |
| **`modeled`** | `bg-warning-bg text-warning ring-warning/30` | `warning.bg` | `warning.DEFAULT` | `warning/30` | bg `#fdf6e8`, text `#c98a1a`, ring `#c98a1a`@30% |
| **`gated`** | `bg-danger-bg text-danger ring-danger/30` | `danger.bg` | `danger.DEFAULT` | `danger/30` | bg `#fbe9e7`, text `#b3261e`, ring `#b3261e`@30% |

Governed-tone semantics (verified against real usage — see consumption table below):
- **`frozen`** (green) — a frozen award/scenario / post-award terminal good state. Reuses the
  `success` green tokens (frozen == committed/good). Used: `AwardsListPanel` "Frozen",
  `AwardDetailPanel` "Frozen · Lens X" / "v0 · FROZEN", `ScenarioDetailPanel` "Frozen · {id8}",
  run page "Post-award", awards page header.
- **`sealed`** (blue, `#1d4ed8`/`#eef4ff`) — an immutable/audit-sealed artifact. Its own dedicated
  `sealed` token (distinct blue, *not* the brand `#084999`). Used: `AssertModal` "Audit event"
  chip (`{eventType}`), `FreezeAwardModal` "Lens {code}", `AnalysisRunsPanel` (non-live analyses),
  awards page "Lens {scenario_code}", alignment page non-recommended comparison row.
- **`modeled`** (amber) — a modeled / not-yet-real / hypothetical value (e.g. a modeled scenario
  number vs an enforced one). Reuses `warning` tokens. Used: `ScenarioDetailPanel` "modeled",
  `ScenarioComparisonTable` (modeled marker).
- **`gated`** (red, `danger`) — an action blocked because a gate/prerequisite isn't met, or an
  infeasible/non-scoreable item. Uses `danger` tokens. Used: `ScenarioDetailPanel` cap-infeasible,
  `ScenarioComparisonTable` gated cell, `ReviewSection` non-scoreable bid.

This map is the canonical "governed status language (locked v2)" referenced in the file comment;
`RunStatusStrip` carries a parallel, smaller governed map (see next file) for the dot colors.

- **`stageTone(stage)` (case-insensitive regex classifier, lowercases first):**
  - `/(done|complete|award|closed)/` → `"green"`.
  - `/(wait|review|action|hold|blocked)/` → `"amber"`.
  - `/(active|progress|doing|open|round)/` → `"accent"`.
  - else → `"slate"`.
  WHY: the backend `RunSummary.stage` is a free-form string; the dashboard (`app/(app)/page.tsx:288`
  `<StatusChip tone={stageTone(run.stage)}>{run.stage}</StatusChip>`) needs a deterministic tone
  without the backend committing to an enum. First-match-wins ordering. Edge cases: an unknown stage
  → `slate` (calm/neutral, never an alarming color by default — fail-safe).

**Side effects / errors.** None.

**Deps.** `react` (`ReactNode`), `@/lib/cn`.

**Consumed by.** `ui/index.ts` exports `StatusChip`, `stageTone`, `StatusChipProps`. ~20 call sites
across alignment/awards/intake/runs (enumerated above and in the consumption grep results).

---

## `ui/Modal.tsx` — census #309 (2799 B, 99 lines)

**What.** The generic dialog: a fixed backdrop + centered panel with a header (title/description +
close X), a body, and an optional footer. `"use client"`.

**Detailed WHY.** One accessible, focus-managed dialog used by every overlay (and the base of
`AssertModal`). It owns Escape-to-close, body-scroll-lock, backdrop-click-to-close (only on the
backdrop itself, not bubbled from inside), `role="dialog" aria-modal` and initial focus — so no
screen re-implements modal a11y/scroll behavior (the correctness reason: getting scroll-lock or
backdrop-click wrong is easy and would differ per screen). It is presentational about content but
strict about behavior.

**Exports.**
- `interface ModalProps`:
  - `open: boolean` (required) — when false the component returns `null` (fully unmounted, line 45).
  - `onClose: () => void` (required) — invoked by Escape, the X button, and backdrop click.
  - `title: ReactNode` (required) — header heading.
  - `description?: ReactNode` — optional subheading under the title.
  - `children: ReactNode` (required) — body.
  - `footer?: ReactNode` — optional footer; only rendered when provided.
  - `className?: string` — extends the panel (e.g. widen past `max-w-md`).
- `function Modal(props)`.

**Behavior / effects (the `useEffect`, lines 29–43, deps `[open, onClose]`).**
- Early-returns if `!open` (no listeners attached while closed).
- Adds a `keydown` listener: `Escape` → `onClose()`.
- Saves `document.body.style.overflow`, sets it to `"hidden"` (scroll-lock the page behind the modal).
- Focuses the panel (`panelRef.current?.focus()`) for a11y (so keyboard users land in the dialog).
- Cleanup: removes the keydown listener and restores the previous `overflow` value (not a hardcoded
  `""` — preserves whatever it was, correct if modals nest or the page had a custom overflow).

**Every visual state / structure (classes → tokens).**
- Closed: renders `null`.
- Backdrop: `fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-ink/30 p-4
  sm:p-8`. `bg-ink/30` = `ink.DEFAULT #16243d` at 30% (scrim). `onMouseDown` closes only when
  `e.target === e.currentTarget` (the backdrop itself), so clicks originating inside the panel don't
  close it.
- Panel: `mt-12 w-full max-w-md rounded-modal border border-border bg-surface-card shadow-modal
  outline-none` (+ `className`). `rounded-modal` = 14px; `border-border` = `#e3e8ef`;
  `bg-surface-card` = `#ffffff`; `shadow-modal` = `0 24px 64px rgba(16,42,76,.3)`. `role="dialog"
  aria-modal="true" tabIndex={-1}` so it's focusable.
- Header: `flex items-start justify-between gap-4 border-b border-line px-5 py-4`. Title `<h2
  className="text-base font-semibold text-ink">`; description `<p className="mt-0.5 text-sm
  text-ink-muted">`. Close button: `-mr-1 -mt-1 rounded-md p-1 text-ink-subtle hover:bg-surface-muted
  hover:text-ink`, `aria-label="Close"`, contains an inline 18px SVG X (stroke `currentColor`).
- Body: `<div className="px-5 py-5">{children}</div>`.
- Footer (only if `footer`): `flex items-center justify-end gap-2 border-t border-line
  bg-surface-subtle px-5 py-3.5` — right-aligned actions on a subtle-tinted footer bar.

**Side effects / errors.** Mutates `document.body.style.overflow` (restored on cleanup) and global
`keydown`. No thrown errors.

**Deps.** `react` (`useEffect`, `useRef`, `ReactNode`), `@/lib/cn`.

**Consumed by.** `ui/index.ts` exports `Modal` + `ModalProps`. Directly used by `AssertModal`, and by
`NewRunModal`, `SaveVersionModal`, `FreezeAwardModal`, `RecordAdjustmentModal`, etc.

---

## `ui/AssertModal.tsx` — census #304 (4507 B, 138 lines) — GOVERNED-ACTION PATTERN

**What.** The single governed-action confirmation pattern, built on `Modal`. Sequence:
**summary → cautions → (optional rationale) → NAMED human assertion (checkbox) → confirm**. The
confirm is disabled until the human checks the assertion box; the audit event that *will* be written
is shown up front as a `sealed` chip. `"use client"`.

**Detailed WHY.** This is the product's accountability gate for irreversible/governed actions
(freeze award, finalize, seal — the audit-writing decisions). It enforces, in one reusable place:
(1) the user sees a summary of what will happen and any cautions; (2) the audit `eventType` is
disclosed *before* confirming (no hidden side effects); (3) the action is attributed to a named human
("I, {actorName}, assert this decision") who must affirmatively check a box; (4) optional rationale
capture (decision capture, tagged E-40). It maps to the ABSOLUTE-REQUIREMENT auditability principle —
governed decisions are named, reasoned, and disclosed, never silent. Without it each governed modal
would hand-roll the assertion/disable logic and could omit attribution or the event disclosure.

**Exports.**
- `interface AssertModalProps`:
  - `open: boolean` — passed through to Modal.
  - `onClose: () => void` — close handler (also the Cancel button).
  - `title: ReactNode` — Modal title.
  - `description?: ReactNode` — Modal subheading.
  - `summary?: ReactNode` — "what this governed action will do"; rendered in a subtle-bordered box.
  - `cautions?: ReactNode` — irreversible/gated warnings; rendered in a warning-bordered box.
  - `eventType: string` (required) — the audit event that WILL be written (e.g. `FROZEN`, `CLOSED`);
    shown as a `sealed` StatusChip. WHY required: disclosure of the audit side effect is mandatory.
  - `actorName: string` (required) — current actor's display name, woven into the assertion sentence.
  - `withRationale?: boolean` — default `false`; reveals a free-text rationale textarea (E-40).
  - `rationaleLabel?: string` — default `"Rationale"`.
  - `rationaleRequired?: boolean` — default `false`; when true the confirm is blocked until rationale
    is non-empty (trimmed).
  - `confirmLabel?: string` — default `"Confirm"`.
  - `destructive?: boolean` — default `false`; renders the confirm as `variant="danger"`.
  - `onConfirm: (rationale: string) => void | Promise<void>` (required) — called with the trimmed
    rationale when confirmed.
  - `loading?: boolean` — default `false`; spins the confirm and disables Cancel + Confirm during the
    request.
  - `error?: string | null` — default `null`; rendered in `text-danger` at the bottom.
- `function AssertModal(props)`.

**Internal state & gating logic.**
- `const [asserted, setAsserted] = useState(false)` — the named-assertion checkbox.
- `const [rationale, setRationale] = useState("")`.
- `useEffect(() => { if (open) { setAsserted(false); setRationale(""); } }, [open])` — **resets the
  assertion and rationale every time the modal opens** (deps `[open]`). WHY: a prior assertion must
  never carry over — each governed action requires a fresh, deliberate check. (Edge: deps are `[open]`
  only; ESLint exhaustive-deps would also want the setters, but setters are stable — behavior correct.)
- `const rationaleOk = !withRationale || !rationaleRequired || rationale.trim().length > 0` — rationale
  passes if rationale isn't shown, OR isn't required, OR is non-empty after trim.
- `const canConfirm = asserted && rationaleOk && !loading` — **the gate**: confirm enabled only when
  the box is checked AND rationale satisfied AND not mid-request.

**Every visual state / structure (classes → tokens).**
- Footer (passed to Modal): `<Button variant="secondary" size="sm" onClick={onClose}
  disabled={loading}>Cancel</Button>` + `<Button variant={destructive ? "danger" : "primary"}
  size="sm" loading={loading} disabled={!canConfirm} onClick={() => void onConfirm(rationale.trim())}>
  {confirmLabel}</Button>`. Confirm disabled until `canConfirm`; loading state from `loading`.
- Body (`space-y-4`):
  - Summary box (if `summary`): `rounded-card border border-border bg-surface-subtle p-3 text-sm
    text-text` — neutral framed box (`#f7f9fc` bg).
  - Cautions box (if `cautions`): `rounded-card border border-warning/40 bg-warning-bg p-3 text-sm
    text-text` — warning-framed (`warning/40` border, `warning.bg #fdf6e8`).
  - Rationale (if `withRationale`): a `<label>` with a `text-2xs font-bold uppercase` caption (+ " *"
    if required) and a `<textarea rows={3}>` styled `w-full rounded-control border border-border
    bg-surface-card px-3 py-2 text-sm text-text placeholder:text-text-faint focus:border-brand-primary`
    (`rounded-control` 8px; focus border → `brand.primary #084999`). Placeholder: "Why this decision
    (recorded in the audit trail)…".
  - **Named assertion (the gate control):** a `<label className="flex items-start gap-2.5 rounded-card
    border border-border bg-surface-subtle p-3 ...">` containing `<input type="checkbox"
    checked={asserted} onChange=... className="mt-0.5 h-4 w-4 accent-brand-primary" />` and the
    sentence "I, **{actorName}**, assert this decision. Recorded against my name in the audit trail."
    (actorName in `text-text-strong` bold). `accent-brand-primary` colors the native checkbox `#084999`.
  - **Audit event disclosure:** `<div className="flex items-center gap-2 text-2xs text-text-muted">
    <span>Audit event:</span><StatusChip tone="sealed">{eventType}</StatusChip></div>` — the
    `sealed`-toned chip naming the event that will be written.
  - Error (if `error`): `<p className="text-sm text-danger">{error}</p>` (`danger #b3261e`).

**Branches / states summary.** (a) summary present/absent; (b) cautions present/absent;
(c) rationale shown/hidden × required/optional × empty/filled; (d) assertion unchecked (confirm
disabled) vs checked; (e) loading (both buttons disabled, confirm spins); (f) destructive (confirm
red) vs not; (g) error shown/absent. Confirm gating = `asserted && rationaleOk && !loading`.

**Side effects / errors.** Calls `onConfirm(rationale.trim())`; supports an async confirm (`void` of a
Promise). No thrown errors of its own.

**Deps.** `react` (`useEffect`, `useState`, `ReactNode`), sibling `./Modal`, `./Button`,
`./StatusChip`.

**Consumed by.** `ui/index.ts` exports `AssertModal` + `AssertModalProps`. The `actorName` is fed from
`useAuth().user.username` at call sites (governed modals in alignment/awards), tying the assertion to
the authenticated user — the Layer-3 link between this slice's auth and its governed-action UI.

---

## `ui/FileInput.tsx` — census #306 (3010 B, 102 lines)

**What.** A styled file picker matching the Input/Button look: a "Choose file" button (label driving
a visually-hidden native `<input type="file">`), the selected filename, and a clear (X) button.
Selection is **controlled by the parent** (`file` prop). `"use client"`.

**Detailed WHY.** Native file inputs are unstyleable and inconsistent across browsers; this wraps one
to match the design system and, critically, makes selection a *controlled* value so the parent can
**reset it after a successful upload** (clearing both the React state and the native input's `.value`,
which otherwise sticks). It defaults `accept=".xlsx"` because the product's ingest path is Excel
workbooks (setup/bids) — the no-file-storage streaming-upload contract. Without parent control, the
input would retain the last file after upload and re-selecting the same file wouldn't fire `onChange`.

**Exports.**
- `interface FileInputProps`:
  - `file: File | null` (required) — the currently-selected file, owned by the parent.
  - `onChange: (file: File | null) => void` (required) — fired on pick (first file or `null`) and on
    clear (`null`).
  - `accept?: string` — default `".xlsx"`; the native `accept` filter.
  - `disabled?: boolean` — disables the control and hides the clear button.
  - `className?: string` — extends the wrapper.
  - `buttonLabel?: string` — default `"Choose file"`; the choose-button text.
- `function FileIcon()` — internal 16px document SVG (not exported).
- `function FileInput(props)`.

**Internals.** `const inputRef = useRef<HTMLInputElement>(null)` (to reset `.value` on clear);
`const id = useId()` (stable id linking the `<label htmlFor>` to the hidden `<input id>`).

**Every visual state (classes → tokens).**
- Wrapper: `flex items-center gap-3 rounded-md border border-line-strong bg-white px-3 py-2`; when
  `disabled`: `cursor-not-allowed bg-surface-muted opacity-70`.
- Choose button (a `<label htmlFor={id}>`): `inline-flex h-8 shrink-0 cursor-pointer items-center
  gap-2 rounded-md border border-line-strong bg-white px-3 text-sm font-medium text-ink
  transition-colors hover:bg-surface-muted`; when `disabled`: `pointer-events-none opacity-70`.
  Contains `<FileIcon />` + `buttonLabel`.
- Hidden native input: `<input id type="file" accept disabled className="sr-only" onChange={(e) =>
  onChange(e.target.files?.[0] ?? null)} />` — visually hidden but accessible; emits the first file or
  null.
- Filename span: `min-w-0 flex-1 truncate text-sm`; color `file ? "text-ink" : "text-ink-subtle"`;
  text is `file ? file.name : "No file selected"`. (Truncates long names.)
- Clear button (only when `file && !disabled`): `-mr-1 shrink-0 rounded-md p-1 text-ink-subtle
  hover:bg-surface-muted hover:text-ink`, `aria-label="Clear selected file"`, 16px X SVG. `onClick`:
  `onChange(null)` AND `inputRef.current.value = ""` (resets native input so the same file can be
  re-picked).
- **States:** empty (no file → muted "No file selected", no clear button); selected (filename + clear
  button); disabled (greyed, no clear button, no pointer events on the label).

**Side effects / errors.** Mutates the native input's `.value` on clear. No thrown errors.

**Deps.** `react` (`useId`, `useRef`), `@/lib/cn`. (Note: does NOT use `forwardRef` — selection is
controlled, not ref-driven.)

**Consumed by.** `ui/index.ts` exports `FileInput` + `FileInputProps`. Used by intake upload sections
(setup/bids ingest), which clear `file` after a successful `apiUpload`.

---

## `ui/index.ts` — census #313 (789 B, 17 lines) — BARREL

**What.** The public barrel for the `ui` primitives — re-exports every component and its prop type.

**Detailed WHY.** Gives the rest of the app a single import surface (`@/components/ui`) instead of
deep per-file paths, so primitives can be moved/renamed internally without touching consumers (the
`AppShell` imports `Button` from `@/components/ui`, not `../ui/Button`). It is the contract boundary of
the design system. An empty/missing barrel would force brittle deep imports everywhere.

**Exact exports (value + type).**
- `Button`, type `ButtonProps`.
- `Input`, type `InputProps`.
- `FormField`, type `FormFieldProps`.
- `Panel`, `PanelHeader`, types `PanelProps`, `PanelHeaderProps`.
- `StatusChip`, `stageTone`, type `StatusChipProps`.
- `Table`, `THead`, `TBody`, `TR`, `TH`, `TD` (no type exports — props inline).
- `Modal`, type `ModalProps`.
- `AssertModal`, type `AssertModalProps`.
- `FileInput`, type `FileInputProps`.

**Not exported here:** `Table`'s inline prop types, `StatusChip`'s `Tone` union (internal),
`RunStatusStrip`/`AppShell`/auth (those live under `shell/`/`auth/` and are imported directly, not via
this barrel).

**Side effects / errors.** None (pure re-export).

---

# Shell — `frontend/components/shell/**`

## `shell/AppShell.tsx` — census #302 (4237 B, 119 lines)

**What.** The authenticated app chrome: a left `Sidebar` (logo + nav), a top `Header` (mobile logo,
user identity, Log out), and a scrollable `<main>` content area. `"use client"`. Three components:
`Sidebar` (internal), `Header` (internal), `AppShell` (exported).

**Detailed WHY.** Provides the persistent frame for every protected route so pages only render their
own content. It centralizes navigation, the brand, the signed-in user's identity, and the logout
affordance. It is rendered by `app/(app)/layout.tsx` *inside* `AuthGuard`, so it only ever shows for
authenticated users — which is why `Header` can assume an auth context and read `user`/`logout`.

**THE NAV — ONE ITEM (and WHY).** `const NAV: NavItem[]` contains **exactly one** entry:
```
{ href: "/", label: "Runs",
  match: (p) => p === "/" || p.startsWith("/runs"),
  icon: <three-bar list SVG> }
```
- `interface NavItem { href: string; label: string; icon: ReactNode; match: (pathname: string)
  => boolean }`. The `match` predicate (not a string compare) decides the active state: a path is
  "Runs-active" when it equals `/` OR starts with `/runs`. WHY a predicate: the dashboard (`/`) and
  every run sub-route (`/runs/[slug]/...`) all belong to the single "Runs" section, so they all
  highlight the one nav item.
- **WHY one item:** the entire console is a single workflow — RFP **Runs** (dashboard → run →
  intake/alignment/awards). There is no second top-level destination; everything is reached by
  drilling into a run. The nav is a list with one element rather than a hardcoded link precisely so
  the structure (NavItem + map) is already in place if a second section is ever added — but as built,
  the product is mono-section. This is a deliberate scope fact, not an omission: the nav reflects the
  app's true shape (Runs is the whole app). The section caption above it reads "Sourcing".

**`Sidebar()` (internal).** `<aside className="hidden w-[248px] shrink-0 flex-col bg-brand-ink
text-white/70 md:flex">` — 248px wide, navy `brand.ink #0b1f3a`, hidden below `md` (mobile uses the
header logo instead). Contents:
- Brand row (`h-14`): a `KR` monogram tile (`bg-white/10`) + "RFP Console" in the display face
  (`font-display text-sm font-bold ... text-white`).
- `<nav>`: caption `<p>Sourcing</p>` (`text-2xs font-bold uppercase tracking-wider text-white/40`)
  then `NAV.map`. Each item is a `next/link` `<Link href icon label>`:
  - active (`item.match(pathname)`): `bg-white/10 font-semibold text-white`, icon `text-white`.
  - inactive: `text-white/65 hover:bg-white/5 hover:text-white`, icon `text-white/45`.
  - `active` computed via `usePathname()` (client nav hook) → `item.match(pathname)`.
- Footer: `<div ...>Enterprise RFP sourcing</div>` (`text-2xs text-white/40`).

**`Header()` (internal).** `<header className="flex h-14 shrink-0 items-center justify-between gap-4
border-b border-border bg-surface-card px-5">`. Reads `const { user, logout } = useAuth()`.
- Mobile-only brand (`md:hidden`): `KR` tile (`bg-brand-primary`) + "RFP Console".
- Spacer `<div className="hidden md:block" />` to push the right cluster right on desktop.
- Right cluster (only when `user`): an avatar circle showing `user.username.slice(0, 2).toUpperCase()`
  (`bg-surface-muted text-text-muted`, `aria-hidden`), then `user.username` (`text-sm font-semibold
  text-text-strong`) and a status line `user.totp_enabled ? "2FA enabled" : "Signed in"`
  (`text-2xs text-text-subtle`).
- **Log out button:** `<Button variant="secondary" size="sm" onClick={() => void logout()}>Log out
  </Button>` — calls `useAuth().logout()` (POST /auth/logout → clear state → route to /login).

**`AppShell({ children })` (exported).** `<div className="flex h-screen overflow-hidden">` →
`<Sidebar />` + a column (`flex min-w-0 flex-1 flex-col`) containing `<Header />` and `<main
className="flex-1 overflow-y-auto">` whose inner wrapper is `mx-auto w-full max-w-6xl px-5 py-6
lg:px-8` (centered, max 72rem content column). Only `<main>` scrolls; the shell is fixed at viewport
height (`h-screen overflow-hidden`).

**Every visual state.** (a) desktop (≥md): sidebar visible, desktop spacer; (b) mobile (<md): sidebar
hidden, mobile brand shown; (c) signed-in user present → identity cluster + avatar; (d) `user` null →
identity cluster omitted but Log out still rendered (in practice `user` is non-null inside AuthGuard,
so the null branch is defensive). Active vs inactive nav item (above).

**Side effects / errors.** `usePathname` (read), `useAuth` (context; throws if used outside
`AuthProvider` — but it always is, via root layout). `logout()` performs the network + redirect.

**Deps.** `react` (`ReactNode`), `next/link`, `next/navigation` (`usePathname`), `@/lib/cn`,
`@/components/auth/AuthProvider` (`useAuth`), `@/components/ui` (`Button`).

**Consumed by.** `app/(app)/layout.tsx` wraps `{children}` in `<AppShell>` inside `<AuthGuard>`.

---

## `shell/RunStatusStrip.tsx` — census #303 (1389 B, 37 lines) — GOVERNED DOT-TONE MAPPING

**What.** A persistent horizontal four-cell status strip (Run · Analysis · Award · Audit). Each cell
= a colored dot + a caps label + a value. Pure presentational (no `"use client"` needed — no hooks).

**Detailed WHY.** Gives every run-scoped page a constant, at-a-glance lifecycle readout (where the run
is across its four governed dimensions). It is fed `cells` by each page (the page computes tones from
run/round state). The governed rule is reiterated in the comment: **"colour is always backed by text
(WCAG AA — never hue alone)"** — every dot is paired with a label and value, never standalone color.

**Exports.**
- `type StatusTone = "live" | "frozen" | "sealed" | "idle"` — the dot-color domain (a *different,
  smaller* governed set than StatusChip's `Tone`: this is for the strip dots specifically).
- `interface StatusCell { label: string; value: ReactNode; tone?: StatusTone }` — `label` is the
  short caps title (e.g. "RUN STATE", "ANALYSIS", "AWARD", "AUDIT"), `value` the rendered content,
  `tone` optional (defaults to `"idle"`).
- `function RunStatusStrip({ cells }: { cells: StatusCell[] })`.

**THE GOVERNED DOT-TONE MAP (EXACT — `const dot: Record<StatusTone, string>`).**

| tone | class | token | resolved hex | meaning |
|---|---|---|---|---|
| `live` | `bg-success` | `success.DEFAULT` | `#1a7a4f` (green) | active / current (e.g. AUDIT "Current") |
| `frozen` | `bg-success` | `success.DEFAULT` | `#1a7a4f` (green) | frozen award present (terminal good) |
| `sealed` | `bg-sealed` | `sealed.DEFAULT` | `#1d4ed8` (blue) | a sealed/immutable analysis exists |
| `idle` | `bg-text-faint` | `text.faint` | `#9aa7b6` (grey) | not yet reached / inactive (default) |

Note: `live` and `frozen` resolve to the *same* green dot (`#1a7a4f`) — both signal a "good/active"
state on the strip; the distinction is carried by the cell's text `value`, consistent with the
never-hue-alone rule. This is the strip's parallel to StatusChip's governed map, but reduced to dots.

**How it's fed (verified Layer-3 binding — `app/(app)/runs/[slug]/page.tsx` `statusCells(run)`):**
- `{ label: "RUN STATE", value: run.stage, tone: runTone }` (runTone derived from the run stage).
- `{ label: "ANALYSIS", value: ..., tone: analysisDone ? "sealed" : "idle" }` — sealed when an
  analysis exists, else idle.
- `{ label: "AWARD", value: ..., tone: awardDone ? "frozen" : "idle" }` — frozen (green) when an
  award is frozen, else idle.
- `{ label: "AUDIT", value: "Current", tone: "live" }` — always live/green (the audit trail is
  always current). Also rendered by intake/awards/alignment pages (`statusCells(run, round)` variants).

**Every visual state (classes → tokens).**
- Container: `flex w-full divide-x divide-border overflow-hidden rounded-card border border-border
  bg-surface-card shadow-card` — a single rounded card, cells separated by vertical hairlines
  (`divide-border #e3e8ef`), 12px radius, `shadow-card`.
- Each cell (`cells.map`, keyed by `c.label`): `flex min-w-0 flex-1 items-center gap-2.5 px-4 py-2.5`
  — equal-width cells (`flex-1`). Dot: `<span className="h-2 w-2 shrink-0 rounded-full" + dot[c.tone ??
  "idle"]} aria-hidden />` (8px dot; tone defaults to `idle`). Text block (`min-w-0 leading-tight`):
  label `<p className="text-2xs font-bold uppercase tracking-wider text-text-subtle">` and value
  `<p className="truncate text-sm font-semibold text-text-strong">` (value truncates if long).
- States: per cell the dot color reflects `tone`; `idle` is the empty/not-reached state. The strip
  itself has no loading/error state — pages render placeholder values.

**Side effects / errors.** None.

**Deps.** `react` (`ReactNode`), `@/lib/cn`.

**Consumed by.** `app/(app)/runs/[slug]/page.tsx`, `.../intake/page.tsx`, `.../alignment/page.tsx`,
`.../awards/page.tsx` (each computes its own `statusCells`). NOT in the `ui` barrel — imported
directly from `@/components/shell/RunStatusStrip`.

---

# Auth — `frontend/components/auth/**`

## `auth/AuthProvider.tsx` — census #286 (2288 B, 80 lines) — SESSION FLOW

**What.** The React context provider for authentication. Holds `status` + `user`, exposes `refresh()`
and `logout()`, and runs the initial session check on mount. `"use client"`. Also exports the
`useAuth()` hook.

**Detailed WHY.** Single source of truth for "who is signed in" across the app. It wraps the whole
tree (root `app/layout.tsx`) so any component can read auth via `useAuth()`. It deliberately leaves
*login* to the login page (which calls the `login` API then `refresh()`); the provider owns
session *state*, the me-check, and logout. Aborting in-flight `me` checks (AbortController) prevents
race conditions / state updates after unmount. It treats *any* `me` failure (401 or backend-down) as
"unauthenticated" — a fail-safe: an unreachable backend should gate the UI, not leave it in limbo.

**Types / context.**
- `type AuthStatus = "loading" | "authenticated" | "unauthenticated"`.
- `interface AuthContextValue { status: AuthStatus; user: User | null; refresh: () => Promise<void>;
  logout: () => Promise<void> }`. (`User` = `{ id: string; username: string; totp_enabled: boolean }`
  from `lib/api/types.ts`.)
- `const AuthContext = createContext<AuthContextValue | null>(null)`.

**`AuthProvider({ children })`.**
- State: `status` (init `"loading"`), `user` (init `null`), `abortRef` (AbortController ref).
- **`refresh` (`useCallback`, deps `[]`):**
  1. Aborts any prior in-flight check (`abortRef.current?.abort()`), creates a new `AbortController`,
     stores it.
  2. `const u = await fetchMe(controller.signal)` → `GET /api/v1/auth/me` with `credentials:"include"`
     (the httpOnly session cookie). On success: `setUser(u); setStatus("authenticated")`.
  3. On error: if it's an `AbortError`, return silently (a newer check superseded it). Otherwise
     (401 unauthenticated, or backend down → 0-status ApiError): `setUser(null);
     setStatus("unauthenticated")`. WHY catch-all: any non-OK me = not signed in (fail-safe).
- **Mount effect (`useEffect`, deps `[refresh]`):** `void refresh()` on mount (the initial session
  probe), and on unmount `abortRef.current?.abort()` (cancel any in-flight me).
- **`logout` (`useCallback`, deps `[router]`):**
  1. `await apiLogout()` → `POST /api/v1/auth/logout` (204, clears the cookie server-side).
  2. On error: if it's NOT an `ApiError`, rethrow (unexpected). If it IS an ApiError (e.g. session
     already expired), swallow it — we still want to clear locally.
  3. `finally`: `setUser(null); setStatus("unauthenticated"); router.replace("/login")` — always
     clear local state and route to login, even if the server call failed. WHY finally: logout must
     be irreversible client-side regardless of the network result.
- Provides `{ status, user, refresh, logout }` to children.

**`useAuth(): AuthContextValue`** — `useContext(AuthContext)`; **throws** `Error("useAuth must be used
within <AuthProvider>")` if null. WHY throw: a component reading auth outside the provider is a
programming error that should fail loudly, not silently return null.

**The `credentials: "include"` / login / logout / me wiring (Layer-3 backend binding).** All three
auth calls route through `lib/api/client.ts apiFetch`, which sets `credentials: "include"` on **every**
request (client.ts:110) plus `cache: "no-store"` — so the httpOnly session cookie always rides along
and responses are never cached. Base URL = `process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost
:8000"` + prefix `/api/v1`.
- **`me(signal?)`** (`lib/api/auth.ts`) → `GET /auth/me` → `200 User` or `401`. Used by `refresh`.
- **`logout()`** → `POST /auth/logout` → `204` (apiFetch returns `undefined` for 204). Used by
  `logout`.
- **`login(payload)`** → `POST /auth/login` (sets the httpOnly cookie). NOT called by the provider —
  it's called by the login page, which then calls `refresh()` to pull the new session into context.
  The provider intentionally has no `login` method (separation: provider owns session state; the page
  owns the credentials form). On a 401 with detail exactly `"2FA code required"`, the `ApiError`
  carries `twoFactorRequired === true` (client.ts:40-42) so the login page reveals the TOTP field;
  `ApiError.isUnauthenticated` is true for a 401 that is NOT the 2FA prompt.

**Side effects / errors.** Network (me/logout), router redirect on logout, AbortController lifecycle.
`useAuth` throws outside provider. Backend-down surfaces as `status="unauthenticated"`.

**Deps.** `react` (`createContext`, `useCallback`, `useContext`, `useEffect`, `useRef`, `useState`,
`ReactNode`), `next/navigation` (`useRouter`), `@/lib/api` (`ApiError`, `me as fetchMe`,
`logout as apiLogout`, `User`).

**Consumed by.** Root `app/layout.tsx` wraps `<AuthProvider>{children}</AuthProvider>`. `useAuth()` is
read by `AuthGuard`, `AppShell` Header, `login/page.tsx`, and every governed modal/page that needs the
actor (`FreezeAwardModal`, `RecordAdjustmentModal`, awards page) — feeding `actorName` into
`AssertModal`.

---

## `auth/AuthGuard.tsx` — census #285 (1035 B, 32 lines)

**What.** A wrapper for protected routes: while the session check is in flight it shows a calm loading
state; if authenticated it renders children; if unauthenticated it redirects to `/login` and renders a
"Redirecting…" state. `"use client"`.

**Detailed WHY.** Enforces the gate at the layout level so no protected page renders for an
unauthenticated user. Splitting it from `AuthProvider` keeps the provider purely about *state* and the
guard about *routing/gating decisions* (single responsibility). It pairs with `AppShell` in
`app/(app)/layout.tsx` so the entire `(app)` route group is protected by one wrapper. Without it, a
page in the protected group could flash its content before the redirect.

**Export.** `function AuthGuard({ children }: { children: ReactNode })`.

**Logic.**
- `const { status } = useAuth();` `const router = useRouter();`
- `useEffect(() => { if (status === "unauthenticated") router.replace("/login"); }, [status,
  router])` — performs the redirect as a side effect when unauthenticated (`replace`, not `push`, so
  back-button doesn't return to the gated page).
- **Render branches:**
  - `status === "authenticated"` → `<>{children}</>` (the only path that renders the protected page).
  - else (loading OR unauthenticated) → a centered overlay: `<div className="flex h-screen items-center
    justify-center">` with a spinner (`h-4 w-4 animate-spin rounded-full border-2 border-line-strong
    border-t-accent`) and text `status === "loading" ? "Checking your session…" : "Redirecting to sign
    in…"` (`text-sm text-ink-muted #5b6b82`). So the unauthenticated state shows "Redirecting…" for the
    instant before the effect navigates away (children never render).

**Every visual state.** (a) loading → spinner + "Checking your session…"; (b) authenticated →
children; (c) unauthenticated → spinner + "Redirecting to sign in…" then route replace to /login.

**Side effects / errors.** `router.replace("/login")` on unauthenticated. Reads `useAuth` (throws
outside provider — but it's always inside via root layout).

**Deps.** `react` (`useEffect`, `ReactNode`), `next/navigation` (`useRouter`), sibling
`./AuthProvider` (`useAuth`).

**Consumed by.** `app/(app)/layout.tsx`: `<AuthGuard><AppShell>{children}</AppShell></AuthGuard>` —
guards the whole protected route group.

---

# Appendix A — Design tokens used by this slice (locked v2 — exact hex)

From `frontend/tailwind.config.ts` (theme.extend.colors / shadow / radius) and `app/globals.css`.
"Legacy alias" = a name retained pointing at the locked value during the E-26 re-skin.

**Colors (used by this slice):**
- `brand.primary`/`accent.DEFAULT` `#084999`; `accent.hover`/`brand.primary-hover` `#0a5bbf`;
  `accent.soft` `#e8eff8`; `brand.ink` `#0b1f3a` (sidebar navy); `brand.sky` `#2478ce` (global focus
  outline in globals.css).
- `text.strong` `#102a4c`, `text.DEFAULT`/`ink.DEFAULT` `#16243d`, `text.muted`/`ink.muted` `#5b6b82`,
  `text.subtle`/`ink.subtle` `#8a97a8`, `text.faint` `#9aa7b6`.
- `surface.DEFAULT`/`card` `#ffffff`, `surface.app` `#eceff4`, `surface.subtle` `#f7f9fc`,
  `surface.muted` `#eef0f3`.
- `border.DEFAULT`/`line.DEFAULT` `#e3e8ef`, `line.strong` `#cdd3dc`, `border.hairline`/`line.hairline`
  `#eef1f5`.
- `success.DEFAULT` `#1a7a4f`, `success.bg` `#e7f3ea` (→ frozen chip, live/frozen dot).
- `warning.DEFAULT` `#c98a1a`, `warning.bg` `#fdf6e8` (→ amber/modeled chip, cautions box).
- `danger.DEFAULT` `#b3261e`, `danger.bg` `#fbe9e7` (→ gated chip, AssertModal error).
- `sealed.DEFAULT` `#1d4ed8`, `sealed.bg` `#eef4ff` (→ sealed chip, sealed dot).

**Radius:** `control` 8px, `card` 12px, `modal` 14px, `pill` 20px, `panel` 12px (alias→card),
`rounded-md` 6px (Tailwind default, used by Button/Input/FileInput).
**Shadow:** `card`/`panel` `0 1px 3px rgba(16,42,76,.05)`, `raised` `0 2px 8px rgba(8,73,153,.14)`,
`modal` `0 24px 64px rgba(16,42,76,.3)`.
**Font sizes:** `2xs` = `0.6875rem`/`1rem` (custom; pervasive for caps labels). Display face =
Montserrat (`--font-montserrat`), body = Nunito (`--font-nunito`). globals.css applies tnum and a
2px `#2478ce` focus-visible outline globally.

# Appendix B — Governed status language (cross-component summary)

Two parallel governed maps both honor "colour + text, never hue alone":
- **StatusChip** (`frozen`/`sealed`/`modeled`/`gated` + generic tones) — exact map in the StatusChip
  section. frozen→success green `#1a7a4f`/`#e7f3ea`; sealed→`#1d4ed8`/`#eef4ff`; modeled→warning amber
  `#c98a1a`/`#fdf6e8`; gated→danger red `#b3261e`/`#fbe9e7`.
- **RunStatusStrip** dots (`live`/`frozen`/`sealed`/`idle`) — live & frozen both green `#1a7a4f`,
  sealed blue `#1d4ed8`, idle grey `#9aa7b6`.
The `sealed` token (blue `#1d4ed8`) is the only governed color that is NOT reused from
success/warning/danger — it's a dedicated immutability/audit color, used for audit events
(`AssertModal` `eventType`), sealed analyses, and lens identifiers.

# Appendix C — Gaps / drift observed (read-only findings, not changes)

1. **Token drift — danger/error use raw Tailwind `red-*`, not the v2 `danger` token.**
   - `Button.tsx` `danger` variant: `text-red-700`, `hover:bg-red-50` (line 25).
   - `Input.tsx` invalid border: `border-red-400` (line 21).
   - `FormField.tsx` required `*` and error text: `text-red-600` (lines 30, 36).
   The locked-v2 `danger` token is `#b3261e` / `danger.bg #fbe9e7`. These three primitives bypass it.
   `StatusChip` `gated` and `AssertModal` error DO use the `danger` token, so error red is inconsistent
   across the slice. Low risk (visual), but a real drift from the "locked tokens" intent in the
   tailwind config header.
2. **`StatusChip` `slate` tone uses raw Tailwind `slate-100/600/300`** (line 27) rather than a locked
   token — the only chip tone not on the v2 palette. Used for "Incumbent"/"Locked"/neutral non-output
   states.
3. **`live` vs `frozen` RunStatusStrip dots are visually identical (both `#1a7a4f`).** Intentional
   per the never-hue-alone rule (text carries the distinction), but worth noting they cannot be told
   apart by dot color alone.
4. **AppShell nav has exactly one item ("Runs").** Verified as a deliberate as-built fact (single-
   section product), not a stub — the `NavItem`/`match`/`map` machinery is fully implemented; there is
   simply one destination. Recorded here so a future reader doesn't mistake it for an unfinished nav.
5. **No `forwardRef` on `FileInput`** (selection is parent-controlled by design) — not a defect; noted
   for symmetry with Button/Input which do forward refs.

# Appendix D — File→census reconciliation (final)

All 14 slice files present in `AS_BUILT/FILE_CENSUS.md` rows 285, 286, 302–313; on-disk sizes match
the census byte counts exactly; none empty. No file in these three directories is missing from the
census, and no census row for these directories lacks a file. Slice complete.
