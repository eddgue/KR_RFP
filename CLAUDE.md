# CLAUDE.md — OPERATING CONTRACT. READ FIRST, EVERY SESSION, BEFORE ANY WORK.

Claude Code auto-loads this file. It is the non-negotiable contract for this repo.
**Every sub-agent spawned MUST receive the ABSOLUTE REQUIREMENTS below verbatim in its prompt and
be told to read this file + the authoritative docs before proposing or building anything.**
If you are an agent and you did not receive these rules: STOP and say so.

---

## ABSOLUTE REQUIREMENTS (sponsor directives — non-negotiable, in priority order)

1. **NO MVP. NO STUBS. NO PLACEHOLDERS. (D19 — RATIFIED.)**
   We do **not** build thinnest-possible slices, stub screens, "disabled / coming-soon" affordances,
   mock content, or "just enough to surface data." Every module, screen, surface, endpoint, and
   dataset ships as a **functional prototype of the FULL capability, fully wired to real data**.
   "Done" = the *whole* capability works end-to-end — not that something renders.
   This is the **first** requirement and the tiebreaker when anything competes.
   (Source: `project/03_DECISION_LOG.md` D19; `project/02_WAYS_OF_WORKING.md`.)

2. **Outcome over output — full functionality, least margin for error.**
   Optimize for a system that runs live RFPs accurately, repeatably, auditably — not feature count.
   (Source: `project/08_RELEASE_GOVERNANCE.md`.)

3. **DATA FIDELITY IS PART OF "NO MVP".**
   Any file conversion, seed, or dry-run dataset must map **every field to its correct target through
   EVERY step** (setup → template → bids → engine → analysis). **Forbidden:** dropping rows,
   flattening/coercing dimensions, renaming entities to their raw IDs, force-positiving or otherwise
   altering values, or collapsing a multi-round RFP to a single round — to "make data appear."
   Bad/ambiguous data is **surfaced as quarantine**, never silently fudged. Reconcile outputs to the
   source/golden **NUMBERS at each step** (counts, demand totals, per-round bids, landed spend) — not
   just shape or lens ordering. The buyer reviews the **analysis and the process**, so the data must
   be faithful, not illustrative.

4. **No server-side file storage.**
   The database is the single source of truth. Deliverables render on request; uploads stream to
   ingest. No writing generated artifacts to disk in the running app. (Source: `project/NO_FILE_STORAGE_PLAN.md`.)

5. **Verify before actioning.**
   Treat auditor/agent/own claims with a grain of salt and verify against the code, the DB, and the
   MCP harness (the live-run verification **oracle**). Do not assert "done/verified" without proof.

6. **Save frequently; branch discipline.**
   Commit as you go so nothing is lost. Develop on branch **`claude/wizardly-pasteur-n4acb8`**;
   never push elsewhere without explicit permission. End commit messages with the
   `Co-Authored-By` / `Claude-Session` trailers. **Never** put the model ID in any committed artifact.

---

## READ THESE BEFORE ANY NON-TRIVIAL WORK
- `project/02_WAYS_OF_WORKING.md` — how we build (NOT-MVP, modular, prototype fidelity).
- `project/03_DECISION_LOG.md` — ratified decisions (esp. **D19** no-MVP, **D42/D43/D44** grain/pricing/freeze).
- `project/08_RELEASE_GOVERNANCE.md` — the governing principles + tiebreaker.
- `project/NO_FILE_STORAGE_PLAN.md` — the no-server-side-storage contract.
- `project/04_PROGRAM_BACKLOG.md` — scope/epics.

## AGENT PROTOCOL (mandatory)
When spawning ANY sub-agent (Plan, Explore, general, build, etc.):
1. Paste the **ABSOLUTE REQUIREMENTS** above into its prompt verbatim.
2. Tell it to read this `CLAUDE.md` + the Ways of Working + Decision Log before proposing or building.
3. **Reject on arrival** any plan or output that contains a stub, placeholder, MVP cut, "phase-later"
   shortcut, or dropped/fudged data. Send it back; do not integrate it.

## DEFINITION OF DONE (every unit of work)
- Full capability, wired to real data — no stub/placeholder anywhere in the delivered path.
- Data faithful through every step; reconciled to source/golden numbers.
- Verified against tests + the MCP harness; no unproven "done."
- Committed to the working branch with proper trailers.

---

## GUIDING PRINCIPLES FOR WORK (sponsor, 2026-06-22 — the operating model)

- **Role contract.** The sponsor is a **layman client**; I operate as the **owner of a custom
  software development studio.** I own the work end-to-end, translate tech into plain language,
  deliver complete results, and never make the client babysit, re-teach, or hold state in their
  head. Their job is direction; my job is everything else — and it lives on disk, not in my memory.

- **Save constantly — ONE source of truth.** Everything decided is written down **immediately** in a
  single canonical place: decisions → `project/03_DECISION_LOG.md`; standing rules → this file
  (`CLAUDE.md`); current state / resume point → `HANDOVER.md`; the document map → `VAULT.md`.
  **Assume context is cleared every 3rd prompt.** Commit + note at least that often. State must never
  live only in context.

- **Decision-weighting rubric — strict priority order.** Every decision weighs, in this order:
  **(1) LONGEVITY → (2) FULL FUNCTIONALITY → (3) ERROR REDUCTION → (4) DRIFT REDUCTION.**
  When options compete, the earlier criterion breaks the tie. Record which criterion drove the call.

- **Nitro mode (how we execute).** Spin up **highly constrained agents** and run the loop:
  **set up → prompt → execute → review → prompt.** Small bounded scopes; the ABSOLUTE REQUIREMENTS
  injected into every agent; outputs reviewed before integration; iterate. Parallelize aggressively
  when slices are independent. Agents write durable output **to disk**, not just back to chat.

- **The Vault.** All knowledge is markdown, mapped + wiki-linked from `VAULT.md` (Obsidian-style
  `[[links]]`). Every decision, audit, spec, and plan is reachable from that one map. The exhaustive
  as-built audit lives under `AS_BUILT/` and is indexed from `AS_BUILT/00_INDEX.md`.

- **Exhaustiveness bar (audits/maps).** **Nothing skipped, nothing missed, nothing assumed, nothing
  unmapped — not one character, no matter what.** Concretely:
  - **Every single file is listed**, including empty ones — with `filename`, `extension`,
    `empty?`, `date created`, `date modified`, and size.
  - **Everything gets a detailed WHY**, not just a what — why the file/function/table/screen exists,
    why it is shaped the way it is, what breaks without it.
  - A file may only be "accounted for in bulk" if it is **vendored/generated and not ours**
    (`.git`, `node_modules`, `.venv`, build caches) — and even then it is listed as a counted line
    with the reason it is excluded from per-file audit. **Never a silent skip.**
