# RFP_MCP — the produce-RFP pilot (MCP server + Claude Code skill)

This is the deployable home of the **RFP pilot**: a stdio **MCP server** that drives a real produce
RFP cycle end to end over the governed Postgres store + a per-run git vault, and a co-located
**Claude Code skill** (`skill/rfp-pilot/SKILL.md`) that orchestrates it in the buyer's language.

You drive everything by talking to Claude Code. The skill walks you step by step — start a run, fill
and upload each document, run the alignment, freeze an award, record post-award reprices, draft
data-merged emails, and close out — always showing a short kanban of where each run stands.

## The three pieces

| Repo / folder | What it is |
|---|---|
| **KR_RFP** (platform) | The engine, the governed Postgres schema, and the MCP server source (`backend/rfp_mcp/rfp_pilot_server.py`). |
| **RFP_MCP** (this) | The MCP registration (`.mcp.json`) + the skill (`skill/rfp-pilot/`). Co-located so Claude Code can register the server and load the skill. |
| **RFP_PILOT_VAULT** | The single git repository the routine runs in. One sub-folder ("run") per RFP, identical structure every run: `inputs/ outputs/ memory/ NOTES.md RUN.md run_data.json cycle_id.txt`. |

Two complementary stores: **Postgres = the governed data** (cycle, bids, sealed analysis runs,
awards, adjustments); **the vault = the documents + their git history**. Each run also keeps a
git-versioned `run_data.json` — a names-not-keys JSON snapshot of that run's governed records — so
the run's **data lives in git per run**, alongside its documents.

## Setup

### 1. Clone the repos

```bash
git clone <KR_RFP>           # the platform (has backend/ + backend/rfp_mcp/)
git clone <RFP_MCP>          # this repo (the .mcp.json + the skill)
git clone <RFP_PILOT_VAULT>  # the run vault the routine runs in
```

### 2. Install the backend + the MCP SDK

The server runs from the platform's virtualenv, which already carries the `mcp` Python SDK and the
app code:

```bash
cd KR_RFP/backend
python -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/pip install mcp        # the MCP Python SDK (FastMCP)
```

### 3. Bring up Postgres + migrate

```bash
export DATABASE_URL="postgresql+psycopg://app:app@localhost:5432/kr_rfp"
cd KR_RFP/backend
.venv/bin/alembic upgrade head
```

### 4. Environment variables

The server reads exactly two env vars:

| Var | Meaning |
|---|---|
| `DATABASE_URL` | The governed Postgres store, e.g. `postgresql+psycopg://app:app@localhost:5432/kr_rfp`. |
| `PILOT_VAULT_ROOT` | Absolute path to your cloned **RFP_PILOT_VAULT** folder (where the runs live). |

It is convenient to also export the path to the backend so `.mcp.json` can reference it:

```bash
export KR_RFP_BACKEND="/abs/path/to/KR_RFP/backend"
export RFP_PILOT_VAULT="/abs/path/to/RFP_PILOT_VAULT"
export DATABASE_URL="postgresql+psycopg://app:app@localhost:5432/kr_rfp"
```

### 5. Register the MCP server

`.mcp.json` (in this folder) registers the stdio server with Claude Code. It launches the server
from the backend venv:

```jsonc
{
  "mcpServers": {
    "rfp-pilot": {
      "command": "${KR_RFP_BACKEND}/.venv/bin/python",
      "args": ["-m", "rfp_mcp.rfp_pilot_server"],
      "cwd": "${KR_RFP_BACKEND}",
      "env": {
        "DATABASE_URL": "postgresql+psycopg://app:app@localhost:5432/kr_rfp",
        "PILOT_VAULT_ROOT": "${RFP_PILOT_VAULT}"
      }
    }
  }
}
```

Replace `${KR_RFP_BACKEND}` and `${RFP_PILOT_VAULT}` with absolute paths (or export them and let your
shell expand them when you copy this into your Claude Code config). The module path is
`rfp_mcp.rfp_pilot_server` and `cwd` must be the **backend/** folder so that `rfp_mcp` and the app
package import correctly.

> Why `rfp_mcp` and not `mcp`? The installed MCP Python SDK owns the top-level `mcp` import. Naming
> our package `mcp` would shadow the SDK and break `from mcp.server.fastmcp import FastMCP`. The
> package is therefore `rfp_mcp`; run it with `python -m rfp_mcp.rfp_pilot_server`.

Smoke-check the server registers all its tools without touching the DB:

```bash
cd KR_RFP/backend && .venv/bin/python -m pytest tests/mcp -q
```

### 6. Install the skill

Copy the skill into your Claude Code skills directory so it loads automatically:

```bash
cp -r RFP_MCP/skill/rfp-pilot  ~/.claude/skills/rfp-pilot
# or, project-scoped, into the working repo:
cp -r RFP_MCP/skill/rfp-pilot  ./.claude/skills/rfp-pilot
```

### 7. Point a routine / session at RFP_MCP

Run Claude Code with the working directory set to **RFP_MCP** (so it picks up `.mcp.json` and the
skill). Start a session — the skill renames it to a findable
`RFP · {commodity} · {run-slug} · {stage}` format and leads with the run's kanban.

For the scheduled nudges, arm a **Claude Code routine** pointed at RFP_MCP that re-opens the session
periodically (e.g. each morning) and asks the skill to "nudge me on every open run." The skill
checks each run's kanban and pings you for the next step (a template to send, an analysis awaiting
sign-off, an un-recorded reprice). Disarm by removing/pausing the routine. See the **Scheduled
nudges** section of `skill/rfp-pilot/SKILL.md`.

## The tools (what the skill calls)

`run_start` · `run_list` · `run_status` · `setup_template` · `setup_ingest` · `bid_template` ·
`ingest_bids` · `ingest_any` · `run_round` · `select_award` · `record_adjustment` · `history` ·
`remember` · `add_memory` · `close_run` · `purge_run`.

Every tool returns a plain-language summary in the buyer's vocabulary (lots, DCs, rounds, awards —
names, never raw keys) and names the exact file it generated and where it lives.

## Data governance

RFP data enters **only** by a formal request → upload → ingest: the skill **requests** a specific
named document, you **upload** it into the run's `inputs/` (or `memory/`), and only then does the
skill ingest it. Nothing is pulled in silently or moved between runs. Generated outputs, notes, and
the `run_data.json` snapshot are written freely; inbound RFP data is always gated.
