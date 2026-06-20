#!/usr/bin/env bash
# Claude-Code-on-the-web ENVIRONMENT SETUP SCRIPT (the cached, run-once step).
#
# Paste the BODY of this file into the environment's "Setup script" field in the web console
# (claude.ai/code → environment settings). It runs ONCE per environment; the resulting filesystem
# (the backend venv + installed deps) is cached and reused by every later session, so the slow
# `pip install` happens only the first time. Keep it under the environment's setup time budget —
# everything that must happen EVERY session (start Postgres, rehydrate, start the MCP server) lives
# in the SessionStart hook (scripts/web_session_start.sh), not here.
#
# It is also safe to run by hand:  bash scripts/web_setup.sh
set -euo pipefail

ROOT="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
BACKEND="${ROOT}/backend"

# The backend needs Python >= 3.12 (pyproject `requires-python`). Prefer an explicit 3.12.
PYBIN=""
for cand in python3.12 python3 python; do
  if command -v "$cand" >/dev/null 2>&1; then
    ver="$("$cand" -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
    if [ "$ver" = "3.12" ] || [ "$ver" \> "3.12" ]; then PYBIN="$cand"; break; fi
  fi
done
if [ -z "$PYBIN" ]; then
  echo "ERROR: Python >= 3.12 not found (backend requires it). Install python3.12 first." >&2
  exit 1
fi
echo "Using $PYBIN ($("$PYBIN" --version 2>&1))"

# Create the backend virtualenv + install the app and its dev extras (which include the MCP SDK).
cd "$BACKEND"
"$PYBIN" -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -e ".[dev]"

echo "Backend environment ready at ${BACKEND}/.venv"
