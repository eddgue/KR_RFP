"""Smoke test for the RFP pilot MCP server (PART B).

Imports the server module and asserts the `FastMCP` app exists and registers every tool the design's
tool surface calls for (PILOT_SYSTEM_DESIGN §7). It does NOT run the stdio loop — it only inspects
the registered tools, so it stays a PURE test (no DB, no transport). This guards against a tool being
renamed/dropped or the module failing to import.
"""

from __future__ import annotations

import asyncio

from mcp.server.fastmcp import FastMCP

from rfp_mcp.rfp_pilot_server import app

# The tool surface the skill orchestrates (PILOT_SYSTEM_DESIGN §7 / the brief's Part 2 list).
EXPECTED_TOOLS = {
    "run_start",
    "run_list",
    "run_status",
    "setup_template",
    "setup_ingest",
    "bid_template",
    "ingest_bids",
    "ingest_any",
    "run_round",
    "select_award",
    "record_adjustment",
    "history",
    "remember",
    "add_memory",
    "close_run",
    "purge_run",
}


def test_app_is_fastmcp() -> None:
    """The module exposes a `FastMCP` app named 'rfp-pilot'."""

    assert isinstance(app, FastMCP)
    assert app.name == "rfp-pilot"


def test_all_expected_tools_registered() -> None:
    """Every tool in the design's surface is registered (and no fewer)."""

    registered = {tool.name for tool in asyncio.run(app.list_tools())}
    missing = EXPECTED_TOOLS - registered
    assert not missing, f"missing MCP tools: {sorted(missing)}"
    assert EXPECTED_TOOLS <= registered
