---
doc: AS-BUILT AUDIT — SLICE D5 — project/triage, reference, mcp (harness), infra, audit (OLD), root .mcp.json
id: ASBUILT-D5
status: COMPLETE (read-only audit). Per-file Layer-2 entries + binary census + supersession notes.
scope: /project/triage/** · /reference/** · /mcp/** · /infra/** · /audit/** (OLD 00–04) · root /.mcp.json
contract: /CLAUDE.md (ABSOLUTE REQUIREMENTS injected) + /AS_BUILT/AUDIT_STANDARD.md (binding bar)
generated: 2026-06-22
method: find → cross-check AS_BUILT/FILE_CENSUS.md → read text files end-to-end → binaries census+describe only
---

# D5 — Triage · Reference corpus · MCP harness · Infra · OLD audit · root .mcp.json

This slice covers the **non-platform-code perimeter**: the project's *triage staging* (discussed-but-not-recorded
candidates, the drift reconciliation, the manual-model findings), the **quarantined reference corpus** (the
clean-room sample register + the real sample binaries + the lifted v3 engine), the **MCP harness** (the
deployable Claude-Code plugin that is the live-run verification *oracle*), the **dev/deploy infra** (docker
compose + schema bootstrap), the **OLD audit 00–04** (the prior as-built/gap audit, now superseded by `AS_BUILT/`),
and the **repo-root `.mcp.json`** (the web-runtime MCP registration).

## Census cross-check (against `AS_BUILT/FILE_CENSUS.md`)

All D5 files are accounted for in `FILE_CENSUS.md`. Mapping (census row # → path):

| Census # | Path | In scope as |
|---|---|---|
| 7 | `./.mcp.json` | root MCP registration (web runtime) |
| 12 | `./audit/00_EXECUTIVE_SUMMARY.md` | OLD audit |
| 13 | `./audit/01_DOCUMENT_AUDIT.md` | OLD audit |
| 14 | `./audit/02_GAP_ANALYSIS.md` | OLD audit |
| 15 | `./audit/03_SCHEMA_DIFF.md` | OLD audit |
| 16 | `./audit/04_RISKS_DECISIONS_ROADMAP.md` | OLD audit |
| 332 | `./infra/.env.example` | infra |
| 333 | `./infra/README.md` | infra |
| 334 | `./infra/docker-compose.yml` | infra |
| 335 | `./infra/postgres/init/01_schemas.sql` | infra |
| 336 | `./mcp/.claude-plugin/plugin.json` | MCP plugin manifest |
| 337 | `./mcp/.mcp.json` | MCP stdio registration (local) |
| 338 | `./mcp/README.md` | MCP harness doc |
| 339 | `./mcp/agents/rfp-engine.md` | MCP subagent (data) |
| 340 | `./mcp/agents/rfp-secretary.md` | MCP subagent (admin/memory) |
| 341 | `./mcp/skills/rfp-pilot/SKILL.md` | MCP orchestrator skill |
| 507 | `./project/triage/BACKFILL_CANDIDATES.md` | triage |
| 508 | `./project/triage/DRIFT_RECONCILIATION.md` | triage |
| 509 | `./project/triage/MANUAL_MODEL_FINDINGS.md` | triage |
| 510 | `./reference/README.md` | reference boundary |
| 511 | `./reference/SAMPLE_REGISTER.md` | sample register |
| 512 | `./reference/as-built-db/.gitkeep` | reference (EMPTY) |
| 513 | `./reference/incoming/README.md` | reference drop-zone |
| 514 | `./reference/samples/.gitkeep` | reference (EMPTY) |
| 515–545 | `./reference/samples/**` (binaries) | sample data (census + describe only) |
| 546 | `./reference/v3-engine/RFP_Analysis_Engine.ipynb` | v3 runner notebook |
| 547 | `./reference/v3-engine/rfp_analysis_engine_v3.py` | v3 engine source (lifted) |

**Census-date note (not a gap, but recorded):** `FILE_CENSUS.md` uses *git author dates* for tracked files and
*filesystem mtime* for untracked. Because `reference/samples/*` and `reference/v3-engine/` are **gitignored**
(quarantined per ADR-0001 — see below), their census Created/Modified dates are filesystem mtimes, which differ
from the on-disk mtimes I observed (e.g. census shows `potato_2026_rfp_input.xlsx` at 2026-06-22T15:27Z, on-disk
mtime is 2026-06-18 10:47 — the census timestamp is a later touch). This is expected for untracked files and is
exactly what the census header discloses; flagged only for completeness.

**Gitignore / quarantine status (verified with `git check-ignore`):**
- `reference/samples/*` → **IGNORED** (`.gitignore:9`, with `!.gitkeep`/`!README.md` re-includes at 10–11).
- `reference/v3-engine/` → **IGNORED** (`.gitignore:47-48`).
- `audit/**` → **NOT ignored**, git-tracked (5 files, all committed).
- `infra/**`, `mcp/**`, `project/triage/**`, root `.mcp.json` → tracked.
- `infra/.env`, `infra/postgres/data/` → gitignored (only `.env.example` is committed).

So the reference *binaries and the v3 engine are present on disk but never enter git history* — the ADR-0001
clean-room rule in physical form. The two `.gitkeep` files exist precisely so the otherwise-empty/ignored
`reference/samples/` and `reference/as-built-db/` directories are preserved in the tree.

---

# PART 1 — `project/triage/**` (3 files)

The triage directory is a **deliberate holding pen, stored APART from the authoritative specs** so unratified
material cannot corrupt the build plan. CLAUDE.md mandates "ONE source of truth" (decisions →
`03_DECISION_LOG.md`, rules → `CLAUDE.md`, state → `HANDOVER.md`, map → `VAULT.md`); these triage files are the
*pre-promotion* staging that protects that single source of truth. Each carries a loud non-authoritative banner.

### `project/triage/BACKFILL_CANDIDATES.md`
- **path:** `/home/user/KR_RFP/project/triage/BACKFILL_CANDIDATES.md`
- **ext:** `.md` · **empty?** no · **size:** 6221 B · **created/modified:** 2026-06-22 (census row 507)
- **what:** A triage register of seven candidates (C1–C7) "discussed in our process but never recorded" in the
  live specs, each with a proposed promotion **Home**, a **Verify** step, and a final **Promotion log** table of
  sponsor decisions.
- **DETAILED WHY it exists:** After ~300 context compactions (the trigger named in DRIFT_RECONCILIATION), some
  things were decided in conversation but never written to disk. CLAUDE.md's iron rule is that state must live on
  disk, not in context, and that nothing unratified may touch the live specs. This file is the *quarantine for
  decisions*: a place to land "discussed-but-not-durable" items so they can be verified and then either promoted
  to their proper authoritative home or discarded — **without** them being mistaken for ratified spec. The status
  line literally reads "⚠️ NON-AUTHORITATIVE STAGING — NOT a live spec. Candidates only." It breaks the
  one-source-of-truth contract if these half-decisions were instead injected into `04_PROGRAM_BACKLOG`/the ADRs.
- **WHY shaped this way:** Each candidate has (a) what was discussed, (b) a spot-checked current state with the
  exact file/commit evidence, (c) a target Home, and (d) a Verify gate — i.e. the "verify before actioning"
  ABSOLUTE REQUIREMENT #5 in template form. The Promotion log uses a single sponsor filter: *does it affect the
  user process or analysis process?* If no → dropped as internal.
- **Substance (the seven candidates + dispositions, recorded so this audit is self-contained):**
  - **C1 — Auditor verdicts (pre-compaction):** ~22 auditor notes; ~18 confirmed TRUE & actioned (capacity NOTE
    fix, commits `3e4abfd`/`643fa74`); **4 OVERSTATED, intentionally NOT actioned** (#1 engine input-hash →
    TRUE-partial → C2; #10 `WEB_DEPLOYMENT` self-discloses status; #15 `gen:api` honestly labelled; #3
    `all_lot_discount` TRUE-but-dead → C6). → **Dropped** (internal record, no user/analysis impact).
  - **C2 — Input-hash completeness (auditor #1, TRUE-partial):** `runner.py` seals `input_hash`
    (`runner.py:90/150` via `_inputs_manifest`) but only the **config** was hashed — components/exclusions/
    thresholds were NOT — so two differing runs could share a hash. → **DONE**: `_inputs_manifest` now seals the
    full `EngineConfig` (`model_dump`), tamper-evident; 4 tests; As-Built v1.25.
  - **C3 — CI hardening:** `frontend/package-lock.json` now committed, but `ci.yml:176` still runs `npm install`
    with a stale "no lockfile yet" comment; `next build` + generated-OpenAPI-client check absent. → **Dropped**
    (dev/infra, no user/analysis impact).
  - **C4 — Frontend "Breaches" rename + missing states:** the "Breaches" column in
    `ScenarioComparisonTable.tsx` needs the locked-design rename (capacity/concentration), names-not-keys, and
    error-vs-empty states. → **DONE**: renamed to "Over capacity" on the current comparison screen.
  - **C5 — in-app close-out:** `PilotService.delete_run` (service.py:1309) had no HTTP route. → **DONE** built as
    a governed *finalize/close-out* (NOT a delete): `PilotService.finalize_run` (service.py:1321) +
    `POST /runs/{slug}/finalize` (runs.py:619); new `EventType.CLOSED` on `cyc.cycle` in-txn via `AuditWriter`;
    award (won) + rejection (not-won) notices render on request (E-42, no file persisted); gated on a frozen
    award (409 else), idempotent, closed-state **derived** from the CLOSED event (no migration); harness
    `close_run`/`purge_run` untouched; 6 tests (`tests/api/test_finalize.py`); 257 pass; As-Built v1.26.
  - **C6 — `all_lot_discount` dead code (auditor #3, TRUE-harmless):** dead path, tech-debt. → **Dropped**
    (internal).
  - **C7 — Working-practice principles (meta):** standing directives (save-as-you-go, verify-before-actioning,
    least-margin-for-error, constrained agents, MCP = oracle) maybe not consolidated. Home = `02_WAYS_OF_WORKING`.
    → **Dropped** (meta/process).
- **What breaks without it:** the four un-actioned auditor verdicts and the discussed-but-unrecorded items would
  have no durable home and would either be silently lost or (worse) get re-litigated / wrongly injected into the
  live specs. It is the audit trail of *what was decided NOT to do, and why* — exactly the kind of negative
  knowledge that vanishes across compactions.
- **Cross-ref:** census row 507. References live specs `04_PROGRAM_BACKLOG`, `07_AS_BUILT_PROCESS_AUDIT`,
  `03_DECISION_LOG`. Cites backend `runner.py`, `service.py`, `runs.py`, `tests/api/test_finalize.py`;
  frontend `ScenarioComparisonTable.tsx`; CI `ci.yml`.

### `project/triage/DRIFT_RECONCILIATION.md`
- **path:** `/home/user/KR_RFP/project/triage/DRIFT_RECONCILIATION.md`
- **ext:** `.md` · **empty?** no · **size:** 6628 B · **created/modified:** 2026-06-22 18:46 (census row 508)
- **what:** The reconciliation of **what the durable record CLAIMS vs what is actually in the repo**, produced
  from two read-only audits (backend/decisions + frontend/design) verified against code, folded with the
  data-fidelity findings. Triggered by the sponsor asking "how much has been lost?" after ~300 compactions.
- **DETAILED WHY it exists:** This is the honest accounting that answers the sponsor's loss question with
  evidence, not reassurance. Its headline: **almost nothing in the recorded core was lost, because the core lives
  on disk, not in context** — which is the entire justification for CLAUDE.md's "state never lives only in
  context" rule. The damage is enumerable, not vague, and is sorted into four categories so remediation can be
  ordered. It belongs in triage (not the live specs) because it *enumerates open violations/drift* that are
  candidates for the backlog/decision-log, not yet themselves ratified spec.
- **WHY shaped this way (the four categories):**
  - **A. TRULY LOST — ~0 material.** The engine + governed-persistence spine is full-fidelity and tested:
    v3 5-factor banded scoring (`engine/scoring.py`), 7 lenses A–G (`engine/allocation.py`), split allocation +
    cap-breach, sealed reproducible runs with sha256 manifests (`runner.py:150-168`), freeze-and-layer
    (`awd/service.py`), canonical formula registry (`engine/formulas.py`), flat-13 period storage (migration
    0014), key-validated ingest/quarantine, stateless render-on-request (`pilot/deliverables.py`), savepoint/
    compare (E-43). "The disk record held."
  - **B. BUILT BELOW THE RECORDED BAR (drift/violations, ~6).** Most important for ABSOLUTE REQUIREMENTS:
    (1) **🔴 the potato converter data-fidelity violation** — `backend/scripts/potato_legacy_dryrun.py`, the
    exact artifact D45 was written to condemn, **still UNREPAIRED** and wired into Cloud Build seed (commits
    `32413af`/`dbbf071`). Verbatim violations: single Delivered round only (`:435`), 141 demand rows dropped
    (`:321-323`), regions flattened unknown→"Central" (`:99-115`), Lot Name == raw Lot_ID (`:460`),
    force-positived values (`_as_positive`, `:145-154`). This taints the data the buyer reviews; D45 ordered it
    rebuilt faithfully FIRST. (2) **4 frontend MVP-cuts** violating D19/NO-MVP (A1 Cycle Setup thin; A3/M1 column
    mapper confirm-only; M5 quarantine surface-only; Alignment single-matrix). (3) **Tenancy drift (D8):** decided
    client_id+RLS, built client_id on a couple of `ref` tables, **no RLS**. (4) **2 write-points outside the audit
    hash-chain** (setup-ingest, capacity-ingest). (5 minor) `bid_line.fiscal_period_id` is `varchar(36)` not
    `uuid`+FK. (6 minor) runner omits `all_lot_discount` in `BidComponents` (`runner.py:300-306`).
  - **C. RECORDED BUT NOT YET BUILT (~13).** Frontend surfaces w/ no route (Sign-off A5, Settings/RBAC A6,
    Suppliers A7, Reconciliation M2/M3/M4, full Cycle Setup, Supplier-comms A4, run-scoped tab rail). Backend
    perimeter (iTrade importer E-08 → "vs STLY" runs on a synthetic ×1.04 proxy; RBAC defined never called;
    sign-off gate E-22; safety reprice+USDA feed E-29; PBA E-33; KCMS E-09; supplier scorecard E-10; comms SEND
    E-37). All in the backlog — deferred, not lost.
  - **D. LOOKS LOST BUT ISN'T (built-but-undocumented).** Award/comms/freeze/savepoint live in
    `api/v1/runs.py` (23+ routes), NOT the same-named domain routers; `awards.py`/`cycles.py`/`documents.py`/
    `ingest.py` are **present-but-empty stub files — dead files, not capability gaps** (except `ingest.py` which
    genuinely has no feed). The two-runtime split (stateless console DB vs MCP harness file-vault) is real and
    deliberate. `construct_price_from_parts` unifies engine+ingester price math, fully tested.
- **Tally + remediation order:** Backend ~17 BUILT-faithful · ~6 PARTIAL · ~6 NOT-BUILT · 1 DRIFTED · 3 in-tree
  stubs · **1 active data-fidelity violation (converter)**. Frontend 7 faithful · 4 MVP-cut · 7 not built; **no
  mock/placeholder data anywhere** — the breach is SCOPE not faked data. Remediation order (per D45 + NO-MVP):
  (1) rebuild the potato converter faithfully FIRST, (2) close the 4 frontend MVP-cuts + build not-built surfaces,
  (3) build recorded backend perimeter + close audit-write-point & tenancy drift, (4) delete dead empty routers.
- **What breaks without it:** without this enumeration the sponsor cannot tell signal (one real violation) from
  noise (recorded-but-deferred backlog); the single active data-fidelity violation could stay buried; the lesson
  (D45: compactions didn't cost the core *because* it was on disk) would not be captured.
- **Cross-ref:** census row 508. relates: CLAUDE.md, `03_DECISION_LOG.md` (D45), `04_PROGRAM_BACKLOG.md`,
  `design/REDESIGN3_GAP_ANALYSIS.md`. The converter §B1 here is the live link to the data-fidelity ABSOLUTE
  REQUIREMENT #3 in CLAUDE.md and the most material as-built finding in the whole slice.

### `project/triage/MANUAL_MODEL_FINDINGS.md`
- **path:** `/home/user/KR_RFP/project/triage/MANUAL_MODEL_FINDINGS.md`
- **ext:** `.md` · **empty?** no · **size:** 6830 B · **created/modified:** 2026-06-22 03:51 (census row 509)
- **source artifact (read by the author, not by this audit):**
  `reference/samples/_allocation_models/2026.05.19_Sweet Potatoes Allocation model RD4_vCurrent.xlsx` (the MANUAL
  RFP model, cross-checked vs the 2026.04.28 RD2 file — sponsor: "make sure its the manual not the golden output").
- **what:** Verification findings from reading the **manual human-built allocation model** to confirm the
  pricing-modality / cost-construction calcs (D43) against evidence rather than recollection. Recorded SEPARATELY
  (triage) so they don't corrupt the live build plan; each finding to be confirmed before changing live code.
- **DETAILED WHY it exists:** Implements "verify before actioning" (ABSOLUTE REQ #5) and the
  "MCP-harness/manual-model = verification oracle" principle: rather than trust memory about how cost is
  constructed, the author opened the *most complex current Excel* and reconciled its columns to our engine fields.
  It is the evidence base for D43 (pricing modality) and the first concrete reconciliation items when D43 is
  built. Triage placement is because the findings (esp. A/B) imply *changes* to live engine code that must be
  confirmed first.
- **WHY shaped this way / substance:**
  - **What the manual model is:** a ~32 MB human-built Excel with sheets: *Controls* (scope/setup, periods =
    weeks/4), *RFP - FOB Bid* (FOB by round RD1/RD2/RD3 + discounts + RPC + capability + should-cost %),
    *RFP - Delivery Charge* (per supplier|DC|item: Delivery Surcharge Per Case + VegCool XDOCK Surcharge Per Case +
    loading location + transit days), *Sweet Potato RFPs* (INDEX/MATCH assembly), *Baseline scenario* (FOB and
    Routing/landed side-by-side + spend + FOB savings), *Data cube* (~700-col per-supplier per-modality price),
    *CBS freight data* (Freight Unit Cost Amount), plus FOB analysis / Supplier overview / Summary / Signoff /
    Booking Guide / Historicals / Supplier mapping.
  - **VERIFIED — confirms D43:** (1) Modality is real and called **"Routing"** — `Baseline scenario` row 7 shows
    Old/Bid FOB AND Old/Bid Routing price side-by-side (the modality picker: FOB / DELIVERED / XDOC).
    (2) The cost catalog maps to our **existing** `engine/interface.py BidComponents` fields:
    `Bid Price ($/Case, FOB)`→`fob`; `Delivery Surcharge Per Case`→`delivery_surcharge`;
    `VegCool XDOCK Surcharge Per Case`→`vegcool_surcharge` (**XDOC leg = our "vegcool"**);
    `% Discount for Full-Lot Award`→`lot_discount`; `Incremental % Discount`→`all_lot_discount`;
    `RPC Cost Impact (+/- $/Case)`→ no distinct field; `CBS freight Freight Unit Cost Amount`→ freight reference.
    (3) **XDOC mechanics corrected:** XDOC = routing through a named cross-dock ("VegCool Xdock") with a
    supplier-stated per-case surcharge; price = FOB + surcharge. It is **NOT** "supplier covers origin→cross-dock,
    Kroger covers cross-dock→DC." Our `vegcool_surcharge` already models this.
  - **FINDINGS to reconcile (confirm first, do NOT silently change live code):**
    - **A. Discounts: PERCENT in the manual, DOLLARS in our engine — ✅ RESOLVED 2026-06-22.** Manual discounts
      are % of FOB; our `construct_price_from_parts` did `fob + delivery + vegcool − lot_discount −
      all_lot_discount` as **$** with no %→$ conversion. **Resolution (D43, refined):** a discount is a cost line
      (sign −) whose base is a buyer-selected set of one-or-many cost lines, configured at setup (A1 cost-line
      manager); unit `%` (preferred — grain-robust) or `$`; default base = FOB. **Action (E-44):** switch
      `construct_price_from_parts` to `−(pct × Σ selected-base-lines)`; ingester reads stated %/$; known-template
      adapter converts legacy $-discounts; add tests.
    - **B. RPC is first-class in the manual, not a distinct engine component.** Manual has `RPC Cost Impact
      (+/- $/Case)` gated by `RPCs? (Y/N)`; ours can only fold RPC into All-In. **Action (to confirm):** add RPC
      as a D43 toggleable cost line (sign +/-, $/case, gated by RPC flag).
    - **C. Grain reality — manual is HORIZON-grain, not per-period-13.** Manual collects one bid per
      supplier|DC|item by round over a horizon (Short/Long; "3 periods" = short). Our D35/D38/D42 **flat-13
      per-period** collection is an *enhancement* beyond the manual (to seed E-35 timeframe discovery), not the
      manual's method — keep this straight when comparing harness vs manual vs app.
- **What breaks without it:** the % vs $ discount mismatch (Finding A) is a real cost-math error that would
  under/over-state landed cost; without this written-down reconciliation it would have stayed a recollection. It
  is the documented bridge between the real human workbook and our engine's `BidComponents`.
- **Cross-ref:** census row 509. relates: `03_DECISION_LOG.md` (D43, D42), `RECONCILIATION_SEAMS.md`,
  `engine/interface.py`, `engine/formulas.py`, `domain/bid/{template_schema.py,bid_ingester.py}`. Its source is a
  D5 reference binary (allocation model #12 in SAMPLE_REGISTER).

---

# PART 2 — `reference/**` (clean-room quarantine: 4 text + 33 binaries + 2 empty markers)

`reference/` is the **clean-room boundary** (ADR-0001). Its whole purpose is to let the sponsor's real repo and
real files *inform* this build without *contaminating* it: nothing here is imported by `backend/` or `frontend/`
(CI enforces this via `backend/tests/test_cleanroom_import.py`), and the real-value binaries are gitignored so
they never enter history. It is reference material for humans and planning agents only.

## 2a. Reference text files (4)

### `reference/README.md`
- **path:** `/home/user/KR_RFP/reference/README.md` · **ext:** `.md` · **empty?** no · **size:** 2140 B
- **created/modified:** 2026-06-18 (census row 510)
- **what:** The boundary note for the clean-room directory. States **the rule** (input only; the old repo is never
  copied in as code; CI fails the build if any `backend/` module imports from `reference/`; sample files arrive on
  demand with provenance), the **data-classification rule** (Security-owned — real values are gitignored until
  classified and allow-listed), and the **layout** (`as-built-db/`, `as-built-digest.md`, `samples/`).
- **DETAILED WHY:** Encodes the sponsor's constraint verbatim — "the repo is in my github, but i dont want it
  contaminating this build … keep it isolated." The quarantine is the only safe way to lift the v3 engine's logic
  and read the real samples without entangling the new build with proprietary/old code or committing sensitive
  commercial values. Without this note and its CI enforcement, the clean-room could silently leak: a stray import
  or a committed sample would breach ADR-0001. It documents the *single dedicated agent → schema+digest only*
  intake path across the quarantine boundary.
- **What breaks without it:** the boundary becomes implicit and unenforced; future agents wouldn't know
  `reference/` is input-only and could wire it into the running system or commit real data.
- **Cross-ref:** census row 510. cites `docs/adr/ADR-0001-clean-room-reconciliation.md`,
  `backend/tests/test_cleanroom_import.py`, `project/squads/security/PLAN.md`.

### `reference/SAMPLE_REGISTER.md`
- **path:** `/home/user/KR_RFP/reference/SAMPLE_REGISTER.md` · **ext:** `.md` · **empty?** no · **size:** 6895 B
- **created/modified:** 2026-06-18 → 2026-06-19 (census row 511)
- **what:** The **only tracked record** of which real sample artifacts arrived (the binaries themselves are
  gitignored/never committed). A sanitized catalog: clean name, type, generic category, cycle year, classification,
  received date, provenance — **no sensitive values** — plus structural-only tab inventories.
- **DETAILED WHY:** ADR-0001 §4 + the Security PLAN forbid committing the real files; but the *fact of their
  existence and their structure* must be durable, or the corpus is unauditable and un-plannable. This register is
  that durable, sensitive-value-free index. It is the human-readable counterpart to the gitignored binaries — the
  bridge that lets planning agents reason about the corpus without opening sensitive data.
- **WHY shaped this way / the catalog (this is the authoritative description of the 33 sample binaries — see 2b):**
  - **Kickoff corpus (items 1–5):** 3 narrative `.docx` kickoffs (field-grown 2026, greenhouse 2025,
    processed-pack 2027–2028) + 2 prep `.xlsx` workbooks. The structural schema lives sanitized in
    `project/squads/product/KICKOFF_KEYSTONE_SPEC.md`. Tab findings: `Scorecard` vs `Scorecard (Signoff)` ⇒ **two
    frozen scorecard snapshots** (kickoff + sign-off windows); `KCMS (subcomm)` vs `KCMS (GTIN)` ⇒ **scan feed at
    two grains**.
  - **Additional feed samples (items 6–10):** (6) iTrade by commodity — `.xlsx`, 43-col "Data" sheet, ~114k rows
    → drives the `perf.itrade_receipt` importer (E-08); (7) **rfp_analysis_engine_v3.py** — 4,198 lines, *the v3
    engine source*, logic LIFTED into our engine, never imported, raw never committed; (8) **RFP_Analysis_Engine
    .ipynb** — the Colab runner harness for v3; (9) **Potato 2026 RFP INPUT** — 13 sheets (CONFIG/IN_*/DIM_*),
    golden-master INPUT, drives the engine-reproducibility test E-13; (10) **Potato 2026 RFP analysis OUTPUT** —
    20 sheets, golden-master OUTPUT (known-good v3 result) the new engine must reproduce. Items 7–10 are the
    "golden v3 pair + engine source — the linchpin for Phase D + the pilot."
  - **Allocation models (items 11–13) — "most complex current Excel":** (11) Sweet Potatoes RD2 (~32 MB, 19
    sheets) drove the scenario-tool design study §7; (12) Sweet Potatoes RD4 (~31 MB, 20 sheets, adds Booking
    Guide + Signoff); (13) Hybrid Onions RD4 (~7 MB, 19 sheets, Conv/Org + vs-STLY). Shared architecture:
    `Controls` cockpit · `Outputs/Calcs/Raw data` divider tabs · `Scenario tool` (Lot×DC rows × 500+ supplier/
    scenario cols) · `Baseline scenario` · `Supplier overview` · `Summary` · `FOB analysis` + `RFP - Delivery
    Charge` · `Data cube` (650–700 cols) · `[Commodity] RFPs`/`Historicals` · `Supplier mapping` · `Sign-off
    tables`. Item 12 is the source for MANUAL_MODEL_FINDINGS above.
  - **Handling rules (binding):** raw stays gitignored; only structure may be committed; any example value must be
    an obviously generic placeholder (`$XXXM`, `<SupplierA>`); the intake path emits schema + digest only.
- **What breaks without it:** the corpus becomes an untracked pile of gitignored binaries with no manifest — no one
  could tell what arrived, what each is for, or that (e.g.) item 9/10 are the golden reproducibility pair. The
  register is the corpus's table of contents and provenance ledger.
- **Cross-ref:** census row 511. relates: ADR-0001, Security PLAN, `specs/rfp-engine/intake/SESSION-02`, `audit/02
  G5`, E-14. Points structure into `KICKOFF_KEYSTONE_SPEC.md`, `FEEDS_ITRADE.md`, `SCENARIO_TOOL_DESIGN_STUDY.md §7`.

### `reference/incoming/README.md`
- **path:** `/home/user/KR_RFP/reference/incoming/README.md` · **ext:** `.md` · **empty?** no · **size:** 1585 B
- **created/modified:** 2026-06-19 (census row 513)
- **what:** The **direct-upload drop-zone** instructions. Tells the sponsor to upload real cycle data here on the
  working branch via GitHub's web UI when files are too large for chat; warns this **commits raw sensitive data
  into the repo** (accepted trade-off, private repo); defines the workflow (ping → pull → map structure → commit
  only sanitized derived artifacts → `git rm` the raw files → optional history purge); lists what to drop in
  priority order (most-complete single cycle's bid workbooks + kickoff + award/booking guide; a second category
  using the *other* template to prove multi-template intake; emails/.eml, booking guides, KCMS).
- **DETAILED WHY:** There are two intake routes: the chat split-upload (keeps raw data out of the repo entirely,
  the ADR-0001 default) and this GitHub-web direct upload (convenient for large files, but commits raw data). This
  README makes the trade-off explicit and gives the cleanup workflow so the convenience route doesn't permanently
  pollute history. It exists because real cycle files are often too big for chat, and the sponsor needs a sanctioned
  way to hand them over.
- **What breaks without it:** the sponsor wouldn't know the large-file path, or (worse) would upload raw data
  without the sanitize-and-`git rm` discipline, leaving sensitive commercial values permanently in history.
- **Cross-ref:** census row 513. Names branch `claude/wizardly-pasteur-n4acb8` (matches CLAUDE.md req #6) and
  ADR-0001's quarantine rule. (Directory currently holds only this README — no incoming files staged.)

### `reference/v3-engine/` text files (the lifted engine)

#### `reference/v3-engine/rfp_analysis_engine_v3.py`
- **path:** `/home/user/KR_RFP/reference/v3-engine/rfp_analysis_engine_v3.py` · **ext:** `.py` · **empty?** no
- **size:** 239466 B · **4198 lines** · gitignored (quarantined) · created/modified per census row 547
- **what:** **The v3 RFP Analysis Engine source** — a single-file, commodity-agnostic Python script (pandas +
  numpy + openpyxl) that reads one RFP input `.xlsx` and writes a styled 10-tab output workbook. Module docstring:
  "Full scoring, eligibility gates, 6 scenarios, data quality validation, and 10-tab output workbook." Usage:
  `python rfp_analysis_engine_v3.py <input_file.xlsx>`.
- **structure (from section markers, not a full re-read — file is a 4198-line monolith):** styling utilities
  (`fp/fn/al/bd/cw/rh/frz/H/D/banner/section`, color palette `C` + scenario palette `SC`); IO/validation
  (`cfg`, `validate_schema`, `load_tab`); standardizers (`std_bids`, `std_inc`, `std_vol`); region/limits
  (`get_region`, `get_vol_limit`); data-quality (`dq`); coverage (`cov_band`, `cov_color`); the **6 scenarios**
  (A Lowest Cost / B Risk-Adjusted Recommendation w/ `_rec_type` / C Incumbent Defense / D `max_two_per_dc` /
  E Exclude / F Custom Override) + `deterministic_sort`, `scen_kpis`, `lc_reason`; and ~13 output-tab builders
  (Scenario Comparison, Award Recommendations (Scenario B), Custom Scenario w/ live dropdowns, Regional Savings,
  Glossary, etc.).
- **DETAILED WHY it lives here (quarantined):** This is "the brain" — the OLD audit (`audit/00`,`02 G2`) and the
  whole reconciliation thesis ("v3 is the brain, the repo is the spine, neither alone") center on it. Per ADR-0001
  it is **read as reference, its logic LIFTED into our own `backend/app/engine/` (scoring/allocation/formulas),
  never imported, and the raw never committed.** It sits in `reference/v3-engine/` so the team can re-read the
  exact banded weights (Price 0.35 banded ≤3→100/≤7→80/≤12→50/>12→20, Coverage 0.25, Historical 0.20, Z-Risk
  0.10, Continuity 0.10) and the `max_two_per_dc` split logic that our engine reproduces and the golden-output
  test must match.
- **What breaks without it:** the source of truth for the scoring model and split allocation would be gone — our
  engine's fidelity (and the E-13 reproducibility test against the golden output) is defined *relative to this
  file's* behavior. It is the specification-by-example for the engine.
- **Cross-ref:** census row 547; SAMPLE_REGISTER item 7; gitignored (`.gitignore:47-48`). NOT read line-by-line
  in this audit (4198-line quarantined reference; characterized by structure markers only).

#### `reference/v3-engine/RFP_Analysis_Engine.ipynb`
- **path:** `/home/user/KR_RFP/reference/v3-engine/RFP_Analysis_Engine.ipynb` · **ext:** `.ipynb` · **empty?** no
- **size:** 7282 B · gitignored · created/modified per census row 546
- **what:** The **Colab runner notebook** for the v3 engine — 7 cells: (1) `pip install pandas openpyxl numpy`;
  (2) clean up duplicate engine files + md5 the engine; (3) Google-Colab `files.upload()` for both the engine
  `.py` and the input `.xlsx`, detect the `*RFP_Input*.xlsx`; (4) `!python rfp_analysis_engine_v3.py "{INPUT}"`;
  (5) `files.download` the `*_RFP_Analysis.xlsx` output; (6) markdown how-to for the live CUSTOM_SCENARIO tab
  (Col F dropdown changes award supplier, H/K/M update live, green = Scenario A, Col N flags DC cap breaches);
  next-cycle instructions.
- **DETAILED WHY:** This is *how v3 was actually run* by the sourcing team — a manual upload-and-run Colab harness,
  no persistence, re-upload every session. It is the concrete artifact behind the audit's verdict that v3 "forgets
  everything each run" (no store) — the very gap the new governed Postgres store fixes. It documents the original
  operator workflow our MCP harness + console replace.
- **What breaks without it:** the original run-context (Colab, manual re-upload, stateless) would be undocumented;
  the "why we need a store" argument loses its concrete reference.
- **Cross-ref:** census row 546; SAMPLE_REGISTER item 8; gitignored. Read in full (small notebook).

## 2b. Reference sample binaries — census + description ONLY (per task: do NOT open .xlsx/.xlsb)

All gitignored (`reference/samples/*`), real commercial values, QUARANTINED. **Not opened.** Sizes are on-disk;
descriptions are from `SAMPLE_REGISTER.md`, `MANUAL_MODEL_FINDINGS.md`, filenames, and the incoming README. Census
rows 515–545.

### `reference/samples/` (top level — 25 files)

| File | Ext | Size (B) | What it is (described, not opened) |
|---|---|---|---|
| `bid_divine_r1.xlsx` | xlsx | 1,980,582 | Supplier **Divine** Round-1 bid workbook (one of the multi-round bid set). |
| `bid_divine_r2.xlsx` | xlsx | 1,990,673 | Divine Round-2 bid workbook. |
| `bid_divine_r3.xlsx` | xlsx | 1,975,650 | Divine Round-3 bid workbook. |
| `bid_lipman_r1.xlsb` | xlsb | 2,029,714 | Supplier **Lipman** Round-1 bid — **binary `.xlsb`** (macro/binary workbook; the second bid-template family). |
| `bid_lipman_r2.xlsb` | xlsb | 2,004,716 | Lipman Round-2 bid (`.xlsb`). |
| `bid_lipman_r3.xlsb` | xlsb | 2,009,358 | Lipman Round-3 bid (`.xlsb`). |
| `bid_marengo_r1.xlsx` | xlsx | 1,980,774 | Supplier **Marengo** Round-1 bid. |
| `bid_marengo_r2.xlsx` | xlsx | 1,994,824 | Marengo Round-2 bid. |
| `bid_marengo_r3.xlsx` | xlsx | 1,978,893 | Marengo Round-3 bid. |
| `bid_marengo_r4.xlsx` | xlsx | 1,980,774 | Marengo **Round-4** bid (evidence R4 exists — "more rounds if there is juice"). |
| `blank_master_template.xlsx` | xlsx | 1,979,074 | The blank master **bid template** suppliers fill out (the strict-ingest template shape). |
| `field_tomato_kickoff_2026.docx` | docx | 272,866 | **Field Tomatoes** kickoff narrative doc (the cycle the incoming README flags as the best complete candidate). |
| `field_tomatoes_booking_guide.xlsx` | xlsx | 33,590 | Field Tomatoes **booking guide** (award/logistics output artifact). |
| `hh_veg_kickoff_2025.docx` | docx | 6,467,390 | Household-veg kickoff narrative (2025); large (embedded media). |
| `itrade_by_commodity_with_calendar_A.xlsx` | xlsx | 22,728,182 | The **iTrade receipt feed** (43-col "Data" sheet, ~114k rows) → `perf.itrade_receipt` importer (E-08); SAMPLE_REGISTER item 6. |
| `kickoff_doc_prep.xlsx` | xlsx | 24,727 | Kickoff prep workbook (small) — `Scorecard`/`Scorecard Export`/`Next Steps` tabs (register item 4). |
| `kickoff_document_prep.xlsx` | xlsx | 1,129,317 | Kickoff prep workbook (full) — scorecard + KCMS (subcomm/GTIN) export tabs (register item 5). |
| `potato_2026_rfp_analysis_output.xlsx` | xlsx | 3,299,268 | **Golden-master OUTPUT** (known-good v3 result, 20 sheets) the new engine must reproduce — register item 10. |
| `potato_2026_rfp_input.xlsx` | xlsx | 394,799 | **Golden-master INPUT** (13 sheets CONFIG/IN_*/DIM_*) driving engine-reproducibility test E-13 — register item 9. |
| `round2_ingestion_final.xlsx` | xlsx | 248,945 | A Round-2 ingestion working file (ingest test fixture / corrected round-2 set). |
| `round3_ingestion_corrections.xlsx` | xlsx | 110,452 | A Round-3 ingestion-corrections working file (fix-and-retry / quarantine evidence). |
| `tomato_2026_rfp_input.xlsx` | xlsx | 115,890 | Tomato 2026 RFP input workbook (a second-commodity input). |
| `tomato_field_split.xlsx` | xlsx | 17,849 | Tomato field-split working file (Conv/Org or field-vs-greenhouse split worksheet). |
| `wet_pack_veg_kickoff_2027-2028.docx` | docx | 242,807 | Wet/processed-pack veg kickoff narrative (2027–2028) — register item 3. |
| `xl_roma_pricing_backtest.html` | html | 24,442 | **HTML** Roma-tomato pricing backtest (a saved web/export pricing back-test; the one non-Office sample — text-ish but a saved report; not opened). |
| `z_tomato_2026_rfp_input.xlsx` | xlsx | 90,317 | A `z`-prefixed (variant/alt) tomato 2026 RFP input workbook. |

### `reference/samples/_allocation_models/` (5 files — the real human decision workbooks)

| File | Ext | Size (B) | What it is (described, not opened) |
|---|---|---|---|
| `2026.04.28_Sweet Potatoes Allocation model RD2_vCurrent.xlsx` | xlsx | 32,326,579 | **Sweet Potatoes RD2** allocation model (~32 MB, 19 sheets) — register item 11; drove scenario-tool design study §7; cross-check source for MANUAL_MODEL_FINDINGS. |
| `2026.05.19_Sweet Potatoes Allocation model RD4_vCurrent.xlsx` | xlsx | 31,587,558 | **Sweet Potatoes RD4** (~31 MB, 20 sheets, adds Booking Guide + Signoff) — register item 12; **the primary source MANUAL_MODEL_FINDINGS reads** for the modality/cost-construction verification. |
| `2026.05.26_Hybrid Onions Allocation model RD4_vCurrent.xlsx` | xlsx | 6,788,587 | **Hybrid Onions RD4** (~7 MB, 19 sheets, Conv/Org + vs-STLY sign-off) — register item 13. |
| `hybrid_onions_alloc_rd4.7z` | 7z | 5,834,735 | **7-zip archive** of the Hybrid Onions RD4 model (compressed upload of item 13; `.7z` accepted per incoming README). |
| `sweet_potatoes_alloc_rd2.7z` | 7z | 25,277,699 | **7-zip archive** of the Sweet Potatoes RD2 model (compressed upload of item 11). |

**Why these binaries exist (collective WHY):** they are the *real-data fidelity anchor* for the whole program.
The golden potato INPUT/OUTPUT pair (E-13) is the reproducibility oracle for the lifted v3 engine; the iTrade feed
seeds the history/scorecard layer (E-08); the bid workbooks (Divine/Marengo `.xlsx` + Lipman `.xlsb`) prove
multi-round, multi-template intake (the `.xlsx`↔`.xlsb` split is exactly the "two bid templates" the incoming
README asks to test); the kickoff `.docx` + prep `.xlsx` define the kickoff keystone schema; the allocation models
are the most complex current Excel and the evidence base for D43 pricing modality. Without them the system would be
validated only against synthetic fixtures — the #1 program risk (R1) the OLD audit names.

## 2c. Reference empty markers (2)

### `reference/as-built-db/.gitkeep`
- **path:** `/home/user/KR_RFP/reference/as-built-db/.gitkeep` · **ext:** (dotfile) · **empty?** **YES (0 B)**
- created/modified 2026-06-18 (census row 512, flagged EMPTY).
- **WHY empty / why it exists:** `as-built-db/` is the reserved landing folder for the *extracted/validated schema
  + Alembic-chain summary* that the single dedicated clean-room intake agent will emit IF/when isolated read
  access to the old repo is granted (per `reference/README.md` + ADR-0001). That intake hasn't happened, so the
  folder is empty — but git won't track an empty directory, so the `.gitkeep` placeholder preserves the reserved
  structure. **Empty is correct and intentional:** it marks "this boundary slot exists and is awaiting intake,"
  not a missing deliverable.
- **What breaks without it:** the reserved `as-built-db/` directory would vanish from the tree, erasing the
  documented intake target.

### `reference/samples/.gitkeep`
- **path:** `/home/user/KR_RFP/reference/samples/.gitkeep` · **ext:** (dotfile) · **empty?** **YES (0 B)**
- created/modified 2026-06-18 (census row 514, flagged EMPTY).
- **WHY empty / why it exists:** `reference/samples/*` is gitignored (real values never committed), but the
  *directory itself* must persist in the tree as the documented on-demand landing zone. `.gitignore:10` explicitly
  re-includes `!reference/samples/.gitkeep` so this one file survives the ignore rule and keeps the directory
  tracked while every actual sample stays ignored. Empty by design.
- **What breaks without it:** the `samples/` directory would not exist for a fresh clone (all contents ignored),
  and the documented drop-target would be gone.

---

# PART 3 — `mcp/**` — the harness (the MCP server's plugin face + the verification ORACLE)

**Two-runtime context (critical to read the rest correctly).** This repo has two runtimes (per CLAUDE.md +
DRIFT_RECONCILIATION §D): the **stateless console** (the web app over the governed Postgres DB) and the **MCP
harness** (a Claude-Code plugin that drives real RFP runs over a *per-run isolated* Postgres DB + a per-run git
file-vault). The MCP harness is the **live-run verification oracle** named in CLAUDE.md req #5 ("verify against …
the MCP harness"). `mcp/` is the **plugin packaging** of that harness — the agent definitions, the orchestrator
skill, and the MCP server registration. The actual server *code* lives at `backend/rfp_mcp/rfp_pilot_server.py`
(census rows 177–179, NOT this slice); `mcp/` is its deployable Claude-Code-plugin shell.

### `mcp/README.md`
- **path:** `/home/user/KR_RFP/mcp/README.md` · **ext:** `.md` · **empty?** no · **size:** 8355 B (census row 338)
- **what:** The harness's operating manual. Describes RFP_MCP as a deployable Claude-Code **plugin** wrapping a
  **stdio MCP server** that drives a real produce RFP end-to-end over a **per-run isolated Postgres DB + per-run
  git vault**, run as a **three-agent harness**. Covers: the three agents + their tool split; the three pieces
  (KR_RFP platform / RFP_MCP plugin / RFP_PILOT_VAULT); per-run isolation (D30) + version pinning (D32); full
  setup (clone, install backend venv + `mcp` SDK, bring up Postgres + migrate, env vars, register the server,
  install the plugin, point a session/routine at it); the tool list split across the two subagents; and the
  request→upload→ingest data-governance rule.
- **DETAILED WHY / what the MCP server exposes + why it is the oracle:** This README is the canonical statement of
  **what the MCP harness IS and why it is the verification oracle.** The harness exposes (via two subagents):
  - **engine (data) tools:** `setup_ingest` · `bid_template` · `ingest_bids` · `ingest_any` · `run_round` ·
    `select_award` · `record_adjustment` · `history` · `feedback`.
  - **secretary (admin/memory) tools:** `run_start` · `run_list` · `run_status` · `setup_template` · `remember` ·
    `add_memory` · `close_run` · `purge_run`.
  Every tool opens a session on the **run's OWN database** (`run_unit_of_work(run_slug)`), returns plain-language
  summaries (lots/DCs/rounds/awards — names, never raw keys), and names the exact file it generated. It is the
  **oracle** because: (a) each run is sealed in its own isolated Postgres DB (D30) + git-versioned `run_data.json`
  + git file-vault — runs can't contaminate each other and every artifact is reproducible/diff-able; (b) data
  enters only by formal request→upload→ingest (no silent pulls), so provenance is clean and auditable; (c) the
  engine subagent's context is data-only, so its commentary is *provably grounded in the sealed records* — exactly
  what you check the console/app against. The README also explains the **`rfp_mcp` not `mcp` package name** (the
  installed MCP Python SDK owns the top-level `mcp` import; naming our package `mcp` would shadow `from
  mcp.server.fastmcp import FastMCP`) and the smoke-check `pytest tests/mcp -q`.
- **What breaks without it:** an operator couldn't stand up or understand the oracle — no setup path, no env-var
  contract (`DATABASE_URL`, `PILOT_VAULT_ROOT`), no knowledge that runs are per-run-isolated or that the package
  must be `rfp_mcp`. The "verify against the harness" requirement would be unactionable.
- **Cross-ref:** census row 338. Points to `backend/rfp_mcp/rfp_pilot_server.py`, the two `agents/*.md`, the
  `skills/rfp-pilot/SKILL.md`, and `.mcp.json`. Decisions D30 (per-run isolation), D32 (version pinning), E-42
  (render-on-request), E-24/G-D (comms send), D28 (no invented reasons).

### `mcp/skills/rfp-pilot/SKILL.md`
- **path:** `/home/user/KR_RFP/mcp/skills/rfp-pilot/SKILL.md` · **ext:** `.md` · **empty?** no · **size:** 14129 B
- (census row 341). This is the **orchestrator skill** — the largest harness file and the behavioral contract.
- **what:** The Claude-Code skill definition (frontmatter `name: rfp-pilot` + description) for the **orchestrator**
  of the three-agent harness. It is the agent the buyer talks to. Sections: the harness/hub-and-spoke discipline;
  voice (produce-sourcing English); lead-with-the-kanban (every interaction); many-RFPs-at-once (always say which
  run); session renaming (`RFP · {commodity} · {run-slug} · {stage}`); formal data governance (request→upload→
  ingest); flexible ingest (`ingest_any` two-beat propose→confirm); scheduled nudges (Claude-Code routine);
  emails + mail-merge (draft→approve→generate from sealed records, names-not-keys); **LEGALESE MODE** (5-beat
  controlled commercial response); closing a run (archive→confirm→purge); the step-by-step loop table; and the
  "Always" checklist.
- **DETAILED WHY / why it is the verification-oracle's human interface:** The orchestrator is the **hub** of the
  hub-and-spoke harness — it touches **no data and no MCP tools directly**; it delegates everything to `rfp-engine`
  (data) or `rfp-secretary` (admin/memory) and relays results. This separation is what makes the harness an
  *oracle you can trust*: data questions are forced onto the engine ("Who did we recommend at Atlanta and why" →
  the engine answers by **reading the data**, never from conversational memory — req #5 + D28), and admin chatter
  is kept off the engine's context so its commentary stays grounded. The skill encodes the non-negotiables: leads
  with the kanban every time, always states which run, gates inbound RFP data behind formal upload, never
  hand-types a price/supplier/lot/date (merge values come from the governed store), and confirms before purge.
  **LEGALESE MODE** is a notable, fully-specified capability: a 5-beat (Acknowledgment / Principle / Application /
  Disposition / Close) controlled response that discloses only what supports the position, volunteers no
  facts/figures, and never implies reconsideration — a real commercial-correspondence tool, not a stub.
- **WHY shaped this way:** every behavior maps to a sponsor directive — calm/brief/one-ask (layman-client role
  contract), names-not-keys (auditability), per-run isolation D30, no-invented-reasons D28, no-file-storage
  (generated artifacts named + located, render-on-request). The step table is the canonical run lifecycle
  (Start → Setup ingest → Bid template → Ingest bids → Run round → Freeze award → Post-award reprice → History →
  Close), with the explicit versioning rule "re-running a round seals a NEW version, nothing overwritten."
- **What breaks without it:** the harness loses its conductor — there'd be no defined buyer-facing behavior, no
  hub-and-spoke discipline, no kanban-first/one-ask cadence, no governance gates. The engine/secretary subagents
  are tools; this skill is the orchestration that makes them an end-to-end run.
- **Cross-ref:** census row 341. Delegates to `agents/rfp-engine.md` + `agents/rfp-secretary.md`; tool names map
  to `backend/rfp_mcp/rfp_pilot_server.py`.

### `mcp/agents/rfp-engine.md`
- **path:** `/home/user/KR_RFP/mcp/agents/rfp-engine.md` · **ext:** `.md` · **empty?** no · **size:** 3417 B
- (census row 339).
- **what:** The **engine subagent** definition (frontmatter: `name: rfp-engine`, a tools allow-list, `model:
  claude-opus-4-8`). The DATA-DEDICATED agent: ingest setup/bids, generate the round's bid template, run the
  alignment, freeze an award, record a post-award reprice, and **answer data questions by reading the run's data**.
- **tools (frontmatter allow-list — the data-only scope):** `Read`, `mcp__rfp-pilot__setup_ingest`,
  `mcp__rfp-pilot__bid_template`, `mcp__rfp-pilot__ingest_bids`, `mcp__rfp-pilot__ingest_any`,
  `mcp__rfp-pilot__run_round`, `mcp__rfp-pilot__select_award`, `mcp__rfp-pilot__record_adjustment`,
  `mcp__rfp-pilot__history`, `mcp__rfp-pilot__feedback`.
- **DETAILED WHY:** This agent is **why the harness is a trustworthy oracle.** Its context is *only* the run's own
  isolated database and the run's files — nothing else. Every number, supplier, savings figure, or reason it gives
  must be **read from the sealed records** (the sealed `analysis_run`, scored bids, award split, ingested bid
  lines, history/feedback); if the data doesn't show a reason it says "the data doesn't show a reason," never a
  guess (D28). It operates on **one run at a time** against that run's own DB (D30). The tool-scoping in
  frontmatter is the mechanism: by *not* giving it Write or the admin/memory tools, its context can't be polluted
  by admin chatter — so its data commentary is provably grounded. Pinned to Opus 4.8 (must not fall back).
- **What breaks without it:** there'd be no data-grounded answerer; data questions would be answered from
  conversational memory (the exact failure mode req #5/D28 forbid), and the oracle property (commentary grounded
  in sealed records) would collapse.
- **Cross-ref:** census row 339. Tools resolve to `backend/rfp_mcp/rfp_pilot_server.py`. Decisions D28
  (no-invented-reasons), D30 (per-run isolation).

### `mcp/agents/rfp-secretary.md`
- **path:** `/home/user/KR_RFP/mcp/agents/rfp-secretary.md` · **ext:** `.md` · **empty?** no · **size:** 2856 B
- (census row 340).
- **what:** The **secretary subagent** definition (frontmatter: `name: rfp-secretary`, tools allow-list, `model:
  claude-opus-4-8`). The admin/memory agent: start a run, list runs, show the proactive kanban/status, generate
  the blank setup doc, write to NOTES.md, drop documents into `memory/`, and close-out (archive→confirm→purge).
- **tools (frontmatter allow-list — the admin/memory scope):** `Read`, `Write`, `mcp__rfp-pilot__run_start`,
  `mcp__rfp-pilot__run_list`, `mcp__rfp-pilot__run_status`, `mcp__rfp-pilot__setup_template`,
  `mcp__rfp-pilot__remember`, `mcp__rfp-pilot__add_memory`, `mcp__rfp-pilot__close_run`,
  `mcp__rfp-pilot__purge_run`. (Note it HAS `Write` — the engine does not; and it does NOT have the data tools.)
- **DETAILED WHY:** It "owns the noise" so the engine's data context stays clean — the complementary half of the
  context-separation that makes the engine grounded. It manages run lifecycle (`run_start` stamps a new run + its
  own isolated DB + setup doc; supports **`rehearsal=true`** → every artifact stamped SYNTHETIC so a practice run
  can never be mistaken for a live cycle — a NO-MVP/data-fidelity safety), the proactive kanban (`run_status` Done·
  Doing·Next·Waiting board), durable memory (`remember`→NOTES.md, `add_memory`→file into `memory/`), and close-out
  (archive then, only after confirm, purge — never purge first). It explicitly does **not** read/run data or
  explain recommendations (that's the engine's job); if handed a data question it bounces it to the engine.
- **What breaks without it:** run lifecycle, the kanban, durable memory, and safe close-out would have no owner; or
  they'd land on the engine and pollute its data context, breaking the oracle's grounding guarantee. The
  rehearsal=SYNTHETIC stamping (live-vs-practice safety) would have no home.
- **Cross-ref:** census row 340. Tools resolve to `backend/rfp_mcp/rfp_pilot_server.py`. D30 (per-run isolation).

### `mcp/.mcp.json` (local/plugin stdio registration)
- **path:** `/home/user/KR_RFP/mcp/.mcp.json` · **ext:** (dotfile) · **empty?** no · **size:** 1514 B (census 337)
- **what:** The MCP server registration for **local terminal Claude Code** (stdio transport). Registers
  `rfp-pilot` to launch `${CLAUDE_PLUGIN_ROOT}/../backend/.venv/bin/python -m rfp_mcp.rfp_pilot_server` with
  `cwd` = `backend/` and env `DATABASE_URL` (template `kr_rfp` DB) + `PILOT_VAULT_ROOT=${RFP_PILOT_VAULT}`.
- **DETAILED WHY:** This is the stdio half of the dual-runtime registration. It uses `${CLAUDE_PLUGIN_ROOT}` so the
  backend resolves *without* exporting `KR_RFP_BACKEND` (valid for the in-repo layout where the plugin is
  `<repo>/mcp` and the backend is `<repo>/backend`); `cwd=backend/` so CWD-relative paths resolve; and the package
  is `rfp_mcp` (NOT `mcp`) to avoid shadowing the MCP SDK. The embedded `//` comments document portability, the
  vault caveat (`PILOT_VAULT_ROOT` is deployment-specific → export `RFP_PILOT_VAULT`), and a **reliable-setup
  fallback** (`claude mcp add rfp-pilot --scope local --env … -- /abs/.venv/bin/python -m
  rfp_mcp.rfp_pilot_server`) for when `--plugin-dir` env-substitution varies by Claude Code version.
- **What breaks without it:** local terminal Claude Code couldn't spawn the stdio MCP server — no local harness.
- **Cross-ref:** census row 337. Pairs with the root `.mcp.json` (web/http variant, see Part 5) and `plugin.json`.

### `mcp/.claude-plugin/plugin.json` (plugin manifest)
- **path:** `/home/user/KR_RFP/mcp/.claude-plugin/plugin.json` · **ext:** `.json` · **empty?** no · **size:** 476 B
- (census row 336).
- **what:** The Claude-Code **plugin manifest**: `name: rfp-pilot`, a description (the 3-agent harness over a
  per-run isolated DB), `version: 0.1.0`, author `KR_RFP`, homepage `https://github.com/eddgue/RFP_MCP`, keywords.
- **DETAILED WHY:** This is what makes `mcp/` an installable Claude-Code **plugin** (so the orchestrator skill +
  the two subagents + the `.mcp.json` travel together as one unit). Critically, its **`version` pins a live run to
  a released build (D32)** — you can develop against a newer build without disturbing runs in flight. Without the
  manifest, the directory is just loose files, not a versioned, installable plugin.
- **What breaks without it:** `claude --plugin-dir`/`/plugin install rfp-pilot` wouldn't recognize the directory as
  a plugin; D32 version-pinning of in-flight runs would have no anchor.
- **Cross-ref:** census row 336. D32 (version pinning). Bundles the skill + agents + `.mcp.json` above.

---

# PART 4 — `infra/**` — local dev + deploy infrastructure (4 files)

Per `infra/README.md`: this phase ships **dev only** (DevOps PLAN §4); cloud/IaC (Terraform, managed Postgres,
secrets) is a later DEP-4 deliverable. The whole `infra/` exists to stand up Postgres 15 + the backend with one
command, and to bootstrap the eight-schema layout + a least-privilege role idempotently.

### `infra/README.md`
- **path:** `/home/user/KR_RFP/infra/README.md` · **ext:** `.md` · **empty?** no · **size:** 2927 B (census 333)
- **what:** Operator guide for the local stack: what's in each file; quick start (`cp .env.example .env`; `docker
  compose up -d`; `docker compose ps`); the API (`:8000 /health`) + Adminer (`:8080`) endpoints; logs/down/down-v;
  **how compose maps to `backend/.env`** (one typed setting `DATABASE_URL`, only the *host* changes across
  contexts — `db` service in compose, `localhost` on host, `postgres:postgres@localhost` in CI Actions, secret
  store in staging/prod); the psycopg-v3 driver matching SQLAlchemy 2.x + Alembic; migrations-on-startup
  (`alembic upgrade head` where rev 0001 runs `db/baseline/schema.sql`); and boundaries (no secrets in git, data
  volume gitignored, least-privilege role is local-only).
- **DETAILED WHY:** Reduces "stand up a working store" to one command (longevity + error-reduction per the
  decision-weighting rubric). The `DATABASE_URL`-shape-is-constant/only-host-changes table is the key idea: the
  same env-var name flows through dev/host/CI/prod, so there is one contract and no per-context rewiring. It also
  documents the **idempotency contract**: both the init script and Alembic rev 0001 `CREATE SCHEMA IF NOT EXISTS`
  the eight schemas, so a fresh container and a fresh DB agree regardless of order.
- **What breaks without it:** an operator wouldn't know the one-command path, the endpoints, the env mapping, or
  that `.env` must never be committed — onboarding friction + a real risk of committing secrets.
- **Cross-ref:** census row 333. Points to `docker-compose.yml`, `.env.example`, `postgres/init/01_schemas.sql`,
  `backend/.env.example`, `db/baseline/schema.sql`, ADR-0001 §4, ADR-0002 (frontend at Phase F), DevOps PLAN.

### `infra/.env.example`
- **path:** `/home/user/KR_RFP/infra/.env.example` · **ext:** (dotfile) · **empty?** no · **size:** 826 B (census 332)
- **what:** The compose-level env **contract** (template): `POSTGRES_USER/PASSWORD/DB` (all `kr_rfp`),
  `DATABASE_URL=postgresql+psycopg://kr_rfp:kr_rfp@db:5432/kr_rfp` (host = compose service name `db`),
  `APP_ENV=dev`. Header comments stress these are **SAFE PLACEHOLDERS for local dev only**, that `.env` is
  gitignored and never committed (ADR-0001 §4), and that CI/prod inject the same variable *names* from a secret
  store — only the *values* differ.
- **DETAILED WHY:** Gives a copy-to-`.env` starting point so `docker compose up` works immediately, while keeping
  the real `.env` out of git. The driver is psycopg (v3) to match SQLAlchemy 2.x + Alembic. The "same names,
  different values" discipline is what lets the README's context table hold (dev↔CI↔prod parity by name).
- **What breaks without it:** no template → operators guess the env shape; higher chance of a malformed
  `DATABASE_URL` or an accidentally-committed real `.env`.
- **Cross-ref:** census row 332. Consumed by `docker-compose.yml` (`${POSTGRES_*}`, `${DATABASE_URL}`,
  `${APP_ENV}`). ADR-0001 §4.

### `infra/docker-compose.yml`
- **path:** `/home/user/KR_RFP/infra/docker-compose.yml` · **ext:** `.yml` · **empty?** no · **size:** 1950 B (census 334)
- **what:** The local dev stack (compose project `kr-rfp`), three services: **`db`** (postgres:15; env from
  `${POSTGRES_*}`; named volume `db_data`; mounts `./postgres/init` → `/docker-entrypoint-initdb.d:ro`; port
  5432; healthcheck `pg_isready` 5s/10retries); **`backend`** (builds `../backend/Dockerfile`; command
  `sh -c "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"`; `DATABASE_URL` →
  the `db` service; `depends_on db: service_healthy`; source-mounts `../backend:/app` for hot reload; port 8000);
  **`adminer`** (adminer:4; default server `db`; port 8080). Named volume `db_data`.
- **DETAILED WHY:** One command → a healthy Postgres, the backend that **migrates then serves**, and a DB UI. The
  `depends_on: service_healthy` + healthcheck guarantees the backend only starts migrating once Postgres is
  actually accepting connections (error-reduction). The init mount bootstraps schemas+role on an empty volume,
  while `alembic upgrade head` (rev 0001 → `db/baseline/schema.sql`) is the authoritative migration — both are
  idempotent so order doesn't matter. The source mount + `--reload` gives dev hot-reload. The frontend (`web`)
  is intentionally absent (added at Phase F per ADR-0002).
- **What breaks without it:** no reproducible local stack; every dev would hand-wire Postgres + migrations + uvicorn.
- **Cross-ref:** census row 334. Reads `.env.example`/`.env`; mounts `postgres/init/01_schemas.sql`; builds
  `backend/Dockerfile`; runs `app.main:app` + Alembic rev 0001 (`db/baseline/schema.sql`).

### `infra/postgres/init/01_schemas.sql`
- **path:** `/home/user/KR_RFP/infra/postgres/init/01_schemas.sql` · **ext:** `.sql` · **empty?** no · **size:** 2201 B (census 335)
- **what:** The idempotent Postgres bootstrap run once on an empty data volume (via
  `/docker-entrypoint-initdb.d`). Creates the **eight domain schemas** (`ref` reference/master+tenant · `norm`
  normalization · `cyc` cycle keystone · `bid` bids/landed-cost/eligibility/capacity · `eng` sealed calc runs/
  scenarios/scores · `awd` awards/layers/signoff/docs · `perf` feeds: iTrade/KCMS/scorecards · `audit` hash-chained
  event log), and a **least-privilege `kr_rfp_app` role** (idempotent `DO` block since `CREATE ROLE` has no
  `IF NOT EXISTS`), with `GRANT USAGE` on the schemas and `ALTER DEFAULT PRIVILEGES` so future tables/sequences are
  app-usable (SELECT/INSERT/UPDATE/DELETE on tables; USAGE/SELECT on sequences).
- **DETAILED WHY:** Establishes the **eight-logical-layer architecture at the database level** before any table
  lands, and makes the app connect as a **non-superuser** (security: least privilege). Kept fully idempotent
  because Alembic rev 0001 (`db/baseline/schema.sql`) *also* ensures these schemas — both paths must be safe to
  run in either order (the README's idempotency contract). The eight schemas here are the same eight the OLD audit
  (`audit/03`) and the whole data model use, so the layering is consistent from bootstrap → baseline → ORM.
- **What breaks without it:** a fresh container would either lack the schema layout/role, or rely solely on Alembic
  — and the app would run as a superuser (no least-privilege boundary). The `ALTER DEFAULT PRIVILEGES` is what lets
  the app role use tables migrations create later without per-table grants.
- **Cross-ref:** census row 335. Mirrored/superseded-at-migrate-time by `db/baseline/schema.sql` (Alembic rev 0001).
  The eight schemas align with `audit/03_SCHEMA_DIFF.md`'s eight-layer crosswalk.

---

# PART 5 — root `.mcp.json` (web-runtime MCP registration)

### `/.mcp.json`
- **path:** `/home/user/KR_RFP/.mcp.json` · **ext:** (dotfile) · **empty?** no · **size:** 563 B (census row 7)
- **what:** The **repo-root** MCP registration read by **Claude Code on the web (cloud runtime)**. Registers a
  single server `rfp-pilot` of `type: "http"` at `url: http://127.0.0.1:8765/mcp`.
- **DETAILED WHY:** The web runtime **does not spawn stdio MCP servers**, so the rfp-pilot server runs as a **local
  HTTP server inside the session container** (started by the SessionStart hook `scripts/web_session_start.sh`) and
  is reached here over **loopback**. This is the web counterpart to `mcp/.mcp.json` (the stdio/local registration):
  same logical server, different transport because the runtime differs. The embedded `//` comment documents exactly
  this and points to `mcp/.mcp.json` / `claude mcp add` for local terminal use. It is the concrete wiring that
  makes the verification oracle reachable from a web session.
- **What breaks without it:** a web Claude Code session couldn't reach the rfp-pilot harness at all (no stdio in
  web; without the http registration there's no transport), so the oracle would be unavailable in the cloud runtime.
- **Cross-ref:** census row 7. Pairs with `mcp/.mcp.json` (stdio/local) + `mcp/.claude-plugin/plugin.json`; depends
  on the SessionStart hook `scripts/web_session_start.sh` to actually start the loopback server.
- **Root JSON census note:** This is the **only** JSON config at repo root in scope. `find . -maxdepth 1 -name
  "*.json"` returns only `.mcp.json`; there is no `package.json`, `tsconfig.json`, or other `*.json` at the repo
  root. (Census confirms exactly one root-level entry, row 7.)

---

# PART 6 — `audit/**` — the OLD as-built/gap audit (00–04), SUPERSEDED by `AS_BUILT/`

**SUPERSESSION (verified):** `VAULT.md:66` states verbatim: *"`audit/00–04` — the OLD as-built/gap audit;
superseded by `AS_BUILT/` (this fresh one). Audited in D5."* (`VAULT.md:23` similarly marks the related
`07_AS_BUILT_PROCESS_AUDIT` as "old — superseded by AS_BUILT/".) These 5 files are **git-tracked, NOT gitignored**,
and remain as historical record. They audit a *different and earlier* subject than `AS_BUILT/`: the OLD audit
(dated 2026-06-18) compares **two SPEC PACKAGES** (`specs/rfp-engine/` BRIEF vs `specs/original-engine/` AS-BUILT)
to recommend a target; `AS_BUILT/` (this current exhaustive audit) maps the **actual built repo** file-by-file.
They are kept because the OLD audit's decisions (D1–D5) and gap analysis (G1–G12) seeded the build that
`AS_BUILT/` now documents — it is the *provenance* of the current architecture, not a duplicate of it.

### `audit/00_EXECUTIVE_SUMMARY.md`
- **path:** `/home/user/KR_RFP/audit/00_EXECUTIVE_SUMMARY.md` · **ext:** `.md` · **empty?** no · **size:** 11567 B
- (census row 12). status: Final v1.0, 2026-06-18.
- **what:** The 2-page executive read of the OLD audit. Establishes the headline: **neither spec package is the
  product; they are two halves of one system** — the BRIEF has the right target shape/brain/governance philosophy
  but a thin/under-constrained data model and no real data; the AS-BUILT has a deep enterprise-grade data+governance
  spine (63 tables, 67 CHECKs, 46 composite FKs, sealed calc runs, 5-mode landed cost, 7-gate eligibility) but the
  *wrong brain* (exact min-cost single-winner) at the *wrong pricing layer*, missing the entire outward-facing half.
  Includes the single most important cross-package fact (the BRIEF's "verify before greenfield" #1 open item is
  **answered** by the AS-BUILT: a real governed store exists → build path is reconcile-and-extend, not greenfield),
  the enterprise-readiness scorecard, the ranked gaps G1–G12, the five sponsor decisions D1–D5, and the recommended
  next step (a single reconciled "v1.0 Build Spec").
- **DETAILED WHY (kept):** This is the origin of the entire program direction — D1 (reconcile-and-extend), D2 (adopt
  v3's scoring + split as the brain), D3 (lift pricing to kickoff + fire the safeties), D4 (outward-facing
  sequence, booking guide first), D5 (net-new tenancy/security/NFR + real-data pilot). Everything `AS_BUILT/` now
  audits descends from these decisions. Superseded *as the live spec* (the build moved past it), retained *as the
  rationale record*.
- **What breaks without it:** the "why is the architecture shaped this way" provenance would be lost; the
  reconcile-vs-greenfield decision could be re-litigated.
- **Cross-ref:** census row 12. depends_on: None (it is the root of the OLD audit chain). Superseded by `AS_BUILT/`.

### `audit/01_DOCUMENT_AUDIT.md`
- **path:** `/home/user/KR_RFP/audit/01_DOCUMENT_AUDIT.md` · **ext:** `.md` · **empty?** no · **size:** 15726 B
- (census row 13). status: Final v1.0; depends_on AUDIT-000.
- **what:** Assesses the two spec packages **as engineering artifacts** (structure, completeness, consistency,
  traceability, enterprise-readiness) independent of the gap analysis. Inventory/provenance table; BRIEF findings
  (strengths: best-in-class traceability via the 20-row discrepancy log, justified ADRs, honest seams; defects
  `[D-1]` foundational decision left open (Blocker), `[D-2]` the five pricing safeties named but unmodeled,
  `[D-3]` under-constrained schema (0 composite FKs, `volume_limit` has no PK, enums in prose, no immutability
  mechanism), `[D-4]` no NFR/security/tenancy, `[D-11]`/`[D-12]` minor); AS-BUILT findings (strengths: radical
  honesty, enterprise-grade modeling, real governance spine; defects `[D-5]` not self-verifiable (ECLS absent),
  `[D-6]` SQLite-shaped DDL + a vacuous CHECK, `[D-7]` audit hash-chain is scaffold not operative, `[D-8]`
  outward-facing half absent, `[D-9]`/`[D-10]` minor); cross-cutting `[X-1]` nothing run on real data (program
  blocker), `[X-2]` the two never reference each other, `[X-3]` naming mismatch; the scored rubric; and six
  document-level recommendations.
- **DETAILED WHY (kept):** Documents the *quality* basis for trusting each package and the specific defects that
  the build had to fix (e.g. `[D-6]` SQLite-isms → "regenerate on real Postgres"; `[D-7]` make the audit chain
  live). These map to drift items still tracked in DRIFT_RECONCILIATION (the audit hash-chain, the 2 write-points
  outside it). Retained as the defect provenance.
- **What breaks without it:** the per-defect rationale (`[D-1]`..`[X-3]`) that drove specific build fixes would be
  un-cited.
- **Cross-ref:** census row 13. depends_on AUDIT-000. Superseded by `AS_BUILT/`.

### `audit/02_GAP_ANALYSIS.md`
- **path:** `/home/user/KR_RFP/audit/02_GAP_ANALYSIS.md` · **ext:** `.md` · **empty?** no · **size:** 24626 B
- (census row 14, the **largest** OLD-audit file). status: Final v1.0; depends_on AUDIT-000, AUDIT-001.
- **what:** The exhaustive AS-BUILT↔BRIEF diff — the "gaps" deliverable. A one-screen capability matrix with a
  **disposition** per row (KEEP / RELAX / CHANGE / BUILD / MERGE) + severity; an ADR-by-ADR reconciliation (agree
  on 5, diverge on 3 — splits, decision-support, two-origins/feeds) with the ADR-numbering caveat; the twelve gaps
  in detail (**G1** single-winner→split [Crit], **G2** min-cost→5-factor scoring [Crit], **G3** entire `awd` layer
  [Crit], **G4** lift pricing to kickoff + fire safeties [High, MERGE both-ways], **G5** thin kickoff keystone
  [High], **G6** scorecard+iTrade receipt+KCMS [High], **G7** two origins + zip-centroid distance [Med], **G8** lot
  attribute taxonomy [Med], **G9** "sent" governance gate [Med], **G10** rail hardcoded→generated [Med], **G11**
  audit log scaffold→live [Med], **G12** Stage-0 in-gate [Med], + net-new tenancy/security/NFR [High]); the "KEEP"
  list (7 reverse-gaps the AS-BUILT is *more* enterprise-ready on); and a reconciliation map of where each target
  capability's shape vs rigor comes from.
- **DETAILED WHY (kept):** This is the *blueprint* the current build executed against. The G-numbers and the KEEP
  list are referenced throughout the live specs and `AS_BUILT/` (e.g. DRIFT_RECONCILIATION's "recorded but not yet
  built" perimeter is largely these gaps; MANUAL_MODEL_FINDINGS' D43 work is G4). Retained as the gap-to-build
  traceability.
- **What breaks without it:** the canonical gap taxonomy (G1–G12) and dispositions that the backlog/epics map to
  would lose their definition.
- **Cross-ref:** census row 14. depends_on AUDIT-000/001. Superseded by `AS_BUILT/`.

### `audit/03_SCHEMA_DIFF.md`
- **path:** `/home/user/KR_RFP/audit/03_SCHEMA_DIFF.md` · **ext:** `.md` · **empty?** no · **size:** 13398 B
- (census row 15). status: Final v1.0; depends_on AUDIT-002.
- **what:** The table-level diff (**AS-BUILT 63 tables vs BRIEF 36**) organized by the shared eight-layer model
  (`ref/norm/cyc/bid/eng/awd/perf/audit`), with a legend (= equivalent · ≈ different · ＋ present-here-only · ∅
  absent). Counts-at-a-glance (67 vs 14 CHECKs; 46 vs 0 composite FKs; SQLite-demo vs unbuilt-PG); per-layer
  crosswalk tables; the note that the AS-BUILT's 27-table surplus is *depth in the middle*, not breadth; and a
  migration-implications section (the AS-BUILT schema is the baseline but must be regenerated on real Postgres;
  additive vs the two breaking/grain migrations G1+G2; re-point not rebuild the commercial layer; the lot-lifetime
  change).
- **DETAILED WHY (kept):** It is the **crosswalk for authoring migrations** — it names which AS-BUILT tables map to
  which BRIEF tables and which are net-new, which is exactly the map the schema build followed. The eight-layer
  layout matches `infra/postgres/init/01_schemas.sql` (Part 4) — the same eight schemas from bootstrap through diff.
- **What breaks without it:** the table-by-table provenance of the current schema (why each table exists / where it
  came from) would be undocumented.
- **Cross-ref:** census row 15. depends_on AUDIT-002. Eight schemas align with `infra/.../01_schemas.sql`.
  Superseded by `AS_BUILT/` (which maps the *actual* schema; this maps the two *spec* schemas).

### `audit/04_RISKS_DECISIONS_ROADMAP.md`
- **path:** `/home/user/KR_RFP/audit/04_RISKS_DECISIONS_ROADMAP.md` · **ext:** `.md` · **empty?** no · **size:** 14524 B
- (census row 16). status: Final v1.0; depends_on AUDIT-000..003.
- **what:** Turns findings into action: (1) a ranked **risk register R1–R10** (R1 nothing-run-on-real-data is
  Critical; R2 wrong-brain lock-in; R3 greenfield-rebuild; R5 safeties decorative; R7 no security/tenancy — all
  High); (2) the **five sponsor decisions D1–D5** with recommended options (reconcile-and-extend; adopt v3 brain +
  split; lift pricing to kickoff + fire safeties; booking-guide-first outward sequence; tenancy+security from the
  start + real-data pilot as the Phase B gate); (3) a prose **target architecture diagram** (kickoff in-gate →
  feeds/norm → bid → eng sealed runs + bid_score + split → awd freeze/layer/signoff/docs → sign-off out-gate, with
  live audit hash-chain + tenancy/RBAC cross-cutting, UI last); and (4) a **phased roadmap 0→A→B→C→D→E→F**, each
  phase gated on a *demonstrated outcome* not a table count, with B (real-data pilot) as the inflection point.
- **DETAILED WHY (kept):** This is the **roadmap the program actually ran** — the phases, the decisions, and the
  risk-mitigations that the current build state (documented in `AS_BUILT/` + DRIFT_RECONCILIATION) is measured
  against. R1 (real-data) and R5 (safeties) are *still live* in DRIFT_RECONCILIATION's category B/C, so this file
  remains the reference for why those items matter. The "UI last / a good front end is a view onto the store"
  principle directly motivates the two-runtime split.
- **What breaks without it:** the risk/decision/phase rationale behind the current architecture and remaining
  perimeter would be un-anchored; R1/R5/R7's framing would lose its source.
- **Cross-ref:** census row 16. depends_on AUDIT-000..003. Decisions D1–D5 here are the OLD-audit decisions
  (distinct from the live `03_DECISION_LOG.md` D-numbers). Superseded by `AS_BUILT/`.

---

# Gaps / anomalies found in D5 (recorded per AUDIT_STANDARD rule 6 — "if unverifiable, say so")

1. **No true gaps in census coverage.** All 41 files in the D5 scope (3 triage + 4 reference text + 33 sample
   binaries + 2 empty markers — wait: 4 text incl. 2 v3-engine + 2 README + 1 register; recount below) are present
   in `FILE_CENSUS.md`. Exact in-scope file count audited: **3 (triage) + 6 (reference text: README, SAMPLE_
   REGISTER, incoming/README, v3 .py, v3 .ipynb) + 2 (empty .gitkeep) + 31 (sample binaries census-only) + 6 (mcp:
   README, 2 agents, SKILL, .mcp.json, plugin.json) + 4 (infra) + 5 (audit OLD) + 1 (root .mcp.json) = 58 files.**
   All matched to census rows.
2. **Census timestamp drift on quarantined files (expected, not a defect).** `reference/samples/*` and
   `reference/v3-engine/*` are gitignored, so the census uses filesystem mtimes which differ from current on-disk
   mtimes (e.g. `potato_2026_rfp_input.xlsx` census 2026-06-22T15:27Z vs on-disk 2026-06-18 10:47). The census
   header discloses this policy; flagged for completeness only.
3. **Two near-duplicate sample names** (not errors, distinct files): `kickoff_doc_prep.xlsx` (24,727 B) vs
   `kickoff_document_prep.xlsx` (1,129,317 B) — SAMPLE_REGISTER items 4 (small/prep) and 5 (full); and
   `tomato_2026_rfp_input.xlsx` (115,890 B) vs `z_tomato_2026_rfp_input.xlsx` (90,317 B) — a `z`-prefixed variant.
   Recorded so the pair isn't mistaken for a stray copy.
4. **Allocation models appear both raw and as `.7z`.** `_allocation_models/` contains both the uncompressed
   `.xlsx` (RD2 ~32 MB, RD4 ~31 MB, Onions ~7 MB) AND `.7z` archives of two of them (`sweet_potatoes_alloc_rd2.7z`
   25 MB, `hybrid_onions_alloc_rd4.7z` 5.8 MB) — i.e. the compressed upload + the extracted file both retained.
   Not a gap; the incoming README says `.7z`/`.zip` are accepted and extracted.
5. **Binaries not opened, per task instruction** (and per ADR-0001 quarantine they are gitignored real-value
   files). All binary descriptions derive from `SAMPLE_REGISTER.md`, `MANUAL_MODEL_FINDINGS.md`, filenames, and the
   incoming README — *not* from inspecting file contents. `xl_roma_pricing_backtest.html` is text-class but is a
   saved report binary-equivalent and was also not opened (census + describe only), consistent with the directive.
6. **v3 engine `.py` (4198 lines) characterized by section markers, not a full line-by-line read** — it is a
   gitignored quarantined reference monolith; AUDIT_STANDARD allows "vendored/generated/not-ours" bulk accounting,
   and this is the closest analogue (lifted reference, never imported). Its scoring weights + scenario set are
   captured from the markers; a deeper line-audit would belong to the engine slice (`backend/app/engine/`), not D5.
7. **Live data-fidelity violation surfaced (not a D5-file defect, but the most material finding the slice
   contains):** `project/triage/DRIFT_RECONCILIATION.md §B1` records that `backend/scripts/potato_legacy_dryrun.py`
   is the **active, unrepaired** data-fidelity violation D45 condemned, still wired into the Cloud Build seed
   (commits 32413af/dbbf071). This is outside D5's file scope (it's a backend script) but is the headline as-built
   risk the triage layer documents; flagged for the synthesizer/parent.
8. **`reference/incoming/` holds only its README** — no incoming files currently staged (the drop-zone is empty
   apart from instructions). Not a gap; it is a landing zone awaiting use.
