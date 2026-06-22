---
slice: F2c
title: AS-BUILT AUDIT — frontend/components/intake/** + frontend/components/runs/**
scope_globs:
  - /home/user/KR_RFP/frontend/components/intake/**
  - /home/user/KR_RFP/frontend/components/runs/**
files_audited: 12
contract: /CLAUDE.md (ABSOLUTE REQUIREMENTS — no MVP, data fidelity, no server-side storage, verify before actioning)
standard: /home/user/KR_RFP/AS_BUILT/AUDIT_STANDARD.md (Layer-2 per-file + Layer-3 UX/UI; exhaustive WHY; every state, every binding, every format)
census_rows: 290–301 (FILE_CENSUS.md) — all present, none empty, sizes match byte-for-byte
read_only: true (no files modified during this audit)
date_audited: 2026-06-22
---

# Slice F2c — Intake & Runs components (excruciating as-built)

This document is the substance-bar audit for the 9 intake components and the 3 runs components.
Per AUDIT_STANDARD.md it carries **Layer-2** (per-file: path · ext · empty? · what · detailed WHY ·
public surface · props · deps · census cross-ref) and **Layer-3** (every screen/component: purpose,
WHY, props, **every state**, **every data binding with format/precision**, every interaction →
outcome/endpoint, navigation reachability). Design-vs-as-built simplifications are flagged inline and
collected at the end.

Reference contracts read end-to-end to ground the bindings (not in this slice, cited for fidelity):
- `frontend/lib/api/types.ts` — the hand-written TS contracts (`RunFile`, `BidLineView`,
  `MappingProposalView`, `Strategy`, `Kanban`, …). Lines cited per binding.
- `frontend/lib/api/intake.ts` — `listRunFiles`, `downloadRunFile`, `downloadRunArchive`,
  `uploadSetup`, `generateTemplate`, `importBids`, `listBids`.
- `frontend/lib/api/runs.ts` — `createRun`, `getStrategy`, `updateStrategy`.
- `frontend/lib/api/client.ts` — `ApiError` (+ `.isGateRequired`, `.code`, `.detail`, `.status`),
  `apiFetch` / `apiUpload` / `apiDownload`.
- `frontend/lib/format.ts` — `formatBytes`, `formatTimestamp`, `formatPrice`, `formatCount`.
- `frontend/lib/cn.ts` — `cn(...)` falsy-filtering classnames joiner.
- `frontend/components/ui/StatusChip.tsx` — chip tones used by these components.
- `frontend/app/(app)/runs/[slug]/intake/page.tsx` — the parent wizard wiring the 4 intake steps.
- `frontend/app/(app)/runs/[slug]/page.tsx` (line 353) — wires `StrategyPanel`.
- `frontend/app/(app)/page.tsx` (line 319) — wires `NewRunModal`.

---

## CENSUS CROSS-CHECK (FILE_CENSUS.md rows 290–301)

| census # | path | ext | bytes | wc -l | empty? | notes |
|---|---|---|---|---|---|---|
| 290 | frontend/components/intake/Alert.tsx | tsx | 885 | 33 | n | matches |
| 291 | frontend/components/intake/DownloadArchiveButton.tsx | tsx | 1786 | 71 | n | matches |
| 292 | frontend/components/intake/ImportSection.tsx | tsx | 9725 | 292 | n | matches |
| 293 | frontend/components/intake/MappingProposal.tsx | tsx | 4117 | 129 | n | matches |
| 294 | frontend/components/intake/ReviewSection.tsx | tsx | 8464 | 252 | n | matches |
| 295 | frontend/components/intake/RunFilesTable.tsx | tsx | 3128 | 109 | n | matches |
| 296 | frontend/components/intake/SetupSection.tsx | tsx | 3816 | 121 | n | matches |
| 297 | frontend/components/intake/StepHeader.tsx | tsx | 1671 | 52 | n | matches |
| 298 | frontend/components/intake/TemplateSection.tsx | tsx | 3536 | 110 | n | matches |
| 299 | frontend/components/runs/KanbanBoard.tsx | tsx | 2372 | 69 | n | matches; **orphaned** (no importer — see entry) |
| 300 | frontend/components/runs/NewRunModal.tsx | tsx | 3909 | 138 | n | matches |
| 301 | frontend/components/runs/StrategyPanel.tsx | tsx | 6628 | 193 | n | matches |

All 12 owned files accounted for. Census `empty?=y` column is the **"has-content?"** flag (y = yes,
has content) — not "is-empty"; none are empty. Census mtime for StrategyPanel (2026-06-22T10:44) and
its on-disk mtime (10:42) confirm it is the most recently touched file in the slice (the A1 strategy
wiring). KanbanBoard's mtime (2026-06-21T03:05, untouched since) corroborates its orphaned status.

---

# PART A — intake/** (the 4-step bid-intake wizard + shared atoms)

The intake folder is **one feature**: the Bid-intake page (`.../runs/[slug]/intake/page.tsx`) renders
four sequential STEP cards — **Setup → Template → Import → Review** — plus two cross-cutting helpers
(an archive download button on the page header, a run-files table reused by steps 1 & 2) and two shared
atoms (`Alert`, `StepHeader`). The page owns the soft-gating state machine and the `round` selector
(1–6); each section is a controlled child that lifts its result up via an `onX` callback so the page
can update the kanban, refresh files, and bump the review refresh key.

---

## A.1 — Alert.tsx  (census 290 · 885 B · 33 lines · tsx · not empty)

**What.** A presentational inline message box. Four tones (`error | success | info | warning`), each a
fixed Tailwind class triple (border + bg + text), rendered as a rounded bordered box with `text-sm`.

**Detailed WHY.** Every intake section surfaces inline status (errors, gate warnings, success
confirmations) and they must look identical and be accessible. Centralizing the four tone treatments
here (a) guarantees the "locked v2 tokens" colour system is applied consistently — the file comment
"Colour is always backed by text" enforces the governed-status rule that colour never carries meaning
alone (matches `StatusChip`'s same rule); and (b) sets the correct ARIA role automatically. Without it,
each section would re-implement the box and the role logic, risking inconsistent colour/role and a
drift from the v2 token set. It is deliberately a **pure** component (no `"use client"`, no state) —
cheap to render anywhere.

**Public surface.**
- `AlertProps { tone: "error"|"success"|"info"|"warning"; children: ReactNode; className?: string }`.
- `Alert(props)` → a single `<div>`.

**Detailed WHY (shape).**
- `role={tone === "error" ? "alert" : "status"}` (line 23): an error is an **assertive** live region
  (screen reader interrupts) — the user must know an action failed; non-error tones are **polite**
  `status` regions (announced without interrupting). This is the accessibility crux and the reason the
  component owns role selection rather than the caller.
- `tones` record (lines 13–18): `error`→danger, `success`→success, `info`→neutral surface/muted text,
  `warning`→warning. Token names (`border-danger/30`, `bg-success-bg`, `text-warning`, …) are the v2
  semantic tokens, not raw colours — so a theme change propagates.
- `cn("rounded-control border px-3 py-2 text-sm", tones[tone], className)` (lines 24–28): base box +
  tone classes + caller override, falsy-filtered by `cn`.

**Deps.** `react` (type `ReactNode`), `@/lib/cn`.
**Consumed by.** SetupSection, TemplateSection, ImportSection, ReviewSection, RunFilesTable,
MappingProposal (every intake section).

**Layer-3 — states.** Stateless. The *tone* is the only variation: 4 visual states, each colour-backed
by its text label/content (no hue-only signalling). No loading/empty/error states of its own.

**Layer-3 — bindings.** No backend binding; renders `children` verbatim inside the toned box. Format:
`text-sm`, `rounded-control`, `border`. No numbers, so no precision concerns.

---

## A.2 — StepHeader.tsx  (census 297 · 1671 B · 52 lines · tsx · not empty)

**What.** The shared header strip for the four sequential intake STEP cards: a 30×30 circular badge
(numbered, or a ✓ checkmark when done) + title (`"{step} · {title}"`) + optional description +
right-aligned `actions` slot (typically a completion `StatusChip` and/or a button).

**Detailed WHY.** All four steps share one visual grammar — a numbered badge that turns into a green
check when complete, with a consistent header layout. Centralizing it (a) makes the wizard read as one
coherent sequence, (b) encodes the three step states (`done`/`current`/`todo`) as one switch so the
colour semantics (green = done, brand = current, faint = todo) are identical everywhere, and (c) frees
each section to pass only its step number, title, state, and an actions slot. Without it, four
hand-rolled headers would drift in spacing, badge colour, and check behaviour.

**Public surface.**
- `StepState = "done" | "current" | "todo"`.
- `StepHeaderProps { step: number; title: string; description?: ReactNode; state: StepState; actions?: ReactNode }`.
- `StepHeader(props)` → header `<div>`.

**Detailed WHY (shape).**
- Badge (lines 27–38): `state==="done"` → green fill + white ✓; `current` → brand-primary text on
  `sealed-bg` with brand border; `todo` → faint text on card bg. `aria-hidden` because the textual
  title already conveys the step number/state to assistive tech (the badge is decorative duplication).
  `tabular-nums` so the digit doesn't shift width. `{state === "done" ? "✓" : step}` (line 37) is the
  number→check swap.
- Title `<h2>` `"{step} · {title}"` (lines 40–42): the step number is repeated in text (not only the
  badge) — robust to the badge being `aria-hidden`.
- `actions` slot (lines 47–49): right-aligned flex with `gap-2`; only rendered when provided.
- Layout: `border-b border-border-hairline px-[18px] py-4` — hairline divider under the header inside a
  `Panel`.

**Deps.** `react` (type `ReactNode`), `@/lib/cn`.
**Consumed by.** SetupSection (step 1), TemplateSection (step 2), ImportSection (step 3),
ReviewSection (step 4).

**Layer-3 — states.** Three explicit visual states via `state` prop: **done** (green badge + ✓),
**current** (brand badge + number), **todo** (faint badge + number). No loading/error of its own.

**Layer-3 — bindings.** `step` (number) → badge digit + title prefix, `tabular-nums`. `title`/
`description` → text. `actions` → arbitrary node (usually a StatusChip whose label is the step's
completion state). No currency/percent; the only numeric binding is the integer `step`.

---

## A.3 — RunFilesTable.tsx  (census 295 · 3128 B · 109 lines · tsx · not empty)

**What.** A compact table of run-folder files, each row with name, kind chip, size, modified timestamp,
and an authenticated **Download** button. Reused by Setup (input workbook) and Template (generated
template). `"use client"` because it holds per-row download state.

**Detailed WHY.** The no-server-side-file-storage contract (CLAUDE.md req 4) means files live in the
run folder and are streamed on request through an authenticated endpoint — a plain `<a href>` would
drop the session cookie and 401. This component wraps each file's download in `downloadRunFile`
(which uses the cookie-bearing `apiDownload`), tracks **which** row is downloading (so only that
button spins and the others disable), and surfaces a per-table error inline (never navigates away on
failure — same rule as the archive button). It exists so Setup and Template don't each re-implement the
file list + authenticated download + busy/error handling.

**Public surface.**
- `RunFilesTableProps { slug: string; files: RunFile[]; emptyLabel?: string }`.
- `RunFilesTable(props)` → either an empty-state `<p>` or a `<Table>`.

**State (useState).**
- `downloading: string | null` — the `f.name` currently downloading (null = idle). Drives per-row
  spinner + sibling-disable.
- `error: string | null` — last download failure message.

**Process / branches (the `download(name)` action, lines 31–45).**
1. Clear `error`, set `downloading=name`.
2. `await downloadRunFile(slug, name)` → `GET /runs/{slug}/files/{name}` via `apiDownload` (blob →
   object-URL anchor click; uses server `Content-Disposition` filename else `name`).
3. **Catch:** if `ApiError` → `err.detail || "Could not download {name}."`; else the generic
   "Could not download {name}." (network/0-status also routed here via ApiError(0,…)).
4. **Finally:** `downloading=null`.
- **Empty branch (lines 47–53):** `files.length === 0` → centered `<p>` with `emptyLabel ?? "No files yet."`.

**Layer-3 — states.**
- **Empty:** `emptyLabel`-driven `<p>` (Setup passes "No setup workbook found for this run yet.";
  Template passes "No generated template yet — generate one above.").
- **Error:** top-of-table `<Alert tone="error">` (line 57) — table still renders below.
- **Per-row downloading:** that row's Button `loading` true (spinner); **all other** rows' buttons
  `disabled` (`downloading !== null && downloading !== f.name`) so only one download at a time.
- **Idle:** plain rows with enabled Download buttons.

**Layer-3 — data bindings (pixel-level, per `RunFile` in types.ts:97–102).**
- `f.name` (string) → **File** cell, `font-semibold` (TD line 71). Key for the row (`key={f.name}`).
- `f.kind` (`"input"|"output"`) → **Kind** cell, a `StatusChip` toned `accent` for output else `slate`
  (line 73). Label text = the literal kind string.
- `f.size_bytes` (number) → **Size** cell, right-aligned `tabular-nums text-text-muted`, formatted by
  `formatBytes` (format.ts:4–15): `<1024`→`"{n} B"`; else divides by 1024 stepping KB/MB/GB/TB,
  `toFixed(value>=10 || unit===0 ? 0 : 1)` — i.e. **0 decimals when ≥10 or in B-rollover, else 1
  decimal** (e.g. 1536→"1.5 KB", 12345→"12 KB"). Negative/non-finite → "—".
- `f.modified` (ISO string) → **Modified** cell, `text-text-muted`, via `formatTimestamp`
  (format.ts:18–28): `toLocaleString` with `{year:numeric, month:short, day:numeric, hour:2-digit,
  minute:2-digit}` in the **browser locale**; invalid date → raw ISO returned.
- Action cell → the Download `<Button variant="secondary" size="sm">` with an inline download SVG;
  `loading={downloading===f.name}`, `disabled` per above.

**Layer-3 — interactions → endpoints.** Download button → `download(f.name)` → `GET
/runs/{slug}/files/{name}` (authenticated blob). No navigation. **Reachability:** rendered inside
Setup (step 1) and Template (step 2) cards.

**Deps.** `react`, `@/lib/api` (`ApiError`, `downloadRunFile`, type `RunFile`), `@/components/ui`
(`Button, StatusChip, Table, THead, TBody, TR, TH, TD`), `@/lib/format` (`formatBytes`,
`formatTimestamp`), `./Alert`.

---

## A.4 — DownloadArchiveButton.tsx  (census 291 · 1786 B · 71 lines · tsx · not empty)

**What.** A standalone "Download run folder (.zip)" button with an inline download icon and a busy
state; on failure shows a small error line beneath (right-aligned) instead of navigating away.

**Detailed WHY.** The buyer must be able to grab the **entire** run folder (inputs + outputs) in one
authenticated request — and per the no-file-storage contract that archive is **streamed on request**,
zipped on the fly, not a stored artifact. A plain link would lose the session cookie; this routes
through `downloadRunArchive` → `apiDownload`. It is split out from RunFilesTable because the archive is
a page-header affordance (rendered on the intake page header, line 181), not a row in a file list. The
"never navigate away on failure" behaviour is the same audit-friendly rule as single-file download:
the user stays put and sees why it failed.

**Public surface.**
- `DownloadArchiveButtonProps { slug: string; variant?: ButtonProps["variant"]; size?: ButtonProps["size"]; className?: string }`
  (variant defaults `"secondary"`, size `"md"`).
- `DownloadArchiveButton(props)`.
- internal `DownloadIcon()` — a 15×15 inline down-arrow-into-tray SVG, `aria-hidden`.

**State.** `busy: boolean` (download in flight), `error: string | null`.

**Process / branches (`onClick`, lines 40–54).** clear error → `busy=true` → `await
downloadRunArchive(slug)` (`GET /runs/{slug}/archive` → `{slug}.zip`) → **catch:** ApiError →
`err.detail || "Could not download the run folder."` else the same generic; → **finally:** `busy=false`.

**Layer-3 — states.** **Idle** (enabled button); **busy** (`loading` true → spinner, button disabled
by the Button primitive); **error** (a `text-xs text-danger` `<p>` beneath the button, right-aligned via
`items-end`). No empty/not-found of its own.

**Layer-3 — bindings.** No backend field rendered (it's an action). Label is the literal
"Download run folder (.zip)". The intake page passes `size="sm"` (line 181). `slug` flows only into the
endpoint path, not the UI.

**Layer-3 — interactions → endpoints.** Click → `GET /runs/{slug}/archive` (authenticated zip stream).
No navigation. **Reachability:** intake page header.

**Deps.** `react`, `@/lib/api` (`ApiError`, `downloadRunArchive`), `@/components/ui`
(`Button`, type `ButtonProps`).

---

## A.5 — SetupSection.tsx  (census 296 · 3816 B · 121 lines · tsx · not empty) — STEP 1

**What.** Step 1 of the wizard. Lists the run's **input** files (the kickoff/setup workbook to download
& fill) via RunFilesTable, then provides an `.xlsx` upload that opens the sourcing cycle. On success it
reports the new `cycle_id` and lifts `(cycle_id, kanban)` to the page.

**Detailed WHY.** A sourcing cycle can't begin until the buyer downloads the kickoff workbook, fills it
(scope: DCs/lots/items/timeframes/suppliers/volumes), and uploads it — `uploadSetup` ingests it and
creates the `cycle` row that every later step keys off (`has_cycle`). This section is the entry gate:
it shows the file to download (so the buyer knows what to fill) and the upload control, and on success
surfaces the cycle id as proof the cycle opened. It owns its own upload/submit/error state so a failed
upload is recoverable in place (the contract's "surface, don't fudge" — a bad workbook errors, it isn't
silently accepted). The `done` flag is derived from EITHER a session `cycleId` OR existing input files,
so a returning user who already ran setup sees it complete.

**Public surface.**
- `SetupSectionProps { slug; files: RunFile[]; filesLoading: boolean; filesError: string | null; cycleId: string | null; onSetupComplete: (cycleId, kanban: KanbanResponse) => void }`.
- `SetupSection(props)`.

**State.** `file: File | null` (chosen upload), `submitting: boolean`, `error: string | null`.
**Derived.** `inputFiles = files.filter(kind==="input")` (line 35); `done = Boolean(cycleId) ||
inputFiles.length > 0` (line 36).

**Process / branches (`onUpload`, lines 38–55).**
1. Guard `if (!file) return` (button is also `disabled={!file}`).
2. clear error, `submitting=true`.
3. `await uploadSetup(slug, file)` → `POST /runs/{slug}/setup` (multipart `file`) → `{cycle_id, kanban}`.
4. **Success:** clear `file`, call `onSetupComplete(result.cycle_id, result.kanban)` — the page sets
   `cycleId`, `setupDoneThisSession=true`, normalizes & stores the kanban, and reloads files.
5. **Catch:** ApiError → `err.detail || "Could not process the setup workbook."`; non-ApiError →
   "Unexpected error uploading the setup workbook."
6. **Finally:** `submitting=false`.

**Layer-3 — states (and where each renders).**
- **Files loading** (`filesLoading`, lines 73–77): spinner + "Loading files…" (the page passes this
  while `listRunFiles` is in flight).
- **Files error** (`filesError`, line 79): `<Alert tone="error">` with the page's files-error message.
- **Files loaded:** RunFilesTable of `inputFiles`, empty label "No setup workbook found for this run yet."
- **Upload idle:** FileInput (`.xlsx`) + "Upload setup" button (disabled until a file is chosen).
- **Submitting:** button `loading`; FileInput `disabled`.
- **Upload error** (line 108): `<Alert tone="error">{error}</Alert>`.
- **Success** (lines 109–116): when `cycleId && !error` → `<Alert tone="success">Cycle opened · <code>{cycleId}</code></Alert>`.
- **Header completion:** `StepHeader state={done?"done":"current"}`; actions = `StatusChip tone="green">Complete` when done else `tone="accent">In progress`.

**Layer-3 — bindings.**
- `cycleId` (string | null) → success Alert, rendered in a `<code>` chip (`bg-white/60 px-1.5 py-0.5
  text-xs`). Raw id, no formatting.
- `inputFiles` → RunFilesTable (see A.3 bindings).
- No numeric/currency bindings here.

**Layer-3 — interactions → endpoints.**
- FileInput → local `setFile`. Upload → `POST /runs/{slug}/setup`. Each row's Download (via
  RunFilesTable) → `GET /runs/{slug}/files/{name}`.
- **Reachability:** first card on the intake page; always rendered (not gated).

**Deps.** `react`, `@/lib/api` (`ApiError`, `uploadSetup`, types `KanbanResponse`,`RunFile`),
`@/components/ui` (`Button, FileInput, Panel, StatusChip`), `./Alert`, `./RunFilesTable`, `./StepHeader`.

---

## A.6 — TemplateSection.tsx  (census 298 · 3536 B · 110 lines · tsx · not empty) — STEP 2

**What.** Step 2. Generates the **round-{round}** supplier bid template (`POST
/runs/{slug}/rounds/{round}/template`), then shows it in a RunFilesTable for download. Handles the
`gate_required` envelope distinctly (setup not done yet).

**Detailed WHY.** Suppliers bid on a generated, round-specific workbook whose columns are determined by
the cycle's active cost lines/scope. The template must be generated **after** setup and **per round**
(rounds 1–6). This section drives that generation, then surfaces the produced file for download. Crucial
fidelity detail (file comment, lines 32–36): the generated template **lands in `inputs/`** (not
`outputs/`), so the section filters input files whose name contains `round{round}_bid_template` — that
filter survives a page reload, unlike the session-only `lastFilename`. So "done" is durable across
reloads, not just an in-memory flag. The `gate` branch keeps the user on this step with a warning when
setup isn't complete (soft gate honours the backend's `gate_required`, not a guessed client lock).

**Public surface.**
- `TemplateSectionProps { slug; round: number; files: RunFile[]; disabled: boolean; onTemplateGenerated: (filename, kanban) => void }`.
- `TemplateSection(props)`.

**State.** `submitting`, `error: string|null`, `gate: string|null` (the gate-required detail),
`lastFilename: string|null` (session memory of the just-generated file).
**Derived.** `templateFiles = files.filter(kind==="input" && name.includes("round{round}_bid_template"))`
(lines 34–37); `done = templateFiles.length > 0 || Boolean(lastFilename)` (line 38).

**Process / branches (`onGenerate`, lines 40–61).**
1. clear `error` & `gate`, `submitting=true`.
2. `await generateTemplate(slug, round)` → `{filename, kanban}`.
3. **Success:** `setLastFilename(result.filename)`, `onTemplateGenerated(filename, kanban)` (page sets
   `templateDoneThisSession=true`, stores kanban, reloads files).
4. **Gate branch:** `if (err instanceof ApiError && err.isGateRequired)` → `setGate(err.detail ||
   "Complete setup before generating the template.")` — this is the **gate_required** envelope code
   path (client honours backend gating).
5. **Else error:** ApiError → `err.detail || "Could not generate the template."`; non-ApiError →
   "Unexpected error generating the template."
6. **Finally:** `submitting=false`.

**Layer-3 — states.**
- **Disabled/todo** (prop `disabled`, i.e. setup not done): StepHeader `state="todo"`; body shows
  `<Alert tone="info">Complete setup first to generate this round's template.` (lines 86–90); the
  Generate button is `disabled`.
- **Gate** (lines 91): `<Alert tone="warning">{gate}</Alert>` (only if the backend returned
  gate_required despite the soft client gate).
- **Error** (line 92): `<Alert tone="error">{error}</Alert>`.
- **Success** (lines 93–100): when `lastFilename && !error && !gate` → `<Alert tone="success">Template
  generated · <code>{lastFilename}</code></Alert>`.
- **Submitting:** the action button `loading`.
- **Done:** StepHeader `state="done"`, a `StatusChip tone="green">Complete`, and the action button label
  flips to **"Regenerate"** (variant secondary) vs **"Generate template"** (variant primary).
- **Files list:** RunFilesTable of `templateFiles`, empty label "No generated template yet — generate
  one above."

**Layer-3 — bindings.**
- `round` (number) → StepHeader description "Generate the round {round} bid template…" and the success
  Alert / file filter. No special numeric formatting (plain integer).
- `lastFilename` / `result.filename` (string) → success Alert `<code>` (mono chip).
- `templateFiles` → RunFilesTable (A.3 bindings; size via `formatBytes`, modified via `formatTimestamp`).

**Layer-3 — interactions → endpoints.**
- Generate/Regenerate → `POST /runs/{slug}/rounds/{round}/template`. Row Download → `GET
  /runs/{slug}/files/{name}`.
- **Reachability:** second card; rendered always but `disabled` until `setupDone` (page line 241:
  `disabled={!setupDone}`).

**Deps.** `react`, `@/lib/api` (`ApiError`, `generateTemplate`, types), `@/components/ui`
(`Button, Panel, StatusChip`), `./Alert`, `./RunFilesTable`, `./StepHeader`.

---

## A.7 — ImportSection.tsx  (census 292 · 9725 B · 292 lines · tsx · not empty) — STEP 3

**What.** Step 3 — the bid-import surface. A **segmented mode control** (strict vs flexible), a
dropzone-styled `.xlsx` upload, and two outcome surfaces: a **success result** (count of ingested bid
lines, "audit event recorded (IMPORTED)") and, for flexible mode, a **MappingProposal** dry-run with a
**Cancel / Confirm & import** pair. The largest intake component.

**Detailed WHY.** This is the data-fidelity crux of intake (CLAUDE.md req 3): bids enter the system here
and must map every field to its target with **no guessing**. Two modes exist because suppliers either
fill the generated template (strict — import directly) or return their own file (flexible — the backend
infers a column mapping and returns a **proposal with nothing written**, which the buyer reviews and
confirms). The component therefore drives a two-phase flexible flow: first submit with `confirm=false`
(get a `MappingProposalView`), then `confirm=true` on the **same file** to actually write. The
"unrecognized rows are quarantined — never guessed" promise is stated in the step description (line 136)
and enforced downstream (Review surfaces quarantine). It also honours `gate_required` (template not
generated yet) as a warning that keeps the user on the step.

**SIMPLIFICATION FLAG (carried from design).** The flexible flow here is **confirm-only**. The design
(`DESIGN_REQUESTS.md` §A3 / §M1 "Editable column mapper") called for the mapping table to be
**editable** — a field dropdown per column, ambiguous columns flagged for assignment — so the buyer can
**override** the inferred mapping and resolve ambiguities before confirming. The as-built has **no
in-app override**: the buyer can only accept (Confirm & import) or Cancel the proposed mapping.
`DATA_AND_PROCESS_MAP.md` records this verbatim as a seam gap: "confirm-only, NO editable override —
G-seam" (line 203) and "◐ partial — infer+confirm; **no editable mapper**" (line 306). See the
Simplifications section at the end. This matters because a near-miss inference on a messy supplier file
cannot be corrected in-app — it must be Cancelled and the source file fixed, then re-uploaded.

**Public surface.**
- `ImportSectionProps { slug; round: number; disabled: boolean; onImported: (ingested: number, kanban) => void }`.
- module const `MODES` (lines 23–34): the two segmented options, each `{ value, title, hint }`:
  - `strict` — "Our template (strict)" — "The supplier filled in the generated template — import directly."
  - `flexible` — "Supplier's own file (flexible)" — "A non-template file — propose a column mapping for you to review first."
- `ImportSection(props)`.

**State (7 fields).**
- `mode: BidImportMode` (default `"strict"`).
- `file: File | null`.
- `submitting: boolean` (initial submit in flight).
- `confirming: boolean` (the confirm-import in flight).
- `error: string | null`.
- `gate: string | null` (gate_required detail).
- `ingested: number | null` (count after a successful write).
- `proposal: MappingProposalView | null` (the flexible dry-run, when present).
**Helpers.** `resetResults()` clears error/gate/ingested/proposal; `handleError(err, fallback)` routes
gate_required → `gate`, else → `error`. **Derived:** `busy = submitting || confirming`;
`imported = ingested != null && !error`; `stepState = disabled ? "todo" : imported ? "done" : "current"`.

**Process / branches — full enumeration.**

*Initial submit (`onSubmit`, lines 70–94):*
1. Guard `if (!file) return` (button also disabled without a file).
2. `resetResults()`, `submitting=true`.
3. `importBids({ run: slug, round, mode, confirm: false, file })` → `POST /bids/import` (multipart file
   + form fields run/round/mode/confirm).
4. **If `isBidImportProposal(res)`** (flexible, confirm=false → dry run): `setProposal(res.proposal)` —
   **nothing written**, the proposal surface appears.
5. **Else** (strict, or a flexible that returned a direct result): `setIngested(res.ingested)`,
   clear `file`, `onImported(res.ingested, res.kanban)` (page stores kanban, bumps `bidsRefreshKey`,
   reloads files).
6. **Catch:** `handleError(err, "Could not import the bid file.")` → gate_required→`gate`, else→`error`.
7. **Finally:** `submitting=false`.

*Confirm (`onConfirm`, lines 97–121):* only reachable when a `proposal` is shown.
1. Guard `if (!file) return`.
2. clear error/gate, `confirming=true`.
3. `importBids({ run, round, mode: "flexible", confirm: true, file })` → re-submits the **same file**
   with confirm=true (writes the bids per the proposed mapping).
4. **If `!isBidImportProposal(res)`** (a real result): `setIngested(res.ingested)`, clear `proposal` &
   `file`, `onImported(...)`.
5. **Catch:** `handleError(err, "Could not confirm the import.")`.
6. **Finally:** `confirming=false`.

*Cancel proposal (`cancelProposal`, lines 123–125):* `setProposal(null)` — discards the dry run; nothing
was written, so this is a pure UI dismiss.

*Mode switch (lines 168–171):* selecting a mode calls `setMode` + `resetResults()` (a mode change
invalidates any prior proposal/result/error).

*New file chosen (lines 220–224):* `setFile(f)` then `setProposal(null)` & `setIngested(null)` — a new
file invalidates any prior proposal/result (comment line 222).

**Layer-3 — states (every one).**
- **Disabled/locked** (`disabled` = template not generated): StepHeader `state="todo"`, action chip
  `StatusChip tone="slate">Locked`; an `<Alert tone="info">Generate this round's template before
  importing bids.` (lines 149–153); the `<fieldset disabled>` greys the whole mode control + upload.
- **In progress (idle, unlocked):** chip `StatusChip tone="accent">In progress`.
- **Mode = strict vs flexible:** segmented control with `aria-pressed` on the active button; the active
  button gets `bg-surface-card text-brand-primary shadow-card`; a hint span shows the active mode's
  `hint`. The submit button label is **"Propose mapping"** (flexible) or **"Import bids"** (strict)
  (line 236).
- **Submitting:** submit button `loading`; fieldset `disabled` (busy); confirm path disabled.
- **Gate** (line 190): `<Alert tone="warning">{gate}`.
- **Error** (line 191): `<Alert tone="error">{error}`.
- **Proposal present** (flexible dry run, lines 272–288): a warning-bordered box wrapping
  `<MappingProposal proposal={proposal}/>` + a **Cancel** (secondary, disabled while confirming) and
  **Confirm & import** (primary, `loading={confirming}`) button row.
- **Imported/success** (lines 242–269): a success-bordered card with a check icon, header "Round
  {round} bids imported · audit event recorded (IMPORTED)", and body "Imported **{ingested}** bid
  line(s). Review them in step 4 below." StepHeader → `state="done"`, chip `green>Complete`.
- **Empty (no file yet):** dropzone shows "Drop a bid workbook here, or browse" + ".xlsx — bids +
  Capacity sheet ingest together"; submit disabled.

**Layer-3 — bindings (pixel-level).**
- `round` (number) → step description, success header "Round {round} bids imported", and the import
  payload. Plain integer.
- `ingested` (number) → success body, rendered `font-display font-extrabold tabular-nums
  text-text-strong` (line 263); pluralization `bid line{ingested === 1 ? "" : "s"}` (line 266). No
  thousands formatting applied here (raw number) — note this differs from ReviewSection's `formatCount`.
- `mode` → which `MODES` entry's title/hint is active; drives the submit label.
- `proposal` → passed whole to MappingProposal (see A.8 for that component's bindings).
- The "Capacity sheet ingest together" hint (line 215) reflects that a bid workbook also carries a
  Capacity sheet that ingests in the same request (data-fidelity: capacity isn't a separate upload).

**Layer-3 — interactions → endpoints.**
- Mode buttons → local `setMode`+reset. FileInput → local set. **Propose mapping / Import bids** →
  `POST /bids/import` (confirm=false). **Confirm & import** → `POST /bids/import` (confirm=true).
  **Cancel** → local dismiss. On success → `onImported` bumps the Review refresh.
- **Reachability:** third card; rendered always but `disabled` until `templateDone` (page line 251).

**Deps.** `react`, `@/lib/api` (`ApiError`, `importBids`, `isBidImportProposal`, types `BidImportMode`,
`KanbanResponse`, `MappingProposalView`), `@/components/ui` (`Button, FileInput, Panel, StatusChip`),
`@/lib/cn`, `./Alert`, `./MappingProposal`, `./StepHeader`.

---

## A.8 — MappingProposal.tsx  (census 293 · 4117 B · 129 lines · tsx · not empty)

**What.** A **read-only** view of a flexible-import **dry run**: a warning banner ("Nothing has been
imported yet…"), a 4-stat summary (sheet name · header row · mapping count · confidence chip), an
optional summary Alert, a table of `field → source header → column → basis → confidence`, and an
optional ambiguities list. No `"use client"` — it is purely presentational.

**Detailed WHY.** Flexible import must make it **explicit that nothing has been written** and show the
buyer exactly how the engine proposes to read their messy file before they commit. This component is
that legibility surface: it renders the inferred mapping per field with the **basis** (why it mapped
that column) and a **confidence** chip, and lists any **ambiguities** the inference couldn't resolve.
It deliberately surfaces (not fudges) uncertainty — the "never guess" contract made visible. It is
extracted from ImportSection so the proposal rendering is testable/reusable and ImportSection stays
focused on the flow.

**SIMPLIFICATION FLAG — read-only / confirm-only (designed-but-simplified MVP cut).** This is the
component the prompt singles out. **By design (A3/M1) the mapping table should be EDITABLE** — each row
a field dropdown so the buyer can reassign a column, and ambiguous columns flagged **for assignment**.
The as-built renders the mapping **strictly read-only**: `field`, `source_header`, `column_index`,
`basis`, `confidence` are displayed as text/chips with **no input controls, no dropdowns, no per-row
override**. The only buyer affordance is the ImportSection-level **Confirm & import** (accept as-is) or
**Cancel**. The ambiguities (lines 115–126) are **listed for the buyer's awareness**, not resolvable
in-app. **Why it matters:** if the inference is wrong or an ambiguity is material, the buyer's only
recourse is to Cancel, fix the source workbook, and re-upload — there is no in-app re-map or
fix-and-retry. This is exactly the documented seam gap ("confirm-only, no editable mapper", G-seam).
It is a deliberate MVP cut of the A3 refinement, not an accidental omission — the propose+confirm half
is real and wired; the override half is the unbuilt half.

**Public surface.**
- `MappingProposal({ proposal: MappingProposalView })`.
- internal `confidenceTone(c: MappingConfidence)`: `high`→green, `medium`→amber, else (`low`)→slate.

**State.** None (stateless / read-only).
**Derived.** `entries = Object.entries(proposal.mappings)` (line 27) — the field→entry pairs.

**Layer-3 — states.**
- **Always-on banner** (lines 31–35): `<Alert tone="warning">` "Nothing has been imported yet. Review
  the proposed mapping below, then choose **Confirm & import** to write the bids." — the not-written
  guarantee.
- **Optional summary** (lines 72–74): `proposal.summary` → `<Alert tone="info">` if present.
- **No mappings** (lines 88–93): if `entries.length === 0` → a single table row spanning 5 cols
  "No fields were mapped." (an explicit empty state for the mapping table).
- **Ambiguities present** (lines 115–126): a warning-toned `<ul>` of `proposal.ambiguities` (only when
  length > 0).
- No loading/error of its own (it's rendered only once ImportSection already has the proposal).

**Layer-3 — data bindings (per `MappingProposalView` types.ts:135–142 and `MappingEntry` 125–131).**
- `proposal.sheet_name` (string) → "Sheet" stat, `text-sm font-semibold text-text-strong`.
- `proposal.header_row` (number) → "Header row" stat, `font-semibold tabular-nums` (a 1-based row index;
  no thousands formatting).
- `entries.length` (number) → "Mappings" stat, `tabular-nums` (count of mapped fields).
- `proposal.is_confident` (boolean) → "Confidence" stat → `StatusChip tone={is_confident?"green":"amber"}`
  labelled "Confident" / "Needs review".
- Table rows, per `[key, m]`:
  - `m.field` → **Field** cell, `font-semibold`.
  - `m.source_header` → **Source header** cell, `text-text-muted`.
  - `m.column_index` (number) → **Column** cell, right-aligned `tabular-nums text-text-muted` (the
    0/1-based column ordinal as returned; rendered raw).
  - `m.basis` → **Basis** cell, `text-text-muted` (the inference reason, e.g. header match / position).
  - `m.confidence` (`high|medium|low`) → **Confidence** cell, `StatusChip tone={confidenceTone(c)}`
    with the literal confidence word as label.
- `proposal.ambiguities[]` (string[]) → bulleted list items (`list-inside list-disc`), keyed by index.
- **No editable bindings** — every cell is display-only.

**Layer-3 — interactions.** None within this component (the only actions — Confirm/Cancel — live in the
parent ImportSection). **Reachability:** rendered inside ImportSection's proposal box (step 3, flexible
mode, confirm=false).

**Deps.** `@/lib/api` (types `MappingConfidence`, `MappingProposalView`), `@/components/ui`
(`StatusChip, Table, THead, TBody, TR, TH, TD`), `./Alert`.

---

## A.9 — ReviewSection.tsx  (census 294 · 8464 B · 252 lines · tsx · not empty) — STEP 4

**What.** Step 4 — the round's imported bid review. Loads `GET /bids?run={slug}&round={round}`, then
renders (a) a top **Exception queue** (quarantine surface) of any non-scoreable/non-awardable lines and
(b) a full table of every bid line with price, basis, min-vol, validity, scoreable/awardable flags, and
incomplete-reason. A **Refresh** button reloads; `refreshKey` forces a reload after import.

**Detailed WHY.** After bids are written, the buyer must **see** them and — critically — see which lines
were **quarantined** rather than silently scored. This is the on-screen manifestation of the
data-fidelity contract (CLAUDE.md req 3): bad/ambiguous lines are surfaced as quarantine, never fudged.
The Exception queue is the human-decision surface ("Nothing is guessed — each needs a human decision",
line 159). It owns its own load/loading/error state and reloads on `refreshKey` bump so a fresh import
immediately reflects here.

**SIMPLIFICATION FLAG — quarantine is surface-only (no fix-and-retry).** The Exception queue **lists**
quarantined lines (with their reason/validity) but provides **no in-app remediation** — no "fix and
retry", no edit, no requeue. The design's **M5 "Ingest exception / quarantine resolution — the
fix-and-retry surface for quarantined rows"** (`DESIGN_REQUESTS.md` line 158) is **not built**; this is
a read-only surfacing. **Why it matters:** the buyer can *see* every quarantined line and why, satisfying
"surface, never fudge", but to actually resolve one they must correct the source workbook and re-import
the round — the in-app fix loop is the unbuilt half. (Consistent with the A8 confirm-only cut: the
intake surfaces are honest about exceptions but defer correction to re-upload.)

**Public surface.**
- `ReviewSectionProps { slug; round: number; refreshKey: number }`.
- internal `validityTone(status: string)`: regex on lowercased status — `valid|ok|complete|accepted`→
  green; `invalid|reject|expired|error`→amber; else slate.
- internal `BoolChip({ value })`: `StatusChip tone={value?"green":"slate"}` "Yes"/"No".
- `ReviewSection(props)`.

**State.** `bids: BidLineView[] | null` (null = not yet loaded), `loading: boolean` (init true),
`error: string | null`.
**Effects.** `load` is a `useCallback` keyed on `[slug, round]`; `useEffect(() => void load(), [load,
refreshKey])` reloads on round change OR a `refreshKey` bump (post-import).
**Derived.** `quarantined = (bids ?? []).filter(b => !b.is_scoreable || !b.is_awardable)` (line 72);
`hasBids = Boolean(bids && bids.length > 0)`.

**Process / branches (`load`, lines 49–64).** `loading=true`, clear error → `await listBids(slug,
round)` → `setBids(data)` → catch: ApiError→`err.detail||"Could not load bids."` else "Unexpected error
loading bids." → finally `loading=false`.

**Layer-3 — states (all rendered conditionally).**
- **Loading** (lines 108–113): spinner + "Loading bids…".
- **Error** (lines 115–127): `<Alert tone="error">{error}</Alert>` + a **Retry** button → `load()`.
- **Empty** (lines 129–136): `bids.length === 0` → "No bids yet" + "Import a bid file above to populate
  this round."
- **Exception queue** (lines 138–185): when `quarantined.length > 0` — a danger-bordered card titled
  "Exception queue" with a count badge and "Nothing is guessed — each needs a human decision"; a list
  of quarantined lines (see bindings).
- **Bids table** (lines 187–249): when `bids.length > 0` — the full 11-column table.
- **Header state:** StepHeader `state={hasBids?"done":"current"}`; actions: if `hasBids &&
  quarantined.length===0` → `StatusChip tone="green">Clean`; if `quarantined.length>0` →
  `StatusChip tone="amber">{n} need review`; always a **Refresh** button (`loading={loading}`).

**Layer-3 — data bindings (pixel-level, per `BidLineView` types.ts:362–381).**

*Exception queue rows (per quarantined `b`):*
- Reason chip: `StatusChip tone={!b.is_scoreable ? "gated" : "amber"}` → label "Not scoreable" (if
  `!is_scoreable`) else "Not awardable" (gated = danger styling; amber = warning).
- Identity line: `{b.supplier_id} · {b.dc_id} / {b.lot_id} / {b.item_id}` — the **raw cell-key ids**
  (note: ids, not resolved names, in the queue — names appear later in the engine/award lenses).
- Sub-line: `b.incomplete_reason_code ? "Reason: {code}" : "Validity: {b.validity_status}"`.

*Main table columns (per `b`):*
- **Supplier** ← `b.supplier_id` (`font-semibold`).
- **DC** ← `b.dc_id` (`text-text-muted`).
- **Lot** ← `b.lot_id`.
- **Item** ← `b.item_id`.
- **All-in / case** ← `price = b.submitted_all_in_case ?? b.fob_case` (line 206 — prefers the submitted
  all-in price, falls back to FOB/case). Rendered right-aligned `tabular-nums` via `formatPrice`
  (format.ts:31–37): `toLocaleString` with **min/max 2 fraction digits** (locale grouping). `null` →
  a muted em-dash "—". A trailing `b.currency_code` in `text-2xs text-text-subtle`.
- **Price basis** ← `basis = b.price_basis_resolved ?? b.price_basis` (line 207 — prefers the resolved
  basis), or "—" when falsy.
- **Min vol** ← `b.volume_minimum_cases` (number|null) right-aligned `tabular-nums` via `formatCount`
  (format.ts:40–43): `toLocaleString()` integer grouping, `null`→"—".
- **Validity** ← `b.validity_status` → `StatusChip tone={validityTone(status)}` with the literal status.
- **Scoreable** ← `b.is_scoreable` → `<BoolChip>` (Yes=green / No=slate).
- **Awardable** ← `b.is_awardable` → `<BoolChip>`.
- **Incomplete reason** ← `b.incomplete_reason_code ?? "—"`.
- Row key = `b.bid_line_id`.
- **Precision note:** prices show exactly 2 decimals (locale-grouped, no currency symbol — the symbol
  is replaced by the `currency_code` suffix); counts show locale-grouped integers; em-dash for any null
  → the decimal's journey is DB `numeric` → JSON number → `formatPrice`'s 2-dp `toLocaleString`.

**Layer-3 — interactions → endpoints.**
- Refresh / Retry → `load()` → `GET /bids?run={slug}&round={round}`.
- Reload trigger: `refreshKey` bumped by the page's `onImported` after a successful import.
- **Reachability:** fourth card; always rendered (loads on mount and on round/refreshKey change).

**Deps.** `react` (`useCallback, useEffect, useState`), `@/lib/api` (`ApiError`, `listBids`, type
`BidLineView`), `@/components/ui` (`Button, Panel, StatusChip, Table, THead, TBody, TR, TH, TD`),
`@/lib/format` (`formatCount`, `formatPrice`), `./Alert`, `./StepHeader`.

---

# PART B — runs/** (run-list & run-detail companion components)

Three components used outside intake: `NewRunModal` (create-run dialog on the runs index),
`StrategyPanel` (engine-config panel on Run Detail), and `KanbanBoard` (a board renderer — **orphaned**,
see below).

---

## B.1 — KanbanBoard.tsx  (census 299 · 2372 B · 69 lines · tsx · not empty) — ORPHANED

**What.** A 4-column kanban board renderer: `Done | Doing | Next | Waiting on you`, each column a card
list with a coloured header dot, a count badge, and an empty-state. Tolerant card typing (string or
object). No `"use client"` — purely presentational.

**Detailed WHY.** The product models run progress as a kanban (the backend returns kanban buckets from
intake/setup/template/import endpoints). This component is the generic renderer for that shape — fixed
four buckets in display order, with a per-bucket accent dot and a `cardTitle`/`cardKey` pair that
handles both the permissive `KanbanCard` forms (a plain string, or an object with `title`/`label`/`id`).
It exists so any surface can drop a board in given a normalized `Kanban`.

**ORPHANED / unused flag.** A repo-wide grep finds **no importer** of `KanbanBoard` anywhere in
`frontend/**` (only its own definition). The intake page **normalizes** kanban (`normalizeKanban`) and
stores it, and Run Detail renders its own progress UI, but **neither mounts this component**. So
`KanbanBoard` is **defined but dead** in the current wiring — a complete, real renderer with no caller.
Its mtime (2026-06-21, untouched since) is consistent with being superseded. This is **not** a stub
(it's fully implemented), but it is **unreferenced**; flag it as latent/orphaned code. (Per the
exhaustiveness bar: noted, not skipped.)

**Public surface.**
- `KanbanBoard({ kanban: Kanban })`.
- internal `Column({ bucket, cards })`; helpers `cardTitle(card)` (string → itself; object → first of
  `title`/`label`/string-`id`/"" → "Untitled item"), `cardKey(card, index)` (stable React key — string
  id when present else `index:title`).
- module const `BUCKET_ACCENT` (lines 6–11): Done→emerald-500, Doing→accent, Next→slate-400, Waiting on
  you→amber-500 (header-dot colour only; the card bodies stay neutral/calm — comment line 5).

**State.** None.

**Layer-3 — states.**
- **Per-column empty** (lines 44–45): "No items" when `cards.length === 0`.
- **Populated:** one card `<div>` per `cardTitle(card)`.
- **Count badge:** `cards.length` per column header.
- Uses `KANBAN_BUCKETS` (types.ts:34–41) to render the fixed four columns in order, defaulting any
  missing bucket to `[]` (line 65: `kanban[bucket] ?? []`).

**Layer-3 — bindings.**
- `kanban[bucket]` (`KanbanCard[]`) → cards; each card's title via `cardTitle`. No numbers except the
  per-column `cards.length` count badge (`text-2xs`).
- Uses Tailwind tokens for the design-token (`bg-surface-subtle`, `border-line`, `text-ink`) — note
  these are a slightly different token family (`ink`/`line`/`surface`) than the intake components'
  (`text-strong`/`border`/`surface-card`), corroborating it predates/diverges from the current intake
  token set.

**Layer-3 — interactions.** None (no clicks; pure display). **Reachability:** **none** (orphaned).

**Deps.** `@/lib/api` (`KANBAN_BUCKETS`, types `Kanban, KanbanBucket, KanbanCard`), `@/lib/cn`.

---

## B.2 — NewRunModal.tsx  (census 300 · 3909 B · 138 lines · tsx · not empty)

**What.** The "New run" creation dialog (rendered from the runs index, `app/(app)/page.tsx` line 319).
A form with **Commodity** (required) + **Label** (required) + a **Rehearsal** checkbox; Create posts to
`POST /runs` and lifts the created `RunDetail` to the parent.

**Detailed WHY.** Every run starts here. A run needs a commodity and a human label, and the **rehearsal**
flag (CLAUDE.md/rehearsal concept) marks practice runs kept separate from production sourcing (the
checkbox copy: "Practice run — kept separate from production sourcing.", line 121). The modal owns its
own form/submit/error state, validates client-side (both fields non-empty after trim), and blocks
double-submit and close-while-submitting. On success it resets and hands the parent the full
`RunDetail` so the list can refresh/navigate.

**Public surface.**
- `NewRunModalProps { open: boolean; onClose: () => void; onCreated: (run: RunDetail) => void }`.
- `NewRunModal(props)`.

**State.** `commodity`, `label` (strings), `rehearsal: boolean`, `error: string|null`,
`submitting: boolean`.
**Helpers.** `reset()` clears all five; `handleClose()` no-ops while submitting else reset + `onClose()`.
**Derived.** `valid = commodity.trim().length>0 && label.trim().length>0` (line 58) → gates the Create
button.

**Process / branches (`onSubmit`, lines 36–56).**
1. `e.preventDefault()`, clear error, `submitting=true`.
2. `await createRun({ commodity: commodity.trim(), label: label.trim(), rehearsal })` → `POST /runs`
   → `RunDetail` (201).
3. **Success:** `reset()`, `onCreated(run)` (parent refreshes/navigates).
4. **Catch:** ApiError → `err.detail || "Could not create the run."`; else "Unexpected error. Please try
   again."; and `submitting=false` (note: on the **success** path `submitting` is reset via `reset()`;
   on error it's set false here).

**Layer-3 — states.**
- **Idle/open:** the form; Create disabled until `valid`.
- **Submitting:** Create `loading`; Cancel disabled; Commodity/Label/checkbox `disabled`; `handleClose`
  is a no-op (can't dismiss mid-create) — prevents a half-created run being abandoned.
- **Error** (lines 127–134): an inline `role="alert"` danger box with `{error}`.
- **Invalid:** Create disabled (no empty commodity/label).
- The dialog itself is controlled by `open`; `noValidate` on the form so the component owns validation
  (not the browser).

**Layer-3 — bindings.**
- `commodity` ↔ Input (placeholder "e.g. Corrugated Packaging", `autoFocus`, `required`).
- `label` ↔ Input (placeholder "e.g. FY26 H1 Rebid", `required`).
- `rehearsal` ↔ checkbox (`h-4 w-4`, brand-primary).
- No backend numbers rendered; the only outputs are the form fields and the error string. The created
  `RunDetail` is handed to the parent, not rendered here.

**Layer-3 — interactions → endpoints.**
- Create (`type="submit" form="new-run-form"`) → `onSubmit` → `POST /runs`. Cancel / backdrop →
  `handleClose`. **Reachability:** opened from the runs-index "New run" affordance (`app/(app)/page.tsx`
  line 319).

**Deps.** `react`, `@/lib/api` (`ApiError`, `createRun`, type `RunDetail`), `@/components/ui`
(`Button, FormField, Input, Modal`).

---

## B.3 — StrategyPanel.tsx  (census 301 · 6628 B · 193 lines · tsx · not empty) — minimal A1

**What.** The Run-Detail engine-strategy panel (mounted at `app/(app)/runs/[slug]/page.tsx` line 353,
only when `run.has_cycle`). Loads `GET /runs/{slug}/strategy`, lets the buyer pick a **weight preset**
and edit the **four safeties** (premium ceiling, coverage floor, concentration threshold, max
suppliers/DC), **shows the five scoring weights read-only** as percentages, and saves via `PUT
/runs/{slug}/strategy`. It is the config the **next** analysis runs under (header note "Used by the next
analysis", line 135).

**Detailed WHY.** Before sealing an analysis the buyer must be able to review and tune the engine
config — without it, setup was a "blind file upload with no review/config surface" (DESIGN_REQUESTS.md
A1). This panel is that surface: the named preset selects a weight profile; the four safeties bound the
engine's selection (premium ceiling caps over-incumbent premium, coverage floor enforces minimum
coverage, concentration threshold caps supplier concentration, max suppliers/DC caps fan-out). It
persists onto the cycle so the next run uses it. It owns load/loading/error/save/dirty/saved state and
only enables Save when the form diverges from the loaded strategy.

**SIMPLIFICATION FLAG — "the minimal A1" (deliberate slice).** The file's own header comment names it:
"The minimal A1 strategy slice: review + tune the engine config the NEXT analysis runs under (the named
weight preset + the four safeties)." The design's **A1** (DESIGN_REQUESTS.md §A1) is much larger — it
called for: the ingested **scope read-back** (DCs/lots/items/timeframes/suppliers/projected volumes),
the **5 weights editable** (not just the preset), **exclusions / preferred suppliers**, **lenses to
run**, **plus the D43 pricing-basis controls** (modality picker FOB/DELIVERED/XDOC + a configurable
**cost-line manager**). The as-built ships only **preset + 4 safeties**, with the **5 weights
READ-ONLY** (display-only percentages) and **none** of: scope read-back, exclusions/preferred,
lens selection, or the pricing-basis/cost-line controls. This is the documented minimal slice of A1.
**Why it matters:** the buyer can choose among preset weight profiles and tune the four guardrails, but
cannot hand-tune individual weights, exclude/prefer suppliers, choose lenses, or set the award
modality/cost-lines in-app — those design surfaces are unbuilt. Wiring to `getStrategy`/`updateStrategy`
is real and complete for what's shipped.

**Public surface.**
- `StrategyPanel({ slug: string })`.
- internal `NumField({ label, value, step, onChange })` — a labelled `type="number"` input (`min=0`,
  `tabular-nums`).
- module consts: `PRESETS` (balanced / price_focus / coverage_focus / risk_averse / custom — value+label,
  lines 11–17); `WEIGHTS` (the five `keyof Strategy` weight keys + labels: Price, Coverage, Historical,
  Z-risk, Continuity, lines 19–25); `pct(n) = "{Math.round(n*100)}%"` (line 27).

**State.** `strategy: Strategy | null` (loaded), `loading` (init true), `error: string|null`, `saving`,
`saved: boolean`; and the editable form mirror: `preset` (default "balanced"), `premium` ("0.12"),
`coverage` ("0.80"), `conc` ("0.40"), `maxSup` ("2") — **strings** (raw input values).
**Helpers.**
- `hydrate(s)` (lines 73–80): stores `strategy` and seeds the five form fields from the loaded values
  (`String(...)` so they bind to text inputs).
- `load` (lines 82–94): `GET /runs/{slug}/strategy` → `hydrate`; error → "Could not load strategy."
- `save` (lines 100–121): `PUT /runs/{slug}/strategy` with `{ weight_preset: preset, premium_ceiling:
  Number(premium), coverage_floor: Number(coverage), conc_thresh: Number(conc), max_sup_dc:
  Number(maxSup) }` → `hydrate(updated)` + `saved=true`; error → "Could not save strategy."
- `dirty` (lines 123–129): true when any of preset/premium/coverage/conc/maxSup differs from `strategy`
  (numeric compares via `Number(...)`).
**Effect.** `useEffect(() => void load(), [load])` on mount.

**Process / branches.**
- **Load:** loading → strategy hydrated, or error.
- **Save:** only reachable when `dirty` (Save `disabled={!dirty}`); on success re-hydrates from the
  server's returned `Strategy` (so `dirty` resets and `saved` shows); on error keeps the form.
- **Note — the PUT does NOT send the five weights** (only preset + 4 safeties); the backend resolves
  weights from the preset and returns them (the panel then displays the resolved weights read-only).
  This is consistent with `UpdateStrategyPayload` (types.ts:83–89) which carries **no** weight fields.

**Layer-3 — states.**
- **Loading** (lines 138–139): "Loading…".
- **Loaded:** the preset `<select>`, the read-only weights box, the four NumFields, the save row.
- **Error** (line 180): `text-xs text-danger` `{error}`.
- **Dirty vs saved vs up-to-date** (lines 182–184): status text "Unsaved changes" (dirty) /
  "Saved ✓" (saved && !dirty) / "Up to date".
- **Saving:** Save button `loading`.
- **Gated mount:** the whole panel only renders when `run.has_cycle` (page line 353) — i.e. after setup
  ingested a cycle; before that, no strategy exists to configure.

**Layer-3 — data bindings (per `Strategy` types.ts:69–80).**
- `strategy.weight_preset` → seeds `preset` ↔ `<select>` (options from `PRESETS`).
- The five weights `weight_price / weight_coverage / weight_historical / weight_zrisk /
  weight_continuity` (numbers, fractions 0–1) → **read-only** percentages in the "Scoring weights" box:
  each `<strong className="tabular-nums">{pct(strategy[w.key])}</strong>` where `pct = Math.round(n*100)
  + "%"` (e.g. 0.35 → "35%"). **Precision: rounded to whole percent, no decimals.** These are
  display-only — no inputs.
- `strategy.premium_ceiling` → `premium` ↔ NumField (step 0.01) "Premium ceiling".
- `strategy.coverage_floor` → `coverage` ↔ NumField (step 0.01) "Coverage floor".
- `strategy.conc_thresh` → `conc` ↔ NumField (step 0.01) "Concentration".
- `strategy.max_sup_dc` → `maxSup` ↔ NumField (step 1) "Max suppliers/DC".
- Inputs are `tabular-nums`; values are raw strings until `Number(...)` at save (so a user can type
  "0.8" / "0.80" freely; `dirty` compares numerically).

**Layer-3 — interactions → endpoints.**
- `<select>` / NumFields → local state. **Save strategy** → `PUT /runs/{slug}/strategy`. On mount →
  `GET /runs/{slug}/strategy`. **Reachability:** Run Detail page, in the right rail, only when
  `has_cycle`.

**Deps.** `react` (`useCallback, useEffect, useState`), `@/lib/api` (`ApiError`, `getStrategy`,
`updateStrategy`, type `Strategy`), `@/components/ui` (`Button, Panel`).

---

# SIMPLIFICATIONS / DESIGN-VS-AS-BUILT (collected — the flags this slice must surface)

| # | Component | Designed (source) | As-built | Why it matters |
|---|---|---|---|---|
| S1 | **MappingProposal** + ImportSection flexible flow | **Editable column mapper** — per-column field dropdown, ambiguity assignment, override then confirm (DESIGN_REQUESTS.md §A3 / §M1) | **Read-only / confirm-only.** Mapping table is display-only; only **Confirm & import** or **Cancel** at the parent level. Ambiguities are listed, not resolvable. (DATA_AND_PROCESS_MAP.md: "confirm-only, NO editable override — G-seam"; "◐ partial — infer+confirm; no editable mapper") | A wrong/near-miss inference on a messy supplier file cannot be corrected in-app — Cancel, fix the source, re-upload. The propose+confirm half is real; the override half is unbuilt. |
| S2 | **ReviewSection** exception queue | **M5 — quarantine resolution / fix-and-retry surface** for quarantined rows (DESIGN_REQUESTS.md line 158) | **Surface-only.** Lists each non-scoreable/non-awardable line with reason/validity; **no edit/requeue/fix-and-retry**. | Satisfies "surface, never fudge" (every quarantined line is visible with why) but resolution requires correcting the source workbook and re-importing the round. |
| S3 | **StrategyPanel** | **Full A1** — scope read-back; 5 weights editable; exclusions/preferred suppliers; lenses to run; D43 pricing-basis (modality picker + cost-line manager) (DESIGN_REQUESTS.md §A1) | **Minimal A1.** Preset + 4 safeties editable; **5 weights READ-ONLY (whole-% display)**; no scope read-back, no exclusions/preferred, no lens picker, no pricing-basis/cost-line controls. (self-described "minimal A1"; page comment "engine strategy (minimal A1)") | Buyer can pick a preset profile and tune the four guardrails, but cannot hand-tune individual weights, exclude/prefer suppliers, choose lenses, or set award modality/cost-lines in-app. Wiring to get/updateStrategy is complete for what ships. |
| S4 | **KanbanBoard** | A board renderer for run progress | **Orphaned** — fully implemented but **no importer** anywhere in `frontend/**`. Diverging token family (`ink`/`line`/`surface`) vs the intake set. | Not a stub (complete renderer) but dead code in the current wiring; noted per the exhaustiveness bar (never a silent skip). |

**Minor binding inconsistency (not a design gap, noted for fidelity):** ImportSection renders the
ingested **count raw** (`{ingested}`, no `formatCount`), whereas ReviewSection formats counts via
`formatCount` (locale grouping). For small import counts this is invisible; for a 4-digit+ import the
two surfaces would group thousands differently. Flagged, not a contract violation.

**No stubs/placeholders found in the shipped paths** (S1–S3 are deliberate scope cuts of refinement
surfaces, documented in the design package as seam gaps / minimal slices; S4 is orphaned-but-complete).
All twelve files are real, wired (except the orphaned KanbanBoard), and bind to live endpoints.
