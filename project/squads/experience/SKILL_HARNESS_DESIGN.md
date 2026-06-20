---
doc: Skill Harness Design — the multi-agent shape of the pilot skill (orchestrator / engine /
     secretary), and the per-run data isolation it depends on.
id: EXP-SKILL-HARNESS
squad: Experience / Platform
status: Notes (captured from sponsor 2026-06-20; informs the skill build — the NEXT step after the
        first MCP commit)
created: 2026-06-20
relates: EXP-PILOT-INPUTS, PILOT_SYSTEM_DESIGN, D28 (comments are engine-derived), ADR-0001
         (clean-room), D29 (column set), the RFP_MCP + RFP_PILOT_VAULT repos
scope: How the pilot skill is structured as a small agent HARNESS, and the data-isolation guarantees
       that keep each agent's context (and each run's data) uncontaminated.
---

# Skill Harness Design (sponsor vision, 2026-06-20)

The skill is not a single agent but a small **harness of three agents** with separated contexts, so
data commentary never gets polluted by operational noise, and runs never bleed into each other.

## The three roles

1. **Orchestrator** — the only agent that talks to the user. Routes work, sequences steps, relays
   results. Holds the conversational context; delegates the actual work.
2. **Engine agent** — DATA-DEDICATED. Takes the data inputs, runs the engine/analysis (via the MCP
   tools over the governed run store), delivers outputs, and posts its comments back to the user
   (through the orchestrator). It **answers data questions by reading the data** — its context is
   the sealed records and nothing else. This keeps every data comment grounded (D28: comments are
   the engine's computed reason, not chatter).
3. **Secretary agent** — handles "the rest of the noise": the memory + memory-file side (NOTES.md,
   `memory/`, reminders, kanban nudges, file naming, admin). It exists so that operational noise
   **never contaminates the data commentary** the Engine agent produces.

## Communication discipline (avoid cross-contamination of context)

Two options; the **hub-and-spoke** one is preferred:

- **Preferred — orchestrator-only:** only the Orchestrator communicates with the Engine and the
  Secretary, under strict constraints. The Engine and Secretary do NOT share context directly; the
  Orchestrator passes only the minimum each needs. This is what keeps the Engine's data context
  pure (no memory/admin text ever entering it) and the Secretary's admin context free of raw data.
- Alternative — peer-to-peer: the agents talk to each other. Riskier: contexts bleed. Use only if a
  task genuinely needs it, and even then mediate through the orchestrator.

The governing aim: **strict context isolation** so the Engine's commentary is provably data-only.

## Data isolation this depends on (sponsor, binding)

The harness is only as clean as the data underneath it:

- **Blank database per run/session.** Each run starts from a BLANK data store — **no demo data
  anywhere**, ever (reinforces ADR-0001 clean-room: demo/synthetic data must never appear in a run
  store).
- **No cross-contamination across concurrent runs.** When multiple RFPs run at once, one run's data
  must never be visible to another. Each run is an isolated data store (own database/schema or a
  hard run-scoped boundary), so the Engine agent reading "the data" can only ever see THIS run's
  sealed records.
- **Why it matters for the harness:** the Engine agent grounds its commentary by reading the run
  store. If that store carried demo rows or another run's rows, the commentary would be
  contaminated at the source — no amount of agent-context discipline could fix it. Isolation at the
  data layer is the precondition for clean data commentary.

### Version isolation (D32) — a live run is frozen against our development

Beyond *data* isolation (above), a **live** run must be isolated from **our ongoing development** of
the MCP and the Vault: once a session is live, no change we make can affect it. A live run is
**version-pinned** across the whole stack — the MCP build, the Vault scaffold/tooling, and the
platform/schema — and only a deliberate, opt-in upgrade moves it forward. Live sessions connect to a
**released/tagged** MCP build (not dev HEAD); a run records its MCP + Vault + migration versions; new
dev migrations are not auto-applied to a live run's store. This extends the existing per-run
`engine_version` seal to the entire stack. It needs a release/versioning discipline (tags/pins) for
RFP_MCP and RFP_PILOT_VAULT — established at the first MCP commit.

### Known gap to close before multi-run

The current pilot shares ONE Postgres database across runs, with globally-unique reference codes
(`ref.dc` DC01.., suppliers, items). A second run/setup collides on those codes (observed: the
`dc_code=DC01 already exists` failures during testing) and a second concurrent run would see the
first's reference rows. The fix is per-run data isolation (database/schema-per-run, or a strict
run-scoped tenant boundary) — this is the substrate the harness requires. Tracked as D30.

## Build sequencing (sponsor)

1. First commit to the **RFP_MCP** repo.
2. Generate the **skill** in this harness shape (orchestrator / engine / secretary).
3. The skill orchestrates the existing MCP tools; the Engine agent is the only one that reads run
   data; the Secretary owns the memory/notes surface.
