# reference/ — Isolated quarantine (INPUT ONLY)

This directory is the **clean-room boundary** defined in `docs/adr/ADR-0001-clean-room-reconciliation.md`. It exists so the sponsor's existing repository and real sample files can **inform** this build without **contaminating** it.

## The rule

- **Input only.** Nothing here is ever imported by `backend/` (or `frontend/`). CI enforces this — `backend/tests/test_cleanroom_import.py` fails the build if any `backend/` module imports from `reference/`.
- **The existing repo is never copied in as code.** Per the sponsor's constraint ("the repo is in my github, but i dont want it contaminating this build … keep it isolated"), the old codebase stays in the sponsor's GitHub. If/when isolated read access is granted, a *single dedicated agent* reads it in an isolated git worktree and emits only:
  - `as-built-db/` — the extracted/validated schema + a summary of the Alembic chain (informs `db/baseline/`, not imported).
  - `as-built-digest.md` — a knowledge digest (services, tests, the ECLS content).
- **Sample files arrive on demand.** Squads request specific real artifacts (a kickoff doc, an iTrade pull, a bid workbook, a sign-off deck); the sponsor uploads them; they land in `samples/` **with provenance**.

## Data-classification rule (Security-owned)

Real commercial values (supplier names, prices, awards) are sensitive. Before anything in `samples/` is committed, the Security & Compliance squad classifies it (see `project/squads/security/PLAN.md`). Unclassified real data is **not** committed; `.gitignore` excludes `reference/samples/*` until a file is explicitly classified and allow-listed.

## Layout

```
reference/
├── README.md            # this boundary note
├── as-built-db/         # (on DEP-1 intake) extracted/validated schema + chain summary
├── as-built-digest.md   # (on DEP-1 intake) services / tests / ECLS digest
└── samples/             # (on demand) real artifacts, classified before commit
```

Nothing in this directory is wired into the running system. It is reference material for humans and planning agents only.
