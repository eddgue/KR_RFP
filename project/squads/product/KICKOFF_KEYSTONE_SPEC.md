---
doc: Kickoff Keystone Specification — the cyc.* field model (G5 / E-14)
id: PROD-KICKOFF-KEYSTONE
squad: Product / BA (Squad 7)
status: Draft
created: 2026-06-18
classification: STRUCTURAL ONLY — no sensitive commercial values; examples are generic placeholders
owner: Product / BA squad
source: 5 sponsor-supplied kickoff artifacts (see reference/SAMPLE_REGISTER.md) + SESSION-02
relates: audit/02 G5, specs/rfp-engine/BUILD_02 Layer 3, specs/original-engine/BUILD_02 Layer 3,
         project/squads/architecture/PLAN.md §2 (cyc table list), E-14/E-15/E-16/E-17, ADR-0001
---

# Kickoff Keystone Specification

The field-level data model for `cyc.*` — the kickoff *setup file*. The kickoff doc is filled by
hand in Word today and stored in a folder; the structure below is consistent across categories and
years, so it lifts into fields. **Governing rule:** structured fields drive the system; narrative
blocks carry the *why* and stay prose — never field-ify the narrative.

> **Data handling.** Every example here is a **generic placeholder** (`$XXXM`, `<SupplierA>`,
> `<SubComm-1>`). No real spend, supplier, threshold, or margin appears. Raw files are quarantined
> (gitignored). See the data-handling note in `project/squads/product/PLAN.md §6`.

---

## a. Source corpus

Five sponsor artifacts (by type/category/year only — see `reference/SAMPLE_REGISTER.md`):

| # | Type | Category (generic) | Cycle year |
|---|---|---|---|
| 1 | Word (narrative kickoff) | Field-grown produce | 2026 |
| 2 | Word (narrative kickoff) | Greenhouse / protected produce | 2025 |
| 3 | Word (narrative kickoff) | Wet + packaged produce | 2027–2028 |
| 4 | Excel (prep workbook) | Field-grown produce | prep |
| 5 | Excel (prep workbook) | Greenhouse / protected produce | prep |

**Consistent structure observed across the three Word docs** (the same section spine every time):

1. Header — *Annual Spend* + *Timeframe* (Kroger fiscal periods **and** calendar dates).
2. **Category Overview** — scan metrics, current vs prior period (window stated).
3. **Background** — sourcing history (prose).
4. **Data Dive** — household/consumer analytics: VPS/PS/LPS mix, leakage, promo uplift (prose).
5. **Industry Insights** — market/weather/tariff/crop (prose).
6. **Supplier Scorecards (ES)** — window + subcommodities in scope.
7. **Category Strategy (CM)** — strategy narrative (prose).
8. **Sourcing Strategy (ES)** — invited-supplier counts, **new RFI questions**, bid-format notes (prose + structured nuggets).
9. **General / Standard Goals** — RPC-vs-corrugate, Kroger-managed-vs-vendor freight (prose with collectable options).
10. **PBA** — addendum + metric thresholds + enforcement language.
11. **84.51° KPM Funding** — amount + treatment.
12. **Working Capital (ES)** — target payment terms + quantified benefit.
13. **Next Steps (CM & ES)** — the per-cycle timeline / rail.
14. **Appendix** — links (USDA market data, OVS/FVC reports).

**Workbooks** carry the structured exports that feed the doc: a **Scorecard** + **Scorecard
Export** snapshot, and (in the full workbook) a **Scorecard (Signoff)** snapshot — i.e. the
**two frozen snapshots** — plus `*USE` reduced views, **KCMS (subcomm) Export** and **KCMS
(GTIN) Export** (scan metrics at two grains, with a manual **Scope** flag separating in-scope
GTINs from noise such as pharmacy/cola/egg/candy rows), and a **Next Steps** tab carrying two
parallel timeline columns (a planned vs revised rail).

---

## b. Field catalog

Class = **S**tructured | **N**arrative. Source feed: **KCMS** (scan) · **iTrade** (PO/receipt) ·
**DECL** (declared at kickoff) · **AUTH** (authored prose). Examples are generic placeholders.

### Group 1 — Cycle identity (S)

| Field | Type | Class | Req | Feed | Example (placeholder) |
|---|---|---|:--:|---|---|
| `category` | text | S | yes | DECL | `<CategoryName>` |
| `cycle_year` / horizon label | text | S | yes | DECL | `2027-2028` |
| `annual_spend` | money | S | yes | KCMS/iTrade | `$XXXM` (size of the prize) |
| `timeframe_start` / `timeframe_end` (fiscal) | text (fiscal period) | S | yes | DECL | `P4 2027 – P3 2028` |
| `timeframe_start` / `timeframe_end` (calendar) | date | S | yes | DECL | `<YYYY-MM-DD>` |
| `subcommodities_in_scope` | list of codes | S | yes | KCMS | `<SubComm-1>, <SubComm-2>, …` |
| `dcs_in_scope` | enum/list | S | yes | DECL | `ALL` (national default) |
| `prior_structure_note` | text | S | no | DECL | "full year, N timeframes negotiated separately" |
| `status` | enum | S | yes | DECL | lifecycle through both gates |

### Group 2 — Objective (S, multi with a primary)

| Field | Type | Class | Req | Feed | Example |
|---|---|---|:--:|---|---|
| `objective_code` | enum | S | yes | DECL | `SAVINGS \| SUPPLY_ASSURANCE \| QUALITY \| DIVERSIFICATION \| STRATEGIC` |
| `is_primary` | bool | S | yes | DECL | exactly one primary |
| `objective_note` | text | N | no | AUTH | one line of rationale |

### Group 3 — Pricing structure + the five safeties (S — the decision layer)

| Field | Type | Class | Req | Feed | Example |
|---|---|---|:--:|---|---|
| `pricing_basis` | enum | S | yes | DECL | `FIXED \| INDEX \| HYBRID` |
| `duration_cadence` | enum | S | yes | DECL | `FULL_YEAR \| SEASONAL \| TIMEFRAMES(n) \| PERIOD_BY_PERIOD \| QUARTERLY \| MONTHLY \| WEEKLY` |
| `baseline_then_negotiate` | bool | S | yes | DECL | true = set a year baseline, negotiate each timeframe separately |
| `volume_split_rule` | text/enum | S | no | DECL | how volume divides across suppliers/timeframes |
| `routing_basis` | enum | S | no | DECL | `FOB \| DELIVERED \| XDOCK \| CBS_FREIGHT` (FOB corrugate / FOB RPC / delivered surcharge by DC) |
| `sourcing_region_per_period` | text | S | no | DECL | supplier-stated grow origin, per period (≠ iTrade ship-from) |

**The five safeties** — each optional, attached to the cycle (a per-cycle configurable menu):

| Safety (`safety_type`) | Parameters (typed) |
|---|---|
| `DISASTER_TRIGGER` (escalator) | trigger condition; supplier reprices up on a market spike |
| `INVERSE_DISASTER_TRIGGER` (de-escalator) | trigger condition; Kroger forces price down inside the collar |
| `COLLAR` | `floor`, `cap` |
| `ROLLING_MIDPOINT` | `window_weeks`, `reevaluation_cadence_weeks` |
| `TOLERANCE_BAND` | `band_pct`, `hold_weeks`, `re_review_window` (move-and-hold, not move-once) |

> Note: of these five, the three Word docs surface **baseline-then-negotiate** and the
> cadence options explicitly in prose; the named safety vocabulary is from the broader intake
> (see §e). All five are modeled as optional so any cycle can declare the subset it uses.

### Group 4 — Scope & items (S, partly manual)

| Field | Type | Class | Req | Feed | Example |
|---|---|---|:--:|---|---|
| `subcommodity_code` | code | S | yes | KCMS | `<SubComm-1>` (the anchor; groups specs + packing variants) |
| `gtin_code` | code | S | yes | KCMS (GTIN export) | `<GTIN>` |
| `gtin_in_scope_flag` | bool | S | yes | DECL (manual) | the manual signal-from-noise call (junk GTINs show once; in-scope show high variant counts) |
| `lot_assignment` | FK → `norm.lot` | S | yes | DECL/norm | sticky map, category-filtered |
| `pack_normalization` | text | S | no | DECL | manual path; raw under, normalized on top |
| `projected_volume` | numeric | S | no | KCMS/planning | DC × item × period demand |

### Group 5 — Historical / baseline (pulled at prep, S)

**KCMS Category-Overview scan metrics** — captured at **subcommodity** and **GTIN** grain,
**current vs previous** period:

| Field | Type | Class | Feed |
|---|---|---|---|
| `scanned_cost_current` / `_previous` | money | S | KCMS |
| `scanned_retail_current` / `_previous` | money | S | KCMS |
| `scanned_movement_current` / `_previous` | numeric | S | KCMS |
| `gross_margin_dollars_current` / `_previous` | money | S | KCMS |
| `gross_margin_pct_current` / `_previous` | pct | S | KCMS |
| `fcb_unit_cost_current` / `_previous` | money | S | KCMS |
| `scope` (GTIN grain only) | flag | S | DECL | manual in-scope marker |

**Supplier scorecard** — exact fields confirmed from the prep workbooks; captured **twice**, on
different windows (a **kickoff snapshot** + a **sign-off snapshot** — confirmed by the
`Scorecard` vs `Scorecard (Signoff)` tabs). Both freeze (freeze-and-layer).

| Field | Type | Class | Feed |
|---|---|---|---|
| `supplier_name` | FK → `ref.supplier` | S | iTrade |
| `volume_cases` | numeric | S | iTrade |
| `pct_of_volume` | pct | S | iTrade |
| `pct_of_cost` | pct | S | iTrade |
| `avg_fill_rate` | pct | S | iTrade |
| `avg_adjusted_fill_rate` | pct | S | iTrade |
| `avg_on_time` (DLVD only) | pct | S | iTrade |
| `avg_dc_rejection` | pct | S | iTrade |
| `rejected_case_qty` | numeric | S | iTrade |
| `rejection_count` | numeric | S | iTrade |
| `avg_cost_per_case` | money | S | iTrade |
| `avg_age_at_receipt` | numeric | S | iTrade |
| `snapshot_window` | text/date-range | S | DECL |
| `snapshot_type` | enum `KICKOFF \| SIGNOFF` | S | DECL |

**Historical awarded cost (PO):** from iTrade/SAP, FOB by commodity, period-stamped to both
calendars (modeled in `perf.*` — the kickoff holds a **pointer**, not a copy).

### Group 6 — Supplier field + configurable RFI (S)

| Field | Type | Class | Req | Feed | Example |
|---|---|---|:--:|---|---|
| `invited_supplier` | FK → `ref.supplier` | S | DECL | yes | `<SupplierA>` |
| `is_incumbent` | bool | S | yes | DECL | denominator: N total (X incumbent, Y non-incumbent) |
| `rfi_question_code` | code | S | yes | DECL | stable code per question (for cross-cycle comparability) |
| `rfi_question_text` | text | S | yes | DECL | category-specific, evolves per cycle |
| `rfi_answer_type` | enum | S | no | DECL | `TEXT \| PCT \| BOOL \| ENUM` |

**RFI questions observed** (the set is configurable, not fixed): harvest & transit times to each
DC; grown vs sourced incl. grower names/locations; clean-sheet cost breakdown (% product / labor
/ packaging / production); TSA duty % included; packaging supplier (group-buy analysis); RPC vs
corrugate; Kroger-managed freight vs vendor-delivered.

### Group 7 — Commercial terms: PBA / working capital / KPM (S)

| Field | Type | Class | Req | Feed | Example |
|---|---|---|:--:|---|---|
| **PBA** `pba_required` | bool | S | yes | DECL | yes for all awarded suppliers |
| `pba_metric` | text/enum | S | yes | DECL | e.g. case-fill-rate metric, promo-volume support |
| `pba_threshold` | numeric/text | S | yes | DECL | `<threshold>` (e.g. fill-rate %) |
| `pba_enforcement` | text | S | yes | DECL | business-removal language; tariff revert/block clauses |
| **Working capital** `target_payment_terms` | text | S | yes | DECL | `NET <nn>` (target) |
| `current_terms_by_supplier` | text per supplier | S | no | DECL | `NET <nn>` (varies by supplier) |
| `working_capital_benefit` | money | S | no | DECL | `$X.XM` (quantified) |
| **KPM** `kpm_amount` | money | S | no | DECL | `$XXXK` (84.51° funding) |
| `kpm_treatment` | enum | S | no | DECL | `HELD_SEPARATE \| NEGOTIATED_INTO_COGS` |

### Group 8 — Timeline / rail from "Next Steps" (S, ordered)

| Field | Type | Class | Req | Feed | Example |
|---|---|---|:--:|---|---|
| `event_seq` | int | S | yes | DECL | ordinal |
| `event_name` | text | S | yes | DECL | see canonical rail below |
| `event_date` | date | S | yes | DECL | `<YYYY-MM-DD>` |
| `is_leadership_gate` | bool | S | yes | DECL | true for the two anchors |
| `round_no` | int | S | no | DECL | round count is variable (3 default, more if there is juice) |
| `bcg_support_needed` | bool | S | no | DECL | seen as a per-task flag in a workbook |

**Canonical rail** (from the full prep workbook): Build RFI/RFP → Send QA Survey → Send RFI/RFP →
QA Survey Responses Due → **Kickoff Meeting with Leadership** → RFI/RFP Responses Due → QA
Roundtable → Review Initial Bids & Set Targets → Send Target Guidance (R2) → R2 Due → Review &
Determine Alignment → Send Proposals (R3) → R3 Due → Finalize Alignment & Phone Negotiations →
**Sign-off Meeting with Leadership** → Send Awards & PBAs → Commitment Start. The two leadership
gates anchor the ends; this ordered list **defines the rail the app renders** (E-16).

### Group 9 — Narrative blocks (N, prose, versioned)

Stored as **versioned rich text** attached to the cycle — never field-ified.

| `narrative_type` | Class | Feed |
|---|:--:|---|
| `BACKGROUND` (sourcing history) | N | AUTH |
| `DATA_DIVE` (VPS/PS/LPS, leakage, promo uplift) | N | AUTH |
| `INDUSTRY_INSIGHTS` (market/weather/tariff/crop) | N | AUTH |
| `CATEGORY_STRATEGY` (CM) | N | AUTH |
| `SOURCING_STRATEGY` (ES) | N | AUTH |
| `GENERAL_GOALS` / `STANDARD_BID_GOALS` | N | AUTH |
| `APPENDIX_LINK` | N | AUTH |

**Field count.** ~70 distinct kickoff data elements cataloged across the 9 groups (identity 9,
objective 3, pricing+5 safeties 6 + 5 safety types, scope 6, baseline 7 KCMS + 14 scorecard,
supplier+RFI 5, commercial 9, timeline 6, narrative 7).

### Data lineage (where each block comes from)

| Block | Feed |
|---|---|
| Category Overview / scan metrics / GTIN+subcommodity scope | **KCMS** |
| Historical awarded cost, FOB, commodity, fiscal stamping | **iTrade / SAP** |
| Supplier scorecard (fill, on-time, rejection, cost/case, age) | **iTrade** PO/receipt |
| Pricing structure, safeties, objective, RFI set, PBA, terms, timeline | **declared at kickoff** |
| Background, strategy, industry, data dive, goals | **authored** (prose) |

Two pulled feeds (KCMS scan, iTrade cost+scorecard), one declared layer (the decisions), one
authored layer (the narrative). The **declared layer is the part that lives in people's heads
today** and is the core of the build.

---

## c. Proposed `cyc.*` model (ADDITIVE migration proposal — DO NOT edit `db/baseline/schema.sql`)

Presented here as the proposal for a **later additive migration** owned by Platform & Data.
Types are illustrative (PostgreSQL); FKs are composite-identity per the as-built KEEP discipline.
`cycle_id` threads tenancy (`client_id`) per ADR-0004; omitted below for brevity.

```sql
-- EXTEND existing cycle (additive columns only; no break to rfp_cycle/cyc.cycle)
ALTER TABLE cyc.cycle
  ADD COLUMN annual_spend            numeric(14,2),       -- size of the prize
  ADD COLUMN horizon_label           text,                -- e.g. '2027-2028'
  ADD COLUMN tf_start_fiscal         text,
  ADD COLUMN tf_end_fiscal           text,
  ADD COLUMN tf_start_calendar       date,
  ADD COLUMN tf_end_calendar         date,
  ADD COLUMN prior_structure_note    text,
  ADD COLUMN dcs_scope               text DEFAULT 'ALL';  -- national default

CREATE TABLE cyc.cycle_objective (
  cycle_id     bigint NOT NULL REFERENCES cyc.cycle,
  objective_code text NOT NULL
     CHECK (objective_code IN ('SAVINGS','SUPPLY_ASSURANCE','QUALITY','DIVERSIFICATION','STRATEGIC')),
  is_primary   boolean NOT NULL DEFAULT false,
  objective_note text,
  PRIMARY KEY (cycle_id, objective_code)
);  -- exactly one is_primary enforced by a partial unique index

CREATE TABLE cyc.cycle_pricing (
  cycle_id     bigint PRIMARY KEY REFERENCES cyc.cycle,
  pricing_basis    text NOT NULL CHECK (pricing_basis IN ('FIXED','INDEX','HYBRID')),
  duration_cadence text NOT NULL,        -- FULL_YEAR|SEASONAL|TIMEFRAMES|PERIOD_BY_PERIOD|QUARTERLY|MONTHLY|WEEKLY
  cadence_n        int,                   -- N for TIMEFRAMES(n)/PERIOD_BY_PERIOD(n)
  baseline_then_negotiate boolean NOT NULL DEFAULT false,
  volume_split_rule text,
  routing_basis    text CHECK (routing_basis IN ('FOB','DELIVERED','XDOCK','CBS_FREIGHT'))
);

CREATE TABLE cyc.cycle_safety (
  cycle_id     bigint NOT NULL REFERENCES cyc.cycle,
  safety_type  text NOT NULL CHECK (safety_type IN
     ('DISASTER_TRIGGER','INVERSE_DISASTER_TRIGGER','COLLAR','ROLLING_MIDPOINT','TOLERANCE_BAND')),
  params       jsonb NOT NULL,           -- typed per type: {floor,cap} | {window_weeks,...} | {band_pct,hold_weeks,...}
  PRIMARY KEY (cycle_id, safety_type)
);  -- parameters are READ by the engine (E-15) to make safeties executable/visualizable

CREATE TABLE cyc.cycle_scope_item (
  cycle_id     bigint NOT NULL REFERENCES cyc.cycle,
  subcommodity_code text NOT NULL,
  gtin_code    text,                      -- nullable: subcommodity-grain rows have no GTIN
  in_scope     boolean NOT NULL DEFAULT false,  -- the MANUAL signal-from-noise flag
  lot_id       bigint REFERENCES norm.lot,
  projected_volume numeric,
  PRIMARY KEY (cycle_id, subcommodity_code, gtin_code)
);

CREATE TABLE cyc.cycle_pba_term (
  cycle_id     bigint NOT NULL REFERENCES cyc.cycle,
  metric       text NOT NULL,            -- e.g. case fill rate, promo volume support
  threshold    text NOT NULL,            -- numeric or banded, kept as text for flexibility
  enforcement  text,                     -- business-removal / tariff revert/block clauses
  PRIMARY KEY (cycle_id, metric)
);

CREATE TABLE cyc.cycle_commercial_term (
  cycle_id     bigint NOT NULL REFERENCES cyc.cycle,
  term_type    text NOT NULL CHECK (term_type IN ('WORKING_CAPITAL','KPM','OTHER')),
  target_value text,                      -- 'NET <nn>' | '$XXXK'
  benefit_value numeric,                  -- quantified working-capital benefit
  treatment    text,                      -- KPM: HELD_SEPARATE | NEGOTIATED_INTO_COGS
  note         text,
  PRIMARY KEY (cycle_id, term_type)
);

CREATE TABLE cyc.cycle_invited_supplier (   -- EXTEND if the as-built table already exists
  cycle_id     bigint NOT NULL REFERENCES cyc.cycle,
  supplier_id  bigint NOT NULL REFERENCES ref.supplier,
  is_incumbent boolean NOT NULL DEFAULT false,
  PRIMARY KEY (cycle_id, supplier_id)
);

CREATE TABLE cyc.cycle_rfi_question (
  cycle_id      bigint NOT NULL REFERENCES cyc.cycle,
  question_code text NOT NULL,            -- stable code for cross-cycle comparability
  question_text text NOT NULL,
  answer_type   text CHECK (answer_type IN ('TEXT','PCT','BOOL','ENUM')),
  seq           int NOT NULL,
  PRIMARY KEY (cycle_id, question_code)
);

CREATE TABLE cyc.cycle_timeline_event (
  cycle_id      bigint NOT NULL REFERENCES cyc.cycle,
  event_seq     int NOT NULL,
  event_name    text NOT NULL,
  event_date    date,
  is_leadership_gate boolean NOT NULL DEFAULT false,
  round_no      int,                       -- variable; null for non-round events
  PRIMARY KEY (cycle_id, event_seq)
);  -- DRIVES the rendered process rail (E-16); replaces the hardcoded stages

CREATE TABLE cyc.cycle_narrative (
  cycle_id      bigint NOT NULL REFERENCES cyc.cycle,
  narrative_type text NOT NULL CHECK (narrative_type IN
     ('BACKGROUND','DATA_DIVE','INDUSTRY_INSIGHTS','CATEGORY_STRATEGY',
      'SOURCING_STRATEGY','GENERAL_GOALS','APPENDIX_LINK')),
  version       int NOT NULL DEFAULT 1,    -- versioned rich text; never field-ified
  body_richtext text NOT NULL,
  authored_by   text,
  authored_at   timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (cycle_id, narrative_type, version)
);
```

The **two scorecard snapshots** and **KCMS scan grain** are modeled in `perf.*`
(`perf.supplier_scorecard` with `snapshot_type ∈ {KICKOFF,SIGNOFF}`; `perf.kcms_movement` at
subcommodity and GTIN grain — E-08/09/10). The cycle holds the **pointers and windows**, not the
copied rows.

---

## d. Crosswalk — to as-built `rfp_cycle` and brief `cyc.cycle`

| Kickoff element | As-built `rfp_cycle` | Brief `cyc.cycle` | Disposition |
|---|---|---|---|
| commodity / category | yes | yes | **KEEP** |
| status lifecycle (2 gates) | yes (12 states) | yes | **KEEP** |
| timeframes (dimension) | `cycle_tf` | `cycle_timeframe` | **KEEP** |
| rounds (variable) | `cycle_round` | `cycle_round` | **KEEP** |
| DC / lot scope | `cycle_*_scope` | `cycle_dc`/`cycle_lot` | **KEEP** |
| subcommodity scope | `cycle_item_scope` | via scope | **KEEP** |
| invited suppliers (denominator) | `cycle_invited_supplier` | (named) | **EXTEND** (+`is_incumbent`) |
| projected volume | `cycle_projected_volume` | via scope | **KEEP** |
| **annual_spend** | no | no | **ADD** (`cycle.annual_spend`) |
| **objective (multi+primary)** | `target_savings_amt` only | single text, no enum | **ADD** (`cycle_objective`) |
| **pricing basis + cadence + baseline-then-negotiate** | no (commercial layer) | partial `pricing_basis` | **ADD** (`cycle_pricing`) |
| **five safeties** | params at commercial layer, inert | named, not modeled | **ADD** (`cycle_safety`) |
| **GTIN in-scope manual flag** | implicit in scoping | no | **ADD** (`cycle_scope_item.in_scope`) |
| **PBA governance** | no `cycle_term` | `cycle_term` (thin) | **ADD** (`cycle_pba_term`) |
| **working capital + KPM** | no | no | **ADD** (`cycle_commercial_term`) |
| **configurable RFI set** | no | no | **ADD** (`cycle_rfi_question`) |
| **timeline / rail** | hardcoded | rail implied | **ADD** (`cycle_timeline_event`) → E-16 |
| **narrative blocks** | no | no | **ADD** (`cycle_narrative`) |
| two scorecard snapshots | no | (perf) | **ADD** in `perf` (E-10) |
| KCMS scan grain | no | `kcms_movement` | **ADD** in `perf` (E-09) |

Everything is **ADD/EXTEND** at the `cyc` layer and additive — no breaking change. (The program's
breaking changes are all in `eng`, per architecture §2.)

---

## e. Validation of Session 2

**Confirmed by the real docs:**
- The consistent section spine across categories and years (the lift-into-fields premise holds).
- The **two-gate model** — *Kick-off Meeting with Leadership* and *Sign-off Meeting with
  Leadership* appear verbatim as the two anchors of every Next Steps list.
- The **per-cycle rail** — Next Steps varies; round count is variable; the workbook even carries
  a planned-vs-revised pair of timeline columns.
- The **SubCommodity anchor** and the **GTIN noise problem** — the KCMS GTIN export is dominated
  by junk (pharmacy/cola/egg/candy), confirming scoping = manual signal-from-noise via a `Scope`
  flag.
- **Freeze-and-layer / two scorecard snapshots** — the `Scorecard` vs `Scorecard (Signoff)` tabs
  are two distinct windows: the kickoff snapshot and the sign-off snapshot.
- The **exact scorecard schema** (12 metric columns) and **KCMS scan metrics** (6 metrics ×
  current/previous) at **two grains**.
- **KCMS as the scan-out source distinct from iTrade**, and **iTrade as the one feed powering
  both historical cost and the scorecard**.

**What the docs ADD beyond Session 2:**
- The **GTIN `Scope` flag as an explicit structured field** (not just a manual act) — the
  in-scope/out-of-scope decision is a stored boolean, the single most useful new structural fact.
- The **`Scorecard ... USE` reduced views** — the prep workbook keeps a curated subset
  (Supplier, % volume, Adjusted Fill Rate, DC Rejection) that the doc actually renders — evidence
  the scorecard has a *display projection* distinct from the full export.
- The **dual Next Steps columns** (planned vs revised, with a "delayed due to vacation schedules"
  annotation) — confirming the rail is editable/versioned per cycle, not just variable.
- A **`bcg_support_needed` per-task flag** in one workbook's Next Steps — an external-support
  marker on timeline events.
- **% of Cost** and **Avg Adjusted Fill Rate** as first-class scorecard columns alongside the
  Session-2 list.

**Correction to Session 2:**
- Session 2 lists the **five named safeties** (disaster trigger, inverse de-escalator, collar,
  rolling midpoint, tolerance band) as if surfaced in these docs. In the three Word kickoffs the
  *explicit prose* only names **baseline-then-negotiate** and the **cadence menu** (full-year /
  per-timeframe / quarterly / monthly / weekly). The named safety vocabulary comes from the
  broader intake, not these four docs. **Resolution:** model all five as an **optional
  configurable menu** (done in `cycle_safety`), but flag for the sponsor (§f.3) that only
  baseline-then-negotiate + cadence are doc-evidenced here; the rest are intended-capability, not
  observed-in-corpus.
- Minor (sanitization, not modeling): Session 2 embeds **real spend figures** as examples. Those
  are replaced here with `$XXXM` placeholders per the data-handling rule. Session 2 predates
  classification, so this is a sanitization correction, not a model error — but the inline real
  values should be scrubbed from that file too.

---

## f. Open questions for the sponsor

1. **One setup per RFP, or multiple structures inside one cycle?** Can a single cycle be
   **heterogeneous** — e.g. different pricing cadence per subcommodity/lot (Field-grown floats
   quarterly/monthly/weekly *and* per-timeframe negotiation in the same doc)? If yes,
   `cycle_pricing` re-grains from one-per-cycle to per-scope. **(Top question — it sets the grain
   of the keystone.)**
2. **RFI question-set governance** — curated, versioned template **library** with stable question
   codes (answers comparable across cycles), or free per-cycle authoring? The set demonstrably
   evolves ("new RFI questions incorporated") so it must be configurable; the open part is
   cross-cycle comparability.
3. **Safety menu** — confirm the full five-safety set is the intended configurable menu (only
   baseline-then-negotiate + cadence are doc-evidenced here).
4. **Objective enum** — confirm the closed set and the single-primary rule.
5. **Scorecard windows** — who defines kickoff vs sign-off windows; is the sign-off snapshot
   always re-pulled?
6. **KPM treatment** — confirm both `HELD_SEPARATE` and `NEGOTIATED_INTO_COGS` are valid per-cycle.

## Changelog

| Version | Date | Author | Change |
|---|---|---|---|
| 0.1 | 2026-06-18 | Product/BA squad | Initial keystone spec from the 5-doc corpus; ~70 fields, 11 cyc.* tables proposed, Session-2 validated/corrected. |
