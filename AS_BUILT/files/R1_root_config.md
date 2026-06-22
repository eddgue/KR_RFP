---
doc: AS-BUILT AUDIT — SLICE R1 — repo-root config + dotfiles
id: ASBUILT-R1
slice: R1
status: DONE (audited 2026-06-22)
contract: /CLAUDE.md (ABSOLUTE REQUIREMENTS injected) + /AS_BUILT/AUDIT_STANDARD.md (substance bar)
method: read each file end-to-end; cross-checked against FILE_CENSUS.md rows; every WHY grounded against
        the real referenced artifact (backend/Dockerfile COPY lines, reference/samples/ contents,
        scripts/web_session_start.sh existence, git add-dates). Nothing assumed; nothing skipped.
scope: root dotfiles + config NOT owned by B9/F3/D5 — `.gitignore`, `.dockerignore`, `.gcloudignore`,
       `.editorconfig`, `.mcp.json`, `docker-compose.yml`, `.github/**`, `.claude/**`.
---

# SLICE R1 — Root config + dotfiles (Layer-2 per-file, detailed-WHY)

## Slice enumeration & census cross-ref

`find . -maxdepth 1 -type f` →
`.dockerignore`, `.editorconfig`, `.gcloudignore`, `.gitignore`, `.mcp.json`, `CLAUDE.md`,
`HANDOVER.md`, `README.md`, `VAULT.md`, `WEB_DEPLOYMENT.md`, `docker-compose.yml`.

`find .github .claude -type f` →
`.github/workflows/ci.yml`, `.claude/settings.web.json.sample`.
`find .github .claude -type d` → `.github`, `.github/workflows`, `.claude`, `.claude/worktrees`.

There is **no** `docker-compose*.yml` variant at root other than `docker-compose.yml` (the `infra/`
and `mcp/` copies are separate files in other slices). `.claude/worktrees/` exists but is **empty**.

**R1-OWNED files (8) — audited here, with census rows:**

| Census row | Path | Ext | Bytes | Empty? | Created | Modified |
|---:|---|---|---:|:---:|---|---|
| 1 | `./.claude/settings.web.json.sample` | sample | 883 | n | 2026-06-20 | 2026-06-20 |
| 2 | `./.dockerignore` | (dotfile) | 1353 | n | 2026-06-22 | 2026-06-22 |
| 3 | `./.editorconfig` | (dotfile) | 300 | n | 2026-06-18 | 2026-06-18 |
| 4 | `./.gcloudignore` | (dotfile) | 931 | n | 2026-06-22 | 2026-06-22 |
| 5 | `./.github/workflows/ci.yml` | yml | 9071 | n | 2026-06-18 | 2026-06-20 |
| 6 | `./.gitignore` | (dotfile) | 1214 | n | 2026-06-18 | 2026-06-21 |
| 7 | `./.mcp.json` | (dotfile) | 563 | n | 2026-06-20 | 2026-06-20 |
| 253 | `./docker-compose.yml` | yml | 5556 | n | 2026-06-22 | 2026-06-22 |

(Created/modified per census; git first-add dates corroborate: `.gitignore`/`.editorconfig`/`ci.yml`
added 2026-06-18, `.mcp.json`/`settings.web.json.sample` 2026-06-20, `.dockerignore`/`.gcloudignore`/
`docker-compose.yml` 2026-06-22.)

**Directory (no file): `.claude/worktrees/`** — empty dir, intentionally so. It is the materialization
point for Claude Code's transient per-agent git worktrees. It is git-ignored (`.gitignore` line 54
`.claude/worktrees/`) precisely so those throwaway worktrees never get committed. It exists on disk
(not via `.gitkeep`) only because the tooling created it; auditing-wise it holds nothing. **What breaks
without it:** nothing — Claude Code recreates it on demand. It is listed here so the slice is exhaustive.

**NOT R1-owned (flagged for other slices — see "Ownership notes" at bottom):**
`.mcp.json` (census row 7) is **also** claimed by **D5** in `00_INDEX.md` (D5 scope text: "root `*.md`,
`*.json`, `.mcp.json`"). The R1 row in the index does NOT list `.mcp.json`, but **this task's prompt
explicitly instructs R1 to audit `.mcp.json`**. I audit it here and flag the overlap. Also out of R1
scope: `backend/.dockerignore` (row 18 → B9), `frontend/.dockerignore` (row 264 → F3),
`infra/docker-compose.yml` (row 334 → D5), `mcp/.mcp.json` (row 337 → D5),
`mcp/.claude-plugin/plugin.json` (row 336 → D5).

---

## FILE 1 — `./.gitignore`  (census row 6)

- **path:** `/home/user/KR_RFP/.gitignore`
- **ext:** dotfile (gitignore) · **bytes:** 1214 · **empty?** no · **created:** 2026-06-18 · **modified:** 2026-06-21
- **what:** Git's untracked-file exclusion list for the whole repo. Pattern-grouped into: secrets/env,
  clean-room quarantine, python, node, os/editor, local infra, demo artifacts, Claude worktrees, vault clone, var/screenshots.

### Detailed WHY — every line / block, why it exists, what breaks without it

```
1   # ---- secrets & env (never commit) ----
2   **/.env
3   **/.env.*
4   !**/.env.example
5   *.pem
6   *.key
```
- `**/.env` + `**/.env.*` (lines 2-3): exclude env files at any depth — both the bare `.env` and any
  variant (`.env.local`, `.env.production`). These hold DB URLs, `AUTH_SECRET_KEY`, etc. **Why both:** a
  bare `.env` is not matched by `.env.*` (no suffix), so both globs are needed to cover both shapes.
  **Breaks without it:** real credentials get committed → secret leak.
- `!**/.env.example` (line 4): **re-include** (negation) the committed template. The repo intentionally
  ships `.env.example` files (per `infra/` / docker-compose usage notes: "Copy .env.example -> .env
  first") so a developer knows which vars to set. The earlier `.env.*` glob would otherwise swallow
  `.env.example`; this `!` rescues it. **Order matters:** the negation must come AFTER the broad glob.
  **Breaks without it:** the onboarding template would be ignored and never tracked.
- `*.pem` / `*.key` (lines 5-6): exclude TLS / private-key material anywhere by extension. Defense in
  depth beyond the env globs. **Breaks without it:** a stray private key gets committed.

```
8   # ---- clean-room quarantine: real sample data not committed until classified (ADR-0001, Security) ----
9   reference/samples/*
10  !reference/samples/.gitkeep
11  !reference/samples/README.md
```
- `reference/samples/*` (line 9): **THE KEY CLEAN-ROOM RULE.** It ignores **everything** inside
  `reference/samples/` (real customer/legacy spreadsheets — bid_*.xlsx/.xlsb, itrade_*, potato_*,
  tomato_*, kickoff docs, etc.; verified present, ~55MB of real `.xlsx`/`.xlsb`/`.docx`/`.html`). Per
  ADR-0001 (clean-room) + Security, this **real sample data is quarantined**: not committed to git until
  it has been classified/cleared. **Why `*` (contents) not the dir:** so the directory can still hold
  its two committed marker files (next two lines). **Breaks without it:** unclassified real third-party
  pricing data lands in version control — the exact thing the clean-room boundary forbids. *(This is the
  rule the prompt asks about: "why `.gitignore` has `reference/samples/*`".)*
- `!reference/samples/.gitkeep` (line 10): re-include the empty keep-marker (verified: 0 bytes) so the
  otherwise-ignored directory still exists in a fresh clone. **Breaks without it:** the dir vanishes on
  clone and the COPY/seed paths that expect `reference/samples/` to exist have nowhere to land a sample.
- `!reference/samples/README.md` (line 11): re-include the committed README that documents what the
  quarantine is and how to drop samples in. **Breaks without it:** the only committed explanation of the
  quarantine folder would itself be ignored.
- **CRITICAL DOWNSTREAM CONSEQUENCE (the seed/build trap):** because line 9 ignores *everything* under
  `reference/samples/`, it **also** ignores `reference/samples/potato_2026_rfp_input.xlsx` — the one file
  the backend image COPYs for the deploy seed. There is **no** `!`-re-include for it here (it is
  deliberately kept out of git as quarantined real data). That omission is exactly what forces
  `.gcloudignore` to exist (see FILE 4): Cloud Build falls back to `.gitignore` and would strip that
  file, breaking the image build. So this single ignore rule is the root cause of the `.gcloudignore`
  potato re-include. The file is present on disk (verified: 394799 bytes) but untracked.

```
13  # ---- python (backend) ----
14  __pycache__/ … 25  *.egg-info/
```
- Standard Python build/runtime detritus: bytecode (`__pycache__/`, `*.py[cod]` = .pyc/.pyo/.pyd),
  virtualenvs (`.venv/`, `venv/`), tool caches (`.mypy_cache/`, `.ruff_cache/`, `.pytest_cache/`),
  coverage (`.coverage`, `htmlcov/`), and packaging output (`dist/`, `build/`, `*.egg-info/`).
  **Breaks without it:** machine-specific caches/venvs/coverage churn the diff and bloat the repo;
  `.mypy_cache/` and `.ruff_cache/` actually exist at root (seen in `ls -la`) — proof these rules are live.

```
27  # ---- node (frontend) ----
28  node_modules/ … 34  .pnpm-debug.log*
```
- Frontend dependency tree (`node_modules/`), Next build output (`.next/`, `out/`), TS incremental
  cache (`*.tsbuildinfo`), and package-manager debug logs (npm/yarn/pnpm). **Breaks without it:** the
  huge `node_modules` tree and generated build artifacts get committed.

```
36  # ---- os / editor ----
37  .DS_Store … 41  .vscode/
```
- OS cruft (`.DS_Store` macOS, `Thumbs.db` Windows), vim swap (`*.swp`), and IDE folders (`.idea/`
  JetBrains, `.vscode/`). **Breaks without it:** per-developer OS/editor noise pollutes the repo.

```
43  # ---- local infra ----
44  infra/postgres/data/
45  *.local
```
- `infra/postgres/data/` — the local Postgres data directory mounted by the `infra/` dev stack; raw
  DB files must never be committed. `*.local` — any `*.local` override file. **Breaks without it:** a
  multi-GB database volume and local-only override files get tracked.

```
47  # clean-room: v3 engine read as reference, logic lifted into our own code, raw never committed (ADR-0001)
48  reference/v3-engine/
```
- Ignores the entire legacy v3 engine source tree. Per ADR-0001 clean-room: the team **read** the v3
  engine as reference and re-implemented the logic in their own code, but the **raw third-party source
  is never committed**. **Breaks without it:** the clean-room import boundary is violated at the VCS
  level (and the `reference-guard` CI job exists precisely to enforce no `backend/` → `reference/` import).

```
50  # generated demo artifacts (regenerated each run; synthetic)
51  backend/demo/output/
```
- Demo outputs are regenerated each run and are synthetic; committing them is churn. **Breaks without
  it:** stale generated demo files drift in the repo. (Aligns with ABSOLUTE REQ #4: no server-side file
  storage — generated artifacts are transient.)

```
53  # ---- claude code transient agent worktrees (auto-cleaned; never commit) ----
54  .claude/worktrees/
55  .claude/settings.local.json
```
- `.claude/worktrees/` — the transient per-agent git worktrees (the empty dir audited above);
  auto-cleaned, never committed. `.claude/settings.local.json` — a developer's **local** Claude Code
  settings override (vs the committed `.sample`). **Breaks without it:** throwaway worktrees and
  machine-local settings get committed; local secrets/paths in `settings.local.json` could leak.

```
57  # Option (b) vault clone target (web session-start); never commit the vault into this repo
58  .rfp_pilot_vault/
```
- The MCP harness "file-vault" clone target used by the web SessionStart flow (the second runtime —
  the MCP file-vault, distinct from the stateless console DB). It is cloned into the session container,
  not committed into THIS repo. **Breaks without it:** the vault clone (run snapshots etc.) would be
  committed into the app repo, conflating the two runtimes.

```
60  # generated/demo artifacts from local screenshot + seed runs (synthetic; never commit)
61  var/
62  screenshots/
```
- `var/` (run vault notes, design snapshots, demo outputs — its own audit slice D6) and `screenshots/`
  (local screenshot runs) are generated/synthetic. **Breaks without it:** generated artifacts churn the
  repo. (Both dirs exist at root — verified in `ls -la`.)

- **gotcha:** the three `!` negations (lines 4, 10, 11) only work because they follow their broad globs;
  reordering would silently break the re-includes. The `reference/samples/*` rule deliberately does NOT
  re-include the potato file — that is by design (quarantine) and is compensated by `.gcloudignore`.
- **dependencies / cross-refs:** ADR-0001 (clean-room), Security; consumed-by `.gcloudignore`
  (`#!include:.gitignore`); referenced-by `.dockerignore` (which mirrors several of these).

---

## FILE 2 — `./.dockerignore`  (census row 2)

- **path:** `/home/user/KR_RFP/.dockerignore`
- **ext:** dotfile · **bytes:** 1353 · **empty?** no · **created/modified:** 2026-06-22
- **what:** The build-context exclusion list for the **root** Docker build context. The backend image
  (`backend/Dockerfile`) builds **from the repo root** (it needs `backend/` AND `db/baseline/schema.sql`
  in their real relative layout). This file keeps that context lean.

### Detailed WHY — header + every exclude (why excluded)

```
1-4  header: backend image builds from REPO ROOT (needs backend/ + db/baseline/schema.sql in real
     relative layout; see backend/Dockerfile). Keep context lean; Dockerfile COPYs only what it needs
     (backend/, db/, deploy/gcp/seed.py, one reference sample), so a broad allow-list is safe.
```
- **WHY root context (the load-bearing design fact):** `backend/Dockerfile` COPYs
  `db/baseline/schema.sql` to `/db/baseline/schema.sql` because alembic migration `0001_baseline.py`
  reads `<repo-root>/db/baseline/schema.sql` (verified: Dockerfile lines 9-11, 32). It also COPYs
  `deploy/gcp/seed.py` (line 41) and `reference/samples/potato_2026_rfp_input.xlsx` (line 47). A
  `backend/`-only context could not reach `db/`, `deploy/`, or `reference/` — hence root context, hence
  this root-level `.dockerignore` to trim everything else.

```
6-15  Python / build noise: **/.venv, **/venv, **/__pycache__, **/*.pyc, **/.pytest_cache,
      **/.mypy_cache, **/.ruff_cache, **/.coverage, **/*.egg-info
```
- Excludes Python caches/venvs/coverage from the build context at any depth. **Breaks without it:** a
  developer's local `.venv` (hundreds of MB) gets sent to the Docker daemon, slowing every build and
  potentially baking host artifacts into a layer.

```
17-20 Node / frontend: frontend/node_modules, frontend/.next, frontend/out
```
- The **frontend has its own image + build context** (`docker-compose.yml` builds `frontend` with
  `context: ./frontend`), so none of its node/build artifacts are ever needed in the BACKEND image.
  Excluding them keeps the root context small. **Breaks without it:** `frontend/node_modules` (massive)
  bloats the backend build context for no reason.

```
22-25 Secrets / env: **/.env, **/.env.*, !**/.env.example
```
- Mirrors `.gitignore`: never ship real env files into a build layer; re-include the `.env.example`
  template (same negation-after-glob pattern). **Breaks without it:** secrets could be copied into the
  image via a broad COPY.

```
27-30 VCS + editor: .git, .gitignore, **/.DS_Store
```
- Exclude the `.git` directory (large, never needed in an image), `.gitignore` itself, and macOS cruft.
  **Breaks without it:** the entire git history ships in the build context.

```
32-48 Large data dirs not needed by the backend image:
      reference/samples/_allocation_models, reference/samples/*.docx, *.html, itrade_*, bid_*,
      var, screenshots, audit, mcp, specs, docs, project, docker-compose*.yml
```
- **THE KEY .dockerignore DESIGN (the prompt's "why .dockerignore excludes what it does"):** `reference/`
  is 150MB+. The backend Dockerfile COPYs **only the single 0.4MB potato sample**
  (`reference/samples/potato_2026_rfp_input.xlsx`, verified line 47). So this block ignores the *rest* of
  the heavy reference samples **selectively by pattern** — `_allocation_models` dir, all `.docx`/`.html`,
  `itrade_*` (the 22MB iTrade workbook), and `bid_*` (the ~2MB-each bid workbooks). It does **NOT**
  blanket-ignore `reference/samples/` because that would also strip the one potato file the COPY needs.
  The header note (lines 32-35) explicitly calls this out: "a later COPY can still reach an ignored path
  only if re-included; we instead keep the one needed file out of these globs." i.e. the design choice is
  to **enumerate the unwanted samples** rather than ignore-all-then-reinclude, guaranteeing the COPY at
  Dockerfile:47 always resolves.
- `var`, `screenshots`, `audit`, `mcp`, `specs`, `docs`, `project` — documentation/tooling/snapshot trees
  the backend image never needs; excluded to keep the context lean. **Breaks without it:** big doc and
  snapshot trees inflate the build context and slow uploads to the daemon/Cloud Build.
- `docker-compose*.yml` — compose files are orchestration, never part of an image; excluded.
- **gotcha:** the potato sample survives BOTH `.dockerignore` (enumerated-exclude approach leaves it in)
  AND must survive Cloud Build (handled by `.gcloudignore`). Two different mechanisms, same goal.
- **dependencies / cross-refs:** `backend/Dockerfile` (COPY targets), `.gitignore` (mirrored env block),
  `.gcloudignore` (the Cloud-Build-side companion). Note `backend/.dockerignore` (row 18, B9) and
  `frontend/.dockerignore` (row 264, F3) are **separate** context files for those sub-builds — not R1.

---

## FILE 3 — `./.gcloudignore`  (census row 4)

- **path:** `/home/user/KR_RFP/.gcloudignore`
- **ext:** dotfile · **bytes:** 931 · **empty?** no · **created/modified:** 2026-06-22
- **what:** Upload filter for `gcloud builds submit` (invoked by `deploy/gcp/deploy.sh`). Controls what
  gets uploaded to Cloud Build as the build context.

### Detailed WHY — the potato re-include (the prompt's headline question)

```
1-10  header: WHY THIS FILE EXISTS — without a .gcloudignore, gcloud falls back to .gitignore to decide
      what to upload. .gitignore excludes reference/samples/*, stripping the one potato sample the
      backend image COPYs for the deploy seed (reference/samples/potato_2026_rfp_input.xlsx) even though
      it's committed... and the build then FAILS at that COPY step. So: import .gitignore for the usual
      noise, then RE-INCLUDE that single sample so it reaches the build context. .dockerignore still
      trims the rest of reference/ out of the actual image layer (only this one file is COPYd in).
12    .git
13    .gcloudignore
14
15    #!include:.gitignore
16
17    # Re-include the single sample the backend image needs (overrides reference/samples/* above).
18    !reference/samples/potato_2026_rfp_input.xlsx
```
- **WHY `.gcloudignore` EXISTS AT ALL / WHY IT RE-INCLUDES THE POTATO SAMPLE (definitive):** `gcloud
  builds submit` has a fallback rule — **if no `.gcloudignore` is present, it uses `.gitignore`** to
  decide what to upload to Cloud Build. But `.gitignore` line 9 (`reference/samples/*`) ignores
  *everything* under `reference/samples/`, INCLUDING `potato_2026_rfp_input.xlsx`. That file is **not
  committed** (it's quarantined real data) but it **is present on disk** (verified: 394799 bytes) and the
  backend Dockerfile **requires** it at COPY (line 47: `COPY reference/samples/potato_2026_rfp_input.xlsx
  /reference/samples/potato_2026_rfp_input.xlsx`). If gcloud used `.gitignore`, that file would be
  stripped from the upload and the image build would FAIL at the COPY step. So `.gcloudignore`:
  1. `.git` / `.gcloudignore` (lines 12-13): never upload the git dir or this filter file itself.
  2. `#!include:.gitignore` (line 15): pull in ALL of `.gitignore`'s rules (so `.venv`, `__pycache__`,
     `node_modules`, `var/`, screenshots, the rest of `reference/samples/*`, etc. stay excluded — no
     duplication of the noise list).
  3. `!reference/samples/potato_2026_rfp_input.xlsx` (line 18): a single **negation that OVERRIDES** the
     included `reference/samples/*` rule, re-including ONLY the potato file so it reaches the Cloud Build
     context and the Dockerfile COPY succeeds.
- **The two-layer separation (why this doesn't bloat the image):** `.gcloudignore` only governs what is
  **uploaded to Cloud Build**. `.dockerignore` still governs the **image build context** and trims the
  rest of `reference/`. So the potato file rides up to Cloud Build, gets COPYd into the image, and the
  other 150MB of reference data never enters either the upload or the layer. The comment at line 10
  spells this out exactly.
- **What breaks without this file:** `gcloud builds submit` falls back to `.gitignore`, the potato file
  is excluded from the upload, and `docker build` fails at Dockerfile:47 (`COPY` of a missing file) →
  the entire Cloud Build / deploy is broken. (Note: Dockerfile:43-46 says the seed *skips the POTATO
  cycle gracefully* if the file is absent at runtime — but a missing-file COPY at BUILD time is a hard
  build failure, not a graceful skip; hence this file is mandatory.)
- **dependencies / cross-refs:** `deploy/gcp/deploy.sh` (invokes `gcloud builds submit`),
  `.gitignore` (included verbatim), `backend/Dockerfile:47` (the COPY that needs the file),
  `deploy/gcp/seed.py` + `scripts/potato_legacy_dryrun.py` (runtime consumers of the sample).

---

## FILE 4 — `./.editorconfig`  (census row 3)

- **path:** `/home/user/KR_RFP/.editorconfig`
- **ext:** dotfile · **bytes:** 300 · **empty?** no · **created/modified:** 2026-06-18
- **what:** Cross-editor formatting baseline (EditorConfig spec) so all editors agree on charset, line
  endings, final newline, trailing-whitespace, and indentation before linters run.

### Detailed WHY — every stanza

```
1  root = true
```
- Marks this the top-most EditorConfig; editors stop searching parent dirs. **Breaks without it:** an
  EditorConfig higher up the filesystem could leak rules into the repo.

```
3-8  [*]: charset=utf-8, end_of_line=lf, insert_final_newline=true, trim_trailing_whitespace=true,
     indent_style=space
```
- Universal defaults for **all** files: UTF-8, **LF** line endings (so Windows checkouts don't introduce
  CRLF that would churn diffs / break shell scripts), a trailing newline (POSIX text-file convention,
  keeps `ruff format`/git happy), trimmed trailing whitespace, and space indentation. **Breaks without
  it:** mixed line-endings and whitespace noise across a cross-platform team; the `ruff format --check`
  CI job (ci.yml step) would start failing on whitespace it expects normalized.

```
10-12 [*.py]: indent_size=4, max_line_length=100
```
- Python: PEP-8 4-space indent and a 100-col line length. The 100 must agree with ruff's config in
  `backend/pyproject.toml` (the `lint` CI job runs `ruff format --check`). **Breaks without it:** editors
  reflow Python differently from ruff → format-check churn/failures.

```
14-15 [*.{ts,tsx,js,jsx,json,yml,yaml}]: indent_size=2
```
- 2-space indent for the JS/TS/JSON/YAML family (the frontend + workflow/config convention). **Breaks
  without it:** inconsistent 2-vs-4 indentation in frontend and YAML files.

```
17-18 [*.md]: trim_trailing_whitespace = false
```
- **Override** the global trim for Markdown — because Markdown uses **two trailing spaces** as a hard
  line break. Trimming them would silently change rendered output. **Breaks without it:** intentional
  Markdown line breaks get stripped on save. (Note: this mirrors AUDIT_STANDARD/CLAUDE conventions where
  docs are markdown-heavy.)

```
20-21 [Makefile]: indent_style = tab
```
- Makefiles **require** literal tabs for recipe lines (a hard `make` rule). Overrides the global
  `indent_style=space`. **Breaks without it:** an editor inserts spaces and `make` fails with
  "missing separator." (Defensive even if no root Makefile is currently present — protects any added later.)

- **gotcha:** the 100-col and indent rules are only meaningful if ruff/prettier agree; EditorConfig is
  advisory (editor-enforced), the CI linters are authoritative.
- **ownership note:** could be argued to overlap F3 (frontend formatting), but it is a **repo-root,
  language-spanning** config (covers `.py` for backend too), so it correctly lives in R1.

---

## FILE 5 — `./.mcp.json`  (census row 7)

- **path:** `/home/user/KR_RFP/.mcp.json`
- **ext:** dotfile (JSON) · **bytes:** 563 · **empty?** no · **created/modified:** 2026-06-20
- **what:** Repo-root MCP-server registration read by **Claude Code on the web** (cloud runtime). It
  points Claude at the `rfp-pilot` MCP server.

### Detailed WHY + what MCP server it points at (the prompt's question)

```json
{
  "//": "...web runtime does NOT spawn stdio MCP servers, so the rfp-pilot server runs as a LOCAL HTTP
         server inside the session container (started by the SessionStart hook, scripts/web_session_start.sh)
         and is reached here over loopback. For LOCAL terminal use, register the stdio server instead via
         mcp/.mcp.json (the plugin) or `claude mcp add` — see mcp/README.md.",
  "mcpServers": {
    "rfp-pilot": { "type": "http", "url": "http://127.0.0.1:8765/mcp" }
  }
}
```
- **What MCP server it points at:** the **`rfp-pilot`** MCP server — the live-run verification *oracle*
  (the MCP harness / file-vault runtime referenced in CLAUDE.md ABSOLUTE REQ #5). Here it is registered
  as **`type: http`** at **`http://127.0.0.1:8765/mcp`** (loopback, port 8765, path `/mcp`).
- **WHY HTTP over loopback (not stdio):** Claude Code on the **web/cloud runtime does NOT spawn stdio MCP
  servers**. So instead of a stdio child process, the `rfp-pilot` server is started as a **local HTTP
  server inside the session container** by the SessionStart hook (`scripts/web_session_start.sh` —
  verified present, executable, 7812 bytes), and Claude reaches it over loopback `127.0.0.1:8765`. The
  `"//"` key is a JSON-comment convention (ignored by the parser) carrying this rationale inline.
- **WHY this file vs `mcp/.mcp.json`:** this root file is the **web/cloud** registration (HTTP). For
  **local terminal** use you instead register the **stdio** server via `mcp/.mcp.json` (the plugin) or
  `claude mcp add` (per `mcp/README.md`). Two registrations for two runtimes; this one is web-only.
- **what breaks without it:** on the web runtime Claude Code has no MCP server registered → the
  verification oracle (the MCP harness used to prove runs are correct) is unreachable in web sessions →
  the "verify before actioning" contract can't be honored there.
- **dependencies / cross-refs:** `scripts/web_session_start.sh` (starts the HTTP server on :8765),
  `.claude/settings.web.json.sample` (the hook that runs that script), `WEB_DEPLOYMENT.md`,
  `mcp/.mcp.json` + `mcp/README.md` (the local/stdio counterpart, owned by D5).
- **OWNERSHIP FLAG:** `00_INDEX.md` lists `.mcp.json` under **D5** ("root `*.md`, `*.json`, `.mcp.json`"),
  NOT under R1's path list. This task's prompt explicitly told R1 to audit it, so it is audited here.
  **Recommend D5 cross-reference this entry rather than re-auditing, to avoid a duplicate / conflicting
  audit of the same file.**

---

## FILE 6 — `./.claude/settings.web.json.sample`  (census row 1)

- **path:** `/home/user/KR_RFP/.claude/settings.web.json.sample`
- **ext:** sample (JSON template) · **bytes:** 883 · **empty?** no · **created/modified:** 2026-06-20
- **what:** A **sample** Claude Code settings file. Copy it to `.claude/settings.json` (in the web repo
  clone) to wire the SessionStart hook that boots the local stack the web runtime needs.

### Detailed WHY — why it's a SAMPLE, what the hook does

```json
{
  "//": "SAMPLE — copy this to .claude/settings.json ... It is a SAMPLE, not active config, on purpose:
         installing a hook that runs on every session is an action you should take deliberately. When
         applied, the hook runs scripts/web_session_start.sh at the start of each session to start
         Postgres, rehydrate each run's isolated DB from its vault snapshot (D34), and start the HTTP
         MCP server that .mcp.json points at. The script is a no-op outside the web runtime
         (CLAUDE_CODE_REMOTE != true), so local terminal sessions are unaffected. See WEB_DEPLOYMENT.md.",
  "hooks": {
    "SessionStart": [
      { "matcher": "startup|resume",
        "hooks": [ { "type": "command",
                     "command": "bash \"$CLAUDE_PROJECT_DIR/scripts/web_session_start.sh\"" } ] }
    ]
  }
}
```
- **WHY a `.sample` and not the live `settings.json`:** installing a hook that fires on **every**
  session is a deliberate, security-relevant action (it auto-runs a script). Shipping it as an inert
  template forces an explicit opt-in (copy → `settings.json`). Note `.gitignore` line 55 ignores
  `.claude/settings.local.json` and the active `settings.json` is not committed — so the `.sample` is the
  only committed, reviewable record of what the hook does. **Breaks without it:** no committed, auditable
  description of the web SessionStart wiring; each user would have to reconstruct the hook by hand.
- **What the hook does (when applied):** `SessionStart` with `matcher: "startup|resume"` runs the command
  hook `bash "$CLAUDE_PROJECT_DIR/scripts/web_session_start.sh"` at the start of each web session. That
  script (verified present): (1) starts **Postgres**, (2) **rehydrates each run's isolated DB from its
  vault snapshot** (decision **D34** — per-run DB isolation), and (3) starts the **HTTP MCP server** on
  loopback that `.mcp.json` registers. It is a **no-op outside the web runtime** (guarded on
  `CLAUDE_CODE_REMOTE != true`), so local terminal sessions are untouched.
- **dependencies / cross-refs:** `scripts/web_session_start.sh`, `.mcp.json` (the HTTP server this hook
  starts), `WEB_DEPLOYMENT.md`, decision D34 (per-run DB rehydration). Lives under `.claude/` (R1-owned).

---

## FILE 7 — `./docker-compose.yml`  (census row 253)

- **path:** `/home/user/KR_RFP/docker-compose.yml`
- **ext:** yml · **bytes:** 5556 · **empty?** no · **created/modified:** 2026-06-22
- **what:** Full-stack **LOCAL** verification of the **Cloud Run deployment shape** — postgres + backend
  + frontend wired the way the two Cloud Run services will be, but on one machine. The de-risk harness
  for `deploy/gcp/`. Compose project name: `kr-rfp` (line 12).
- **header WHY (lines 1-11):** build both images, bring the stack up, confirm green
  (postgres healthy → migrations applied → backend `/ready` → frontend HTML → seed runs). Documents the
  three commands: `up --build -d`, `run --rm seed`, `down -v`. Explicitly a **DEV convenience**: the DB
  password is a well-known local default and `AUTH_COOKIE_SECURE` is off (plain http on localhost); Cloud
  Run uses Secret Manager + HTTPS (see `deploy/gcp/README.md`).

### Per-service — every service, port, healthcheck, depends_on + WHY

**`db` (lines 16-31)** — Postgres, the governed system of record.
- image `postgres:15` (pinned — matches CI's `postgres:15` service and prod).
- env: `POSTGRES_USER/PASSWORD/DB` all default to `kr_rfp` (well-known local defaults).
- **port `5432:5432`** — exposes Postgres to the host for local inspection.
- volume `db_data:/var/lib/postgresql/data` — persists DB across restarts (named volume, line 132-133).
- **healthcheck:** `pg_isready -U $POSTGRES_USER -d $POSTGRES_DB`, interval 5s / timeout 5s / retries 12
  / start_period 10s. **WHY:** downstream services gate on `service_healthy`, so the DB must report ready
  before migrate/backend/seed start. **Breaks without it:** migrations race a not-yet-accepting Postgres.

**`migrate` (lines 36-49)** — one-shot `alembic upgrade head`, gated on a healthy DB, runs before the API serves.
- build: **`context: .` (repo root)**, `dockerfile: backend/Dockerfile`. **WHY root context:** the image
  needs `db/baseline/schema.sql` alongside `backend/` in real relative layout because alembic 0001 reads
  `<repo-root>/db/baseline/schema.sql` (lines 38-39 say exactly this; corroborated by Dockerfile:9-11).
- command `["alembic","upgrade","head"]`.
- env: `DATABASE_URL` (default `postgresql+psycopg://kr_rfp:kr_rfp@db:5432/kr_rfp` — note host `db`, the
  compose service name), `ENV=local`.
- depends_on `db: service_healthy`. `restart: "no"` — it's a job: run to completion and exit.
- **WHY decoupled:** Cloud Run runs migrations as a separate job too; the backend waits for this via
  `service_completed_successfully`. **Breaks without it:** the API could serve against an unmigrated DB.
- (No port / no healthcheck — correct for a run-to-exit job.)

**`backend` (lines 52-83)** — FastAPI on uvicorn, binds `0.0.0.0:8000`.
- build: root context + `backend/Dockerfile` (same reason as migrate).
- env: `DATABASE_URL` (same default), `ENV=local`,
  `CORS_ALLOW_ORIGINS` default `http://localhost:3000` — **WHY:** the frontend is a separate origin and
  sends the session cookie cross-origin, so credentialed CORS must allow its EXACT origin (cloud = the
  deployed frontend URL).
  `AUTH_COOKIE_SECURE` default `false` — **WHY:** on plain-http localhost a Secure cookie is silently
  dropped, so login would "succeed" with no session; Cloud Run is HTTPS so the prod default stays `true`.
  `AUTH_SECRET_KEY` default `dev-insecure-local-compose-secret` — throwaway local; Cloud Run sources it
  from Secret Manager. `PORT=8000`.
- depends_on: `db: service_healthy` AND `migrate: service_completed_successfully` — **WHY:** serve only
  after the DB is up and migrations have fully applied.
- **port `8000:8000`**.
- **healthcheck:** runs **python** (no curl in the image) to GET `http://localhost:8000/api/v1/ready` and
  exit 0 only on HTTP 200 — the readiness probe (DB reachable). interval 5s / timeout 5s / retries 12 /
  start_period 15s. **WHY:** frontend and seed gate on backend health; `/ready` confirms DB reachability,
  not just process-up. **Breaks without it:** frontend starts against a not-yet-ready API.

**`frontend` (lines 86-108)** — Next standalone server.
- build: **`context: ./frontend`** (its OWN context — note: this is why `.dockerignore` excludes
  `frontend/node_modules` from the *root* context; the frontend builds separately), `dockerfile: Dockerfile`.
- build **arg** `NEXT_PUBLIC_API_BASE_URL` default `http://localhost:8000` — **WHY:** `NEXT_PUBLIC_*` is
  **inlined at build time**, and the **browser** talks to the backend on the **HOST** (`localhost:8000`),
  NOT the compose-internal `backend` name, because the browser runs **outside** the compose network. This
  is a subtle but load-bearing distinction (build-time inline + host-vs-network-name).
- env `PORT=3000`.
- depends_on `backend: service_healthy`.
- **port `3000:3000`**.
- **healthcheck:** runs **node** (`require('http').get('http://localhost:3000/login', ...)`) and exits 0
  if status < 500. interval 5s / timeout 5s / retries 12 / start_period 15s. **WHY:** confirm the Next
  server actually serves the `/login` route, not just that the process booted. **Breaks without it:** the
  stack reports green while the frontend is still compiling/unserveable.

**`seed` (lines 112-130)** — admin user + TOMATO synthetic cycle + POTATO real-data cycle, run on demand.
- build: root context + `backend/Dockerfile` (reuses the backend image/DB).
- command `["python","/app/deploy/gcp/seed.py"]` — **WHY `/app/deploy/gcp/seed.py`:** the Dockerfile
  COPYs `deploy/gcp/seed.py` to that path (Dockerfile:41) and it adds `backend/` to `sys.path` itself.
  The POTATO half reads the potato sample shipped at `/reference/samples/...` (Dockerfile:47) — the very
  file the `.gcloudignore`/`.dockerignore` dance preserves.
- env: `DATABASE_URL`, `ENV=local`, `SEED_ADMIN_PASSWORD` default `admin-local-dev-pw`.
- depends_on: `db: service_healthy` + `migrate: service_completed_successfully`.
- `restart: "no"` + **`profiles: [seed]`** — **WHY:** seed is a JOB, not a long-running service, so it is
  kept OUT of plain `up`; you start it explicitly (`docker compose run --rm seed` or `--profile seed up
  seed`). **Breaks without the profile:** `up` would try to run the seed every time and it'd appear as a
  failed/exited "service."
- (No port / no healthcheck — correct for a job.)

**`volumes` (lines 132-133):** `db_data` — the named volume backing Postgres; `down -v` wipes it.

- **gotchas:** (1) DB host is the service name `db` *inside* the compose network but `localhost` from the
  host/browser — the backend uses `db`, the frontend build-arg uses `localhost:8000`. (2) Every long-lived
  service has a healthcheck; the two jobs (migrate, seed) deliberately have none and `restart: "no"`.
  (3) All three services that need the image build from **root context** — only `frontend` builds from
  `./frontend`; this asymmetry is the reason the root `.dockerignore` exists and is shaped as it is.
- **dependencies / cross-refs:** `backend/Dockerfile`, `frontend/Dockerfile`, `db/baseline/schema.sql`
  (via alembic 0001), `deploy/gcp/seed.py`, `deploy/gcp/README.md`, `reference/samples/potato_2026_rfp_input.xlsx`.
  Distinct from `infra/docker-compose.yml` (row 334, D5 — the Phase-0 dev store with adminer, no frontend)
  which is a **different** compose file for a different purpose.

---

## FILE 8 — `./.github/workflows/ci.yml`  (census row 5)

- **path:** `/home/user/KR_RFP/.github/workflows/ci.yml`
- **ext:** yml · **bytes:** 9071 · **empty?** no · **created:** 2026-06-18 · **modified:** 2026-06-20
- **what:** The single CI workflow (`name: ci`). The program's non-negotiables encoded as gates.
  Independent jobs run in parallel and fan into one required `ci-pass` status — the only check branch
  protection needs to require.

### Triggers, env, concurrency (lines 11-25) + WHY
- **`on` (11-15):** `pull_request` to `main` (the full gate on every PR) and `push` to `main` (the gate
  PLUS the future build-push/deploy-to-staging continuation, pending DEP-4). **WHY:** PRs are gated
  before merge; main pushes will additionally deploy once cloud/IdP resolves.
- **`env` (17-20):** `PYTHON_VERSION=3.12`, `NODE_VERSION=20` — pinned to the backend skeleton + ADR-0002.
  **WHY centralize:** every job references `${{ env.* }}` so the toolchain versions are set once.
- **`concurrency` (22-25):** `group: ci-${{ github.ref }}`, `cancel-in-progress: true` — cancel superseded
  runs on the same ref to save Actions minutes. **WHY:** rapid pushes don't pile up redundant runs.

### Every job — trigger context, every step, and WHY

**Job 1 `lint` (29-42)** — ruff format + lint. Fast, no DB.
- steps: checkout@v4 → setup-python@v5 (3.12, `cache: pip`) → `pip install -e "backend/[dev]"` →
  `ruff check backend/` → `ruff format --check backend/`.
- **WHY:** style/lint gate; no DB needed so it's the fastest signal. `ruff format --check` (non-mutating)
  pairs with `.editorconfig`'s 100-col/whitespace rules. **Breaks the build if:** lint or format drift.

**Job 2 `types` (45-59)** — mypy on the `app` package. No DB.
- steps: checkout → setup-python (cache pip) → install dev extras → `mypy app` **with
  `working-directory: backend`**.
- **WHY working-directory: backend:** mypy must run from `backend/` to pick up its config (pydantic
  plugin + 3rd-party import overrides in `backend/pyproject.toml`); from repo root that config isn't
  found. **Breaks the build if:** a type error in `app`.

**Job 3 `reference-guard` (63-76)** — the clean-room invariant (ADR-0001).
- steps: checkout → setup-python → install dev extras → `pytest tests/test_cleanroom_import.py -v`
  (`working-directory: backend`).
- **WHY:** asserts `backend/` does NOT import from `reference/` — a **program non-negotiable**, not a
  lint nicety (mirrors `.gitignore`/`.dockerignore` keeping `reference/` out). The test FAILS the build
  if the boundary is crossed. **Breaks the build if:** any `backend → reference` import appears.

**Job 4 `test` (79-112)** — full pytest against a **real Postgres 15** service container.
- `services.postgres`: `postgres:15`, env `postgres/postgres/kr_rfp`, port `5432:5432`, health-cmd
  `pg_isready -U postgres -d kr_rfp` (interval 5s / timeout 5s / retries 10).
- job env `DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/kr_rfp` — **WHY same
  variable NAME everywhere (DevOps PLAN §2):** only host/creds differ between CI/compose/cloud.
- steps: checkout → setup-python (cache pip) → install dev extras →
  **`alembic upgrade head`** (working-dir backend; the comment notes this executes
  `db/baseline/schema.sql`) → **`pytest -v -m "" --cov=app --cov-report=term-missing`** (working-dir backend).
- **WHY `-m ""`:** runs ALL markers **including integration** — there is NO SQLite anywhere (architecture
  §7, R8); tests must hit real Postgres. **Breaks the build if:** any test fails or migrations don't apply.

**Job 5 `migration-roundtrip` (118-150)** — WAYS-OF-WORKING §3, on a fresh Postgres.
- same `postgres:15` service block as job 4.
- steps: checkout → setup-python → install → `alembic upgrade head` →
  `pytest tests/test_migrations_roundtrip.py -v` (working-dir backend).
- **WHY:** the test drives `downgrade base → upgrade head` (up→down→up) and asserts the schema is
  clean/unchanged. The header note (114-117) records that the byte-identical dump compare, `alembic
  check` drift, and the **≥46-composite-FK floor** are asserted INSIDE that test as the full DDL lands at
  M0 (Platform & Data PLAN §2 / R-PD2). **Breaks the build if:** a migration isn't reversible or drifts
  the schema. (The 46 composite-identity FKs tie to AUDIT_STANDARD's Layer-1 "all 46 composite-identity keys".)

**Job 6 `frontend-build` (155-180)** — path-filtered; install + typecheck only (this phase, ADR-0002).
- steps: checkout → **`dorny/paths-filter@v3`** (id `changes`, filter `frontend: ['frontend/**']`) →
  setup-node@v4 (Node 20) **`if: steps.changes.outputs.frontend == 'true'`** → `npm install`
  (working-dir frontend, `if` frontend changed) → `npm run typecheck` (working-dir frontend, `if`
  frontend changed).
- **WHY path-filter:** keeps the job a no-op (and green) on PRs that don't touch `frontend/`, saving
  minutes. **WHY `npm install` not `npm ci`, no npm cache:** no lockfile committed yet in this phase;
  `npm ci` + cache + `next build` + the generated-OpenAPI-client check all turn on at **Phase F** once
  `package-lock.json` is committed. **Breaks the build if:** frontend typecheck fails (when frontend changed).

**Job 7 `ci-pass` (183-209)** — the single required status for branch protection.
- `if: always()`, `needs: [lint, types, reference-guard, test, migration-roundtrip, frontend-build]`.
- step: echoes each job result, then loops over the FIVE required results (lint, types, reference-guard,
  test, migration-roundtrip) and `exit 1` if any `!= success`; then separately allows `frontend-build` to
  be EITHER `success` OR `skipped` (the path-filter no-op case), failing only on a real `frontend-build`
  failure; finally prints `ci-pass: green`.
- **WHY:** branch protection requires exactly ONE check (`ci-pass`) instead of six; `if: always()` means
  it runs even if a needed job failed, so it can deterministically report red. **WHY the skipped
  exception:** a path-filtered `frontend-build` legitimately reports `skipped` and must NOT fail the gate.
  **Breaks the build if:** any of the five required jobs is non-success, or frontend-build is an actual failure.

### Commented main-only continuation (211-223) — WHY it's text not code
- Documents the **future** push-to-main pipeline: `build-push` (build backend image, immutable `:<sha>` +
  `:main` tags, push to registry; `needs: [ci-pass]`, `if: github.ref == 'refs/heads/main'`) and
  `deploy-staging` (deploy the digest, run gated migrations, smoke). Prod is a **manual** promotion of the
  staging-validated digest (`workflow_dispatch` behind an environment approval), never automatic.
- **WHY commented/not authored:** the cloud/registry/secret-store choices fork on **DEP-4** (a sponsor
  decision); authoring them now would hard-code unknowns. Tracked as DEP-4 (DevOps PLAN §3/§4/§7).
- **gotcha:** this is the one place the workflow is intentionally incomplete — and it's documented as a
  pending dependency, not a stub of delivered functionality (so it does not violate the no-stub rule;
  it's a *plan annotation* for unmade infra decisions).
- **dependencies / cross-refs:** `backend/pyproject.toml` (ruff/mypy config + `[dev]` extra),
  `backend/tests/test_cleanroom_import.py`, `backend/tests/test_migrations_roundtrip.py`,
  `db/baseline/schema.sql` (via alembic), `frontend/package.json` (`typecheck` script), ADR-0001,
  ADR-0002, DevOps PLAN §2/§3/§4/§7, WAYS-OF-WORKING §3, Platform & Data PLAN §2 (R-PD2), DEP-4.

---

## Empty files in this slice
None. All 8 R1-owned files are non-empty. (The 18 census EMPTY files are owned by other slices; the only
empty thing in R1's directory footprint is the `.claude/worktrees/` directory — not a file — explained above.)

## Verification notes (grounding the WHYs — nothing assumed)
- `reference/samples/potato_2026_rfp_input.xlsx` exists on disk: **394799 bytes** (≈0.4MB) — matches the
  Dockerfile/`.gcloudignore`/`.dockerignore` "single 0.4MB sample" claims.
- `backend/Dockerfile` confirmed COPYs: `db/baseline/schema.sql` → `/db/...` (lines 9-11,32),
  `deploy/gcp/seed.py` → `/app/...` (line 41), `reference/samples/potato_2026_rfp_input.xlsx` →
  `/reference/...` (line 47). These ground every "repo-root context" and "single sample" WHY.
- `scripts/web_session_start.sh` exists, executable, 7812 bytes — grounds `.mcp.json` + settings-sample WHYs.
- `reference/samples/.gitkeep` is **0 bytes** (the keep-marker the `.gitignore` re-includes).
- git first-add dates corroborate census created dates for all 8 files.
