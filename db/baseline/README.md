# db/baseline/ — the migration baseline

This directory holds the as-built schema **re-expressed as clean PostgreSQL** — our own artifact,
**not** an import of the existing project (ADR-0001 clean-room reconciliation). Alembic revision
`0001` applies `schema.sql` as the baseline of the chain; every later migration builds on it.

## Provenance

The baseline is derived from two inputs and re-authored by hand into clean PG:

1. **`specs/original-engine/BUILD_03_schema.sql`** — the as-built schema (63 tables, 67 CHECK
   constraints, 46 composite-identity FKs), auto-generated from the original `models.py`. We hold
   this today, so M0 is **non-blocking** on DEP-1 (Platform & Data `PLAN.md` §6, R-PD6).
2. **`reference/as-built-db/`** — on DEP-1 intake, a single isolated worktree agent emits the
   extracted/validated schema + Alembic-chain summary here for cross-checking. **Informs, never
   imported** (ADR-0001).

It is **re-expressed, not copied**: SQLite-isms removed, the no-op CHECK deleted, flat physical
names canonicalized to schema-qualified names. See `NAMING_MAP.md` for the crosswalk and
Platform & Data `PLAN.md` §2 (M0) for the defect list:

- boolean `DEFAULT 0/1` → native `boolean DEFAULT false/true`;
- `is_eligible = 0` / `constraint_satisfied = 1` comparisons → real boolean predicates;
- drop the no-op branch `length(error_log) >= 0` in `ck_calcrun_failed_has_errorlog`;
- prose-only enums → native `CREATE TYPE ... AS ENUM` (or `CHECK ... IN`);
- `VARCHAR(36)` UUID PKs reviewed — adopted tables keep text-UUID for FK fidelity; net-new
  spine tables (`ref.client`, `ref.commodity`) use native `uuid`. (Decision documented here per
  Platform & Data `PLAN.md` §2 M0.)

## Status — FULL M0 BASELINE (delivered)

`schema.sql` now holds the **full reconciled baseline**: the eight schemas plus all **63 as-built
tables re-expressed as clean PostgreSQL 15** (64 `CREATE TABLE`s = 62 adopted/cleaned + the
reconciled `audit.event_log` + the net-new `ref.client` tenant root), organized into the eight
logical-layer schemas and schema-qualified per `NAMING_MAP.md`.

What landed and what was verified:

- **All 46 composite-identity FKs** preserved (verified in the live catalog: 46 multi-column FKs).
- **All 67 as-built CHECK constraints** preserved (DB shows 69 CHECKs = 67 + the two net-new
  `ck_*_not_empty` on `ref.client`/`ref.commodity`).
- **All partial unique indexes** preserved (`uq_supplier_alias_norm_typed_active`,
  `uq_item_alias_norm_typed_active`, `uq_dc_alias_normalized_active`,
  `uq_historical_price_basis_one_preferred`, plus the `COALESCE`-expression
  `uq_loc_supplier_name_geo`).

SQLite-isms cleaned (audit `[D-6]`):

- `BOOLEAN DEFAULT 0/1` → native `boolean DEFAULT false/true` (e.g. `bid.bid_line.is_scoreable/
  is_awardable/leverage_signal_flag/best_in_class_signal_flag/follow_up_recommended_flag`);
- comparison SQLite-isms `is_eligible = 0`, `is_cost_awardable = 1`, `constraint_satisfied = 1/0`,
  `active_flag = 1/0` → real boolean predicates (`= true` / `= false`);
- **the no-op `OR length(error_log) >= 0` branch is DELETED** from
  `ck_calcrun_failed_has_errorlog`, leaving the real rule: FAILED ⇒ `error_log IS NOT NULL`,
  non-FAILED ⇒ `error_log IS NULL`;
- money kept as `numeric(18,6)`; UUID PKs handled per the convention below.

**Enums.** The as-built SQL is auto-generated and does **not** emit the `CREATE TYPE ... AS ENUM`
value lists, so the full value sets are not knowable from the source. Rather than invent values,
enum-typed columns are rendered as governed `text` and **every as-built CHECK that constrains an
enum's membership is preserved** (e.g. `landed_cost_mode IN (...)`, the capacity scope/field-match
CHECK, the calc-run status/contract CHECKs). This is the `CHECK ... IN` option in
`PLAN.md` §2 M0 — faithful, not lossy. Promoting specific columns to native `CREATE TYPE` enums
is a clean follow-up once a confirmed value list lands.

**PK convention.** Net-new spine tables (`ref.client`, `ref.commodity`, `audit.event_log`) use
native `uuid` PKs; the ~60 adopted as-built tables retain their text-UUID (`varchar(36)`) PKs so
the 46 composite-identity FKs re-express byte-for-byte.

**Reconciled toward live code** (live code wins, ADR-0001):

- `ref.client` / `ref.commodity` columns are kept **exactly** as `app/domain/ref/models.py` maps
  them (`uuid id`, `client_id`, `client_code`/`client_name`/`is_active`, `commodity_code`/
  `commodity_name`/`active_flag`). Because the canonical `ref.commodity` is uuid-keyed (no text
  `commodity_id`), the **4 single-column as-built FKs** that pointed at
  `commodity_master_db(commodity_id)` (from `item`, `subcommodity`, `cycle`, `item_alias`) are
  dropped — but those tables keep their own `commodity_id` columns and **all composite identity
  pairs/FKs among themselves** (item↔subcommodity↔cycle), so the enterprise rigor is intact.
- `audit.event_log` columns are kept **exactly** as `app/core/audit/writer.py` INSERTs
  (`id, client_id, occurred_at, actor, source, event_type, entity_type, entity_id, cycle_id,
  before_state_hash, after_state_hash, prev_event_hash, event_hash, seq`). The as-built
  `audit_event` (which had `event_id`/`event_ts`/`success_status` and no per-tenant `seq` chain)
  is reconciled toward the writer — verified by replaying the writer's exact INSERT.

**Tenancy (M10, not M0).** ADR-0004's broad `client_id` weave across all 63 tables is migration
**M10** (E-03). M0 keeps `client_id` only where it already exists: `ref.client` + `ref.commodity`.

**Verified on real PostgreSQL** (PG16 local): `schema.sql` applies twice idempotently (zero
errors), and the backend migration roundtrip `alembic upgrade head → downgrade base → upgrade head`
is clean (downgrade drops the eight schemas `CASCADE`). Pure + integration test suites pass (10/10).
A two-edge cross-schema reference cycle (`ref↔cyc↔norm`) is resolved by deferring two FKs
(`fk_quarantine_cycle`, `fk_volume_normalization_run`) to a guarded `ALTER TABLE` block at the end
of the file — still fully idempotent.

The roundtrip + `alembic check` + constraint-count floor (≥46 composite FKs) gate this fidelity in
CI (R-PD2).

## Files

| File | Purpose |
|---|---|
| `schema.sql` | clean PG DDL: 8 schemas + all 63 re-expressed as-built tables (full M0 baseline) |
| `NAMING_MAP.md` | as-built-flat → target schema-qualified crosswalk + the canonicalization rule |
| `README.md` | this provenance note |

> The full physical→canonical table lands as `CROSSWALK.md` at M0 (Platform & Data `PLAN.md` §3 step 5);
> `NAMING_MAP.md` here is the key-mappings seed of that crosswalk.

## Why a `.sql` baseline, not autogenerated models

The as-built's rigor (composite identity FKs, the sealed calc-run spine, landed-cost shapes) is the
asset we keep. Re-expressing it as reviewed SQL — then having `0001` execute that file — makes the
clean-room boundary auditable: the baseline is data we re-authored, not code we inherited.
