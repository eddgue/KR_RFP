"""The RFP pilot MCP server package (PILOT_SYSTEM_DESIGN §4, §7).

A thin stdio MCP server (`rfp_pilot_server`) that wraps `app.pilot.PilotService` so Claude Code can
drive a real produce RFP cycle end to end. The server holds NO business logic — every tool opens a
`unit_of_work()` where the governed Postgres store is touched, calls `PilotService`, and returns a
PLAIN-LANGUAGE summary (names, never keys — D23). It reads `DATABASE_URL` (the governed store) and
`PILOT_VAULT_ROOT` (the cloned RFP_PILOT_VAULT) from the environment.

The package is named `rfp_mcp` (NOT `mcp`) on purpose: the installed MCP Python SDK owns the
top-level `mcp` import, so naming our package `mcp` would shadow the SDK and break
`from mcp.server.fastmcp import FastMCP`. Run it with `python -m rfp_mcp.rfp_pilot_server`.

This lives in the platform repo (KR_RFP); the sponsor's RFP_MCP repo registers it via `.mcp.json`.
"""

from __future__ import annotations
