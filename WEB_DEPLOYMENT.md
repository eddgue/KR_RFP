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

## One-time environment setup (web console)

Do these once when you create the environment at claude.ai/code (environment settings):

1. **Setup script** — paste the body of [`scripts/web_setup.sh`](scripts/web_setup.sh) into the
   "Setup script" field. It runs once and is cached: it creates `backend/.venv` and installs the
   backend + dev extras (which include the MCP SDK). Keep slow installs here; anything that must run
   every session is in the SessionStart hook below.
2. **Environment variables** (no quotes):
   - `PILOT_VAULT_ROOT` — absolute path to the cloned vault in the container (see "The vault" below).
   - `DATABASE_URL` — optional; defaults to `postgresql+psycopg://app:app@localhost:5432/kr_rfp`.
   - `RFP_MCP_PORT` — optional; defaults to `8765` (must match `.mcp.json`).
3. **Network policy** — **Trusted** is enough (package installs + GitHub over the proxy; the MCP
   server and Postgres are loopback). Use **Custom** only if you point at an *external* Postgres.
4. **SessionStart hook** — copy [`.claude/settings.web.json.sample`](.claude/settings.web.json.sample)
   to `.claude/settings.json` in the web clone and commit it. (It is shipped as a sample, not active
   config, so installing a per-session hook is a deliberate choice.) The hook runs
   [`scripts/web_session_start.sh`](scripts/web_session_start.sh) which, **every session**: starts
   Postgres, ensures the `app` role + base DB, **rehydrates every run's DB from its vault snapshot**
   (`python -m rfp_mcp.rehydrate`), and starts the HTTP MCP server — then returns so Claude Code
   connects to it. It is a no-op outside the web runtime, so local sessions are unaffected.

## The vault in the container — OPEN, needs your decision

The harness reads/writes the vault at `PILOT_VAULT_ROOT` and **commits** every governed change to it
locally (including the DB snapshot). For that state to survive the ephemeral container it must reach
the vault's **git remote**. Two things still need wiring and a decision from you:

- **Getting the vault into the container.** Either (a) make RFP_PILOT_VAULT the session's repo and
  KR_RFP a secondary repo, or (b) have the setup/session-start script `git clone` the vault to a
  fixed path and set `PILOT_VAULT_ROOT` to it. Cloning needs credentials (a deploy token / the git
  proxy) — that is the decision.
- **Pushing the vault back.** The service commits to the vault locally but does **not push**. For
  ephemeral persistence the vault clone's commits must be pushed to the remote (at session end or on
  a cadence). This push step is not yet wired — flag for the next increment.

## Scheduled nudges (Routines)

Create a **Routine** at claude.ai/code/routines pointed at this environment with a prompt like
"nudge me on every open run": each trigger starts a session (so the hook rehydrates + brings the
server up) and the harness checks each run's kanban and pings you for the next step. Routines are
configured in the web console only.

## What is built and verified vs. what needs a real web session

**Built + tested locally (in this repo):**
- DB snapshot/restore round-trip — `dump → drop → restore` keeps the data intact
  (`tests/pilot/test_run_persistence.py`), wired after every governed write + a `rehydrate` entry.
- The MCP server serves over HTTP (`RFP_MCP_TRANSPORT=streamable-http`), verified responding on a
  loopback port.
- `scripts/web_session_start.sh` end to end against a local Postgres: starts/locates Postgres,
  ensures the role/DB, rehydrates, and brings the HTTP server up.

**Needs validation in an actual web session (cannot be tested from here):**
- That the web runtime loads `.claude/settings.json` hooks and runs the SessionStart hook **before**
  connecting to `.mcp.json` servers, and that it reaches the loopback HTTP MCP server.
- The exact Postgres start command for the web image (the script tries `service postgresql start`
  then `pg_ctlcluster 16 main start`, with and without `sudo`) — adjust if the image differs.
- The vault clone + push wiring above.

First web session: run `bash scripts/web_session_start.sh` by hand (or check `/tmp/rfp_mcp.log`) and
confirm `rfp-pilot` shows connected via `/mcp` before relying on the routine.
