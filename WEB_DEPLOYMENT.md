# Running the RFP harness on Claude Code for the web

This is the runbook for driving the produce-RFP harness from **Claude Code on the web**
(claude.ai/code) instead of a terminal — a cloud session in an **ephemeral** container. Everything
the harness needs lives in that one container: Postgres, the per-run isolated databases (D30), the
HTTP MCP server, and the cloned vault. Because the container is reclaimed between sessions, the only
state that survives is what is committed to git — which is exactly why a run's governed database
rides the vault as a SQL snapshot (D34) and is rehydrated on session start.

## What runs where

| Piece | Where | Persists how |
|---|---|---|
| Platform code + MCP server (`backend/`, `rfp_mcp/`) | this repo (KR_RFP), cloned into the container | git (the repo) |
| Postgres + the per-run isolated DBs | started inside the container each session | **`<run>/db/run_db.sql`** snapshot in the vault (D34) |
| The run vault (documents, NOTES, `run_data.json`, DB snapshots) | cloned RFP_PILOT_VAULT, `PILOT_VAULT_ROOT` | git (the vault repo) |
| The MCP server transport | **HTTP** on `127.0.0.1:8765` (the web runtime does not run stdio servers) | restarted each session by the hook |

## Why HTTP, not stdio

Local Claude Code talks to the MCP server over **stdio** (the plugin in `mcp/.mcp.json`). The web
runtime does **not** spawn stdio MCP servers, so the same server is started in **streamable-HTTP**
mode inside the container and reached over loopback. The server supports both transports from one
entry point — `RFP_MCP_TRANSPORT=streamable-http` selects HTTP (`rfp_mcp/rfp_pilot_server.py`,
`main()`). The repo-root **`.mcp.json`** registers the HTTP URL the web runtime connects to.

## The 3-agent harness (skill + subagents) on the web

The web runtime auto-loads project skills/subagents from **`.claude/skills/`** and **`.claude/agents/`**
at clone time, but it does **not** auto-load the `mcp/` plugin layout. It also does **not** reliably
load subagents added *during* a SessionStart hook — `reloadSkills` re-scans skills only, and a
subagent file dropped in at session start isn't picked up until a restart (confirmed by review).

So the harness is **committed under `.claude/`**: `.claude/skills/rfp-pilot/SKILL.md` and
`.claude/agents/rfp-engine.md` / `.claude/agents/rfp-secretary.md`. Present in the clone, they load at
session start — both the skill and the subagents — with nothing for the hook to do. (The canonical
copies still live under `mcp/` for the local `--plugin-dir` plugin / stdio path; **keep the two in
sync** — they are duplicated on purpose so each runtime loads its native way.)

- **Validate once in a real web session:** confirm `/agents` shows `rfp-engine` and `rfp-secretary`
  and that invoking the `rfp-pilot` skill can delegate to them. (Local copies loading on web is the
  documented "present before startup" path; this just hasn't been exercised on the cloud yet.)
- The raw MCP **tools** work on the web regardless (they come from the HTTP server), so a single
  session can drive a run even if the skill/subagents ever fail to load — the harness is the curated
  UX on top.
- Later option (drops the duplication): publish `RFP_MCP` as a marketplace and **declare the plugin
  in `.claude/settings.json`** so the cloud installs it at session start (preserves the versioned
  plugin design, D31/D32).

## One-time environment setup (web console)

Do these once when you create the environment at claude.ai/code (environment settings):

1. **Setup script** — paste the body of [`scripts/web_setup.sh`](scripts/web_setup.sh) into the
   "Setup script" field. It runs once and is cached: it creates `backend/.venv` and installs the
   backend + dev extras (which include the MCP SDK). Keep slow installs here; anything that must run
   every session is in the SessionStart hook below.
2. **Environment variables** (no quotes):
   - `PILOT_VAULT_ROOT` — absolute path to the cloned vault in the container. Optional if you use
     option (a) or (b) below (the session-start hook resolves it); set it explicitly to be sure.
   - `RFP_PILOT_VAULT_REMOTE` — optional; the vault's git URL. If set (and the vault isn't already
     present), the hook clones it for you — option (b).
   - `DATABASE_URL` — optional; defaults to `postgresql+psycopg://app:app@localhost:5432/kr_rfp`.
   - `RFP_MCP_PORT` — optional; defaults to `8765` (must match `.mcp.json`).
   - `RFP_VAULT_AUTOPUSH` — optional; defaults to `1` in the web runtime (set `0` to disable push).
3. **Network policy** — **Trusted** is enough (package installs + GitHub over the proxy; the MCP
   server and Postgres are loopback). Use **Custom** only if you point at an *external* Postgres.
4. **SessionStart hook** — copy [`.claude/settings.web.json.sample`](.claude/settings.web.json.sample)
   to `.claude/settings.json` in the web clone and commit it. (It is shipped as a sample, not active
   config, so installing a per-session hook is a deliberate choice.) The hook runs
   [`scripts/web_session_start.sh`](scripts/web_session_start.sh) which, **every session**: starts
   Postgres, ensures the `app` role + base DB, **rehydrates every run's DB from its vault snapshot**
   (`python -m rfp_mcp.rehydrate`), and starts the HTTP MCP server — then returns so Claude Code
   connects to it. It is a no-op outside the web runtime, so local sessions are unaffected.

## The vault in the container

The harness reads/writes the vault (**`eddgue/RFP_PILOT_VAULT`**, private) at `PILOT_VAULT_ROOT` and
**commits** every governed change to it locally (including the DB snapshot). For that state to
survive the ephemeral container it must reach the vault's **git remote**. Both the push and the clone
are now wired; you pick how the clone gets its credentials:

- **Pushing the vault back — BUILT.** Vault commits are pushed to the remote when
  `RFP_VAULT_AUTOPUSH` is set (every commit path goes through it). The session-start hook defaults it
  **on** in the web runtime, so each governed write that commits a DB snapshot also pushes it. It is
  off for local/tests, and a push failure is swallowed (git is a convenience layer, never a blocker).
- **Getting the vault into the container — BUILT, pick the credential path:**
  - **Option (a), recommended — attach the vault as a SECOND repo.** Add `eddgue/RFP_PILOT_VAULT` to
    the environment alongside KR_RFP; push then uses the attached repo's own credentials (no token to
    manage). Point `PILOT_VAULT_ROOT` at its checkout (the hook also auto-detects a sibling
    `RFP_PILOT_VAULT` clone).
  - **Option (b) — clone from a URL.** Set `RFP_PILOT_VAULT_REMOTE` to the vault's git URL; the hook
    clones it (to `.rfp_pilot_vault`, gitignored) using the env's git credentials / proxy.
  - Either way the hook checks the clone has an **upstream branch** (so `git push` has a target) and
    warns if not — set one once with `git -C <vault> push -u origin main`. Verified end to end via
    option (b) against a local remote: clone → rehydrate → server up, upstream present.

## Scheduled nudges (Routines)

Create a **Routine** at claude.ai/code/routines pointed at this environment with a prompt like
"nudge me on every open run": each trigger starts a session (so the hook rehydrates + brings the
server up) and the harness checks each run's kanban and pings you for the next step. Routines are
configured in the web console only.

## What is built and verified vs. what needs a real web session

**Built + tested locally (in this repo):**
- DB snapshot/restore round-trip — `dump → drop → restore` keeps the data intact
  (`tests/pilot/test_run_persistence.py`), wired after every governed write + a `rehydrate` entry.
- Vault auto-push — a commit reaches a real (bare) remote when `RFP_VAULT_AUTOPUSH` is on and does
  not when off (`tests/pilot/test_vault_autopush.py`).
- The MCP server serves over HTTP (`RFP_MCP_TRANSPORT=streamable-http`), verified responding on a
  loopback port.
- `scripts/web_session_start.sh` end to end against a local Postgres: starts/locates Postgres,
  ensures the role/DB, resolves + clones the vault (option b), rehydrates, and brings the HTTP server
  up — with the vault's upstream branch present so autopush has a target.
- The session-start hook's **stdout is clean JSON** (`reloadSkills`) with all logs on stderr, and it
  symlinks the harness skill + subagents into `.claude/` (verified locally).

**Needs validation in an actual web session (cannot be tested from here):**
- That the web runtime loads `.claude/settings.json` hooks and runs the SessionStart hook **before**
  connecting to `.mcp.json` servers, and that it reaches the loopback HTTP MCP server.
- That the harness loads after the hook: the orchestrator **skill** AND the `rfp-engine` /
  `rfp-secretary` **subagents** (subagent live-reload is undocumented — fall back to Alternative A/B
  in "The 3-agent harness on the web" if the subagents don't appear).
- The exact Postgres start command for the web image (the script tries `service postgresql start`
  then `pg_ctlcluster 16 main start`, with and without `sudo`) — adjust if the image differs.
- The credential path for the vault: that an attached second repo (option a) pushes, or that the
  env's git proxy authorizes the clone/push for a URL (option b).

First web session: run `bash scripts/web_session_start.sh` by hand (or check `/tmp/rfp_mcp.log`) and
confirm `rfp-pilot` shows connected via `/mcp` before relying on the routine.
