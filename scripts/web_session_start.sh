#!/usr/bin/env bash
# Claude-Code-on-the-web SESSION-START hook (runs at the start of EVERY web session).
#
# The environment cache captures FILES, not running processes, so the things that must be *running*
# for the harness — Postgres and the HTTP MCP server — have to be (re)started each session, and the
# per-run isolated databases have to be rehydrated from their vault snapshots (D34). This script does
# exactly that, idempotently, then returns so Claude Code can connect to the MCP server declared in
# .mcp.json (SessionStart completes before MCP connections are made).
#
# Wired via .claude/settings.json (SessionStart → command). It is a NO-OP outside the web runtime
# (CLAUDE_CODE_REMOTE != true) so local terminal sessions keep using the stdio MCP plugin unchanged.
set -uo pipefail  # not -e: best-effort; a soft failure must not abort session start

# Only do the web wiring in the cloud runtime; local Claude Code uses the stdio plugin (mcp/.mcp.json).
[ "${CLAUDE_CODE_REMOTE:-}" = "true" ] || { echo "[session-start] not the web runtime — skipping." >&2; exit 0; }

# This hook produces NO stdout: the harness skill + subagents are committed under .claude/ (loaded at
# clone time, so no reloadSkills signal is needed). Route all logs + command output to stderr so the
# hook's stdout stays clean.
exec 1>&2

ROOT="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
BACKEND="${ROOT}/backend"
PY="${BACKEND}/.venv/bin/python"
PORT="${RFP_MCP_PORT:-8765}"
export DATABASE_URL="${DATABASE_URL:-postgresql+psycopg://app:app@localhost:5432/kr_rfp}"
# In the web runtime the local vault clone is discarded between sessions, so vault commits must be
# PUSHED to persist (D34). Default on here; override by setting RFP_VAULT_AUTOPUSH=0 in the env.
export RFP_VAULT_AUTOPUSH="${RFP_VAULT_AUTOPUSH:-1}"

log() { echo "[session-start] $*" >&2; }

# Build the venv if it's missing OR incomplete. Checking only that python exists would accept a
# PARTIAL install (venv created but `pip install` interrupted), so verify the key deps actually
# import. Configuring scripts/web_setup.sh as the env Setup script caches a complete build so this
# fallback (1-3 min) doesn't run every session and the server is up before the MCP client connects.
venv_ready() {
  [ -x "$PY" ] && (cd "$BACKEND" && "$PY" -c "import mcp, sqlalchemy, app.pilot.service") >/dev/null 2>&1
}
if ! venv_ready; then
  log "backend venv missing or incomplete — building it (set scripts/web_setup.sh as the env Setup script to cache this)..."
  bash "$ROOT/scripts/web_setup.sh" || log "WARNING: venv build failed (see above)."
fi
if ! venv_ready; then
  log "venv still not usable after build attempt (deps missing?) — cannot start the harness; aborting."
  exit 0
fi

# --- Resolve the vault location (RFP_PILOT_VAULT = the run store that carries state across boxes) - #
# Option (a, recommended): attach eddgue/RFP_PILOT_VAULT as a SECOND repo and point PILOT_VAULT_ROOT
#   at its checkout — push works natively via the attached repo's credentials.
# Option (b): set RFP_PILOT_VAULT_REMOTE and this clones it here (the clone needs push credentials).
# Auto-detect an attached/sibling vault clone across the locations a second repo tends to land.
if [ -z "${PILOT_VAULT_ROOT:-}" ]; then
  parent="$(dirname "$ROOT")"
  for cand in \
    "$parent/RFP_PILOT_VAULT" "$parent/rfp_pilot_vault" \
    "$ROOT/../RFP_PILOT_VAULT" "${HOME:-/root}/RFP_PILOT_VAULT"; do
    [ -d "$cand/.git" ] && { PILOT_VAULT_ROOT="$(cd "$cand" && pwd)"; break; }
  done
fi
# Last resort: search a couple levels down for a git repo named like the vault (case-insensitive).
if [ -z "${PILOT_VAULT_ROOT:-}" ]; then
  hit="$(find "$(dirname "$ROOT")" "${HOME:-/root}" -maxdepth 3 -type d -iname 'rfp_pilot_vault' 2>/dev/null | head -1)"
  [ -n "$hit" ] && [ -d "$hit/.git" ] && PILOT_VAULT_ROOT="$hit"
fi
# Or clone it from a configured remote (set RFP_PILOT_VAULT_REMOTE in the env).
if [ -z "${PILOT_VAULT_ROOT:-}" ] && [ -n "${RFP_PILOT_VAULT_REMOTE:-}" ]; then
  PILOT_VAULT_ROOT="${ROOT%/}/.rfp_pilot_vault"
  if [ ! -d "$PILOT_VAULT_ROOT/.git" ]; then
    log "cloning the vault from RFP_PILOT_VAULT_REMOTE..."
    git clone "$RFP_PILOT_VAULT_REMOTE" "$PILOT_VAULT_ROOT" 2>&1 | sed 's/^/[session-start] /' >&2 || true
  fi
fi
export PILOT_VAULT_ROOT="${PILOT_VAULT_ROOT:-}"
if [ -n "$PILOT_VAULT_ROOT" ]; then
  log "vault: $PILOT_VAULT_ROOT"
else
  log "vault not found — attach eddgue/RFP_PILOT_VAULT as a second repo or set RFP_PILOT_VAULT_REMOTE; \
runs won't persist until then (rehydrate skipped)."
fi

# --- run a psql command as a Postgres SUPERUSER, trying the usual local auth strategies ---------- #
super_psql() {
  if command -v sudo >/dev/null 2>&1 && sudo -n -u postgres psql -v ON_ERROR_STOP=1 "$@" 2>/dev/null; then return 0; fi
  if psql -U postgres -v ON_ERROR_STOP=1 "$@" 2>/dev/null; then return 0; fi
  psql -v ON_ERROR_STOP=1 "$@" 2>/dev/null
}

# --- 1. Postgres is pre-installed but NOT running by default in the web container — start it ------ #
if ! pg_isready -q 2>/dev/null; then
  log "starting Postgres..."
  { command -v sudo >/dev/null 2>&1 && sudo -n service postgresql start; } 2>/dev/null \
    || service postgresql start 2>/dev/null \
    || { command -v sudo >/dev/null 2>&1 && sudo -n pg_ctlcluster 16 main start; } 2>/dev/null \
    || pg_ctlcluster 16 main start 2>/dev/null \
    || true
  for _ in $(seq 1 40); do pg_isready -q 2>/dev/null && break; sleep 0.5; done
fi
pg_isready -q 2>/dev/null && log "Postgres is up." || log "WARNING: Postgres did not come up."

# --- 2. Ensure the app role + governed base DB exist (the credential template for per-run DBs) --- #
super_psql -d postgres -c \
  "DO \$\$ BEGIN IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname='app') THEN CREATE ROLE app LOGIN PASSWORD 'app' CREATEDB; END IF; END \$\$;" \
  && log "app role ensured." || log "note: could not ensure app role (may already exist / insufficient privs)."
super_psql -d postgres -tc \
  "SELECT 'CREATE DATABASE kr_rfp OWNER app' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname='kr_rfp')\gexec" \
  >/dev/null 2>&1 && log "kr_rfp base DB ensured." || true

# --- 3. Rehydrate every run's isolated DB from its committed vault snapshot (D34) ---------------- #
if [ -n "${PILOT_VAULT_ROOT:-}" ]; then
  ( cd "$BACKEND" && PILOT_VAULT_ROOT="$PILOT_VAULT_ROOT" "$PY" -m rfp_mcp.rehydrate ) 2>&1 | sed 's/^/[session-start] /' >&2 \
    || log "WARNING: rehydrate failed (see above)."
else
  log "PILOT_VAULT_ROOT unset — skipping rehydrate (set it in the environment's variables)."
fi

# --- 4. Start the HTTP MCP server in the background (the web runtime won't spawn a stdio server) - #
if curl -s "http://127.0.0.1:${PORT}/mcp" >/dev/null 2>&1; then
  log "MCP server already serving on :${PORT}."
else
  log "starting HTTP MCP server on 127.0.0.1:${PORT}..."
  ( cd "$BACKEND" && RFP_MCP_TRANSPORT=streamable-http RFP_MCP_HOST=127.0.0.1 RFP_MCP_PORT="$PORT" \
      DATABASE_URL="$DATABASE_URL" PILOT_VAULT_ROOT="${PILOT_VAULT_ROOT:-}" \
      RFP_VAULT_AUTOPUSH="$RFP_VAULT_AUTOPUSH" \
      setsid nohup "$PY" -m rfp_mcp.rfp_pilot_server >/tmp/rfp_mcp.log 2>&1 & ) || true
  for _ in $(seq 1 40); do curl -s "http://127.0.0.1:${PORT}/mcp" >/dev/null 2>&1 && break; sleep 0.5; done
  curl -s "http://127.0.0.1:${PORT}/mcp" >/dev/null 2>&1 \
    && log "MCP server is up on :${PORT}." \
    || log "WARNING: MCP server did not come up — see /tmp/rfp_mcp.log."
fi

# The 3-agent harness (skill rfp-pilot + subagents rfp-engine/rfp-secretary) is committed under
# .claude/skills and .claude/agents, so the cloud runtime loads it at clone time — nothing to do here
# (subagents added at SessionStart would NOT load until restart; committing them avoids that).
exit 0
