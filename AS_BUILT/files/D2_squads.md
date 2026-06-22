---
doc: AS-BUILT EXHAUSTIVE AUDIT — Slice D2 — project/squads/**
id: ASBUILT-D2
slice: D2
scope: /home/user/KR_RFP/project/squads/** (8 squad dirs · 22 .md files)
status: DONE (read end-to-end, cross-checked FILE_CENSUS rows 485–506, cross-ref project/triage/DRIFT_RECONCILIATION.md)
contract: /CLAUDE.md ABSOLUTE REQUIREMENTS injected; AUDIT_STANDARD.md honored (per-file: path·ext·empty?·what·detailed WHY·section outline·key specs/decisions·implemented-vs-aspirational)
census_xref: FILE_CENSUS.md rows 485–506 — exact 1:1 match with `find project/squads -type f`; no gaps, no extras; 0 empty files in this slice (all 22 non-empty)
---

# Slice D2 — `project/squads/**` exhaustive per-file audit

## 0. Scope reconciliation (census cross-check)

`find /home/user/KR_RFP/project/squads -type f | sort` → **22 files**, all `.md`, across **8 squad
directories**: architecture, engine-domain, experience, platform-data, platform-devops, product,
quality, security. Every file maps 1:1 to FILE_CENSUS.md rows **485–506**. No file in the census's
squads range is missing from disk; no file on disk is missing from the census. **Zero empty files**
in this slice (the 18 empty files tracked program-wide live elsewhere). Census byte-sizes match disk
exactly (e.g. architecture/PLAN.md 18547, security/PLAN.md 24694).

> **What this slice IS.** The squads tree is the program's **design/planning record** — one folder per
> delivery squad, each holding that squad's PLAN plus specs/spikes/studies it authored. These are
> *specifications and decisions*, not runtime code. Their implemented-vs-aspirational status is
> cross-referenced against `project/triage/DRIFT_RECONCILIATION.md` (the 2026-06-22 reconciliation of
> "record CLAIMS vs code") and noted per file. Recurring cross-references throughout: ADR-0001
> (clean-room), ADR-0003 (plan-then-scaffold), ADR-0006 (adopt v3 brain), ADR-0014 (pricing safeties),
> the D-series decisions (D11/D17–D32/D42–D45), the E-series epics, the G-series gaps, the S-series NFR
> criteria, and the R-series risks.

Per-file metadata (path · bytes · created · modified · lines · census row):

| # | Path | Bytes | Created | Lines | Census |
|---|------|-------|---------|-------|:------:|
| 1 | architecture/PLAN.md | 18547 | 2026-06-18 05:19 | 158 | 485 |
| 2 | architecture/SKELETON.md | 16909 | 2026-06-18 05:21 | 266 | 486 |
| 3 | engine-domain/GOLDEN_MASTER.md | 11227 | 2026-06-18 11:03 | 164 | 487 |
| 4 | engine-domain/PLAN.md | 9258 | 2026-06-18 05:20 | 128 | 488 |
| 5 | engine-domain/SPIKE_D2_engine.md | 9833 | 2026-06-18 05:19 | 142 | 489 |
| 6 | engine-domain/TOMATO_RUN.md | 5112 | 2026-06-19 13:26 | 87 | 490 |
| 7 | engine-domain/V3_ENGINE_LOGIC.md | 20054 | 2026-06-18 11:03 | 320 | 491 |
| 8 | experience/EMAIL_STYLE_AND_MAILMERGE.md | 3960 | 2026-06-19 21:25 | 64 | 492 |
| 9 | experience/HARNESS_REHEARSAL.md | 9248 | 2026-06-20 19:12 | 133 | 493 |
| 10 | experience/INTAKE_TEMPLATE_DESIGN.md | 13035 | 2026-06-21 00:01 | 166 | 494 |
| 11 | experience/PILOT_INPUT_DOCS_SPEC.md | 7577 | 2026-06-19 20:32 | 106 | 495 |
| 12 | experience/PILOT_SYSTEM_DESIGN.md | 11790 | 2026-06-19 21:25 | 149 | 496 |
| 13 | experience/SCENARIO_TOOL_DESIGN_STUDY.md | 35244 | 2026-06-19 19:26 | 417 | 497 |
| 14 | experience/SKILL_HARNESS_DESIGN.md | 5658 | 2026-06-20 16:21 | 93 | 498 |
| 15 | platform-data/CYCLE_FIELDTOMATO_STRUCTURE.md | 22885 | 2026-06-19 13:29 | 277 | 499 |
| 16 | platform-data/FEEDS_ITRADE.md | 6682 | 2026-06-18 10:36 | 94 | 500 |
| 17 | platform-data/PLAN.md | 18850 | 2026-06-18 05:20 | 192 | 501 |
| 18 | platform-devops/PLAN.md | 20312 | 2026-06-18 05:23 | 307 | 502 |
| 19 | product/KICKOFF_KEYSTONE_SPEC.md | 25817 | 2026-06-18 10:40 | 466 | 503 |
| 20 | product/PLAN.md | 9437 | 2026-06-18 10:37 | 155 | 504 |
| 21 | quality/PLAN.md | 21082 | 2026-06-18 05:24 | 275 | 505 |
| 22 | security/PLAN.md | 24694 | 2026-06-18 05:23 | 331 | 506 |

---

# A. ARCHITECTURE squad (`architecture/`) — 2 files

## A1 — `architecture/PLAN.md`
- **path:** `project/squads/architecture/PLAN.md` · **ext:** md · **empty?** no (158 lines, 18547 B) · created/modified 2026-06-18.
- **what:** ARCH-001 v0.1 "Target Architecture Plan" — the binding target architecture the Phase 0/A
  scaffold realizes; an *enterprise system of record*, not "a script with a database." No code in the doc.
- **DETAILED WHY:** This is the **architecture squad's keystone**. It exists to state the target shape
  so every other squad builds against one spine, and to enforce the inheritance rule (*shape/intent from
  the BRIEF; constraint discipline + the seven KEEP capabilities from the AS-BUILT; never regress to the
  brief's thinner schema, never carry the as-built's wrong brain*). Without it, the eight-layer model,
  engine-as-library boundary, and the immutability-by-construction posture would not be uniformly held;
  the program would risk hardening breadth on the wrong grain (R2). It is **binding under** ADR-0001
  (clean-room reconciliation), ADR-0002 (React/Next UI built last), ADR-0003 (plan-then-scaffold,
  backend-first).
- **section outline:** front-matter (id ARCH-001, depends_on audit/00–04 + spec packages + ADR-0001/2/3)
  → §1 Architectural principles (7 non-negotiables) → §2 Logical layers mapped to modules (the 8-layer
  table) → §3 Engine as a library behind a stable interface → §4 Cross-cutting concerns (4.1 multi-tenant
  context, 4.2 auth/RBAC boundary, 4.3 live audit event bus, 4.4 immutability app+DB) → §5 API style
  (contract-first OpenAPI) → §6 Component view (C4-ish, prose; Context/Containers/Components/Code) → §7
  Tech standards (config, typing, transaction discipline, migrations, naming, testing, observability) →
  §8 ADR backlog (0004–0015 table) → §9 What this plan defers → Changelog.
- **key specs / decisions recorded:**
  - **7 architectural principles:** (1) Store first; engine as a library; UI last. (2) Decision-support,
    never auto-assert. (3) Immutability by construction (enforced at *both* app and DB — "one layer is a
    convention, two is a control"). (4) Clean-room boundary (`backend/` never imports `reference/`; CI
    enforces). (5) Multi-tenant from the first migration (`client` first-class before breadth). (6)
    Contract-first (OpenAPI is source of truth; FE types generated). (7) Logical layers are physical PG
    schemas (`ref norm cyc bid eng awd perf audit`).
  - **The 8-layer→module map (§2 table)** — each PG schema = a `backend/app/domain/<layer>/` package,
    with owned tables and the "KEEP from as-built" column: ref (alias kinds + partial-unique-active index
    + quarantine), norm (sticky resolution + sha256 file lineage), cyc (scope-consistency trigger +
    invited-supplier denominator), bid (5-mode landed cost + 7-gate eligibility + capacity scopes +
    demand≠capacity CHECK), eng (sealed calc-run spine + hashed manifests + version pins), awd (net-new;
    lift v1.4 generators to render *from records*), perf (importer discipline + commercial component
    storage), audit (hash-chain design made live + write-only). **Reconciliation rule per layer:** brief
    gives shape/intent, as-built gives storage/constraints; the two breaking changes (`scenario_a_*` →
    `scenario`/`scenario_award`; single-winner → `volume_share`) ship together (G1+G2) and land in `eng`.
  - **Engine = pure library (§3):** single entry `run(inputs)->result` over dataclasses/pydantic; no DB/
    session/HTTP/clock/randomness except injected config; internals stubbed until the D2 spike resolves;
    the Runner seals the run (freezes inputs, hashes input/output manifests, records version pins).
  - **Transaction discipline (§4/§7):** services `add`+`flush`, **never `commit`**; one unit-of-work per
    request owns the commit (keeps audit writes in the same txn as the change).
  - **ADR backlog (§8):** ADR-0004 tenancy, 0005 audit-chain, 0006 engine-library interface, 0007 error
    taxonomy, 0008 naming canonicalization, 0009 RBAC, 0010 immutability strategy, 0011 lot lifetime,
    0012 pricing-at-kickoff + safeties, 0013 migration/baseline, 0014 document generation, 0015 data
    classification/retention. (0004–0008 needed for the scaffold.)
- **implemented vs aspirational (DRIFT xref):** The *architecture itself* is the foundation that DRIFT
  category A confirms held: the engine spine, governed-persistence, sealed/immutable runs, freeze-and-
  layer, the two-runtime split — all built faithfully. **Drifted/below-bar:** principle #5 (multi-tenant
  from migration one) — DRIFT B.3: built as `client_id` on a couple of `ref` tables, **no RLS**;
  principle #1's "UI last" landed but with 4 MVP-cut frontend surfaces (DRIFT B.2). The ADR backlog is
  partially realized (ADR-0001/0003/0006 ratified and enforced; 0009 RBAC defined but zero routes call it
  — DRIFT C). The §4.3 audit bus has 2 write-points outside the hash-chain (setup-ingest, capacity-
  ingest — DRIFT B.4).

## A2 — `architecture/SKELETON.md`
- **path:** `project/squads/architecture/SKELETON.md` · **ext:** md · **empty?** no (266 lines, 16909 B).
- **what:** ARCH-002 v0.1 "Phase 0/A Repository Skeleton Spec" — the exact monorepo layout + must-have
  starter files, "precise enough to create verbatim." Realizes ARCH-001; obeys ADR-0001/0003.
- **DETAILED WHY:** Translates the abstract architecture into a concrete, buildable tree so the scaffold
  is unambiguous and the clean-room boundary is physically expressed (`reference/` is input-only;
  `db/baseline/` is the re-expressed schema, never imported). It exists so an agent can scaffold the repo
  without re-deciding layout, and so the layer map is visible "from day one" (the other 7 domain packages
  ship as empty-but-present so the 8-layer spine is legible even before they fill). Without it the
  scaffold's directory conventions, the CI gate set, and the build order would be improvised.
- **section outline:** §0 Top-level layout (the tree + per-dir purpose table) → §1 `backend/` full tree
  (core/{config,db,security,audit,errors}, domain/{ref,norm,cyc,bid,eng,awd,perf,audit}, engine/
  {interface,stub}, api/v1/*, alembic, tests) + must-have starter list → §2 `frontend/` stub-only → §3
  `db/baseline/` (schema.sql, NAMING_MAP.md, README) → §4 `infra/` (docker-compose, postgres/init/
  01_schemas.sql) → §5 `reference/` quarantine → §6 `.github/workflows/ci.yml` (6 jobs) → §7 root
  housekeeping → §8 build order + exit gate → Changelog.
- **key specs / decisions recorded:**
  - **The canonical backend tree** — `app/core/` (config, db {base,session,types}, security {principal,
    tenant,rbac,deps}, audit {events,writer,guards}, errors {taxonomy,handlers}); `app/domain/<layer>/`
    each with (models, schemas, repository, service); `app/engine/{interface,stub}.py`; `app/api/v1/`
    (health, cycles, bids, runs, awards, documents, ingest).
  - **`ref` is wired end-to-end first** as the reference-implementation pattern; other 7 domain packages
    ship as empty-but-present `models.py` stubs so the layer map is visible.
  - **5 CI guard tests from day one:** `test_health.py`, `test_migrations_roundtrip.py` (up→down→up),
    `test_cleanroom_import.py` (backend never imports reference), `test_tenant_isolation.py`,
    `engine/test_engine_stub.py` (pure + deterministic).
  - **CI `ci.yml` 6 jobs:** lint (ruff), types (mypy), clean-room guard, migrations (roundtrip),
    tests (pytest on real PG), frontend (light). Gate: merge only on green; clean-room + roundtrip
    non-negotiable.
  - **Exit gate (§8):** `docker-compose up` → healthy Postgres w/ 8 schemas; `alembic upgrade head`
    applies the baseline clean; `/health` green; CI passes incl. clean-room + roundtrip; engine interface
    fixed with a stub behind it.
- **implemented vs aspirational (DRIFT xref):** Largely realized — the backend tree, the engine
  interface+stub, the migration chain, and the CI guards exist (DRIFT A confirms the spine and the two-
  runtime split). Notable drift from this skeleton: the `api/v1/awards.py`/`cycles.py`/`documents.py`/
  `ingest.py` routers named here are **present-but-empty stub files** — the real award/comms/freeze/
  savepoint capability lives in `api/v1/runs.py` (23+ routes) instead (DRIFT D — "looks lost but isn't";
  dead files, not capability gaps, except `ingest.py` which genuinely has no feed). The `frontend/` grew
  beyond the stub but with MVP cuts. `db/baseline/schema.sql` exists (the baseline is real).

---

# B. ENGINE-DOMAIN squad (`engine-domain/`) — 5 files

## B1 — `engine-domain/V3_ENGINE_LOGIC.md`  ★ (prompt-named priority)
- **path:** `project/squads/engine-domain/V3_ENGINE_LOGIC.md` · **ext:** md · **empty?** no (320 lines,
  20054 B) · status: **Verified (reproduced the golden output, 2026-06-18)**.
- **what:** ENG-V3-LOGIC — the **clean-room logic extraction** of `rfp_analysis_engine_v3.py` (4,198
  lines, QUARANTINED/gitignored, read-never-imported). Describes v3's LOGIC only (algorithms, thresholds,
  weights) with line refs. No verbatim engine code, no real prices/names/values.
- **DETAILED WHY:** This is **the single most load-bearing spec in the slice** — it is the authoritative
  description of the engine "brain" the program adopts (ADR-0006, Option A). It exists so the lifted
  clean-room implementation reproduces v3 *bit-for-bit on the numbers* without ever importing the
  quarantined source (ADR-0001). Constants (band thresholds, weights, caps) are reproduced exactly
  because they are **logic, not sensitive**. Validation status: run against the golden Potato 2026 input,
  reproduced the golden output with **zero numeric diffs across 180,600 numeric cells** (Detailed
  Scoring, Recommendations, DC Constraint Review, Bidder Detail). Without this file, the engine cannot be
  faithfully rebuilt, the golden-master test has no spec to assert against, and the "no wrong brain" rule
  (R2) cannot be met.
- **section outline:** front-matter → intro (stateless file-in/file-out monolith; lift steps 1–7, replace
  8–9 with the doc generator) → §1 the 9-step pipeline (table, lines 117–4198) → §2 scoring — the five
  banded factors (2.1 price, 2.2 coverage, 2.3 historical, 2.4 Z-risk, 2.5 continuity, 2.6 composite +
  weights + normalization) → §3 eligibility gates → §4 allocation `max_two_per_dc` split (4.1 strength
  rank, 4.2 per-lot award, 4.3 fallback fill, 4.4 cap-breach, 4.5 concentration cap) → §5 scenario lenses
  A–G → §6 deterministic tie-break sort → §7 cost construction (All-In primary + fallback) → §8 CONFIG
  schema (every key) + input tab→column contract → §9 mapping to our reconciled store + the gap list.
- **key specs / decisions (VALUE-LEVEL — every band/formula recorded):**
  - **9-step pipeline:** 1 Load config (117–202), 2 Schema validation (warn-only, 204–218), 3 Load input
    (220–519), 4 DQ checks (non-blocking, 521–577), 5 Price construction & scoring (579–813), 6 Scenarios
    (815–1111), 7 Analytics (1113–1335), 8 Build workbook (openpyxl, **not lifted**), 9 Save (**not
    lifted** — our Runner writes sealed records).
  - **Five banded factors (all 0–100):**
    - **Price** (w 0.35): `PremVsLow=(Price−MktMin)/MktMin`; ≤3%→100, ≤7%→80, ≤12%→50, >12%→20.
    - **Coverage** (w 0.25): `TotalCovRatio=TotVolOffered/TotVolReq`; As-Needed→**70** (fixed); NaN→30;
      <0.50→0; <0.80→40; <1.00→70; ≤1.20→100; >1.20→95.
    - **Historical** (w 0.20): `DeltaVsHistPct=(Price−IncRouting)/IncRouting`; no baseline→50; ≤−10%→100;
      ≤−3%→85; ≤+3%→70; ≤+7%→45; >+7%→20.
    - **Z-Risk** (w 0.10): `ZScore=(Price−MktAvg)/MktStd`; in[−1,+1]→100; <−2→60; >+2→40; else→80.
    - **Continuity** (w 0.10): `Supplier==Incumbent ? 100 : 0`.
    - **Composite:** `RecScore = Σ(factor·weight)`, `.round(2)`; NaN factors `.fillna(0)` first.
    - **Weight normalization (lines 143–146):** if `|Σw − 1.0| > 0.01`, WARN and divide every weight by
      `Σw` (e.g. 120% → renormalized to 1.0). **"Cost is 35% of the decision, not 100%."**
  - **Eligibility gates (785–800):** Eligible iff (1) Price not NaN AND >0, (2) PremVsLow ≤ MaxPremThresh,
    (3) As-Needed OR coverage NaN OR TotalCovRatio ≥ 0.80. `GateFlag` reason codes: No valid price / Price
    premium exceeds threshold / Insufficient volume (<80%) / Low price outlier (Z<−2) / High price outlier
    (Z>+2) / Low bidder count (<3). Outlier + low-bidder flags are **advisory** (recorded, not
    disqualifying); only gates 1–3 set `Eligible=False`.
  - **Split allocator `max_two_per_dc` (963–1000):** per (DC,TF) — strength `SupRankScore =
    AvgScore·0.60 + LotsCovered·5 + clip(AvgCoverage,0,1.2)·10`; sort `[SupRankScore desc, AvgPrice asc]`;
    keep top `max_sup_dc` (default **2**); award each lot to best by deterministic sort; fallback fill
    from the wider field tagged `_D_Fallback=True`. **Cap-breach** (1909–1912): per (DC_ID,TF) in
    Scenario B, `CapBreach = nunique(Supplier) > max_sup_dc` → `cap_breach_flag`. **Concentration cap
    0.40** (3998–4075): `conc_pct = supplier_RecSpend / total_B_RecSpend ≥ conc_thresh` → category-spend
    flag (distinct from the per-DC cap; both surface, neither auto-rejects).
  - **Scenario lenses A–G (913–1085):** A Lowest Cost (benchmark, never auto-applied); B Risk-Adjusted
    (highest RecScore, the main recommendation, with a `RecType` label: Lowest cost ≤2% / Coverage
    advantage WeeklyCovRatio>1.2 / Comparable ≤3% / Defensible ≤7% / else Risk-adjusted); C Incumbent
    Defense (incumbent if `PremVsLow≤0.03` AND coverage≥0.80, else fall back to B); D Max-N per DC (the
    split allocator); E Exclusion; F Custom Override; G Preferred Supplier.
  - **Deterministic tie-break sort (903–911):** `[RecScore desc, Price asc, TotalCovRatio desc, _IncBoost
    desc, Supplier asc]` where `_IncBoost=(Supplier==Incumbent)`. **"Load-bearing for reproduction."**
  - **Cost construction (589–603):** `Price = AllIn` if present else `FOB + DeliverySurcharge +
    VegCoolSurcharge − LotDiscount − AllLotDiscount`. **The double-subtract footgun:** discounts only
    applied in the fallback branch; our store enforces ONE path via the `no_double_discount` CHECK. Rows
    with Price NaN or ≤0 are dropped. **Prior-round price caveat (884–896):** R1 lookup keys
    `(Lot_ID,TF,Supplier)` — **no DC** → round deltas are lot-level only until prior bids carry DC pricing.
  - **CONFIG schema (§8):** every key + default — `max_sup_dc`=2, `global_thresh`=0.12, `conc_thresh`=
    0.40, weights 0.35/0.25/0.20/0.10/0.10, THRESH_COMPARABLE=0.03, THRESH_DEFENSIBLE=0.07,
    THRESH_MAX=global; active TFs (`TFn`, col E=YES), active rounds (`Rn`, col D=YES). Input tab→column
    contract for all 13 tabs (IN_Bids/Incumbents/Volumes/Premiums/Custom/Exclusions/Preferred/
    VolumeLimits + DIM_Suppliers/Lots/DCs/Rounds; header row 4 except IN_Custom row 6).
  - **§9 store mapping + the 5 gaps:** (1) **Split grain — the top gap:** as-built `scenario_award` has
    `UNIQUE(run,dc,lot,tf)` single-winner + no `volume_share`/`is_fallback`/`cap_breach_flag` → relax +
    add 3 columns (ships with E-18/E-20). (2) incumbent identity per (DC,Lot). (3) vol-offered columns on
    `bid.bid`. (4) prior-round price keyed without DC. (5) per-lot premium override + As-Needed flag.
- **implemented vs aspirational:** DRIFT A confirms the engine logic is **built full-fidelity and
  tested** — v3 5-factor banded scoring (`engine/scoring.py`), 7 lenses A–G (`engine/allocation.py`),
  split + cap-breach, canonical formula registry (`engine/formulas.py`). The §9 split-grain gap was
  **closed** (DRIFT A lists sealed reproducible runs + split awards as built). Caveat flagged in DRIFT
  B.6: the runner omits `all_lot_discount` when building `BidComponents` (`runner.py:300-306`) though the
  formula supports it — possible silent under-count needing a check.

## B2 — `engine-domain/GOLDEN_MASTER.md`  ★ (prompt-named priority)
- **path:** `project/squads/engine-domain/GOLDEN_MASTER.md` · **ext:** md · **empty?** no (164 lines,
  11227 B) · status: **Designed (golden pair verified to reproduce, 2026-06-18)**.
- **what:** ENG-GOLDEN-MASTER — designs the **Phase-D exit gate** (ADR-0006, S2): the test that proves
  the lifted engine reproduces v3's scored/allocated numbers. Structure + assertions only; **no real
  prices/names/values**. The real golden pair (`potato_2026_*`) is QUARANTINED/gitignored; CI uses a
  SYNTHETIC fixture.
- **DETAILED WHY:** This is **how "the engine IS v3" stops being a claim and becomes a test.** It exists
  to (a) record that v3 was already run (pandas 3.0.3, numpy 2.4.6, openpyxl 3.1.5) and reproduced the
  golden output with **zero numeric diffs across 180,600 cells**, confirming the golden pair is a valid
  fixed target and v3 is deterministic; and (b) design a **committable synthetic golden** so CI can gate
  the stub→v3 swap without exposing real commercial data. Without it the reproducibility gate has no
  assertion set and no non-sensitive fixture; the swap could ship unverified.
- **section outline:** front-matter (note: synthetic CI fixture) → intro (validation already performed:
  Detailed Scoring 95,251 + Recommendations 43,771 + DC Constraint Review 4,797 + Bidder Detail 36,781 =
  180,600 cells, zero diffs) → §1 INPUT schema 13 tabs → §2 OUTPUT schema 20 tabs (with golden
  rows×cols dims) → §3 Assertion set (3.1 scoring band edges, 3.2 eligibility, 3.3 split allocation, 3.4
  scenarios, 3.5 cost construction) → §4 durable fixture strategy (the committable synthetic golden, 5
  steps) → "Why synthetic, not the real pair."
- **key specs / decisions recorded:**
  - **20 output tabs with golden dims:** Executive Summary 40×10, Award Recommendations 328×26, Preferred
    Scenario 339×20, Regional Summary 77×25, Vol Utilisation 17×20, Share of Business 71×30,
    Recommendations 2272×35, Scenario Comparison 328×35, Lowest Cost Check 328×16, Top 5 Bids 545×22, DC
    Constraint Review 1020×22, Bidder Detail 4824×20, Custom Scenario 339×38, Supplier Overview 21×19, TF
    Comparison 198×16, Round Evolution 4824×21, Coverage Analysis 4824×18, **Detailed Scoring 4824×30**
    (the primary reproduction target), Missing Data 18×10, Glossary 48×14.
  - **Assertion tolerances:** ≤0.5 on each band/RecScore; spend/savings exact to the cent; flags/codes
    exact (string equality). Band-edge rows placed *exactly at boundaries* to prove the cascades (Price
    0.00/0.03/0.0301/0.07/0.0701/0.12/0.1201; Coverage 0.49/0.50/0.79/0.80/0.99/1.00/1.20/1.21/NaN/
    As-Needed; Historical −0.11/−0.10/−0.03/+0.03/+0.07/+0.08/no-baseline; Z 0/−2.1/+2.1/+1.5).
  - **The committable synthetic golden (§4):** author `synthetic_rfp_input.xlsx` (same 13-tab schema,
    generic S01..S06/DC01..DC03/LT01..LT04/TF1..TF2/R1-R2) engineered so **every band edge and branch
    fires once** (~30–60 bid rows); run v3 once locally; distill to `golden_expectations.json` under
    `backend/tests/fixtures/`; CI test `test_engine_reproduces_v3`; regeneration discipline recorded.
    **Do NOT commit the full 20-tab workbook.**
- **implemented vs aspirational:** The golden-master *test design* is the Phase-D gate; DRIFT A confirms
  the engine is "tested" and reproducible. QA/PLAN.md §2 operationalizes this same assertion set. The
  real-pair validation is done (recorded here); the synthetic CI fixture is the committable form. Note:
  the TOMATO_RUN (B6) surfaced a NEW required fixture case — a **single-round cycle** — not in this doc's
  R1/R2 multi-round synthetic plan.

## B3 — `engine-domain/SPIKE_D2_engine.md`
- **path:** `project/squads/engine-domain/SPIKE_D2_engine.md` · **ext:** md · **empty?** no (142 lines,
  9833 B) · status: Spike (recommends; does not assume the answer).
- **what:** ENG-SPIKE-D2 — the architecture spike that decides the **engine brain**: Option A (adopt v3's
  5-factor scoring + `max_two_per_dc` split) vs Option B (keep the as-built min-cost single-winner solver
  and bolt scoring on later). **Recommends Option A.**
- **DETAILED WHY:** This is the decision record that retires **R2 (wrong-brain lock-in)** before any
  breadth hardens on a wrong grain. It exists because the program can keep only one brain at the core; the
  as-built default of a single lowest-cost winner is contradicted by the real sign-off decks (which split
  DCs across suppliers, e.g. "Onions52, Owyhee") and by the 5-factor decision (cost only 35%). Choosing
  wrong here would force re-graining every downstream `awd.*` consumer. The recommendation is explicitly
  **pending validation** against the golden pair (which GOLDEN_MASTER then closed).
- **section outline:** §1 the decision stated once (A vs B) → §2 what "the real behavior" is (4 verified
  facts) → §3 evaluation matrix (4 axes: fidelity / rework / R2 lock-in / G1+G2 ship-together) + clean-
  room note → §4 RECOMMENDATION Option A + scope guard (permit-not-force) → §5 validation method
  (reproduce v3) → §6 what's needed to finalize (the v3 `.py` + a golden input/output pair) → §7 decision
  record.
- **key specs / decisions recorded:**
  - **Recommendation: Option A** — adopt v3; retire the as-built min-cost solver to **Scenario A =
    lowest-cost reference** (a benchmark lens, never auto-applied). Single strongest reason: only Option A
    is faithful to the verified real behavior at the core.
  - **Ship together:** G1 (split / `volume_share`) + G2 (scoring / `bid_score`) as ONE increment (E-18 +
    E-20), Phase D — which Option B "structurally cannot."
  - **Scope guard (permit-not-force):** the auto scenario still defaults to one supplier/DC; a cell *may*
    split only when a per-DC/per-lot `splittable` flag is set, bounded by capacity.
  - **Clean-room note:** "adopt v3" = lift LOGIC only; no Excel-formatting code ported (~2/3 of the
    monolith); v3's `.py` enters only via the ADR-0001 isolated reference intake; read-never-imported.
  - **Restraint preserved:** decision-support only; `BANNED_DECISION_WORDS` guard; human selects.
  - **§6 the two sponsor asks:** the v3 `.py` (md5 `c73ffc5…`, ~4,244 lines) + one golden input workbook
    that v3 ran clean + its output. "Single most important file to request first: the golden input + its
    v3 output pair."
- **implemented vs aspirational:** Option A was **adopted and built** (DRIFT A: v3 5-factor scoring + 7
  lenses + split allocation are all in code). The validation it was "pending" on is **closed** (V3_LOGIC
  + GOLDEN_MASTER both record zero-diff reproduction). Permit-not-force is realized via the splittable-
  flag posture. Fully resolved spike.

## B4 — `engine-domain/PLAN.md`
- **path:** `project/squads/engine-domain/PLAN.md` · **ext:** md · **empty?** no (128 lines, 9258 B) ·
  status: Draft.
- **what:** ENG-PLAN — the Engine & Domain squad plan: the engine as a **library behind a stable
  interface**, its service decomposition, what it writes (sealed `eng.*`), the REST surface, the stub
  strategy while D2 is open, and the squad's roadmap slice.
- **DETAILED WHY:** This is the squad's execution contract. It exists to decompose the engine into pure,
  independently-testable services (so the lifted v3 logic can be built and tested piecewise), to fix the
  `run()` boundary so every upstream/downstream consumer builds against the contract not the math (enabling
  a stub→real swap with no consumer churn), and to declare the sealed write tables and the **banned-from-
  the-engine** rules (no code asserts an award / writes `awd.*` / emits a decision verb). Without it the
  engine could leak decision authority or couple consumers to an unvalidated implementation.
- **section outline:** §1 the stable interface (`run(cycle_id, round_code, config) -> run_id`) → §2
  service decomposition (eligibility consumer, landed-cost consumer, scorer, scenario builder A–G, split
  allocator, pricing-safety executor G4, engine runner) + "Banned from the engine" → §3 what it writes
  (sealed `eng.analysis_run`/`bid_score`/`scenario`/`scenario_award`) + the breaking migration → §4 REST
  API surface (7 representative endpoints) → §5 engine stub strategy (4 steps) → §6 sequencing.
- **key specs / decisions recorded:**
  - **Interface:** `run(cycle_id, round_code, config) -> run_id`; reads bids/volume/incumbent-cost/config;
    computes `bid_score` + eligibility + scenarios A–G incl. split; writes sealed `eng.*`. **A correction
    is a new run, never an edit.**
  - **KEEP vs LIFT per service:** eligibility (consume as-built 7-gate/12-code, don't reimplement),
    landed-cost (consume as-built 5-mode, enforce single All-In path via `no_double_discount`), scorer
    (**lift v3 logic**), scenario builder (lift v3 lens semantics), split allocator (**lift v3** —
    permit-not-force, `conc_thresh` 0.40 → `cap_breach_flag`), pricing-safety executor G4 (MERGE: as-built
    `commercial_*` storage + brief placement; the five safeties read from kickoff), engine runner (lift
    v3 9-step, drop steps 8–9).
  - **Banned from the engine:** any code that asserts an award, writes `awd.*`, or emits a decision verb;
    `BANNED_DECISION_WORDS` guard; selection (`scenario`→`awd.award`) is a separate downstream service.
  - **Breaking migration:** relax `UNIQUE(run,dc,lot,tf)` + add `volume_share`; generalize `scenario_a_*`
    → `scenario`/`scenario_award`; ships with E-18/E-20 as one increment.
  - **REST surface:** `POST /cycles/{id}/rounds/{r}/run` (async 202+poll), `GET /runs/{id}`,
    `/runs/{id}/scores`, `/runs/{id}/scenarios`, `/runs/{id}/scenarios/{code}/awards`,
    `/runs/{id}/scenarios/compare`, `/cycles/{id}/pricing/safeties`. Selection/freeze/sign-off endpoints
    are owned downstream (E-21–E-23), not the engine.
  - **Stub strategy (§5):** freeze the signature now; ship a deterministic stub (as-built min-cost solver
    writing valid-shaped `bid_score` cost-only, single scenario A, single-winner awards `volume_share=1.0`,
    tagged `engine_version=stub`); swap-don't-rewrite when D2 validates; CI fails if backend imports
    reference.
- **implemented vs aspirational:** Most built (DRIFT A). The G4 pricing-safety executor is **NOT built**
  (DRIFT C: E-29 safety reprice + USDA feed — "5 safety types stored, never computed"). The REST surface
  reality: award/comms/freeze capability lives in `api/v1/runs.py` (23+ routes), not the same-named domain
  routers (DRIFT D). The stub existed and was swapped per the validated path.

## B5 — `engine-domain/TOMATO_RUN.md`
- **path:** `project/squads/engine-domain/TOMATO_RUN.md` · **ext:** md · **empty?** no (87 lines, 5112 B)
  · status: Run attempted 2026-06-19 — completed steps 1–5 + most of 6, **crashed at step 6/9**.
- **what:** ENG-TOMATO-RUN — the outcome of running v3 against the **real Field Tomatoes 2026** engine
  input (quarantined, read+run, never imported). STRUCTURE + OUTCOME ONLY; no real values; no output
  workbook produced (crashed before save); run in `/tmp`.
- **DETAILED WHY:** This file exists to record a **genuine latent v3 defect** discovered by running a
  second, structurally different real cycle: **v3 cannot complete on a single-round cycle.** It matters
  because it (a) corroborates that lifted steps 1–5 are sound on real data beyond Potato, and (b) adds a
  hard requirement to the lifted engine + its test fixtures (guard the prior-round lookup; add a single-
  round case). Without it, the lifted engine could inherit the same crash and the synthetic fixture
  (R1/R2 only) would miss it.
- **section outline:** intro → Environment (pandas 3.0.3 / numpy 2.4.6 / openpyxl 3.1.5) → Outcome (step
  table 1–9; crash at 6 with `TypeError: 'NoneType' object is not subscriptable`) → Root cause (the
  unguarded prior-round price lookup `prior_round['Round']` when `prior_round=None`) → Reproduction value
  → Data-handling confirmation.
- **key specs / decisions recorded:**
  - **Root cause:** the step-6 prior-round price lookup indexes `prior_round['Round']` unconditionally;
    CONFIG correctly sets `prior_round=None` for a single-round cycle, so `None['Round']` → TypeError.
    Never fired in the multi-round Potato golden run; the real Tomato cycle is **R1-only** (first input to
    exercise the unguarded branch). Not caused by empty incumbents/volumes or stale identity (those only
    warned).
  - **New requirement:** the lifted engine must guard the prior-round lookup (skip round-evolution /
    R1_Price derivation when `prior_round is None`, emit lot-level-only deltas per V3_LOGIC §7); add a
    **single-round cycle** case to the golden/synthetic fixture matrix (E-13). Per clean-room rules the
    quarantined `.py` was **not modified** — bug reported, not patched.
  - **Corroboration:** steps 1–5 (config parse, weight renormalisation 120%→1.0, group-key, 5 banded
    factors, eligibility) ran clean on 360 bid rows across 1 round / 40 DCs.
- **implemented vs aspirational:** This is an empirical finding feeding the lifted engine's requirements;
  the guard is a build requirement carried to E-13. The single-round-fixture gap it identifies is not yet
  in GOLDEN_MASTER's synthetic plan (consistency note for the synthesis layer).

---

# C. EXPERIENCE squad (`experience/`) — 7 files

## C1 — `experience/PILOT_SYSTEM_DESIGN.md`  ★ (prompt-named priority)
- **path:** `project/squads/experience/PILOT_SYSTEM_DESIGN.md` · **ext:** md · **empty?** no (149 lines,
  11790 B) · status: Draft (master design; consolidates the sponsor's pilot requirements 2026-06-19).
- **what:** EXP-PILOT-SYSTEM — the **master design** for the interactive pilot: a Claude Code SKILL + an
  MCP SERVER that run a real produce RFP cycle end-to-end, in parallel with the manual process, with
  versioning + history + multi-RFP.
- **DETAILED WHY:** This is the design that turns the platform into a **driven, operable product** — it
  consolidates the sponsor's pilot requirements into one architecture (three repos, per-run vault folders,
  the cycle loop, flexible ingest, buyer-language voice, proactive kanban + nudges, the MCP tool surface,
  build order). It exists so a buyer can run live RFPs with Claude generating every fill-out doc,
  ingesting messy returns, running the engine, and producing versioned analysis after each round — with
  governance (request→upload→ingest→commit) keeping provenance clean (ADR-0006) and **no MVP** (D19:
  every module a working prototype of the whole capability).
- **section outline:** §1 the three repositories (KR_RFP / RFP_MCP / RFP_PILOT_VAULT) → §2 multi-RFP (one
  vault, a sub-repo per run; the fixed run-folder scaffold; normalized workflow-stage file naming; NOTES.md
  + memory; data governance — RFP data moves only by formal request+upload) → §3 the cycle loop (steps 0–10)
  → §4 flexible ingest (`ingest_any`) → §5 voice (buyer's language) → §6 proactive kanban + scheduled
  nudges → §7 MCP tool surface → §8 build order (5 modules).
- **key specs / decisions recorded:**
  - **Three repos / two complementary stores:** KR_RFP (platform: engine, Postgres, generators, pilot
    service, MCP source, skill); `RFP_MCP` (sponsor, deployable MCP copy); `RFP_PILOT_VAULT` (sponsor, the
    git-versioned run vault). **DB = governed data; vault = the documents + git history.**
  - **Fixed per-run folder:** `runs/<rfp-slug>/{inputs,outputs,memory}/ + NOTES.md + RUN.md + cycle_id.txt`,
    structurally identical every run. **Normalized file naming** (zero-padded by workflow step:
    `01_setup_kickoff.xlsx` … `09_post_award_v2.xlsx`); in-file version heading matches the suffix + git
    commit.
  - **Data governance:** inbound RFP data is **gated** (request → upload → ingest → commit); generated
    outputs/notes written freely; nothing pulled silently or moved between runs.
  - **Cycle loop (steps 0–10):** start run → setup ingest → bid template per round → ingest bids → run →
    `alignment_v{n}.xlsx` → overrides (E/F/G) → select & freeze → post-award versioned adjustments →
    history → emails + mail merge (LEGALESE MODE) → close run (**archive → confirm → purge**; Postgres
    records remain).
  - **Flexible ingest `ingest_any(file)`:** Claude reads any file as-is, infers structure, maps, shows a
    confirm, writes a clean key-stamped input file into the vault, ingests that. Ambiguity → quarantine +
    ask, never guessed.
  - **MCP tool surface (~25 tools):** run_start/run_list/run_status, setup_template/setup_ingest,
    bid_template/ingest_bids/ingest_any, run_round, override_*, select_award, booking_guide,
    adjustment_template/record_adjustment, history, schedule_nudge, draft_email/generate_mail_merge,
    remember, close_run.
  - **Build order:** Foundation ✅ (`app.output` + load_cycle + version heading) → Post-award (`awd.*`
    versioned freeze-and-layer) → Pilot core (`app.pilot`) → MCP server → Skill + routines.
- **implemented vs aspirational:** The pilot is a built capability (DRIFT D references `app.pilot/
  deliverables.py` stateless render, the savepoint/compare E-43). The harness shape it implies is
  detailed in C7 (SKILL_HARNESS) and exercised in C2 (HARNESS_REHEARSAL). Build order items 1–2 confirmed;
  the skill/MCP harness is the live-run path. Comms send + 4/7 touchpoints are unrouted (DRIFT C, E-37) —
  the email/mail-merge workflow (C5) is partly aspirational.

## C2 — `experience/SCENARIO_TOOL_DESIGN_STUDY.md`  (largest file in slice, 417 lines)
- **path:** `project/squads/experience/SCENARIO_TOOL_DESIGN_STUDY.md` · **ext:** md · **empty?** no (417
  lines, 35244 B) · status: Verified (v3 golden reproduced + real allocation models analysed + redesign
  built 2026-06-19).
- **what:** EXP-SCEN-STUDY — a four-way side-by-side design study for the **scenario workbook** (the team
  alignment/comparison deliverable the buyer plays with to decide), synthesizing a target design + a
  practitioner decision layer + a negotiation-instrument frame. **FUNCTIONAL/STRUCTURAL/UX ONLY** — visual
  design-language deferred to the downstream design review. No real names/prices.
- **DETAILED WHY:** This is the **most detailed UX spec in the slice** and the source of the alignment-
  workbook's tab architecture. It exists to learn what works/doesn't by putting OURS (7 tabs) vs V3-GOLDEN
  (20 tabs) vs COMPLEX-REAL (171–176-col messy real files) side by side, then to synthesize a workbook
  that is **rich like the real models, clean like nothing they have** — adding the views OURS lacked
  (Lowest-Cost Check, Coverage, Detailed Scoring depth, TF Comparison, Round Evolution, Data Quality) and
  the practitioners' savings-first sign-off ergonomics, all grounded in the sealed records (so no view
  needs data we don't seal — the data-fidelity rule). It also fixes D28 (engine-derived explanations).
- **section outline:** intro (three files compared; v3 RAN confirmed; 20-tab inventory) → §1 side-by-side
  (the key views matrix) → §2 what works/doesn't (V3-GOLDEN / OURS / COMPLEX-REAL) → §3 UI/UX lessons (9)
  → §4 synthesized target design (ADD/KEEP/CUT tabs; layout & interaction; explicitly-deferred visual
  language) → §5 grounding in our schema (every view → backing records) → §6 provenance & quarantine → §7
  the real Kroger allocation models — the practitioner layer (7.1 architecture, 7.2 what we built, 7.3 the
  15-tab result, 7.4 schema-backed vs DEMO-illustrative) → §8 the negotiation frame (8.1 game-theoretic
  reads, 8.2 visual readability, 8.3 synthetic calibration, 8.4 17-tab result, 8.5 live custom, 8.6 D28
  engine-derived explanations).
- **key specs / decisions recorded:**
  - **The synthesized tab set evolved 7 → 12 → 15 → 17 → 18 tabs** as practitioner + negotiation layers
    were added. Final 18: Overview (4-lens KPI band), Controls, **Award Summary** (sign-off), Scenario
    Comparison, Lowest-Cost Check, Supplier Comparison, **Landed & Hidden Costs**, **Share &
    Relationships**, **Negotiation Dynamics**, Coverage, Detailed Scoring, TF Comparison, Round Evolution,
    Data Quality, Custom Scenario (+live transit), Custom Dashboard, Data (pivot me) (+transit/relationship),
    `_Prices` (hidden).
  - **9 UI/UX lessons:** one tab = one question; depth-on-demand beats everything-at-once and too-light;
    suppliers-as-columns + scenarios-as-rows; always show against-what (incumbent/baseline/STLY/min);
    expose reasoning (recommend-don't-assert); surface DQ never block; give a front door (nav hub); keep
    the live-custom edge; never width-blow-out / merge-nest headers.
  - **§5 grounding (data-fidelity):** every proposed view maps to real columns — Lowest-Cost Check ←
    `eng.bid_score` + `eng.analysis_scenario_award`; Coverage ← `bid.bid_line` vol-offered +
    `cyc.cycle_projected_volume` + `eng.bid_score`; Detailed Scoring ← 5 factors + computed market stats;
    TF Comparison ← the 2 seeded `cyc.cycle_timeframe`s; Round Evolution ← priced `bid.bid_line` per round;
    Data Quality ← ingest quarantine + no-bid cells + gate_flags; Supplier roll-up ← award aggregation +
    `conc_thresh`.
  - **Practitioner layer (§7):** real allocation models (Sweet Potatoes RD2/RD4 19–20 tabs, Hybrid Onions
    RD4) validate the architecture — they build composite keys (`ATLANTAONIONS ORGANIC` = DC+Lot) next to
    readable names + UPC (our D21 key-ID + D23 names-not-keys). Added Controls cockpit, Award Summary
    (per-DC Incumbent→Recommended, Savings $ vs incumbent + vs STLY + negotiation R1→Final, Conv/Org split),
    FOB vs All-In (FOB→+Delivery→+VegCool=All-In; regional freight), banded navigation.
  - **§7.4 + §8.3 honesty line (data-fidelity discipline):** **Schema-backed** (real records): incumbent
    baseline + savings $, FOB/Delivery/VegCool components + regional freight, round-over-round capture, 5
    factors, coverage, the split. **DEMO-illustrative** (clearly labelled in-file): STLY uplift (no STLY
    feed; modelled +4%), product type Conv/Organic (no schema column; derived by lot), transit-time lane
    proxy, synthetic round-over-round behaviour calibration. Closing them is a feeds/schema roadmap item.
  - **§8 negotiation frame** — four lenses (Cost & savings / Hidden costs / Relationships / Negotiation-
    fairness), game-theoretic reads (concession behaviour, real-risk-vs-theater via Z<−2, dependency
    flag at concentration threshold). §8.6 **D28:** every explanatory string is the engine's authoritative
    computed reason rendered from sealed records — `rec_type` computed by `V3Engine`, sealed on
    `eng.analysis_scenario_award.rec_type` (migration 0009), rendered per cell; pinned by an engine
    invariant test.
- **implemented vs aspirational:** Largely **built** — the study says "redesign built 2026-06-19"; the
  generator output is the 18-tab workbook. DRIFT B.2 (frontend) is the web-app analogue but Alignment
  depth is an MVP-cut there (single matrix; missing the designed diligence tabs + B6 landed view + B5
  filter-recompute). The Excel-workbook study itself is realized in `app.output`. STLY/product-type/transit
  remain DEMO-illustrative (clearly flagged) pending feeds.

## C3 — `experience/INTAKE_TEMPLATE_DESIGN.md`
- **path:** `project/squads/experience/INTAKE_TEMPLATE_DESIGN.md` · **ext:** md · **empty?** no (166
  lines, 13035 B) · status: Notes (sponsor 2026-06-20; informs the **post-pilot** intake build — NOT the
  pilot). Most-recently-modified file in the slice (2026-06-21).
- **what:** EXP-INTAKE-TEMPLATE — forward-looking requirements for the **real software's** intake
  templates: a buyer-side column-selecting template builder + saved mapping presets, the **flat-13 fiscal-
  period** storage model with template-side grouping + intake fan-out, and the supplier-side locked
  governed-form behaviour.
- **DETAILED WHY:** This is the spec for the **period model** — the load-bearing pricing-intake decision
  chosen for **error-protection**: exactly ONE canonical storage grain (the 13 fiscal periods) so every
  downstream calc/group/compare runs on a uniform structure; the supplier never faces 13 cells (the
  template groups for them); the grouping is resolved at the intake boundary (fan-out), so a regrouping
  later is a different fan-out/roll-up over the same flat periods, never a re-collect. It also specs the
  supplier-facing form (locked cells, password-protected, per-row traffic light mirroring the ingester's
  completeness classes). It exists so the post-pilot product inherits these verbatim-in-intent and so the
  fiscal-calendar foundation is recorded.
- **section outline:** §1 buyer-side template builder (full column superset, natural selection, grouping
  incl. period axis compact/expand, saved presets→schema mapping, walk-through wizard) → §1a the period
  model (flat-13 storage; template groups periods into timeframes; intake fans out; compact/expand is a
  view; buyer trades precision vs supplier burden) → §2 supplier-side governed form (only entry points
  editable; per-row readiness traffic light Not bid / Incomplete / Complete) → Build status (graduating
  notes to code, increment-by-increment) → Implementation anchors.
- **key specs / decisions recorded:**
  - **Flat-13 period model:** a fiscal year = **13 periods** (Kroger 4-5-4 calendar). Every price recorded
    against **exactly ONE of 13 periods**; the template groups periods into a few timeframes (e.g. A=P1–2,
    B=P3–9, C=P10–12) so the supplier prices a handful; **intake FANS OUT** each timeframe price flat to
    every period in its span. Storage always the 13 periods regardless of grouping.
  - **Confirmed fiscal facts (corrects earlier assumptions):** 13 periods/year; **quarters are 4-3-3-3**
    (Q1=P1-4, Q2=P5-7, Q3=P8-10, Q4=P11-13) not 3-3-3-4; a **53-week leap year** (FY17/23/28/34) gives
    Period 13 a 5th week — a period is **not always 28 days**; always read the span from the table.
  - **Supplier governed form:** only price/volume/input cells unlocked; keys/names/headers/structure
    hard-coded + sheet password-protected; per-row traffic light mirrors the ingester's
    `NO_BID`/`INCOMPLETE`/`BID` classes.
  - **Build status (with code anchors):** §2 supplier form **DONE** (`app/domain/bid/template_generator.py`);
    §1 column selection **DONE** (`BidTemplatePreset` in `template_preset.py`; presets full/all_in_simple/
    components); period model calendar foundation **DONE** (`app/fiscal/calendar.py` + 273-row CSV FY16–
    FY36); DB dimension `ref.fiscal_period` **DONE** (migration 0014); storage column `bid.bid_line.
    fiscal_period_id` nullable **DONE** (migration 0015) + pure `period_fanout.py`; period-grain uniqueness
    **PROVEN** (migration 0016, two filtered unique indexes; potato sample e2e); **ACTIVATION DEFERRED**
    until after the first live run (touches the engine read-path — wrong risk before going live).
  - **TYPE NOTE (a recorded cleanup):** `bid.bid_line.fiscal_period_id` is `varchar(36)` while
    `ref.fiscal_period.id` is `uuid` → joins need an explicit `::text` cast and an FK isn't enforceable
    as-is; reconcile at activation.
- **implemented vs aspirational:** Substantial increments **built and tested** (calendar foundation, DB
  dimension, storage column, fan-out logic, period-grain uniqueness, by-period import proven on the potato
  sample — all backward-compatible/inert). **Deferred:** ACTIVATION (wiring fan-out into live ingest +
  the engine read-path fallback + the compact/expand view) — intentionally deferred until after the first
  live run. The TYPE NOTE is the same `varchar(36)` vs `uuid` item DRIFT B.5 flags (D38 acknowledged
  cleanup). Renamed-column mapping / custom-preset persistence / the wizard are LATER.

## C4 — `experience/HARNESS_REHEARSAL.md`
- **path:** `project/squads/experience/HARNESS_REHEARSAL.md` · **ext:** md · **empty?** no (133 lines,
  9248 B) · status: Runbook.
- **what:** EXP-HARNESS-REHEARSAL — a turnkey **fully-LOCAL rehearsal kit** that exercises the real
  harness (the plugin's subagents) on synthetic data ("Test Greens"), with a pass/fail watch-list, plus
  the cutover note for going live.
- **DETAILED WHY:** It exists to validate the **part that is new and only runs for real inside Claude
  Code** — the orchestrator delegating hub-and-spoke, tool-scoping holding, context staying isolated, the
  Opus-4.8 pin taking — *before* a live RFP. The substrate (engine, per-run DB isolation, MCP, vault) is
  already covered by the automated suite; this kit is specifically about the agents. Without it, harness
  regressions (an agent leaking roles, a run colliding, a silent model fallback) would only surface on real
  data. It pairs with `backend/rehearsal/synthetic_fill.py`.
- **section outline:** §1 local setup (Postgres + app DB migrated; `ALTER ROLE app CREATEDB` for D30 per-
  run DBs; throwaway vault; `claude mcp add rfp-pilot` with absolute paths; `claude --plugin-dir ./mcp`) →
  §2 how you drive it → §3 the scripted cycle + 6 edge cases (11-step table) → §4 the watch-list (the
  pass/fail gate, 9 checkboxes) → §5 going live (the cutover).
- **key specs / decisions recorded:**
  - **Everything local + synthetic** — no GitHub repos, no real RFP data; commodity "Test Greens"; one
    `mkdir` is the only priming; commits local-only.
  - **Why `claude mcp add` not just `.mcp.json`:** `--plugin-dir` reliably loads agents+skill, but
    autoloading the MCP server + `${ENV}` substitution varies by Claude Code version (first rehearsal: the
    server silently failed because path placeholders weren't substituted) → register once with absolute
    paths + `PYTHONPATH` for determinism.
  - **The scripted cycle (11 steps) + 6 EDGE cases:** re-run R1 (new version not overwrite); flex ingest
    (Alpha's own messy file → engine proposes mapping → confirm → supersede); supersession (Beta corrected
    R3 — prior lines superseded not double-counted); post-award reprice (version 1, names-based); second
    concurrent run (its own database — no DC01 collision); close (archive→confirm→purge drops the run DB).
    Step-2 detail: **33 priced lines** = 3 DCs × 3 lots × 4 suppliers − Gamma's 3 Spinach NO-BIDs.
  - **The watch-list (9 pass/fail gates):** engine stays data-only; secretary never touches data; every
    number traceable (D28, spot-check 3 cells); hub-and-spoke held; **model stayed pinned (Opus 4.8, no
    silent fallback)**; isolation held (separate DBs, purge drops run DB); provenance honest (rehearsal
    stamped **SYNTHETIC**, never "LIVE CYCLE DATA"); no orphans; voice + governance.
  - **Cutover (§5):** only the vault pointer + real-vs-synthetic data change — nothing in the harness
    changes; pin the plugin to released tag (`RFP_MCP v0.1.0`, D32); `rehearsal=false` → stamped "LIVE
    CYCLE DATA — real names & prices"; stop using `synthetic_fill`; each real run gets its own isolated DB
    (D30).
- **implemented vs aspirational:** A runbook for the built harness — references real artifacts
  (`backend/rehearsal/synthetic_fill.py`, the `rfp-pilot` MCP server `rfp_mcp.rfp_pilot_server`, the
  plugin agents). The per-run DB isolation (D30) is its substrate (see C7 known gap). This documents
  exercising real components, not aspiration; its existence implies the harness + MCP + per-run isolation
  are built to the point of being rehearsable.

## C5 — `experience/PILOT_INPUT_DOCS_SPEC.md`
- **path:** `project/squads/experience/PILOT_INPUT_DOCS_SPEC.md` · **ext:** md · **empty?** no (106 lines,
  7577 B) · status: Draft (guides the pilot service + MCP + skill build).
- **what:** EXP-PILOT-INPUTS — defines **every input document** the pilot generates at each step, what it
  ingests back (by key, D20/D21), and the versioned artifact produced after each run.
- **DETAILED WHY:** It exists to make the pilot's loop **predictable and reproducible**: generate fill-out
  doc → sponsor fills → ingest (key-validated) → act → produce versioned output → keep history. It maps
  every setup tab to its destination tables (the data-fidelity contract — every field to its correct
  target), specifies key generation/embedding so later docs cascade by key while the sponsor only types
  names (D23), and pins the alignment/post-award version headings. Without it the pilot's documents would
  be ad-hoc and round-trip-by-key (D20) would have no field-level spec.
- **section outline:** intro (the guiding loop) → Step 0 Cycle Setup/Kickoff workbook (tab→lands-in table)
  → Step 1 bid template per round → Step 2 run + versioned alignment file → Step 3 optional override docs
  (E/F/G) → Step 4 award selection → freeze → Step 5 post-award adjustments (versioned, ADR-0014) → Step 6
  history → MCP tool surface.
- **key specs / decisions recorded:**
  - **Step 0 setup → store mapping (field-level fidelity):** Cycle tab → `cyc.cycle` + run `EngineConfig`;
    DCs → `ref.dc`; Lots/Items (incl. **product type Conventional/Organic**) → `ref.item` + `cyc.cycle_lot`
    + `cyc.cycle_lot_item`; Suppliers → `ref.supplier` + `cyc.cycle_invited_supplier`; Volumes →
    `cyc.cycle_projected_volume`; Incumbents (**routing baseline $/case = prior-period actual-paid**) →
    `perf.historical_award_assignment`; Timeframes → `cyc.cycle_timeframe`; Premiums → `cyc.*` threshold;
    Scenario rules → `cyc.*` scenario-rule tables; Safeties → `cyc.cycle_safety`.
  - **Step 1:** owned bid template, key IDs embedded at line level (D21), one row per (DC×Lot×TF×invited
    supplier); All-In OR component split (FOB+Delivery+VegCool−Lot Discount); ingest by key, quarantine
    MISSING_KEY/UNKNOWN_KEY; **no-bid = blank price (recorded, not dropped)**.
  - **Step 2 version heading:** `MID-CYCLE ALIGNMENT ANALYSIS — {cycle} · Round {n} · Analysis v{seq} ·
    sealed {timestamp}`; each run a sealed immutable `eng.analysis_run`; re-run = new version, nothing
    overwritten. Run path: read by key → `EngineInputs` → `V3Engine.run` → seals `analysis_run` +
    `bid_score` + `analysis_scenario` + `analysis_scenario_award` incl. authoritative `rec_type` (D28).
  - **Step 5 post-award:** `awd.award_adjustment` v1,v2,…; raw `award_line` never overwritten; heading
    `POST-AWARD ADJUSTMENTS — {award} · Version {N} · as of {date}`.
  - **MCP tool surface** (~16 tools) mirrors PILOT_SYSTEM_DESIGN; each returns names not keys (D23),
    deterministic, writes/reads the governed store.
- **implemented vs aspirational:** The setup→engine→alignment→freeze→post-award path is built (referenced
  by `V3Engine.run`, `eng.analysis_scenario_award.rec_type` migration 0009, the post-award freeze-and-
  layer E-43). DRIFT C notes sign-off gate (E-22, SIGNED_OFF enum never emitted) is not built and the
  full Cycle Setup frontend is an MVP-cut/not-built — but the pilot's *document* loop is the live path.

## C6 — `experience/EMAIL_STYLE_AND_MAILMERGE.md`
- **path:** `project/squads/experience/EMAIL_STYLE_AND_MAILMERGE.md` · **ext:** md · **empty?** no (64
  lines, 3960 B; smallest file in slice) · status: Draft (sponsor-specified 2026-06-19).
- **what:** EXP-PILOT-EMAIL — the email drafting + mail-merge capability + the LEGALESE style mode: draft
  the structure → sponsor approves → generate the mail-merge template + recipients data **from the
  governed records**.
- **DETAILED WHY:** It exists so every email is **fully accurate, always** — because sends are mail-merged
  from sealed data, no price/supplier/lot/date is ever hand-typed (D28: deterministic, data-derived). It
  keeps the human in the loop (the sponsor approves structure; the sponsor sends), and it records the
  sponsor's verbatim LEGALESE MODE spec for controlled commercial correspondence. Without it, outbound
  comms would risk inaccurate improvised figures and the legalese governance posture would be unrecorded.
- **section outline:** intro → Workflow (1 draft structure with `{{merge_field}}` placeholders → 2 approve
  → 3 generate mail merge template + recipients CSV → 4 send is the sponsor's action) → Style modes
  (default business voice; LEGALESE MODE verbatim spec + operationalization).
- **key specs / decisions recorded:**
  - **Workflow:** draft structure (purpose, recipients, merge fields, body skeleton, tone) → sponsor
    approves → on approval generate a template + recipients data file (one row/recipient with exact merge
    values pulled from the store — awarded lots/prices/volumes/DCs/round/dates, **names not keys** D23) →
    drop into `outputs/` (e.g. `NN_round2_invite_mailmerge.docx` + `NN_round2_invite_recipients.csv`),
    committed. Send is the sponsor's action.
  - **LEGALESE MODE (verbatim sponsor spec):** controlled commercial response — neutral, procedural,
    brief, non-defensive; anchor to process not opinion; disclose only what supports the position; do not
    volunteer facts/calculations/motives/approvals/timelines/alternatives/precedent; do not validate/debate
    counterpart claims; do not imply review/escalation/flexibility/reconsideration unless instructed;
    declarative wording; structure: **acknowledgment → principle → application → disposition → close**;
    objective: preserve position, optionality, and a defensible record. (Still mail-merge-accurate; legalese
    discloses sparingly, so most figures are omitted unless they support the position.)
- **implemented vs aspirational:** **Aspirational-leaning.** DRIFT C lists "comms SEND + 4/7 touchpoints
  unrouted (E-37)" as recorded-but-not-built. The mail-merge generator and LEGALESE mode are designed here
  and align to D28; some of the comms surface is built but the send path and most touchpoints are not yet
  routed. Human-in-the-loop send is by design (not a gap).

## C7 — `experience/SKILL_HARNESS_DESIGN.md`
- **path:** `project/squads/experience/SKILL_HARNESS_DESIGN.md` · **ext:** md · **empty?** no (93 lines,
  5658 B) · status: Notes (sponsor 2026-06-20; informs the skill build — the NEXT step after the first MCP
  commit).
- **what:** EXP-SKILL-HARNESS — the **multi-agent shape** of the pilot skill (orchestrator / engine /
  secretary) and the per-run **data isolation** it depends on.
- **DETAILED WHY:** It exists so the pilot skill is a small **harness of three agents with separated
  contexts**, so data commentary is never polluted by operational noise and runs never bleed into each
  other. The Engine agent grounds its commentary by reading the run store — so the store must carry only
  THIS run's sealed records (no demo rows, no other run's rows); isolation at the data layer is the
  precondition for clean data commentary, which no amount of agent-context discipline could fix after the
  fact. It records the model pin (Opus 4.8), version isolation (D32), and the known gap (shared DB / code
  collision) that blocks multi-run.
- **section outline:** intro → The three roles (orchestrator / engine agent DATA-DEDICATED / secretary
  "the rest of the noise") → Communication discipline (hub-and-spoke preferred over peer-to-peer) → Model
  (Opus 4.8 "ultracode", pinned) → Data isolation this depends on (blank DB per run; no cross-contamination;
  why it matters) → Version isolation D32 (a live run frozen against our dev) → Known gap to close before
  multi-run (D30) → Build sequencing.
- **key specs / decisions recorded:**
  - **Three roles:** Orchestrator (only agent that talks to the user; routes/sequences/relays); Engine
    agent (data-dedicated; runs engine/analysis via MCP over the governed run store; answers data questions
    by reading the data; context = sealed records only — D28); Secretary (memory/NOTES.md/`memory/`,
    reminders, kanban nudges, file naming, admin — so operational noise never contaminates data commentary).
  - **Hub-and-spoke preferred:** only the Orchestrator talks to Engine + Secretary; they don't share
    context directly; the Orchestrator passes the minimum each needs — strict context isolation.
  - **Model pin:** the harness **always operates on Opus 4.8 ("ultracode")**; pin in skill/agent defs so a
    run does not silently fall back; the model is part of the version a live run pins to (D32).
  - **Data isolation (binding):** blank database per run/session (no demo data ever — reinforces ADR-0001
    clean-room); no cross-contamination across concurrent runs (each run an isolated store).
  - **Version isolation (D32):** a live run is version-pinned across the whole stack (MCP build + Vault
    scaffold + platform/schema); live sessions connect to a released/tagged MCP build (not dev HEAD); new
    dev migrations are not auto-applied to a live run's store.
  - **Known gap (D30):** the current pilot shares ONE Postgres DB across runs with globally-unique
    reference codes (`ref.dc` DC01..); a second run collides (`dc_code=DC01 already exists` observed) — fix
    is per-run data isolation (database/schema-per-run, or a strict run-scoped tenant boundary).
- **implemented vs aspirational:** The three-agent harness + Opus-4.8 pin are the shape HARNESS_REHEARSAL
  (C4) exercises; the per-run DB isolation (D30) is shown working there (`ALTER ROLE app CREATEDB`,
  concurrent runs use separate DBs, purge drops the run DB) — so D30 moved from "known gap" to addressed.
  Version isolation (D32) needs the release/tag discipline established at the first MCP commit (`RFP_MCP
  v0.1.0` referenced in C4's cutover). Largely realized for the rehearsal path.

---

# D. PLATFORM-DATA squad (`platform-data/`) — 3 files

## D1 — `platform-data/FEEDS_ITRADE.md`  ★ (prompt-named priority)
- **path:** `project/squads/platform-data/FEEDS_ITRADE.md` · **ext:** md · **empty?** no (94 lines, 6682
  B) · status: Draft (derived from a real export). STRUCTURE ONLY — column headers are schema, no data-row
  values.
- **what:** PD-FEEDS-01 v1.0 — the **iTrade feed structure + importer mapping (E-08)**: the real 43-column
  export mapped column-by-column to `perf.itrade_receipt`, the importer rules, and the "one feed, two
  jobs" confirmation.
- **DETAILED WHY:** This is the spec for the **keystone feed** — iTrade powers BOTH historical cost AND the
  supplier scorecard. It exists to firm up E-08 by reconciling the brief's `perf.itrade_receipt` model
  against a real export the sponsor provided (quarantined; only structure recorded), confirming no column
  is unmapped and that the real export is *richer* than the brief (a fuller 7-date chain + both shipped &
  received quantities — exactly what the scorecard derivations need). Without it the importer's column map,
  flag semantics, and date-span rules would be unverified (R-PD1).
- **section outline:** intro → Observed shape (one `Data` sheet, 43 cols, ~113,986 rows; a 51-col variant
  also exists) → Column → model mapping (43-row table grouped identity/lineage/date-chain/vendor-origin/
  performance/cost/flag/fiscal) → Importer rules confirmed (6 rules) → One feed, two jobs → Outstanding →
  Action.
- **key specs / decisions recorded:**
  - **43 columns → `perf.itrade_receipt`** — every column mapped: the anchor is col 2 `Cas Fyt Sub Com Cct
    Dsc Tx` → `ref.subcommodity`; a **7-date chain** (cols 5–11); both `qty_received` (27) and `qty_shipped`
    (28); cost columns `final_price_fob` (30, FOB), `freight` (32), `total_w_freight` (33, delivered),
    xdock (34–35), `cogs` (43); **two origins kept separate** — `ship_from_state`/`ship_from_zip` (24–25)
    are ship-from, never grow-origin (G7); fiscal stamp (39–42); dirty flags Canceled/Zero-Cost/Zero-Qty
    (36–38).
  - **6 importer rules:** (1) flag-first validation (cols 36–38 are the first gate); (2) date-span sanity
    (7-date chain → reject impossible spans like received-before-shipped, persist an issue, never silently
    compute); (3) key off codes not filename (a "Garlic Herbs" file contained tomatoes); (4) two origins
    separate (distance is a freight proxy via `ref.zip_centroid` on col 25); (5) template variants — detect
    43-col "Data" vs 51-col "Query/Calendar" by header signature, map both to one grain; (6) identity
    resolution — Vendor→supplier alias, UPC→item alias, unresolved → quarantine, never guess (KEEP the
    as-built alias+quarantine machinery).
  - **One feed, two jobs:** historical awarded cost = cost columns at receipt grain; the supplier scorecard
    (two frozen snapshots) derives entirely from this feed (fill/adjusted-fill from 27 vs 28, on-time from
    the date chain, DC rejection from 29, cost/case from 30/43, age at receipt). No separate scorecard feed.
  - **Outstanding:** the 51-col variant; KCMS (distinct feed); a golden v3 input/output pair (the top ask
    — this proves the *importer*, not the *engine reproduction*).
- **implemented vs aspirational:** **NOT BUILT** (the importer). DRIFT C lists "iTrade importer (E-08,
  table+view exist, nothing populates — so 'vs STLY' runs on a synthetic ×1.04 proxy)" as recorded-but-not-
  built backend perimeter. So `perf.itrade_receipt` exists as a table (M4 migration), but the importer that
  populates it from a real export is unbuilt; this directly explains the STLY DEMO-illustrative flag in
  SCENARIO_TOOL_DESIGN_STUDY §7.4/§8.3 (no STLY feed yet). High-value gap, fully recorded.

## D2 — `platform-data/CYCLE_FIELDTOMATO_STRUCTURE.md`
- **path:** `project/squads/platform-data/CYCLE_FIELDTOMATO_STRUCTURE.md` · **ext:** md · **empty?** no
  (277 lines, 22885 B) · status: Draft (derived from a real, near-complete RFP cycle). **AS-IS REFERENCE,
  NOT TARGET (D17+D18).** STRUCTURE ONLY (no real values; CONFIG values are logic, recorded).
- **what:** PD-CYCLE-FIELDTOMATO v1.1 — the **structural map of a real, near-complete Field Tomatoes 2026
  RFP cycle**: engine I/O, ingestion grain, booking output, raw-bid template, the `.xlsb` requirement, and
  the runnable pricing-safety visualizer — each artifact's structure mapped to the reconciled store.
- **DETAILED WHY:** Unlike the golden Potato pair (the engine *reproducibility* anchor), this Tomato cycle
  is the **end-to-end artifact set** — it exists to extract the contract/grain/cost-stack/config from a
  full real cycle (engine input + supplier-facing raw-bid template in two physical formats + normalized
  intake R2/R3 + award/booking output + a runnable safety visualizer) and confirm the importer + safety
  requirements concretely. Framed AS-IS-NOT-TARGET (D17/D18): KEEP the contract/grain/cost-stack/config;
  BUILD OUR OWN store/app/outputs/template/process; the cycle is one single-strategy mold, we build the
  strategy-agnostic platform (ADR-0016). It is where the **176-column myth** is debunked and the `.xlsb`
  multi-format requirement is proven.
- **section outline:** intro (P6–P7 Field Tomatoes, Jun 21–Aug 15 2026, 4-week bridge; USDA FVWTRDS 1662)
  → §1 engine I/O contract (11 tabs; 1.1 CONFIG block → cyc.* + run config; 1.2 IN_/DIM_ tabs → store) →
  §2 ingestion grain (R2 1028×176 / R3 682×179 — "why 176 cols, it is NOT 176 fields") → §3 award/booking
  output (booking guide 64×42; group bands; External/Internal volume; savings checks) → §4 raw bid template
  (14 tabs; pricing tab `6. Vol and Pricing Capability` 78×171; two-block layout; No-Bid handling) → §5
  `.xlsb` requirement (Lipman binary) → §6 price visualizer HTML (tolerance band/collar/midpoint; seeds
  E-29) → §7 what this proves / what's still partial.
- **key specs / decisions recorded:**
  - **11-tab engine input (vs the golden 13):** no IN_Preferred / IN_VolumeLimits sheets (engine warns +
    skips); header row 4 (IN_Custom row 6). **Identity caveat:** CONFIG still reads `Colored Potatoes /
    Potato 2026` (template copied, identity not re-stamped) — our store must key on its own `cyc.cycle`
    row, never the spreadsheet's identity strings.
  - **CONFIG deltas:** Tomato is **single-round (only R1 active**, R2–R6 NO); TF1+TF2 active; **weights sum
    to 120% → engine renormalises**; Z-Risk + Continuity default to 0.10; premium bands 0.03/0.07/**0.15**
    here; `Coverage Eligibility Floor` is documentary (0.80 is hard-coded); `Single Supplier per Lot`=YES.
  - **The "176 columns" debunk (§2):** 176/179 is the **stored sheet width** (trailing styled/merged
    columns), NOT the data grain — body data occupies cols 2–39 (~37 cols R2) / 2–27 (~23 R3). The shape is
    **one row per Supplier×DC×Item bid line** with **two side-by-side bid blocks** (primary spec cols 14–23
    + Roma alternative-spec cols 28–37 — a lower-cost alt path, NOT a second DC). **Importer rule: do not
    trust `max_column`; key off the header row (row 4) and the block-pair pattern.**
  - **Raw bid template (§4):** 14 tabs identical across blank template + every supplier round; pricing on
    `6. Vol and Pricing Capability` (78×171); the ingestion sheet IS the stacked/normalized projection of
    every supplier's tab-6 (the raw→normalized bridge in one picture); `No Bid` (cols 9/23) = non-bid not
    zero price.
  - **`.xlsb` requirement (§5):** Lipman rounds are **binary Excel** (`PK\x03\x04`, not openpyxl-readable
    → needs **pyxlsb**); DiVine/Marengo are `.xlsx`; all carry the identical 14-tab template → the importer
    must parse one logical template across two physical formats. Corpus: DiVine R1–R3, Marengo R1–R4,
    Lipman R1–R3.
  - **Price visualizer (§6) seeds E-29:** `xl_roma_pricing_backtest.html` implements collar + rolling-
    midpoint + tolerance-band with ADR-0014 persistence (CONFIRM=2 weeks / LAG=1 week), Kroger-optional
    collar asymmetry, on the identified market feed **USDA AMS FVWTRDS / report 1662** (Roma plum, weekly =
    midpoint of the "mostly" range). Maps each safety element to a visualizer control + formula.
  - **§7 still partial:** single round only; ingestion exists R2/R3 only; Incumbents+Volumes empty (all
    bids → As-Needed coverage); identity not re-stamped; no IN_Preferred/IN_VolumeLimits.
- **implemented vs aspirational:** This is a **reference extraction** (AS-IS), not a build claim — it
  drives requirements for E-08 (the unbuilt importer, D1), E-23 (booking guide, built), E-29 (the unbuilt
  safety monitor/visualizer, DRIFT C). The single-round finding here is the same defect TOMATO_RUN (B5)
  hit at runtime. The `.xlsb` + two-block parse and the 176-col debunk are concrete importer requirements;
  the importer itself is not yet built (DRIFT C).

## D3 — `platform-data/PLAN.md`
- **path:** `project/squads/platform-data/PLAN.md` · **ext:** md · **empty?** no (192 lines, 18850 B) ·
  status: Draft.
- **what:** SQUAD-PLATDATA-001 v1.0 — the Platform & Data squad plan: it owns the governed PostgreSQL
  system of record (clean baseline, Alembic chain, naming canonicalization, the three feeds, the
  persistent-lot change), keeps the seven KEEP capabilities, and ships exactly two breaking migrations
  (G1/G2) isolated behind a flag.
- **DETAILED WHY:** This is the **schema/data execution contract**. It exists to disposition all 63
  as-built tables (ADOPT/CLEAN/ADD), define the Alembic migration chain (M0 baseline + M1–M10 additive +
  M-G1/M-G2 breaking), fix the naming canonicalization (schema-qualified brief-style names), spec the three
  feeds' importer discipline, and plan the persistent-lot change (G8). It explicitly does NOT own the
  engine brain, the awd generators, or RBAC policy — it provides the tables those squads write to. Without
  it the store's fidelity (46 composite FKs, 67 CHECKs, the de-SQLite-ism'd baseline) and migration
  discipline would be unspecified (R-PD2).
- **section outline:** §1 baseline assessment (the 63-table disposition matrix by layer; Net: ~42 ADOPT /
  ~9 CLEAN / ~18 ADD) → §2 migration strategy (M0 clean baseline + the SQLite-ism fixes; M1–M10 additive;
  M-G1/M-G2 breaking, feature-flagged) → §3 naming canonicalization (schema-qualified canonical; the
  mechanical crosswalk rule) → §4 data feeds design (iTrade E-08, KCMS E-09, scorecard-as-derivation E-10)
  → §5 persistent-lot change plan (G8/E-11) → §6 risks + sample files needed.
- **key specs / decisions recorded:**
  - **63-table disposition:** ADOPT the KEEP spine + reference + cyc/bid/eng governance near-verbatim;
    CLEAN the defect-fixes/merges; ADD ~18 net-new (taxonomy, zip, three feeds, awd layer, bid_score,
    kickoff satellites, client/tenant).
  - **M0 baseline + SQLite-ism fixes:** boolean `DEFAULT 0/1` → native `boolean`; `is_eligible = 0` → `IS
    false`; delete the no-op `length(error_log) >= 0` branch in `ck_calcrun_failed_has_errorlog`; prose
    enums → native `CREATE TYPE ... AS ENUM`; VARCHAR(36) UUID PKs reviewed. Roundtrip + `alembic check`
    green is the E-01 exit gate; ships the full KEEP spine + all 46 composite-identity FKs.
  - **Additive migrations M1–M10:** audit-live (E-05), attribute-taxonomy (E-11), zip-distance (E-12),
    itrade-receipt (E-08), kcms (E-09), scorecard (E-10), bid-score (E-18), awd-layer (E-21/22/23),
    kickoff-satellites (E-14), client-tenant (E-03).
  - **Breaking M-G1/M-G2 (Phase D, flagged, ship together per Ed):** M-G1 drop
    `uq_scenario_a_cell_assignment_cell UNIQUE(scenario_run_id,dc_id,lot_id,tf_id)`, re-grain to
    `(run,dc,lot,tf,supplier)`, add `volume_share NUMERIC(9,6)` + `cap_breach_flag`, rewrite the capacity-
    arithmetic CHECK to sum across split suppliers; M-G2 `scenario_a_result`→`eng.scenario` (+
    `scenario_code` A–G), `scenario_a_cell_assignment`→`eng.scenario_award`. Gated by `feature.split_award`
    + `feature.scenario_lenses`; permit-not-force.
  - **Naming:** schema-qualified brief-style names canonical (`cyc.cycle`, `eng.scenario_award`,
    `perf.itrade_receipt`); mechanical crosswalk at M0; keep as-built column names inside adopted tables
    (only table names + schema placement canonicalize); publish `db/baseline/CROSSWALK.md`.
  - **Feeds:** iTrade receipt-grain importer (flag-first, impossible-date-span HARD_REJECT, key off codes,
    43/51-col variant detection, unknown-header HARD_REJECT); KCMS a DISTINCT feed (refuse to merge);
    scorecard a **derivation** over `itrade_receipt` (two frozen snapshots kickoff/signoff, append-only).
  - **Persistent-lot (§5):** introduce `norm.lot` (persistent asset) + taxonomy + sticky `norm.item_lot_map`
    (proposed→confirmed); back-fill `cyc.cycle_lot` as a scope/view; lands Phase B (M2); one-time migration
    with quarantine-on-ambiguity.
  - **Risks (§6):** R-PD1 real iTrade shape unverified; R-PD2 M0 fidelity (63 tables/46 FKs/67 CHECKs);
    R-PD3 persistent-lot back-fill ambiguity; R-PD4 G1/G2 blast radius; R-PD5 client/tenant policy; R-PD6
    nothing run on real data. **7 sample files needed** from the sponsor (top: a real iTrade export w/
    headers, ideally each variant).
- **implemented vs aspirational:** Core spine **built** (DRIFT A: governed-persistence, sealed runs,
  flat-13 period storage migration 0014, the formula registry; the M-G1 split-grain was closed). **Not
  built / partial:** the iTrade importer (E-08, D1), KCMS (E-09, DRIFT C), supplier scorecard (E-10, DRIFT
  C). **Drifted:** tenancy (M10) — client_id on a couple of `ref` tables, no RLS (DRIFT B.3). The `bid_line.
  fiscal_period_id` varchar(36) vs uuid is DRIFT B.5/the C3 TYPE NOTE.

---

# E. PLATFORM-DEVOPS squad (`platform-devops/`) — 1 file

## E1 — `platform-devops/PLAN.md`
- **path:** `project/squads/platform-devops/PLAN.md` · **ext:** md · **empty?** no (307 lines, 20312 B) ·
  status: Draft.
- **what:** SQUAD-DEVOPS-001 v1.0 — the Platform Engineering / DevOps squad plan: environments, local
  dev, CI/CD, IaC, secrets, the DB-migration pipeline, observability, and performance/sizing. It owns the
  running ground and the CI that gates the program's non-negotiables; it does NOT own the schema, the
  engine, or RBAC/tenancy policy.
- **DETAILED WHY:** It exists to make the program's invariants **enforced in the pipeline on every commit**
  — lint, type, test, migration roundtrip, the `reference/`-import guard, the frontend build — so "enforced"
  is mechanical, not hoped (R-DO4). It defines parity-as-a-control (stage differs from prod only in scale +
  data, never topology), the one-image-promoted-by-digest deploy path, and the **G1/G2 migration safety**
  (feature-flagged, expand/contract, blue/green, post-pilot sequencing) so the two breaking migrations
  cannot strand data. It stays provider-neutral until DEP-4 (cloud + IdP).
- **section outline:** §1 environments (dev/stage/prod table; promotion path; DB-per-tenant vs shared-
  schema OPEN question) → §2 local dev (docker-compose 3 services + adminer; Makefile targets) → §3 CI/CD
  pipeline (7 jobs + branch protections + the YAML skeleton) → §4 IaC & hosting (container + managed
  Postgres; AWS default recommendation; Terraform module layout; secrets; image build/push; deploy
  strategy) → §5 observability (structured logging, health/readiness, metrics, audit-event sink, error
  tracking) → §6 performance/sizing → §7 migration safety (G1/G2) → §8 risks → §9 what this plan defers →
  Changelog.
- **key specs / decisions recorded:**
  - **Environments:** three tiers, one image, config-by-environment; parity is a control. **Recommended
    default: single shared-schema database with RLS** (keeps "open last cycle" one query, migrations
    singular) — but the **OPEN QUESTION for Security/Sponsor:** does commercial/PII classification mandate
    physical per-tenant isolation, or is RLS + app-filter sufficient? "the single biggest fork in our IaC."
  - **CI 7 jobs (the contract):** lint (ruff), type (mypy), **reference-guard** (fail if `backend/`
    imports `reference/` — grep/AST), test (Postgres service → migrate → pytest, never SQLite), **migration-
    roundtrip** (up→dump→down→up→dump byte-identical + `alembic check` no drift + the **constraint-count
    floor ≥46 composite FKs** so M0 fidelity is gated R-PD2), frontend-build (path-filtered until Phase F),
    **ci-pass** (the single required status). Branch protections: PR + owning-squad-lead review; ci-pass
    required; linear history; breaking-migration PRs additionally require Architect + Platform&Data review.
  - **IaC/hosting:** container + managed Postgres; default recommendation (pending DEP-4) **AWS — ECS
    Fargate/App Runner + RDS PostgreSQL 15 + ECR + Secrets Manager** (Azure/GCP drop-in equivalents);
    Terraform under `infra/terraform/`, module-per-concern, per-env `.tfvars`; the **digest** deploys
    (stage + prod run the identical digest); no secret in git ever.
  - **Observability:** JSON logs with `request_id`/`tenant`/`principal`/`route`/`status`/`latency_ms` (a
    log line without a tenant is a bug); `/healthz` (liveness) + `/readyz` (readiness — DB reachable +
    migrations at head + engine-impl selected); Prometheus `/metrics`; the **audit log is NOT an
    observability concern** — it's the live hash-chained governance record owned by Security; DevOps must
    never sample/drop it, must keep it in PITR scope, may surface a chain-verify metric without reading
    payloads.
  - **Sizing:** modest, bounded (tens of categories, dozens of DCs, hundreds of lots, single-digit-thousand
    bids/cycle); one engine run sub-second to low-seconds; **the binding NFR is "open last cycle" < 2s**
    (an indexing/query-shape problem, held as a CI/perf-smoke assertion); over-provision only durability.
  - **G1/G2 migration safety (§7):** feature-flagged + shipped together, deployed flag-off (new grain
    exists, old behavior preserved); sequenced after the Phase-B pilot; expand/contract discipline +
    forward data-migration assertion + rewritten capacity-arithmetic CHECK before flag-on; blue/green for
    breaking releases; rollback before flag-flip = redeploy previous digest.
  - **Risks:** R-DO1 DEP-4 unresolved; R-DO2 tenancy topology fork; R-DO3 breaking-migration blast radius;
    R-DO4 CI gate erosion (gates are *required* via ci-pass — removal is auditable not quiet); R-DO5 secret
    leakage / sample-data classification.
- **implemented vs aspirational:** The CI gates + migration roundtrip + clean-room guard are **built and
  enforced** (architecture SKELETON ships them day one; QA PLAN confirms merge-blocking from Phase 0). The
  IaC/cloud (stage/prod, IdP, secret store, metrics/error vendors) is **deferred — scaffolded-but-not-
  applied** pending DEP-4 (DRIFT does not contradict; this is recorded deferred scope). The tenancy topology
  fork is the same `no RLS` reality (DRIFT B.3) — the shared-schema default landed, RLS did not.

---

# F. PRODUCT squad (`product/`) — 2 files

## F1 — `product/KICKOFF_KEYSTONE_SPEC.md`  ★ (prompt-named priority; 466 lines — longest in slice)
- **path:** `project/squads/product/KICKOFF_KEYSTONE_SPEC.md` · **ext:** md · **empty?** no (466 lines,
  25817 B) · status: Draft. STRUCTURAL ONLY — examples are generic placeholders (`$XXXM`, `<SupplierA>`).
- **what:** PROD-KICKOFF-KEYSTONE — the **field-level data model for `cyc.*`** (the kickoff *setup
  file*): source corpus, a ~70-field catalog across 9 groups classified structured-vs-narrative, the
  proposed additive `cyc.*` DDL (~11 tables), a crosswalk, Session-2 validation, and sponsor open
  questions.
- **DETAILED WHY:** The kickoff doc is "the setup file of the whole system" — "declare structure once at
  kickoff, store it, render everything downstream from it." This spec exists because **both source specs
  under-model the kickoff (G5)**: the as-built `rfp_cycle` carries commodity/objective/dates only; the
  brief's `cyc.cycle` adds a thin `pricing_basis` and names the safeties without modeling them. The five
  real kickoff docs prove the structure is **consistent across categories and years** and lifts into
  fields. **Governing rule:** structured fields drive the system; narrative blocks carry the *why* and stay
  prose — never field-ify the narrative. Without it the cycle layer would be incomplete and the rail,
  safeties, RFI, PBA, and terms would have no field model.
- **section outline:** §a source corpus (5 sponsor artifacts; the consistent 14-section spine) → §b field
  catalog (9 groups: 1 cycle identity, 2 objective, 3 pricing + five safeties, 4 scope & items, 5
  historical/baseline incl. KCMS scan + 12-col scorecard, 6 supplier field + configurable RFI, 7 commercial
  terms PBA/working-capital/KPM, 8 timeline/rail, 9 narrative blocks) + field count + data lineage → §c
  proposed `cyc.*` model (additive DDL — DO NOT edit baseline) → §d crosswalk to as-built `rfp_cycle` + brief
  `cyc.cycle` → §e validation of Session 2 (confirmed / adds / correction) → §f open questions → Changelog.
- **key specs / decisions recorded:**
  - **~70 kickoff data elements across 9 groups**, each classified S (structured) or N (narrative) with
    type/cardinality/source feed (KCMS / iTrade / DECL declared / AUTH authored).
  - **Group 3 — the five safeties (the decision layer):** `DISASTER_TRIGGER`, `INVERSE_DISASTER_TRIGGER`,
    `COLLAR` (floor/cap), `ROLLING_MIDPOINT` (window_weeks, reevaluation_cadence_weeks), `TOLERANCE_BAND`
    (band_pct, hold_weeks, re_review_window) — each optional, a per-cycle configurable menu. Plus
    `pricing_basis` (FIXED/INDEX/HYBRID), `duration_cadence`, `baseline_then_negotiate`, `routing_basis`.
  - **Group 5 — the exact 12-column scorecard schema** (volume_cases, pct_of_volume, pct_of_cost,
    avg_fill_rate, avg_adjusted_fill_rate, avg_on_time, avg_dc_rejection, rejected_case_qty,
    rejection_count, avg_cost_per_case, avg_age_at_receipt) + snapshot_type KICKOFF/SIGNOFF; KCMS scan
    metrics (6 × current/previous) at subcommodity + GTIN grain with the manual `Scope` flag.
  - **Group 8 — the canonical rail** (Build RFI/RFP → … → **Kickoff Meeting with Leadership** → … →
    **Sign-off Meeting with Leadership** → Send Awards & PBAs → Commitment Start) — the two leadership gates
    anchor the ends; drives the rendered rail (E-16), replacing hardcoded stages.
  - **§c additive DDL:** ALTER `cyc.cycle` (annual_spend, horizon_label, fiscal/calendar timeframes, dcs_scope)
    + `cycle_objective` (one is_primary), `cycle_pricing`, `cycle_safety` (params jsonb), `cycle_scope_item`
    (the manual in_scope flag), `cycle_pba_term`, `cycle_commercial_term`, `cycle_invited_supplier`
    (+is_incumbent), `cycle_rfi_question`, `cycle_timeline_event`, `cycle_narrative` (versioned rich text).
    All ADD/EXTEND, additive — no break to `cyc` (the program's breaking changes are all in `eng`).
  - **§e Session-2 correction:** the three Word kickoffs surface only **baseline-then-negotiate + cadence**
    explicitly in prose; the five named safeties come from the broader intake — model all five as optional
    but flag that only those two are doc-evidenced here (intended-capability, not observed-in-corpus).
  - **§f open questions:** the top one — **one setup per RFP, or heterogeneous (different cadence per
    subcommodity/lot)?** — sets the grain of the keystone (`cycle_pricing` one-per-cycle vs per-scope).
- **implemented vs aspirational:** **Largely aspirational / recorded scope.** The full kickoff `cyc.*`
  satellite set is the E-14 deliverable; DRIFT C lists "full Cycle Setup" as recorded-but-not-built (the
  A1 Cycle Setup/Strategy frontend is an MVP-cut, no `/setup` route). Some pieces landed (the bid template,
  product type Conv/Organic flag in setup, the invited-supplier denominator), but the kickoff-satellite
  tables (objective/pricing/safety/PBA/RFI/timeline/narrative) and the rail render (E-16) are deferred
  scope. The five safeties are **stored but never computed** (DRIFT C, E-29). This is the richest *unbuilt*
  spec in the slice.

## F2 — `product/PLAN.md`
- **path:** `project/squads/product/PLAN.md` · **ext:** md · **empty?** no (155 lines, 9437 B) · status:
  Draft.
- **what:** PROD-PLAN — the Product / BA squad plan: owns the kickoff keystone field model (`cyc.*`,
  E-14/G5), the structured-vs-narrative governing rule, the supplier field + configurable RFI, E-14
  acceptance criteria, and the sponsor open-questions backlog.
- **DETAILED WHY:** It exists to frame and own the kickoff keystone (the deliverable is
  KICKOFF_KEYSTONE_SPEC + the SAMPLE_REGISTER), to hold the structured-vs-narrative rule throughout, to
  slice E-14 into vertical store-first increments, and to bind the data-handling rule (real commercial
  values quarantined; committed output structural-only). Without it the kickoff work would lack acceptance
  criteria and the clean-room sample-handling posture for the five real kickoff docs.
- **section outline:** intro → §1 scope (in-now / in-next / out-of-scope-to-other-squads) → §2 the
  governing rule → §3 backlog slices for E-14 (E14-S1..S7 table) → §4 acceptance criteria (8) → §5 open
  questions for the sponsor (6) → §6 data-handling note (binding — ADR-0001 + Security PLAN) → Changelog.
- **key specs / decisions recorded:**
  - **The governing rule:** structured fields drive the system; narrative blocks carry the *why* and stay
    prose; never force narrative into fields; never bury a decision in prose.
  - **E-14 slices (store-first, vertical):** S1 identity+objective, S2 pricing+five safeties, S3 scope &
    baseline pointers, S4 commercial terms, S5 supplier field + configurable RFI, S6 timeline/rail (feeds
    E-16), S7 narrative blocks. Each lands additively (no break to `cyc`).
  - **8 acceptance criteria:** a full cycle declarable from one real kickoff doc end-to-end; structured
    drives + prose stays prose; two scorecard snapshots + KCMS two grains representable; timeline drives the
    rail (not hardcoded); RFI configurable per cycle; objective multi-valued with a primary; no change to
    `db/baseline/` (DDL is a reviewed proposal for Platform & Data); no sensitive commercial value committed.
  - **Out-of-scope boundaries:** physical schema/migrations → Platform & Data; safety execution/
    visualization → Engine (E-15/G4); scorecard/iTrade/KCMS ingestion → Platform & Data; RBAC/Stage-0
    internals → Security.
  - **Data-handling (binding):** the five source files contain real commercial values → quarantined under
    `reference/samples/*` (gitignored); committed output is structural only; examples are placeholders;
    sanitized record is `reference/SAMPLE_REGISTER.md`.
- **implemented vs aspirational:** A planning doc whose deliverable (KICKOFF_KEYSTONE_SPEC) is written; the
  *build* it plans (E-14) is largely deferred (see F1 drift). The data-handling clean-room posture is
  enforced program-wide (CI clean-room guard + the commercial-value scanner Security owns).

---

# G. QUALITY squad (`quality/`) — 1 file

## G1 — `quality/PLAN.md`
- **path:** `project/squads/quality/PLAN.md` · **ext:** md · **empty?** no (275 lines, 21082 B) · status:
  Draft.
- **what:** QA-PLAN — the Quality & Assurance squad plan: the test pyramid, engine-reproducibility (S2),
  governance/invariant tests (S6), the **real-data pilot (E-13, the Phase B exit gate that retires R1)**,
  UAT with Sourcing, and per-phase quality gates.
- **DETAILED WHY:** It exists because the program's **#1 risk (R1 / [X-1])** is that nothing has run on
  real data — both packages are validated only against fixtures their own authors designed. QA's charter
  deliverable is the real-data pilot that retires R1 at the Phase B exit gate; everything else makes that
  pilot trustworthy and repeatable. **Principle: a test against author-designed synthetic data proves the
  code does what the author expected; only the pilot proves it survives the mess it exists to absorb** —
  the first real cycle is treated as a test, not a delivery. Without it the governance invariants, the
  engine-reproduction gate, and the clean-room test discipline would be unspecified.
- **section outline:** intro + principle → §1 test strategy & the 5-layer pyramid (Unit/Integration/
  Contract/E2E/Pilot; what each must cover; how synthetic fixtures stay synthetic) → §2 engine
  reproducibility (the golden-master approach + 6 assertion groups + the stub→swap gate) → §3 governance/
  invariant tests (6 invariants, "the negative case is the real test") → §4 tenancy/security test hooks
  (with Security) → §5 THE REAL-DATA PILOT (E-13) — objectives, the 6 exact artifacts needed, entry
  criteria, 10 end-to-end steps, pass/fail acceptance, data-handling, what success proves → §6 UAT with
  Sourcing & per-phase quality gates.
- **key specs / decisions recorded:**
  - **5-layer pyramid:** Unit (pure domain, synthetic fixtures — scoring bands at 3/7/12% edges, eligibility
    codes, All-In fallback no-double-subtract, weight-normalization), Integration (real Postgres, never
    SQLite — CHECK/identity-FK rejection, migration roundtrip, guard-listeners, RLS), Contract (Schemathesis
    — every endpoint matches schema, no read returns "awarded", authn/authz on every route), E2E (full
    synthetic cycle through the real API + event trail + "open last cycle" <2s), **Pilot** (the apex, one
    real cycle).
  - **Clean-room test discipline:** synthetic fixtures live only in `backend/tests/fixtures/` (clearly
    fabricated, `ACME-SYN`); real samples only in `reference/samples/` (gitignored, never a fixture); CI
    guard `test_no_real_data_in_tests.py` greps for real tokens; `test_cleanroom_import.py` enforces
    backend-never-imports-reference.
  - **§2 engine reproducibility (6 assertion groups):** the five banded factors (tol ≤0.5); band edges fire
    at 3/7/12%; eligibility gate_flags; `max_two_per_dc` same top-N + same lot split + cap_breach_flag;
    Scenario A reproduces the Lowest Cost Check total; footguns (All-In no double-subtract; prior-round
    lot-level only). **Stub→swap gate:** no run tagged `engine_version != stub` may merge unless this suite
    is green; CI forbids `engine_version = stub` runs in the pilot.
  - **§3 six governance invariants:** immutable sealed runs (UPDATE/DELETE rejected by trigger; a correction
    is a new run); freeze-and-layer (raw award byte-recoverable from the layer chain); no hard deletes
    anywhere (repo-wide AST/grep guard); live audit event log (every state change emits one event;
    hash-chain links verify; mid-chain tamper detectable — retires R4); decision-support only
    (BANNED_DECISION_WORDS guard raises; no read returns "awarded"; engine never writes `awd.*`); draft→SENT
    gate (approver + timestamp required).
  - **§5 the real-data pilot (E-13):** 6 exact artifacts (A real iTrade export, B real bid round, C real
    kickoff doc, D **a known-good v3 output** = the golden master, the single most important; E the v3
    `.py` via the isolated intake; opt Norm sheet + booking guide); 10 end-to-end steps; PASS line = "the
    engine reproduces v3 on the real input within tolerance — **this is the line that retires R1.**"
  - **§6 per-phase gates:** 0 (roundtrip + SQLite-isms gone + guards live), A (live audit chain + tenant
    isolation + open-last-cycle <2s), **B (THE PILOT PASSES + UAT sign-off → R1 retired)**, C (cycle from
    real kickoff + Stage-0 in-gate), D (engine-reproducibility green → authorizes the stub→v3 swap), E
    (freeze-and-layer + no-hard-delete + draft→sent + booking guide from records + savings-vs-STLY), F
    (full contract suite + every endpoint guarded). Standing gate from Phase B: every slice works against
    the pilot dataset, not only synthetic.
- **implemented vs aspirational:** The test pyramid + governance invariants + engine-reproducibility gate
  are built and CI-enforced (DRIFT A: engine tested; the immutability/freeze/audit invariants are realized,
  though DRIFT B.4 flags 2 audit write-points outside the chain). **The real-data pilot (E-13) is NOT yet
  run** — DRIFT R1 ("nothing has run on real data") is the program's open #1 risk; the artifacts A–E remain
  sponsor-pending. RBAC route-guard tests (S8) can't pass because rbac.py is defined but zero routes call it
  (DRIFT C). Tenant isolation/RLS tests (S7) blocked by the no-RLS drift (B.3).

---

# H. SECURITY squad (`security/`) — 1 file

## H1 — `security/PLAN.md`  ★ (prompt-named priority)
- **path:** `project/squads/security/PLAN.md` · **ext:** md · **empty?** no (331 lines, 24694 B; most
  lines in slice) · status: Draft.
- **what:** SQUAD-SEC-001 v1.0 — the Security & Compliance squad plan: **the net-new enterprise layer
  neither original package contained** — multi-tenant isolation, identity/RBAC, the live audit hash-chain
  (G11), the two governance gates (G12 in / G9 out), data protection, the threat model, and the security
  NFR acceptance criteria (S7–S15). Owns the clean-room CI rule.
- **DETAILED WHY:** This is the layer that makes the system an **enterprise system of record** rather than
  a single-operator tool — it exists to retire **R7** ("commercial data with no RBAC/PII/retention is an
  enterprise non-starter"). It applies the inheritance rule to security (shape/intent from the brief —
  client as first-class, portfolio sign-off, draft→sent as a gate, live event log; constraint discipline
  from the as-built — composite-identity FKs, the hash-chain design, app+DB double enforcement; never
  weaken an as-built control). It models policy + enforcement points; Platform & Data ships the columns/
  migrations/triggers, Engine wires the guards, DevOps provides the IdP/secret-store. Without it tenancy
  leakage, privilege escalation, and commercial-data leakage have no controls.
- **section outline:** §1 tenancy model (E-03/ADR-0004 — `ref.client`, RLS strategy, defence-in-depth,
  composition with composite-identity FKs, leakage checklist) → §2 identity/authn/RBAC (E-03/04/ADR-0009 —
  IdP-delegated authn, the role catalog, the permission×lifecycle matrix, API authz) → §3 the live audit
  hash-chain (E-05/G11/ADR-0005 — the row schema, population, write-only enforcement, tamper-evidence,
  "open last cycle" reads it) → §4 governance gates (E-17 G12 in / E-24 G9 out / portfolio sign-off) → §5
  data protection (ADR-0015 — C0–C3 classification, retention, the reference/samples rule, clean-room CI
  rule) → §6 threat model (STRIDE) → §7 NFR security acceptance criteria S7–S15 → §8 what we need from the
  sponsor (DEP-4 + sample intake) → §9 sequencing & ownership boundaries → Changelog.
- **key specs / decisions recorded:**
  - **Tenancy (§1):** `ref.client` first-class; every tenant-scoped table carries non-null `client_id` FK;
    isolation is **defence-in-depth two layers** — app-layer (tenant context set at the auth edge from the
    verified principal's claim, **never** from a request body/param/header; every repository injects
    `WHERE client_id=:ctx_tenant`) + DB-layer (**PostgreSQL RLS** keyed to `SET LOCAL app.current_tenant`;
    app connects as a non-superuser non-`BYPASSRLS` role). **Tenancy composes with the as-built's 46
    composite FKs by prepending `client_id`** → cross-tenant referential leakage is structurally
    impossible, not merely filtered. Global reference (commodity, dc, fiscal_calendar, zip_centroid) is NOT
    tenant-scoped.
  - **RBAC (§2):** authn delegated to an external IdP (OIDC/SAML, provider-neutral adapter); a 7-role
    catalog (Sourcing Analyst, Category Manager, Leadership/Approver, Admin, Auditor, Platform Admin
    cross-tenant break-glass, Service account); a permission×lifecycle matrix where **the author cannot
    approve their own gate** (Analyst/Cat Man produce, Approver ratifies — separation of duties); approval
    transitions are distinct permissioned verbs, never side-effects of a GET or a run.
  - **Audit hash-chain (§3):** the `audit.event_log` row (client_id, occurred_at, actor, source,
    event_type, entity, before/after_state_hash sha256, prev/this `event_hash = sha256(fields ‖
    prev_event_hash)`, per-tenant monotonic `seq`); population by a **single audit writer** in the same
    transaction as the change (a change without its event cannot commit; an event without its change cannot
    exist); write-only enforced app + DB (BEFORE UPDATE OR DELETE trigger raises; role has INSERT+SELECT
    only); `verify_chain(tenant, [from,to])` walks the chain and pinpoints the first break.
  - **Governance gates (§4):** Stage-0 in-gate G12 (`cyc.cycle_ingate_approval`; a cycle cannot leave DRAFT
    or bind real feeds without an Approver approval); draft→SENT G9 (a `sent` lifecycle state on feedback/
    awards/documents; irreversible; writes a SENT event; the `BANNED_DECISION_WORDS` guard coexists);
    portfolio sign-off (out-gate, portfolio-level, freezes a set of awards together — Session 4 "$5.0M
    across categories").
  - **Data protection (§5):** four classification tiers C3 (commercial-sensitive — bid/landed/awarded
    prices, scorecards, savings — encrypted, never committed/logged), C2 (internal), C1 (PII limited), C0
    (public/reference); append-only effectively-permanent retention (the audit chain exempt from purge); the
    **reference/samples rule** (C3 samples git-ignored, referenced by hash; a CI commercial-value scanner
    fails on staged price/PII-shaped values; the reference-intake agent emits only schema + digest); the
    clean-room CI rule (backend never imports reference).
  - **STRIDE (§6):** each threat → control (spoofing→IdP-signed tokens/tenant-from-token; tampering→app+DB
    immutability + hash-chain; repudiation→actor-stamped chained events; info-disclosure→RLS + composite
    client_id keys + log scrubbing + C3 gitignore; DoS→rate/payload caps; EoP→separation of duties +
    non-BYPASSRLS role + gated cross-tenant).
  - **NFR criteria S7–S15:** S7 tenant isolation (RLS denies even with the app filter removed), S8 RBAC
    enforced (author≠approver), S9 audit live + write-only (`verify_chain`), S10 open-last-cycle reads the
    chain <2s, S11 Stage-0 in-gate, S12 draft→SENT, S13 classification + sample rule, S14 clean-room
    boundary, S15 IdP integration. Each a tested invariant (QA runs in CI), directly retiring R7.
- **implemented vs aspirational:** **Largely NOT YET ENFORCED — the biggest concentration of recorded-
  but-not-built / drifted scope in the slice.** Per DRIFT: tenancy (D8) **drifted** — client_id on a couple
  of `ref` tables, **no RLS** (B.3); RBAC (rbac.py defined, **zero routes call it** — C); Stage-0 in-gate
  (E-22/sign-off, SIGNED_OFF enum never emitted — C); Settings/Admin/RBAC UI (A6) not built (C). What IS
  built: the live audit hash-chain spine and immutability (DRIFT A: append-only audit, sealed runs,
  freeze-and-layer) — **except 2 write-points (setup-ingest, capacity-ingest) emit no event** (B.4). The
  clean-room CI rule (S14) is enforced. So §3 (audit chain) is mostly real with two gaps; §1/§2/§4 (RLS,
  RBAC enforcement, gates) are designed-not-enforced — acceptable for the single-operator pilot, a real gap
  before multi-tenant/external use (exactly as DRIFT frames it).

---

# I. SLICE-LEVEL SYNTHESIS — implemented vs aspirational (DRIFT cross-reference)

Across the 22 squad docs (cross-ref `project/triage/DRIFT_RECONCILIATION.md`):

- **BUILT FAITHFULLY (DRIFT A):** the engine brain (V3_ENGINE_LOGIC, GOLDEN_MASTER, SPIKE_D2 — 5-factor
  banded scoring, 7 lenses A–G, split allocation + cap-breach, sealed reproducible runs, the formula
  registry, the split-grain G1 closed), the governed-persistence spine + freeze-and-layer (architecture
  PLAN/SKELETON, platform-data PLAN), flat-13 period storage (INTAKE_TEMPLATE increments 2a/2b — migrations
  0014/0015/0016, all backward-compatible/inert), the pilot document loop + harness rehearsal path
  (PILOT_SYSTEM_DESIGN, PILOT_INPUT_DOCS, SKILL_HARNESS, HARNESS_REHEARSAL — per-run DB isolation D30
  addressed), the alignment-workbook redesign (SCENARIO_TOOL_DESIGN_STUDY, 18 tabs, all schema-grounded),
  the CI gates + migration roundtrip + clean-room guard (platform-devops PLAN, quality PLAN), the live
  audit hash-chain (security PLAN §3, with 2 write-point gaps), engine-derived explanations D28.

- **BUILT BELOW THE BAR / DRIFTED (DRIFT B):** tenancy no-RLS (security §1, architecture #5 — B.3);
  `bid_line.fiscal_period_id` varchar(36) vs uuid (INTAKE TYPE NOTE — B.5); the runner's `all_lot_discount`
  omission (V3_LOGIC adjacency — B.6); 2 audit write-points outside the chain (security §3 — B.4); 4
  frontend MVP-cuts incl. Alignment depth vs the SCENARIO_TOOL design (B.2).

- **RECORDED BUT NOT YET BUILT (DRIFT C):** the iTrade importer (FEEDS_ITRADE / platform-data PLAN §4 /
  CYCLE_FIELDTOMATO §2 — E-08, table exists, nothing populates → STLY runs on the ×1.04 proxy flagged in
  SCENARIO_TOOL §8.3); KCMS (E-09); supplier scorecard (E-10); the five pricing safeties (KICKOFF_KEYSTONE
  Group 3 / engine PLAN G4 / CYCLE_FIELDTOMATO §6 — E-29, stored never computed); the full kickoff `cyc.*`
  satellite set + the rail render (KICKOFF_KEYSTONE / product PLAN — E-14/E-16); RBAC enforcement +
  Stage-0/sign-off gates (security §2/§4 — E-17/E-22/E-24); comms SEND + most touchpoints
  (EMAIL_STYLE_AND_MAILMERGE — E-37); the real-data pilot itself (quality PLAN §5 — E-13, R1 still open);
  the period-model ACTIVATION (INTAKE_TEMPLATE — deferred until after the first live run); the cloud/IdP IaC
  (platform-devops — DEP-4 pending).

- **EMPIRICAL FINDINGS feeding requirements:** TOMATO_RUN's single-round v3 crash (a guard requirement +
  a missing fixture case); the "176 columns is not 176 fields" debunk + the `.xlsb` multi-format
  requirement (CYCLE_FIELDTOMATO — concrete E-08 parse rules).

**Net for D2:** the squads tree is the program's design/decision record. The *engine, persistence, audit-
spine, CI, period-storage, pilot-document, and alignment-workbook* designs are substantially built; the
*feeds (iTrade/KCMS/scorecard), pricing-safety execution, kickoff-satellite build, RBAC/RLS/gates
enforcement, comms send, and the real-data pilot* are recorded-but-deferred or drifted — every one
enumerated in DRIFT_RECONCILIATION. No silent loss; the disk record held.
