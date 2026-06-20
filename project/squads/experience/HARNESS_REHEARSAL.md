---
doc: Harness Rehearsal Kit — shake out the orchestrator/engine/secretary harness on synthetic data
     before a live RFP, then cut over to live.
id: EXP-HARNESS-REHEARSAL
squad: Experience / Platform
status: Runbook
created: 2026-06-20
relates: EXP-SKILL-HARNESS (D31), D30 (per-run data isolation), D32 (version pinning), D28 (engine
         comments), RFP_MCP plugin v0.1.0, backend/rehearsal/synthetic_fill.py
scope: A turnkey, fully-LOCAL rehearsal that exercises the real harness (the plugin's subagents) on
       synthetic data, with a pass/fail watch-list — and the note for pointing it at a live cycle.
---

# Harness Rehearsal Kit

Validate the **harness behaviour** — the part that's new and only runs for real inside Claude Code:
the orchestrator delegating hub-and-spoke, tool-scoping holding, context staying isolated, and the
Opus-4.8 pin taking. The substrate underneath (engine, per-run DB isolation, MCP, vault) is already
covered by the automated suite; this kit is specifically about the agents.

Everything is **local and synthetic** — no GitHub repos, no real RFP data (the commodity is
"Test Greens"). One `mkdir` is the only "priming" needed (the vault git-inits itself; commits are
local-only, no push).

## 1. Local setup (once)

```bash
# Postgres up + the shared app DB migrated (credentials/template for the per-run DBs)
export DATABASE_URL="postgresql+psycopg://app:app@localhost:5432/kr_rfp"
cd KR_RFP/backend && .venv/bin/alembic upgrade head

# the app role must be able to create per-run databases (D30)
psql -d postgres -c "ALTER ROLE app CREATEDB;"   # (Homebrew: connects as your user; Linux: sudo -u postgres)

# a throwaway vault folder — this is the entire "prime the vault" step
mkdir -p ~/rfp-rehearsal-vault

# register the MCP server with ABSOLUTE paths (the reliable method — see note below).
# run this from the KR_RFP repo root so --scope local keys to this project:
cd ..
claude mcp add rfp-pilot --scope local \
  --env DATABASE_URL=postgresql+psycopg://app:app@localhost:5432/kr_rfp \
  --env PILOT_VAULT_ROOT="$HOME/rfp-rehearsal-vault" \
  --env PYTHONPATH="$PWD/backend" \
  -- "$PWD/backend/.venv/bin/python" -m rfp_mcp.rfp_pilot_server
claude mcp list      # expect: rfp-pilot ... ✓ Connected

# launch Claude Code with the harness plugin (agents + skill) loaded from the local folder
claude --plugin-dir ./mcp
```

> **Why `claude mcp add` and not just the plugin's `.mcp.json`?** `--plugin-dir` reliably loads the
> agents + skill, but autoloading the plugin's MCP server (and substituting `${ENV}` in it) varies by
> Claude Code version — in the first rehearsal the server silently failed to start because its path
> placeholders weren't substituted. Registering it once with absolute paths + `PYTHONPATH` (so
> `rfp_mcp` imports without depending on the process CWD) is deterministic. The plugin's `.mcp.json`
> now uses `${CLAUDE_PLUGIN_ROOT}` and may also work directly; `claude mcp add` is the guaranteed path.

The plugin registers the three agents (orchestrator skill + `rfp-engine` + `rfp-secretary`); the
`claude mcp add` step registers the `rfp-pilot` MCP server they call. You talk to the
**orchestrator**; it delegates.

## 2. How you drive it

You are the operator. At each step you (a) tell the orchestrator what to do in plain language, then
(b) when it asks you to fill + upload a doc, run the matching `synthetic_fill` command on the file it
just generated (it lands in `~/rfp-rehearsal-vault/runs/<slug>/inputs/`), then (c) tell the
orchestrator the file is ready to ingest. The orchestrator should be delegating each action to the
engine or the secretary — watch that it does (see §4).

> Tip: you can run the operator side as a second Claude session if you want a hands-off two-agent
> rehearsal — one session is the buyer/operator, the other (with the plugin) is the harness.

## 3. The scripted cycle + edge cases

| # | Say to the orchestrator | Then run / upload | Watch for |
|---|---|---|---|
| 1 | "Start a Test Greens run **as a rehearsal**." | `python -m rehearsal.synthetic_fill setup <inputs>/01_setup_kickoff.xlsx` → tell it to ingest setup | secretary did `run_start` **with rehearsal=true** (artifacts stamped SYNTHETIC); engine did `setup_ingest`; cycle = 3 DCs, 3 lots, 4 suppliers, 3 rounds |
| 2 | "Generate the Round 1 bid template." | `synthetic_fill bids <inputs>/0X_round1_bid_template.xlsx 1` → "load Round 1 bids" | engine generated + ingested; **33 priced lines** (3 DCs × 3 lots × 4 suppliers − Gamma's 3 Spinach NO-BIDs) |
| 3 | "Run the Round 1 alignment." | — | engine sealed Analysis v1; names the file; the file is stamped **SYNTHETIC, never "LIVE CYCLE DATA"**; Delta priced out on Spring Mix/Romaine (surfaced in **Incumbent Retention**) but **competitive on Spinach** so continuity is in play |
| 4 | **EDGE — re-run R1.** "Re-run Round 1." | — | new version v2 (not an overwrite); engine, not secretary |
| 5 | "Round 2 template / bids / run." | `synthetic_fill bids ...round2... 2` | drift down; Analysis v3; round-over-round movement shows |
| 6 | **EDGE — flex ingest.** "Round 3 template; I have Alpha's own file." | `synthetic_fill bids ...round3... 3` (the others) + `synthetic_fill messy <round3 template> /tmp/alpha_messy.xlsx` → upload, "ingest this as-is" | engine proposes the column mapping (confirm=false) → you confirm → ingests; supersedes Alpha's bulk line |
| 7 | **EDGE — supersession.** "Beta re-sent a corrected Round 3 file." | re-fill + re-upload Round 3 | prior Beta lines superseded, not double-counted |
| 8 | "Freeze the award on Scenario B." | — | engine froze the award + booking guides; names the files |
| 9 | **EDGE — post-award reprice.** "Reprice Dallas Lot 2 to 13.50, effective next week." | — | engine recorded version 1 (names-based change); post_award_v1 file |
| 10 | **EDGE — second run, concurrently.** "Start another Test Greens run and ingest its setup." | new `synthetic_fill setup ...` | **its own database** — no DC01 collision; the two runs never see each other |
| 11 | "Close the first run." | confirm the archive | secretary archived → you confirm → purge drops the run's DB |

## 4. The watch-list — the pass/fail gate

Tick every box. A miss is a finding to fix in the skill/agent definitions, not something to wave past.

- [ ] **Engine stays data-only.** The `rfp-engine` never writes NOTES.md, never manages files/memory,
      never shows a kanban. If it does, its tool-scoping or instructions leaked.
- [ ] **Secretary never touches data.** The `rfp-secretary` never ingests, runs, scores, or explains a
      recommendation. If asked a data question it defers to the engine.
- [ ] **Every number is traceable.** Each figure/supplier/reason the engine states can be traced to
      the records or the output file — no invented numbers, no generic "risk-adjusted" boilerplate
      (D28). Spot-check 3 cells against the analysis file.
- [ ] **Hub-and-spoke held.** Only the orchestrator talked to the subagents; the engine and secretary
      never addressed each other.
- [ ] **Model stayed pinned.** Both subagents ran on Opus 4.8 (no silent fallback) — check the
      session's agent/model indicator.
- [ ] **Isolation held.** The two concurrent runs used separate databases (no `DC01` collision); the
      shared `kr_rfp` DB stayed empty of run cycles; purge dropped the run DB.
- [ ] **Provenance is honest.** Every rehearsal artifact (alignment workbooks + booking guides) is
      stamped **SYNTHETIC** — never "LIVE CYCLE DATA — real names & prices". (A real run is the
      inverse: LIVE, never SYNTHETIC.)
- [ ] **No orphans.** A failed/aborted `run_start` leaves no run folder and no leftover
      `kr_rfp_run_*` database. `run_list` shows only the runs you actually started.
- [ ] **Voice + governance.** Buyer language, one ask at a time, names-not-keys, and inbound data only
      via request → upload → ingest.

**Pass** = every box ticked across the full cycle + all six edge cases. Record misses, fix them in
`skills/rfp-pilot/SKILL.md` / `agents/*.md`, bump the plugin `version`, re-tag, and re-run the gate.

## 5. Going live (the cutover)

When the rehearsal passes, the only changes for a real cycle are **where the vault points** and
**real data instead of synthetic** — nothing in the harness changes:

- Point `PILOT_VAULT_ROOT` at a clone of the real **RFP_PILOT_VAULT** instead of the throwaway folder
  (`git clone <RFP_PILOT_VAULT>`; it's an empty repo that fills run-by-run — no priming beyond
  existing). Optionally add `git remote` push as a backup step on the vault folder; the pilot itself
  only commits locally.
- Pin the plugin to the released tag (`RFP_MCP` `v0.1.0`) so the live run is frozen against ongoing
  development (D32).
- Start the run **without** the rehearsal flag (`rehearsal=false`, the default) — a live run is
  stamped **"LIVE CYCLE DATA — real names & prices"**, while a rehearsal is stamped SYNTHETIC, so the
  two can never be confused in the output files.
- Use the real fill-out docs (the buyer/suppliers fill them) — **stop using `synthetic_fill`**.
- Each real run still gets its own isolated database automatically (D30).
