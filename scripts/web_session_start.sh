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

ROOT="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
BACKEND="${ROOT}/backend"
PY="${BACKEND}/.venv/bin/python"
PORT="${RFP_MCP_PORT:-8765}"
export DATABASE_URL="${DATABASE_URL:-postgresql+psycopg://app:app@localhost:5432/kr_rfp}"
# In the web runtime the local vault clone is discarded between sessions, so vault commits must be
# PUSHED to persist (D34). Default on here; override by setting RFP_VAULT_AUTOPUSH=0 in the env.
export RFP_VAULT_AUTOPUSH="${RFP_VAULT_AUTOPUSH:-1}"

log() { echo "[session-start] $*" >&2; }

if [ ! -x "$PY" ]; then
  log "backend venv missing ($PY) — run scripts/web_setup.sh as the environment setup script first."
  exit 0
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

exit 0
