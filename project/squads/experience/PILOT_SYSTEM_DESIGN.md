---
doc: Pilot System Design — run real RFPs with Claude, in parallel, version-controlled
id: EXP-PILOT-SYSTEM
squad: Experience / Output + Platform
status: Draft (master design; consolidates the sponsor's pilot requirements 2026-06-19)
created: 2026-06-19
relates: PILOT_INPUT_DOCS_SPEC.md (the fill-out docs), D19/D20/D21/D23/D24/D25/D28, ADR-0006,
         ADR-0014 (post-award freeze-and-layer), the scenario-workbook generator (app.output)
scope: The interactive pilot — a Claude Code SKILL + an MCP SERVER that run a real produce RFP cycle
       end to end, in parallel with the manual process, with versioning + history + multi-RFP.
---

# Pilot System Design

Run a **real RFP cycle with Claude, alongside the manual process** — Claude generates every fill-out
document, ingests what comes back (even messy files), runs the engine, produces a **versioned
analysis file after every round**, keeps the **history**, handles **versioned post-award
adjustments**, speaks the **buyer's language**, **nudges** you for next steps on a schedule, shows a
**proactive kanban** of where things stand, and runs **many RFPs at once** — each in its **own
git-versioned run folder**.

## 1. The three repositories

| Repo | Owner | Holds |
|---|---|---|
| **KR_RFP** (this) | platform | The engine, the governed Postgres schema, the document generators (`app.output`), the **pilot service** (`app.pilot`), the **MCP server** source, and the **skill** |
| **MCP repo** (sponsor creates on GitHub) | sponsor | A thin deployable copy/submodule of the MCP server so Claude Code can register it (`.mcp.json`) — points at the platform + the run vault |
| **Run Vault** (sponsor creates on GitHub) | sponsor | The **main single repository** the routine runs in. One **sub-folder ("run") per RFP**, git-versioned: the fill-out inputs, the filled files, and every generated/versioned output + a status manifest |

The platform's **Postgres** is the governed system of record (cycle, bids, sealed analysis runs,
awards, adjustments). The **Run Vault** is the **file/document** record (the actual workbooks the
buyer fills + the generated versioned outputs), under git. Two complementary stores: DB = governed
data; vault = the documents + their git history.

## 2. Multi-RFP: one vault, a sub-repo per run, the session pointed at it

- The routine runs in the **single Run Vault repository**. When a new RFP starts, the pilot
  **creates a per-RFP run folder** (a self-contained "sub-repo": `runs/<rfp-slug>/`) and **points the
  session window at it** (the working directory / the active run). Each run folder:
  ```
  runs/<commodity>-<cycle>-<id>/
    inputs/      # the fill-out docs Claude generates + the files the buyer drops back in
    outputs/     # generated, VERSIONED: alignment_v1.xlsx, booking_guide.xlsx, post_award_v2.xlsx…
    RUN.md       # the kanban/status manifest (where we are, what's next, history of versions)
    cycle_id.txt # the link to the governed Postgres cycle
  ```
- Because each RFP is its own folder + Postgres cycle_id, the sponsor can **start a second one** and
  run **multiple RFPs in parallel** — `list runs` shows them all; the skill always states *which run*
  it is acting on.
- Everything in a run folder is **committed to the vault** as it changes (inputs interpreted,
  outputs generated) — git is the version history of the documents; the version headings in the
  files (Analysis v_n_, Post-Award Version _N_) match the committed artifacts.

## 3. The cycle loop (what the skill drives, per run)

Per `PILOT_INPUT_DOCS_SPEC.md`, each step: **generate the fill-out doc → buyer fills (or drops any
file) → ingest → act → produce the versioned output → commit to the vault → update the kanban.**

0. **Start run** → create the run folder + a Postgres cycle; generate the **Setup/Kickoff** workbook into `inputs/`.
1. **Setup ingest** → create cycle scope from the filled setup (or any file, §4).
2. **Bid template per round** → generated into `inputs/`; buyer fills / suppliers return.
3. **Ingest bids** (key-validated; or flexible, §4) → `bid.bid_line`.
4. **Run** → seal `eng.*`; generate **`alignment_v{n}.xlsx`** (the mid-cycle alignment test, clear version heading) into `outputs/`; commit.
5. **Overrides** (E/F/G) optional → generate, fill, ingest, re-run (new alignment version).
6. **Select & freeze award** → `awd.award`; generate the booking guide.
7. **Post-award adjustments** → each negotiation/reprice = a new **version** (`awd.award_adjustment`); generate **`post_award_v{N}.xlsx`** (clear "Version N · as of DATE" heading); commit.
8. **History** → all versions in Postgres + the vault; any version's records/doc can be re-pulled.

## 4. Flexible ingest — "take my file as-is, figure it out, parse it" (sponsor requirement)

Not every file the buyer has matches the generated template. Beyond the strict key-validated path,
the pilot offers **`ingest_any(file)`**: Claude (the skill) **reads the file as-is, infers its
structure** (which columns are supplier / DC / lot / price / volume — using the produce lingo + the
cycle's known scope), **maps it** to the engine's needs, shows the buyer the inferred mapping for a
quick confirm, then **writes a clean, key-stamped input file** into `inputs/` and ingests that. So
the buyer can drop a supplier's own spreadsheet and Claude adapts it — interpreting, adjusting, and
**pushing the corrected input file into the run's vault folder** (git-stored) for traceability.
Ambiguity is surfaced in plain language, never guessed silently (quarantine + ask).

## 5. Voice — speaks the buyer's language, calm under stress (sponsor requirement)

The skill communicates in **produce-sourcing language** (lots, DCs, FOB vs landed/routing, rounds,
kickoff, coverage, incumbents, awards) and **plain English**, never platform jargon (no "ingest the
key-validated template into bid.bid_line"; instead "drop me Round 2's bids and I'll load them"). It
stays **calm and clear even when the buyer is stressed** — short, concrete next steps, one ask at a
time, no walls of text. Every request tells the buyer exactly **what to do and why**, in their terms.

## 6. Proactive kanban + scheduled nudges (sponsor requirements)

- **Kanban, proactively.** On every touch (and on a schedule) the skill leads with a short **status
  board** for the run — *Done · Doing · Next · Waiting on you* — drawn from `RUN.md` + Postgres
  (which rounds are in, which analysis versions exist, whether an award is frozen, open adjustments).
  It shows where things are **without being asked** — "like opening the kanban."
- **Scheduled nudges.** The skill schedules **routine check-ins** (Claude Code routines / a
  `send_later`-style timer) to **bug the buyer for the next step** — "Round 2 closes tomorrow, here's
  the template" / "Round 1 analysis is waiting for your sign-off" / "the negotiated reprice on Dallas
  hasn't been recorded yet." Nudges are per-run, so multiple RFPs each get their own reminders.

## 7. MCP tool surface (the skill orchestrates; the server is in the MCP repo)

`run_start(commodity, …) → run_id+folder` · `run_list()` · `run_status(run_id)` (the kanban) ·
`setup_template(run_id)` · `setup_ingest(run_id, file)` · `bid_template(run_id, round)` ·
`ingest_bids(run_id, round, files)` · `ingest_any(run_id, file, hint?)` (flexible, §4) ·
`run_round(run_id, round) → alignment_v{n}` · `override_template/ingest_overrides` ·
`select_award(run_id, run, scenario)` · `booking_guide(run_id)` ·
`adjustment_template(run_id)` · `record_adjustment(run_id, file) → post_award_v{N}` ·
`history(run_id)` · `schedule_nudge(run_id, when, message)`. Every tool: names not keys (D23),
deterministic, writes the governed store + the run's vault folder, returns plain-language summaries.

## 8. Build order (modules, prototype fidelity — D19)

1. **Foundation** ✅ — `app.output` importable generator + `load_cycle` + the mid-cycle version heading.
2. **Post-award** — `awd.*` versioned freeze-and-layer + service + the post-award doc (Version-N heading).
3. **Pilot core** — `app.pilot`: the run/vault manager (per-RFP folder + git), setup template + ingest, flexible `ingest_any`, the per-round run→versioned-alignment, status/kanban, history.
4. **MCP server** — wraps the pilot service (stdio); `.mcp.json`; README to register in Claude Code.
5. **Skill + routines** — `.claude/skills/rfp-pilot/` (voice, kanban, nudges, the step-by-step flow).

Each is a working prototype of the whole capability (no MVP). Synthetic test data only; the buyer's
real files live in the Run Vault, never in the platform repo.
