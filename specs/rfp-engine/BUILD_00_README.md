# RFP / Sourcing Engine — Backend Build Package

This package turns the six-session intake into buildable artifacts. It is **backend-first**: the data layer and engine integration come before any UI. Hand it to whoever is building — it should need no verbal explanation.

---

## Read in this order

| # | File | What it is | For |
|---|------|------------|-----|
| 0 | `BUILD_00_README.md` | This file. Index + how to use + the one thing to verify first. | Everyone |
| 1 | `BUILD_01_SYSTEM_OVERVIEW_AND_ADRS.md` | What the system is + 8 architecture decisions that lock in the corrections. | Architect, audit AI |
| 2 | `BUILD_02_DATA_MODEL.md` | Readable data model: layers, grain rules, lifecycle, what each table fixes. | Architect, backend dev |
| 3 | `BUILD_03_schema.sql` | Runnable PostgreSQL DDL. The actual tables. | Backend dev |
| 4 | `BUILD_04_TECH_SPEC.md` | Components, data flow, engine integration, API surface, build sequence. | Backend dev, audit AI |

The intake itself (`00_INDEX.md` + `SESSION-01..06`) is the evidence base behind every decision here. Keep it alongside; it answers "why" for anything below.

---

## The one thing to verify before writing code

The scoring/allocation **engine already exists and is good** (`rfp_analysis_engine_v3.py`, verified). What is missing is a persistent, governed **store** under it — the engine is stateless (file in, file out), so it does not by itself solve "open last cycle."

But there is a deployed Streamlit app and a `_event_log` utility that **may already persist some state.** Before building this schema from scratch:

> **Confirm whether the live app writes to a database or just returns a zip.**
> - If a real store exists → reconcile it to `BUILD_03_schema.sql` (migrate, don't rebuild).
> - If it is file-in/file-out → this is the greenfield backend; build it as specified.

Files that answer this: `_event_log.py`, `init_cycle.py`, and the Streamlit app's data layer. (These were likely produced in a Claude Code session, outside the chat record.)

---

## What this package gets right that the original spec got wrong

Three foundational corrections, each verified against real artifacts, are baked into the schema and ADRs:

1. **Awards are split** — multiple suppliers per cell with volume shares, not one winner. (Old spec locked the opposite; the sign-off deck and the engine's `max_two_per_dc` disprove it.)
2. **Decision-support, not auto-award** — the engine scores five weighted factors (cost is 35%) and proposes; the human selects. (Old spec built an auto-solver.)
3. **Persistence is the point** — immutable runs, freeze-and-layer, an event log, nothing deleted. (The engine and the Excel tooling have none of this; it is the whole job.)

---

## Build sequence (summary)

A. Data layer (schema + reference load) →
B. History + normalization (iTrade, KCMS, lot mapping, scorecard) →
C. Cycle + bid import (one grain, multi-template) →
D. Engine (lift v3 to a `run()` library on the store) →
E. Awards + generated outputs (selection, freeze, booking guide, sign-off, letters) →
F. API hardening, **then** UI.

UI is last, on purpose. A good front end is a view onto the store; it cannot exist before the store does. (ADR-001.)

---

## Document headers

Each doc carries a header (`doc / id / version / status / depends_on`) and a changelog. They are versioned so the audit AI and the builder can track changes as the spec evolves. Revise in place, increment the version, add a changelog row.
