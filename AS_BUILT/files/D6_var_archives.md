---
doc: AS-BUILT AUDIT — SLICE D6 — /home/user/KR_RFP/var/** (archives, design uploads/snapshots, MCP run-vault)
id: ASBUILT-D6
status: COMPLETE. Read-only audit. Every one of the 323 files under var/ accounted for.
scope: /home/user/KR_RFP/var/**
census_xref: AS_BUILT/FILE_CENSUS.md rows 574–896 (323 rows; all 323 carry the `var/` prefix)
contract: /CLAUDE.md ABSOLUTE REQUIREMENTS honored; AUDIT_STANDARD.md exhaustiveness bar applied.
generated: 2026-06-22
---

# SLICE D6 — `var/**` exhaustive as-built audit

## 0. Scope, method, and headline classification

**Scope.** Everything under `/home/user/KR_RFP/var/` — 323 files total. Breakdown verified by
`find`:

| Sub-tree | Files | Nature |
|---|---:|---|
| `var/*.zip` (top level) | 2 | Packaged bundles (binary; zip) |
| `var/design_deliverable/**` | 19 | SNAPSHOT — the round-2 design deliverable, mirrors `project/design/handoff/` + `project/*.md` |
| `var/design_review/**` | 50 | SNAPSHOT — design-tool working dir, review iteration #1 (v2 baseline) |
| `var/design_review2/**` | 52 | SNAPSHOT — review iteration #2 (v2 baseline + 1 paste + 1 draft) |
| `var/design_review3/**` | 61 | SNAPSHOT — review iteration #3 (v3 = the FINAL baseline that became `design_deliverable/handoff`) |
| `var/vault/.git/**` | 113 | REAL artifact — the MCP harness run-vault's **own internal git repo** (separate VCS) |
| `var/vault/runs/**` | 26 | **REAL artifacts** — the two genuine MCP-harness live-run records (field-tomatoes + iceberg-lettuce) |
| **TOTAL** | **323** | |

(19 + 50 + 52 + 61 + 113 + 26 + 2 = 323. Matches `find var -type f | wc -l`.)

**Method.** `find var -type f` (323) → cross-checked against `FILE_CENSUS.md` (`grep -c "var/"` = 323,
exact match; var rows are census #574…#896). All text files (`.md`, `.txt`, `.json`, `.dc.html`
headers, `support.js` header) read end-to-end. Binaries / large generated trees (`.xlsx`, `.png`,
`.pdf`, `.svg`, `.webp`, `.zip`, git loose objects) → described + duplication proven by `md5sum`.
xlsx internal structure introspected via `python3 zipfile`.

**ONE headline classification fact governing this whole slice:**
> **The entire `var/` tree is GITIGNORED.** `.gitignore` line 62 = `var/` under the comment
> *"# generated/demo artifacts from local screenshot + seed runs (synthetic; never commit)"*.
> `git ls-files var` returns 0 files; `git status --short var/` is empty (fully ignored, not merely
> untracked). `git check-ignore var var/vault var/design_review var/design_deliverable` → all ignored
> (exit 0). The census itself notes these are untracked (its dates for var rows are filesystem mtime,
> not git author dates). **Nothing under var/ is in the committed repo.** This is correct and
> intentional per the no-file-storage posture (CLAUDE.md req #4) and the synthetic/demo nature of the
> contents. See §6 (keep-vs-gitignore) for the per-item recommendation — short version: **keep ignored.**

**Census format for these rows (verified, e.g. row 574):**
`| 574 | ./var/KR_RFP_design_package.zip | zip | 115882 |  | 2026-06-22 | 2026-06-22 | n |`
Columns = `# | path | ext | size | empty? | created | modified | tracked?`. The `tracked?` column is
**`n` for every var row** (confirming the gitignore). Empty cells in the `empty?` column = not-empty.

---

## 1. Top-level packaged bundles (`var/*.zip`) — 2 files

### 1.1 `var/KR_RFP_design_package.zip`
- **path · ext · empty?:** `var/KR_RFP_design_package.zip` · `zip` · not empty (115,882 B) · mtime 2026-06-22 04:29 · census #574.
- **WHAT:** A zip archive of a `design_deliverable/` tree — **24 entries** (verified `unzip -l`):
  `DATA_AND_PROCESS_MAP.md`, `PRE_TEST_READINESS.md`, `DESIGNER_PROMPT.md`, `DESIGN_REQUESTS.md`,
  `RECONCILIATION_SEAMS.md`, `SCREEN_COVERAGE_AUDIT.md`, `DESIGN_PACKAGE.md`, and the `handoff/`
  sub-tree (6 screen `.dc.html` + `Handoff.dc.html` + `support.js` + 4 Kroger SVGs +
  `HANDOFF_NOTES.md` + `DESIGN_FEEDBACK_v2.md`).
- **DETAILED WHY:** This is the **packaged, send-ready round-2 design deliverable** — the zip a human
  would download and hand to the external design team / use as the Claude-Design upload. It is a
  *superset* of the on-disk `var/design_deliverable/` directory (§2): the zip additionally contains
  **`PRE_TEST_READINESS.md` and `DESIGNER_PROMPT.md`** (which are NOT present in the on-disk
  `design_deliverable/` folder), and a **newer `DESIGN_PACKAGE.md` (9,942 B in zip vs 8,239 B on
  disk)**. So the zip is a *later, more complete* package than the loose `design_deliverable/` dir —
  the dir is an earlier export of the same deliverable. It exists because the build process packages
  the deliverable for hand-off; mtime 04:29 (latest of all var artifacts) confirms it was generated
  last.
- **CLASSIFY:** **SNAPSHOT / package** of the design deliverable (which itself mirrors `project/`
  canonical docs). Not a unique source of truth — its contents derive from `project/design/*` and
  `project/*.md`. Generated artifact.

### 1.2 `var/KR_RFP_review_bundle.zip`
- **path · ext · empty?:** `var/KR_RFP_review_bundle.zip` · `zip` · not empty (670,134 B) · mtime 2026-06-21 19:29 · census #575.
- **WHAT:** A zip of `KR_RFP_review_bundle/` — **20 entries** (verified): `README.txt`,
  `01_audit/{07_AS_BUILT_PROCESS_AUDIT.md (v1.19), DESIGN_BRIEF.md, 08_RELEASE_GOVERNANCE.md,
  04_PROGRAM_BACKLOG.md}`, `02_screens/{01-login … 07-run-intake-setup-only}.png` (7 screenshots),
  `03_output_files/{8 .xlsx}` (the tomato-run lifecycle outputs).
- **DETAILED WHY:** This is the **as-built REVIEW bundle** — the single package assembled (per its own
  `README.txt`, §4.1) for (a) the manual auditor to review the As-Built Spec against, and (b) the
  UX/UI design session to design *from*. Its `03_output_files/` are byte-identical copies of the
  field-tomatoes run outputs (proven §5), i.e. the bundle was assembled FROM the live tomato run.
  It is the upstream source that was unzipped into `var/design_review*/uploads/KR_RFP_review_bundle/`
  (§3). 670 KB (largest var item besides the run-vault) because it carries the 7 PNG screenshots +
  8 xlsx.
- **CLASSIFY:** **SNAPSHOT / package.** Its md docs are *older snapshots* of the canonical
  `project/*.md` (the README labels the audit "v1.19"; canonical `project/07_AS_BUILT_PROCESS_AUDIT.md`
  is a later version). Its xlsx are duplicates of the field-tomatoes run outputs. Generated artifact.

---

## 2. `var/design_deliverable/**` — 19 files — SNAPSHOT of the round-2 design deliverable

This directory is the **loose (unzipped) round-2 design deliverable**. Verified by `md5sum`: its
`handoff/*` files are **byte-identical** to the canonical `project/design/handoff/*`, and its top-level
md files mirror canonical `project/` / `project/design/` copies (some are the same checksum, some are
slightly-older on-disk variants — detailed per file). **It mirrors a canonical doc; it is not itself a
source of truth.**

### 2.1 Top-level design docs (5 md files)

| File | ext | empty? | size | census | mirrors which canonical | md5 vs canonical |
|---|---|---|---:|---:|---|---|
| `DATA_AND_PROCESS_MAP.md` | md | n | 24,181 | #576 | `project/DATA_AND_PROCESS_MAP.md` | **IDENTICAL** (9c9139e9…) |
| `DESIGN_PACKAGE.md` | md | n | 8,239 | #577 | `project/design/DESIGN_PACKAGE.md` | DIFFERS (var=ed080eb1 vs project/design=08b531db) — var is an **older** export (canonical is newer; the zip §1.1 has a still-newer 9,942 B copy) |
| `DESIGN_REQUESTS.md` | md | n | 11,783 | #578 | `project/design/DESIGN_REQUESTS.md` | DIFFERS (var=da3af847 vs 3312e491) — var is an older export |
| `RECONCILIATION_SEAMS.md` | md | n | 5,601 | #579 | `project/RECONCILIATION_SEAMS.md` | DIFFERS (var=0fe1d4fc vs project=ae14e3d6) — var is an older export (canonical 6,600 B in zip) |
| `SCREEN_COVERAGE_AUDIT.md` | md | n | 6,314 | #580 | `project/design/SCREEN_COVERAGE_AUDIT.md` | **IDENTICAL** (d005705a…) |

**WHAT / WHY (read end-to-end; content summarized — these are SNAPSHOTS, the canonical originals are
audited in the `project/` slices):**
- **`DATA_AND_PROCESS_MAP.md` (PM-MAP).** The companion "middle-steps" map: a mermaid ERD (Diagram 1,
  spine + 6 `((SEAM))` reconciliation nodes) and a mermaid process flowchart (Diagram 2, system steps /
  USER-DECISION diamonds / seam hexagons / gap dashed-nodes), plus enumerated DECISION points (D1–D8,
  five wired/three gaps), ACCESS points (6 screens → endpoints), the seam register, the gap register,
  and 6 "relationships I was unsure of" notes (eng.* FKs logical-not-enforced; awd→eng selection edge;
  capacity↔submission cardinality; pilot.run↔cyc.cycle text-not-FK; eng/awd naming collision baseline
  vs live; finalize/CLOSED semantics). **WHY it exists:** the lifecycle ends are documented but the
  *middle* (where data is reconciled across grains/systems) is not — this surfaces the human-assertion
  points, the access points, and the seams so the design team can design the midpoints. Explicitly a
  **DERIVED VIEW, not a source of truth** (its own header: "the database and 07 win").
- **`DESIGN_PACKAGE.md` (PM-007-DR-PKG).** The cover of the design package. Spine: (1) treat data like
  data — every control is a DATA operation (view/live-edit/version-switch/governed classification); (2)
  full-screen gaps (A1 Cycle Setup … A7 supplier mgmt); (3) design the midpoints (M1–M6). Verdict: the
  v2 handoff is the **LOCKED UI baseline — extend, don't redesign.** Lists the 3 corrections, the new
  screens, the visuals to produce, the recommended order, and the bundle manifest. **WHY:** the single
  entry-point doc the design team reads first.
- **`DESIGN_REQUESTS.md` (PM-007-DR-REQ).** Designer-ready briefs: §A missing SCREENS (A1 Cycle
  Setup/Strategy, A2 Finalize/Close-out [backend built], A3 editable column mapper, A4 supplier comms
  E-37 [parked], A5 sign-off G-D, A6 settings/admin G-C/G-J, A7 supplier mgmt E-34); §B visuals (the 3
  tweaks, non-happy-path states, visualizations B3, iconography B4, **B5 interaction-correctness rules**
  = "totals/% follow the filter, never a stale full-table number"); §C the 6 midpoints M1–M6.
- **`RECONCILIATION_SEAMS.md` (PM-SEAMS).** The standing watch-list of mapping seams between grains
  (lot↔item↔SKU↔period) and systems (RFP↔iTrade↔KCMS↔supplier master): a status table (◐/⬜/✅ per seam),
  newly-surfaced gaps (editable mapper, unit/pack), the planned known-template deterministic-parser
  adapter, and the standing rule (add a seam before building across a boundary). The two headline OPEN
  seams: **lot/item→iTrade SKU (1→many, blocks real STLY)** and **unit/pack normalization (unmodeled)**.
- **`SCREEN_COVERAGE_AUDIT.md` (PM-007-DR-AUDIT).** Delivered-vs-needed table: 6 shipped screens +
  Handoff page (✅ strong core happy path) against the full lifecycle; tiered gaps (Tier-1 cycle setup /
  comms / editable mapper; Tier-2 sign-off / admin / supplier mgmt; Tier-3 analytics/contract). The
  source the §A requests derive from.

### 2.2 `var/design_deliverable/handoff/**` (14 files) — byte-identical to `project/design/handoff/`

All 10 named files below verified **SAME** md5 as `project/design/handoff/*`:

| File | ext | empty? | size | census | WHAT / WHY |
|---|---|---|---:|---:|---|
| `Alignment Workspace.dc.html` | html | n | 100,303 | #581 | The centerpiece screen prototype (7 lenses A–G, engine rec, capacity feasibility, freeze modal, version picker, diligence tabs). `.dc.html` = a self-contained "Design Canvas" prototype (DOCTYPE html + inline styles + a `support.js` runtime). Visual source of truth to rebuild in Next.js+Tailwind, **not merged**. |
| `Awards.dc.html` | html | n | 36,956 | #582 | Awards screen prototype (frozen v0, append-only adjustment layers, version history, RecordAdjustmentModal). `CELLS()` defines `demand:5200` on all 4 cells (the "stale screenshot error" is export-lag, not a live defect — per DESIGN_FEEDBACK_v2 §2). |
| `Bid Intake.dc.html` | html | n | 28,753 | #583 | Bid-intake prototype (kickoff upload → template → load bids; strict/flexible; exception queue). |
| `DESIGN_FEEDBACK_v2.md` | md | n | 2,796 | #584 | **Round-2 auditor feedback** on the v2 handoff: 3 items only — (1) compact-width status-strip truncation fix [Live/Sealed v1/Not frozen/Current], (2) Awards "runtime error" = VERIFIED STALE SCREENSHOT (no code fix), (3) "Hash-chain current" drill-through to the latest audit event. Verdict: **this is the LOCKED UI baseline.** |
| `Dashboard.dc.html` | html | n | 15,184 | #585 | Runs-portfolio prototype (list + "New run"). |
| `HANDOFF_NOTES.md` | md | n | 3,472 | #586 | The v2 handoff cover (PM-007-DR2 v2.0): point dev at `Handoff.dc.html` first; the "all prior feedback incorporated" table; the **one fidelity note** — finalize writes a `CLOSED` audit event but `EventType` enum has no `CLOSED` (add it or map to SIGNED_OFF/SENT); build classification (B restyle / C new modules). |
| `Handoff.dc.html` | html | n | 32,983 | #587 | The **design-system + developer-handoff page**: color tokens for Tailwind `theme.extend`, typography (Montserrat + Nunito, tabular-nums), 4px grid, component inventory with states (AssertModal, DataTable), non-happy-path states, real field reference, a11y/Lucide. The first thing the dev reads. |
| `Login.dc.html` | html | n | 7,849 | #588 | Login prototype (username → TOTP 2FA → httpOnly session). |
| `Run Detail.dc.html` | html | n | 21,565 | #589 | Run-overview prototype (lifecycle stepper, activity kanban, audit trail, run facts, file list + zip). |
| `support.js` | js | n | 53,975 | #594 | The `.dc.html` runtime — header: `// GENERATED from dc-runtime/src/*.ts — do not edit. Rebuild with cd dc-runtime && bun run build`. A bundled "use strict" IIFE that powers the prototypes; viewing `file://` directly can blank it (must serve locally). **Generated/vendored** (not hand-written here). |

`var/design_deliverable/handoff/assets/` (4 Kroger brand SVGs — census #590–593):

| File | ext | size | census | WHAT/WHY |
|---|---|---:|---:|---|
| `kroger-k-blue.svg` | svg | 1,323 | #590 | Kroger "K" mark, blue. Brand asset for the prototypes. |
| `kroger-k-white.svg` | svg | 1,323 | #591 | Kroger "K" mark, white (dark-bg variant). |
| `kroger-wordmark-blue.svg` | svg | 3,803 | #592 | Kroger wordmark, blue. |
| `kroger-wordmark-white.svg` | svg | 3,803 | #593 | Kroger wordmark, white. |

**CLASSIFY (all of §2):** **SNAPSHOT.** `handoff/*` mirrors canonical `project/design/handoff/*`
byte-for-byte; the 5 top-level md mirror canonical `project/` / `project/design/` copies (2 identical,
3 older on-disk exports). The canonical originals are audited in the `project/` slices. Generated/copied.

---

## 3. `var/design_review/`, `var/design_review2/`, `var/design_review3/` — 50 + 52 + 61 = 163 files — SNAPSHOT

These three are **the design-tool (Claude Design / "Design Canvas") working directories** for three
review iterations. Each contains: the 6–7 screen `.dc.html` at root, a `support.js` runtime, an
`assets/` Kroger-SVG dir, a `.thumbnail` (a **WebP image** — `file` reports `RIFF … Web/P`, the
canvas preview thumbnail, listed in census as ext `(dotfile)`), a `screenshots/` dir, and an
`uploads/` dir holding the **unzipped `KR_RFP_review_bundle/`** (= the §1.2 zip contents) plus loose
upload assets (Kroger logo SVGs, the Kroger Brand Guidelines PDF, pasted screenshots).

**Lineage proven by md5 (the key structural fact):**
- `design_review` (iter 1) and `design_review2` (iter 2) carry the **v2 baseline** `.dc.html` (e.g.
  `Alignment Workspace.dc.html` = 93,575 B). `diff -rq design_review design_review2` shows they differ
  only by: the `.thumbnail`, plus `design_review2` ADDS `drafts/Alignment Workspace - draft 1.dc.html`
  (93,575 B — a working draft) and `uploads/pasted-1782077933482-0.png`. So **review2 ≈ review1 + one
  draft + one pasted image.**
- `design_review3` (iter 3) carries the **v3 / FINAL baseline** `.dc.html` (`Alignment Workspace.dc.html`
  = 100,303 B, adds `Handoff.dc.html`). **Verified `md5sum` SAME for all 7 `.dc.html`:
  `design_review3/*` == `design_deliverable/handoff/*` == `project/design/handoff/*`.** I.e.
  **design_review3 is the iteration that produced the locked baseline** now in design_deliverable.
- The `uploads/KR_RFP_review_bundle/**` under all three is the **same unzipped review bundle** (§1.2):
  4 audit md (07 v1.19 / DESIGN_BRIEF / 08 governance / 04 backlog), 7 screen PNGs, 8 output xlsx,
  `README.txt`. These audit md are **OLDER SNAPSHOTS** of canonical `project/*.md` (`diff -q` confirms
  `04_PROGRAM_BACKLOG.md` and `07_AS_BUILT_PROCESS_AUDIT.md` differ from the canonical `project/`
  copies; identical copies of these bundle files also live at `project/design/redesign3/uploads/…`).

### 3.1 Per-directory file inventory

**`var/design_review/` (50 files) — census #595–644:**
- Root: `.thumbnail` (WebP, 8,578 B, #595), 6 `.dc.html` (Alignment 93,575 / Awards 25,291 / Bid Intake
  23,130 / Dashboard 15,184 / Login 7,849 / Run Detail 19,576 — #596–601), `support.js` (53,975 B,
  identical to deliverable's — #621 area).
- `assets/`: 4 Kroger SVGs (k-blue/k-white/wordmark-blue/wordmark-white, #602–605).
- `screenshots/` (10 PNGs, #606–615): `01-top2.png`=`02-top2.png` (md5 bcbcf554, identical pair);
  `drill.png`=`drill2.png`=`drill3.png` (md5 bba256c8, three identical copies); `body / explain / full /
  nav / wide`. **WHY duplicates:** the design tool exports numbered/retry frames of the same canvas
  state, so byte-identical "drill2/drill3" and "01/02-top2" recur. These are the in-canvas render
  snapshots (distinct from the uploaded `02_screens/` app screenshots).
- `support.js` (#…), `.thumbnail`.
- `uploads/`: 4 Kroger logo SVGs (`KR.svg` 1,308 / `KR.D.svg` 1,369 / `KR_BIG.svg` 3,788 /
  `KR_BIG.D.svg` 3,788), `Kroger Brand Guidelines_4-8-25.pdf` (**16,738,537 B** — the single largest
  file in var/; the official Kroger brand PDF, an upload reference), three macOS screenshots
  (`Screenshot 2026-06-21 at 4.36.46/5.13.02/5.18.50 PM.png`), and the full unzipped
  `KR_RFP_review_bundle/` (4 audit md + 7 screen PNGs + 8 xlsx + README.txt).

**`var/design_review2/` (52 files) — census #645–696:** identical structure to `design_review` PLUS
`drafts/Alignment Workspace - draft 1.dc.html` (93,575 B — a saved working draft of the alignment screen)
and `uploads/pasted-1782077933482-0.png` (335,614 B — a pasted reference image). Same `.dc.html` v2
baseline, same screenshots set, same unzipped bundle, same brand PDF.

**`var/design_review3/` (61 files) — census #697–757:** the FINAL iteration.
- Root: `.thumbnail` (WebP 5,930 B), **7** `.dc.html` (adds `Handoff.dc.html` 32,983 B; Alignment now
  100,303 / Awards 36,956 / Bid Intake 28,753 / Run Detail 21,565 — the v3 sizes, **md5-identical to
  design_deliverable/handoff**), `support.js`.
- `drafts/Alignment Workspace - draft 1.dc.html` (93,575 — the prior-version draft retained).
- `screenshots/` (17 PNGs): the same `body/drill*/explain/full/nav/wide/01-02-top2` set PLUS the v3
  additions `01-adj.png`=`02-adj.png`=`03-adj.png` (md5 3bb6e858, three identical — the post-award
  adjustment frames), `exq.png` (exception queue), `finalize.png`, `freeze2.png`, `freeze-fixed.png`.
  **WHY:** iteration 3 added the finalize/freeze/adjustment/exception-queue states, so its screenshot
  set is larger.
- `assets/` (4 Kroger SVGs), `uploads/` (4 KR logo SVGs + brand PDF + 3 macOS screenshots +
  `pasted-1782077933482-0.png` + an additional `pasted-1782080027937-0.png` [1,364,100 B] + the full
  unzipped `KR_RFP_review_bundle/`).

### 3.2 The uploaded review-bundle docs (snapshot detail — applies to all 3 dirs' `uploads/KR_RFP_review_bundle/`)
- `01_audit/07_AS_BUILT_PROCESS_AUDIT.md` (61,800 B) — the **As-Built Spec v1.19** (per README). **OLDER
  SNAPSHOT** of canonical `project/07_AS_BUILT_PROCESS_AUDIT.md` (86,058 B, later version) — `diff` confirms differ.
- `01_audit/04_PROGRAM_BACKLOG.md` (18,984 B) — **OLDER SNAPSHOT** of `project/04_PROGRAM_BACKLOG.md`
  (43,116 B) — differs.
- `01_audit/08_RELEASE_GOVERNANCE.md` (9,912 B) — snapshot of `project/08_RELEASE_GOVERNANCE.md`.
- `01_audit/DESIGN_BRIEF.md` (3,700 B) — read in full: the one-page external-design-session orientation
  (form factor, Next.js+React18+TS+Tailwind / FastAPI stack, Vercel host, the 6 screens today, the
  single biggest design question = gap **G-I** "the ~18-tab Excel alignment workbench must come onto the
  screen", the net-new surfaces, the design constraints). Mirrors `project/DESIGN_BRIEF.md` /
  `project/design/redesign3/uploads/…/DESIGN_BRIEF.md`.
- `02_screens/*.png` (7) — app screenshots on seeded tomato demo data (login / runs-list / run-detail /
  run-intake / run-alignment / run-awards / run-intake-setup-only). Synthetic; safe to share (README).
- `03_output_files/*.xlsx` (8) — the tomato-run output lifecycle (see §5; byte-identical to the run-vault).
- `README.txt` (1,546 B) — read in full (§1.2): the bundle's purpose, contents, data note ("all SYNTHETIC
  demo data, a tomato sample run, safe to share"), and review sequence.

**CLASSIFY (all of §3, 163 files):** **SNAPSHOT / design-tool working directories.** review3's
`.dc.html` are the canonical locked baseline (duplicated into design_deliverable and project/design/
handoff); review1/2 are earlier (v2) iterations; all uploaded bundle docs are *older* snapshots of the
canonical `project/*.md`; all xlsx are duplicates of the field-tomatoes run. **No unique source of truth
here** — every file mirrors a canonical doc, the review bundle, or the live run. Generated/uploaded.

---

## 4. `var/vault/.git/**` — 113 files — REAL artifact (the run-vault's OWN internal git repo)

- **WHAT:** A complete, standard git repository **internal to the MCP harness run-vault** — i.e.
  `var/vault/` is itself a git working tree with its own `.git/`, **separate from the main KR_RFP
  repo** (and ignored by it via `var/`). Contains the usual git plumbing:
  - `HEAD` (23 B → `ref: refs/heads/master`), `config` (148 B), `description`, `COMMIT_EDITMSG` (67 B),
    `index` (3,708 B), `info/exclude` (240 B), `refs/heads/master` (41 B → the tip SHA),
    `logs/HEAD` + `logs/refs/heads/master` (2,271 B each — the reflog), 15 `hooks/*.sample` (the stock
    git sample hooks, vendored), and **90 loose objects** under `objects/xx/…` (blobs/trees/commits;
    sizes 15 B–40,344 B; the 40,344 B object is the packed alignment-workbench xlsx blob).
- **DETAILED WHY:** The MCP harness keeps each run-vault under version control so that **every governed
  step in a run is a git commit** — making the vault an auditable, append-only run record (mirrors the
  hash-chained DB audit log). `git --git-dir=var/vault/.git log` shows the real commit history on
  branch `master`, one commit per lifecycle step:
  ```
  3320be6 [iceberg-lettuce] setup/kickoff workbook generated
  07a0450 run iceberg-lettuce created
  4bdfd76 [field-tomatoes] memory file added: buyer_note.txt
  92cc983 [field-tomatoes] post-award adjustment v1 recorded
  d6cab9a [field-tomatoes] award AWD-2026-TOMATO-1 frozen → booking guides
  8123037 [field-tomatoes] round 1 alignment analysis v1 sealed
  4033339 [field-tomatoes] round 1 bids ingested → 8 bid line(s)
  cd24b1c [field-tomatoes] round 1 bid template generated
  e1216d0 [field-tomatoes] setup ingested → cycle created
  c93f10c [field-tomatoes] setup/kickoff workbook generated
  8b9fb03 run field-tomatoes created
  ```
  `git ls-tree -r HEAD` confirms the tracked working-tree files = exactly the 26 `runs/**` files in §5.
  **This is the harness's verification-oracle file vault retained on disk** (CLAUDE.md: the MCP harness
  is the live-run oracle; the no-file-storage rule applies to the *running app*, not the harness vault).
- **CLASSIFY:** **REAL artifact** (the run-vault VCS) but **vendored/generated git internals** — per the
  AUDIT_STANDARD, `.git` trees are *counted, not per-file audited*. All 113 files are accounted for here
  as one counted block with the reason: standard git plumbing (1 HEAD, 1 config, 1 description, 1
  COMMIT_EDITMSG, 1 index, 1 info/exclude, 2 logs, 15 stock sample hooks, 1 master ref, **90 loose
  objects**). No per-object audit (machine-generated content-addressed blobs).

---

## 5. `var/vault/runs/**` — 26 files — **REAL artifacts** (the two genuine MCP-harness live runs)

These are **the genuine run records** the task flagged: the field-tomatoes (a complete end-to-end run)
and iceberg-lettuce (a freshly-created, setup-only run) MCP-harness runs. Each is a per-run folder with
`RUN.md`/`NOTES.md`/`FEEDBACK.md` markers, `cycle_id.txt`, `run_data.json`, and `inputs/ outputs/
memory/` (each seeded with a `.gitkeep`). **These are NOT snapshots — they are the actual artifacts the
harness produced, retained under the §4 git history.** All text files read end-to-end below.

### 5.1 `field-tomatoes-20260621-a3d618/` (18 files, census #862–879) — a COMPLETE run

The full lifecycle: run created → setup ingested → cycle created → template generated → R1 bids ingested
(8 lines) → R1 alignment sealed (v1) → award AWD-2026-TOMATO-1 frozen (Scenario B) → post-award
adjustment v1 → buyer memory note.

| File | ext | empty? | size | census | WHAT it shows (REAL run record) |
|---|---|---|---:|---:|---|
| `RUN.md` | md | n | 622 | #862 | The buyer-facing status board (Done/Doing/Next/Waiting-on-you). Records: cycle `30bc179d-…`, "2 lots, 2 DCs, 2 suppliers, 1 timeframes", "Bids loaded for 1 of 2 round(s)", "1 alignment version sealed", "Award frozen", "Post-award adjustment v1 recorded". Next: record further reprices; Waiting: upload next round's bids. |
| `NOTES.md` | md | n | 263 | #863 | "Spring 2026 Tomatoes" running notes: `2026-06-21: run created` + `Buyer ask captured (file: buyer_note.txt)`. |
| `FEEDBACK.md` | md | n | 1,203 | #864 | **Development feedback generated from the sealed records** (the platform-team signal doc): Cycle = 2 DCs/2 lots/2 suppliers/2 rounds; **no-bid lots 0 of 4**; **thin competition (<3 bidders): 4 (DC×lot)**; gate flags raised R1 — "Low bidder count (<3): 8", "Price premium exceeds threshold: 4"; cap-breach cells 0; all bids on the owned template; 1 sealed alignment, 1 award frozen, 1 post-award version. |
| `cycle_id.txt` | txt | n | 36 | #871 | The governed cycle UUID: `30bc179d-2bd2-439b-a259-a9e6b664fd7a`. Links the file-vault run to the DB cycle. |
| `run_data.json` | json | n | 2,398 | #877 | **The structured run export** (`exported_at 2026-06-21T18:53:30Z`). Cycle "Spring 2026 Tomatoes Cycle" (commodity_id `385518f8-…`); scope = DCs [Atlanta, Dallas], lots [Lot 1 Grape, Lot 2 Roma], TF [Spring 2026], suppliers [Green Valley Farms, Sunbelt Produce], rounds [Round 1, Round 2 — Final]; `bid_lines_by_round` = 8 in R1; 1 analysis version (round 1, engine `v3-cleanroom`, sealed 18:53:30); award `AWD-2026-TOMATO-1` scenario **B**, 4 award lines (each volume_share 1.000000, frozen_price 10.500000 across Atlanta/Dallas × Grape/Roma), 2 award versions: v0 FROZEN (4 cells, 2026-06-21, by pilot) + v1 MARKET_HIKE (1 cell, 2026-07-01, "Spring freight surcharge on the first awarded cell", by pilot). |
| `inputs/.gitkeep` | (none) | **y (0 B)** | 0 | #865 | **EMPTY by design** — keeps the empty `inputs/` dir under git (git won't track empty dirs). Placeholder. |
| `inputs/01_setup_kickoff.xlsx` | xlsx | n | 15,820 | #866 | The setup/kickoff workbook the buyer filled (10 tabs: Cycle, DCs, Lots and Items, Suppliers, Volumes, Incumbents, Timeframes, Premiums, Scenario rules, Safeties). **md5-identical** to the review-bundle copy. |
| `inputs/02_round1_bid_template.xlsx` | xlsx | n | 9,830 | #867 | The generated R1 bid template (key-stamped owned template; 3 sheets incl. Capacity). md5-identical to bundle copy. |
| `memory/.gitkeep` | (none) | **y (0 B)** | 0 | #868 | EMPTY by design — keeps `memory/` under git. |
| `memory/buyer_note.txt` | txt | n | 26 | #870 | The captured buyer ask: **"Prioritize Dallas coverage"**. The run's persisted memory/instruction. |
| `outputs/.gitkeep` | (none) | **y (0 B)** | 0 | #872 | EMPTY by design — keeps `outputs/` under git. |
| `outputs/04_round1_alignment_v1.xlsx` | xlsx | n | 42,586 | #873 | **The ~17-tab ALIGNMENT WORKBENCH** (the gap-G-I centerpiece). Verified 17 sheets: Summary, Controls, Award Summary, Scenario Comparison, Lowest-Cost Check, Supplier Comparison, Landed & Hidden Costs, Share & Relationships, Incumbent Retention, Negotiation Dynamics, Coverage, Detailed Scoring, Data Quality, _Prices, Custom Scenario, Custom Dashboard, Data (pivot me). md5-identical to bundle copy. |
| `outputs/08_award_booking_guide.xlsx` | xlsx | n | 6,407 | #874 | The internal booking guide (1 sheet "Internal Booking Guide"). Inline header: "INTERNAL BOOKING GUIDE — Spring 2026 Tomatoes Cycle / Awarded from Scenario B / LIVE CYCLE DATA — real names & prices / DECISION-SUPPORT". Columns DC·Lot·Item·Timeframe·Awarded Supplier·Volume Share·FOB $/case·Landed $/case·Awarded Period Cases·Line Spend·Routing Baseline·Savings·Key ref. Rows = the 4 awarded cells (Atlanta/Dallas × Grape→Green Valley / Roma→Sunbelt). md5-identical to bundle. |
| `outputs/08_award_guide_awd_2026_tomato_1_green_valley_farms_4ab5e3_f4e89bfb_…20.xlsx` | xlsx | n | 5,957 | #875 | Per-supplier award guide for **Green Valley Farms** (award AWD-2026-TOMATO-1). md5-identical to bundle. |
| `outputs/08_award_guide_awd_2026_tomato_1_sunbelt_produce_c901c4_f4e89bfb_…20.xlsx` | xlsx | n | 5,948 | #876 | Per-supplier award guide for **Sunbelt Produce**. md5-identical to bundle. |
| `outputs/08_award_supplier_guides.xlsx` | xlsx | n | 7,206 | #… | The combined supplier-guides workbook. md5-identical to bundle. |
| `outputs/09_post_award_v1.xlsx` | xlsx | n | 7,992 | #879 | The post-award adjustment workbook (3 sheets: Versions, Current Effective Prices, This Version's Changes) — reflects the v1 MARKET_HIKE. md5-identical to bundle. |

### 5.2 `iceberg-lettuce-20260621-398777/` (8 files, census #880–887) — a SETUP-ONLY run

A freshly-created run that has only reached "setup/kickoff workbook generated" (no cycle yet). It is the
genuine record of an *incomplete* run — equally a real artifact, and notable because it shows the
**empty-state branch** of every marker file.

| File | ext | empty? | size | census | WHAT it shows |
|---|---|---|---:|---:|---|
| `RUN.md` | md | n | 356 | #880 | "Iceberg Lettuce" status board: **Cycle: not created yet**; Done = run folder + Setup workbook generated; Doing/Next = "_(nothing here)_"; Waiting-on-you = "Fill in the Setup/Kickoff workbook and upload it". The pre-cycle empty-state of RUN.md. |
| `NOTES.md` | md | n | 194 | #881 | "Summer 2026 Lettuce": only `2026-06-21: run created`. |
| `FEEDBACK.md` | md | n | 198 | #882 | The **empty-state of FEEDBACK.md**: "_No run yet. This file fills in once the first alignment runs…_". (Contrast the rich tomato FEEDBACK.) |
| `cycle_id.txt` | txt | **y (0 B)** | 0 | #886 | **EMPTY by design** — no cycle created yet, so the cycle id is blank (vs the tomato run's populated UUID). A genuine empty-state, not an error. |
| `run_data.json` | json | n | 81 | #883 | The pre-cycle export: `{"status": "no cycle yet — run setup ingest to create the governed cycle"}`. The empty-state of run_data.json. |
| `inputs/.gitkeep` | (none) | **y (0 B)** | 0 | #884 | EMPTY by design — keeps `inputs/` under git. |
| `inputs/01_setup_kickoff.xlsx` | xlsx | n | 16,110 | #885 | The lettuce setup/kickoff workbook (16,110 B; **md5 differs from the tomato kickoff** — a distinct commodity's workbook, confirming these are not copied: iceberg=5c1dc7c1…, tomato=865f013d…). |
| `memory/.gitkeep` | (none) | **y (0 B)** | 0 | #887 | EMPTY by design — keeps `memory/` under git. |
| `outputs/.gitkeep` | (none) | **y (0 B)** | 0 | #… | EMPTY by design — keeps `outputs/` under git (no outputs produced yet). |

**Empty-file accounting (per AUDIT_STANDARD rule: empty files explained, not skipped).** 7 empty
non-`.git` files exist under var/, ALL in the run-vault and ALL intentional:
`field-tomatoes/{inputs,memory,outputs}/.gitkeep` (3), `iceberg-lettuce/{inputs,memory,outputs}/.gitkeep`
(3), and `iceberg-lettuce/cycle_id.txt` (1). The six `.gitkeep` are zero-byte by convention (force git to
track otherwise-empty dirs); the empty `cycle_id.txt` is the genuine no-cycle-yet state. None is an error.

**CLASSIFY (all of §5, 26 files):** **REAL artifacts.** The field-tomatoes run is a complete, verifiable
end-to-end harness run record (its outputs are the *source* the review bundle and design uploads copied
FROM — proven by the md5 SAME results in §1.2/§3/§5); the iceberg-lettuce run is a genuine setup-only
run exercising the empty-state path. These are the harness's run-vault records the task asked to
document, not snapshots of any canonical doc.

---

## 6. Keep-vs-gitignore flags (every var item)

**Current state: the entire `var/` tree is gitignored (`.gitignore:62 = var/`). Recommendation: KEEP it
gitignored — this is correct.** Per-group rationale:

| Group | Keep ignored? | Why |
|---|:--:|---|
| `var/*.zip` (2 packaged bundles) | **YES — stay ignored** | Generated/packaged deliverables; large (670 KB review bundle); reproducible by re-packaging from `project/`. Committing them would duplicate canonical docs as opaque blobs. |
| `var/design_deliverable/**` | **YES — stay ignored** | Byte-for-byte mirror of canonical `project/design/handoff/*` + `project/*.md`. The canonical copies ARE committed; this is a redundant export. |
| `var/design_review{,2,3}/**` | **YES — stay ignored** | Design-tool working dirs / re-uploaded snapshots; includes a **16.7 MB Kroger Brand Guidelines PDF ×3** (50 MB total just in that PDF), large pasted PNGs, duplicate screenshots, and OLDER snapshots of canonical docs. Definitely do not commit. |
| `var/vault/.git/**` | **YES — stay ignored** | A nested git repo. Committing a `.git/` into the parent repo is never correct (would be a submodule-shaped accident). |
| `var/vault/runs/**` | **YES — stay ignored, but it IS the real run record** | These are genuine live-run artifacts (real supplier names/prices in the tomato run, e.g. Green Valley Farms @ 10.50). Two reasons to keep ignored: (a) CLAUDE.md req #4 — the DB is the source of truth, no server-side file storage; the vault is the harness's own retained oracle, versioned by its OWN git (§4), not the repo's. (b) clean-room / data-fidelity posture — real run data is kept out of the committed repo (the synthetic demo copies live elsewhere). **Flag:** these are the only var files that are *unique real data*; they are correctly preserved under the run-vault's internal git, so "ignored by the main repo" does not mean "unsaved." |

**No file under var/ should be moved INTO the committed tree.** The one thing to be aware of (not a fix,
a note): the var/ copies of design docs are **stale snapshots** of the canonical `project/` docs (07 is
"v1.19" here vs the later canonical; backlog/seams/package on-disk copies are older than canonical). If
anyone reads from `var/` they would get an out-of-date doc — but since `var/` is ignored and labeled
"generated/demo," that is acceptable; the canonical source remains `project/`.

---

## 7. Cross-check & completeness statement

- **Census reconciliation:** `find var -type f` = **323**; `grep -c "var/" FILE_CENSUS.md` = **323**;
  per-group sum 19+50+52+61+113+26+2 = **323**. Exact 1:1 match — **no var file missing from the census,
  no census var row without a file.**
- **`tracked?` column** = `n` for all 323 var rows; `git ls-files var` = 0; `git status --short var/`
  empty → confirms full gitignore. Census var-row dates are filesystem mtime (its header says so).
- **Every text file read end-to-end:** all 5 design_deliverable md, both HANDOFF_NOTES/DESIGN_FEEDBACK,
  DESIGN_BRIEF, README.txt, all run-vault RUN/NOTES/FEEDBACK/run_data.json/cycle_id.txt/buyer_note.txt;
  `.dc.html`/`support.js`/`.thumbnail`/SVG/PDF/PNG/xlsx/zip/git-objects described as binaries/generated
  with duplication proven by md5/unzip/zipfile introspection.
- **Empty files (7, non-.git):** all enumerated and explained (6 `.gitkeep` + 1 `iceberg cycle_id.txt`).
- **Duplication map proven (md5):** design_deliverable/handoff == project/design/handoff (10/10 SAME);
  design_review3 .dc.html == design_deliverable/handoff (7/7 SAME); run-vault inputs/outputs xlsx ==
  review-bundle 03_output_files (6/6 SAME); iceberg vs tomato kickoff DIFFER (distinct commodities);
  within-dir screenshot dups (drill=drill2=drill3; 01-top2=02-top2; 01/02/03-adj) confirmed.

**GAPS / unverifiable:** none material. Two notes for the record: (1) I did not byte-diff the OLDER
`var/` md snapshots line-by-line against canonical — I confirmed they DIFFER (md5) and identified them
as older versions via README version labels + file sizes; a line-level diff was unnecessary to classify
them as snapshots. (2) xlsx cell-value fidelity (e.g. that the alignment workbench numbers reconcile to
golden) is out of D6 scope — it belongs to the engine/data-flow slices; here I documented structure (tab
lists, header rows) and proved byte-identity to the committed-elsewhere demo copies.
