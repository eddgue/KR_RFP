---
doc: AS-BUILT AUDIT — SLICE B3 — domain/ref · domain/cyc · domain/bid
id: ASBUILT-B3
status: DONE (read-only audit; no code changed)
scope_globs:
  - backend/app/domain/ref/**
  - backend/app/domain/cyc/**
  - backend/app/domain/bid/**
contract: /CLAUDE.md (ABSOLUTE REQUIREMENTS honored — nothing skipped/assumed; detailed WHY; every
  file incl. empty; every column/CHECK/UNIQUE/FK; every transformation with formula + file:line;
  every branch/edge; decisions tied to the file:line that enforces them).
standard: /AS_BUILT/AUDIT_STANDARD.md (Layer-1 data + Layer-2 code/process/decisions).
census_rows: FILE_CENSUS.md rows 106–113 (bid), 114–115 (cyc), 124–128 (ref).
generated: 2026-06-22
---

# SLICE B3 — `domain/ref`, `domain/cyc`, `domain/bid`

## 0. Slice inventory & census cross-check

`find` over the three scope trees yields **15 owned `.py` files** + **13 vendored/generated
`__pycache__/*.pyc`** byte-caches. The `.pyc` files are CPython 3.12 bytecode caches — generated, not
ours — so per the exhaustiveness rule §6 they are **counted in bulk** here (13 files), never per-file
audited; they are not in `FILE_CENSUS.md` (the census tracks owned source). They contain no authored
content; deleting them changes nothing but a cold-import microsecond.

| # | Path | Ext | Empty? | Census row | size (B) (census) |
|---|------|-----|--------|-----------|-------------------|
| 1 | backend/app/domain/ref/__init__.py | py | no (12 lines) | 124 | 546 |
| 2 | backend/app/domain/ref/models.py | py | no (106 lines) | 125 | 4550 |
| 3 | backend/app/domain/ref/repository.py | py | no (65 lines) | 126 | 2214 |
| 4 | backend/app/domain/ref/schemas.py | py | no (44 lines) | 127 | 1169 |
| 5 | backend/app/domain/ref/service.py | py | no (66 lines) | 128 | 2552 |
| 6 | backend/app/domain/cyc/__init__.py | py | no (1 line, docstring only) | 114 | 72 |
| 7 | backend/app/domain/cyc/models.py | py | no (281 lines) | 115 | 12619 |
| 8 | backend/app/domain/bid/__init__.py | py | no (1 line, docstring only) | 106 | 70 |
| 9 | backend/app/domain/bid/models.py | py | no (135 lines) | 109 | 7797 |
| 10 | backend/app/domain/bid/bid_ingester.py | py | no (751 lines) | 107 | 30396 |
| 11 | backend/app/domain/bid/legacy_adapter.py | py | no (138 lines) | 108 | 5714 |
| 12 | backend/app/domain/bid/period_fanout.py | py | no (79 lines) | 110 | 3203 |
| 13 | backend/app/domain/bid/template_generator.py | py | no (314 lines) | 111 | 13204 |
| 14 | backend/app/domain/bid/template_preset.py | py | no (107 lines) | 112 | 4403 |
| 15 | backend/app/domain/bid/template_schema.py | py | no (289 lines) | 113 | 12591 |

**Census reconciliation:** all 15 owned files appear in `FILE_CENSUS.md` (rows above), all marked
owned `y`. **No empty files** in this slice (the slice has zero of the project's 18 empties). The two
"stub" `__init__.py` (cyc, bid) are NOT empty — each carries a one-line docstring; they are
present-but-thin **package markers** (see per-file WHY). The census byte-sizes match the on-disk
sizes within the census snapshot tolerance (census captured `bid_ingester.py` at 30396 — identical;
`models.py` ref at 4550 — identical). mtimes on disk (e.g. bid models 2026-06-21 18:27) are newer than
some census mtimes because the census snapshot predates the last edit pass; the census `created`
columns match. **No file in scope is missing from the census; no census row in scope lacks a file.**

**Scope-word note (prompt said "models, read, service, repository, schemas, __init__"):** there is
**no `read.py`** in any of the three trees (verified by `find`). `ref` is the only tree with the full
service/repository/schemas trio; `cyc` is models-only; `bid` is models + a set of intake/template
modules (ingester, generator, schema, preset, fanout, legacy adapter) rather than a service/repo
pair. This is **by design** (PLAN §2): `ref` is the *reference implementation* of the layered pattern
(models→schemas→repository→service→audit), and the other layers ship the pattern that fits their job.
Flagged here so the absence of `read.py`/`service.py`/`repository.py` in cyc & bid is an explained
architectural choice, **not a missing file**.

---

# PART 1 — `domain/ref` (the reference-implementation layer)

`ref` is the canonical, fully-wired demonstration of the eight-layer pattern: an ORM model
(`models.py`) → a Pydantic boundary (`schemas.py`) → a tenant-scoped repository (`repository.py`) →
a service that stamps tenant + emits audit (`service.py`), all re-exported from `__init__.py`. WHY it
exists as a *reference*: PLAN §2 ships `client` (the tenant keystone) and `commodity` (a tenant-scoped
dimension) **fully** so the add+flush+audit + tenant-scoping pattern is concrete and testable before
the other seven layers replicate it. Per CLAUDE.md D19 this is NOT a stub: it is the full capability
for these two tables, wired to the real DB columns and the real audit chain.

## 1.1 `ref/__init__.py` — census row 124 (546 B, 12 lines)

- **What:** Package docstring + `from app.domain.ref.models import Client, Commodity` and
  `__all__ = ["Client", "Commodity"]`.
- **Detailed WHY:** Makes `ref` an importable package and gives a single import surface for the two
  shipped entities. The docstring records the **target table list** (PLAN §2: client, commodity,
  subcommodity, dc, supplier(+alias), item(+alias), loading_location, fiscal_calendar, zip_centroid,
  master_data_quarantine) and states that *this phase ships client + commodity as the pattern* — so a
  reader knows the layer's full intended footprint vs. what is wired today. **What breaks without it:**
  `import app.domain.ref` would not re-export the models; callers (`service.py`, tests, the API layer)
  that do `from app.domain.ref import Commodity` would break. Not empty — it is a real package
  manifest, not a placeholder.
- **Dependencies:** `app.domain.ref.models`.

## 1.2 `ref/models.py` — census row 125 (4550 B, 106 lines) — ORM for `ref` schema

**File WHY:** Maps three `ref` tables to SQLAlchemy mapped classes. The module docstring fixes the
**COLUMN-ALIGNMENT contract**: these classes must mirror `db/baseline/schema.sql` column names
verbatim (the migration `0001_baseline` applies `schema.sql` verbatim — confirmed: `0001_baseline.py`
line 54 `CREATE TABLE ... ref.client`, line 64 `ref.commodity`), or the reference round-trip breaks.
**What breaks without it:** no ORM handle to the tenant root or the tenant-scoped dimension; the
repository/service/audit demonstration has nothing to read or write.

**Base wiring:** `RefBase = SchemaBase("ref")` at runtime (line 38); under `TYPE_CHECKING` it aliases
to the static `Base` (lines 33–36) so mypy sees a valid declarative base while the runtime base injects
`__table_args__ = {"schema": "ref"}` (`app/core/db/base.py:53–62`). WHY the dual-path: `SchemaBase`
returns a dynamically-built class (`Any`), which a type checker cannot treat as a statically known
base; the `TYPE_CHECKING` alias is the documented workaround (base.py docstring). Helpers `uuid_pk()`
and `created_at_column()` come from `app/core/db/types.py` (uuid4-defaulted PK; `timestamptz NOT NULL
DEFAULT now()`).

### Model `Client` (`__tablename__ = "client"`, schema `ref`) — the tenancy keystone

| Column | Python type | DB type (schema.sql L74–82) | Null | Default | Constraints |
|--------|-------------|------------------------------|------|---------|-------------|
| `id` | `uuid.UUID` | `uuid` | NOT NULL | `uuid.uuid4` (ORM) / `gen_random_uuid()` (DDL) | **PK** `pk_client` |
| `client_code` | `str` | `varchar(40)` | NOT NULL | — | **UNIQUE** `uq_client_code`; DDL also `ck_client_code_not_empty CHECK(length>0)` |
| `client_name` | `str` | `varchar(160)` | NOT NULL | — | — |
| `is_active` | `bool` | `boolean` | NOT NULL | `True` (ORM) / `true` (DDL) | — |
| `created_at` | `datetime` | `timestamptz` | NOT NULL | `now()` (server) | — |

**WHY each:** `id` UUID surrogate is the FK target every tenant-scoped table hangs off (the tenancy
keystone, models.py docstring + schema.sql COMMENT). `client_code` unique because a tenant is
addressed by a stable human code (the API resolves a tenant by code via `ClientRepository.get_by_code`,
repository.py:62). `client_name` is the display label (160 chars to fit a long org/BU name). `is_active`
governs whether the tenant is live (deactivate without delete — preserves audit history). `created_at`
is server-defaulted UTC for provenance. **DRIFT NOTE (precise):** the ORM does **not** declare the
`ck_client_code_not_empty` CHECK — it exists only in the DDL (schema.sql L81). This is intentional
(the "partial-map" rule — the DB owns the persistence-side CHECK), but it means an ORM-only insert of
`client_code=""` would pass Python and be rejected by Postgres, not by SQLAlchemy. Documented as a
known DB-backstop, not a bug.

### Model `Commodity` (`__tablename__ = "commodity"`, schema `ref`) — tenant-scoped dimension

`__table_args__` (lines 63–66): `UniqueConstraint("client_id","commodity_code",
name="commodity_code_per_client")` + `{"schema":"ref"}`.

| Column | Python type | DB type (schema.sql L90–100) | Null | Default | Constraints |
|--------|-------------|-------------------------------|------|---------|-------------|
| `id` | `uuid.UUID` | `uuid` | NOT NULL | uuid4 / `gen_random_uuid()` | **PK** `pk_commodity` |
| `client_id` | `uuid.UUID | None` | `uuid` | **NULLABLE** | — | **FK** → `ref.client.id` (`fk_commodity_client_id_client`); `index=True` (`ix_commodity_client`) |
| `commodity_code` | `str` | `varchar(40)` | NOT NULL | — | part of UNIQUE `uq_commodity_code_per_client`; DDL `ck_commodity_code_not_empty CHECK(length>0)` |
| `commodity_name` | `str` | `varchar(120)` | NOT NULL | — | — |
| `abbreviation` | `str | None` | `varchar(20)` | NULLABLE | — | — |
| `active_flag` | `bool` | `boolean` | NOT NULL | `True` / `true` | — |
| `created_at` | `datetime` | `timestamptz` | NOT NULL | `now()` | — |

**WHY `client_id` is NULLABLE (the load-bearing decision):** the model comment (lines 16–17, 69) is
explicit — security/PLAN §1 classes pure global reference (commodity) as NOT tenant-scoped in the
*final* model, but the baseline carries `client_id` **nullable for now**; it becomes `NOT NULL` + RLS
when Security ratifies (decision tag **R-PD5** / Platform&Data M10). The column is kept here **on
purpose** to make tenant-scoping concrete + testable in the reference package this phase. The DDL
matches: `client_id uuid REFERENCES ref.client(id)` with no NOT NULL (schema.sql L92). **What this
means for behavior:** today a commodity *can* be written with `client_id=NULL` at the DB level, but the
**service always stamps it** (service.py:46) so the live write path never produces a NULL — the
nullability is a migration-window allowance, not a live gap. The per-tenant UNIQUE
`(client_id, commodity_code)` (DDL L100, ORM L64) replaces the as-built global UNIQUE so the same
commodity code can exist once per tenant (schema.sql comment L88–89). `index=True` on `client_id`
because every scoped read filters on it (repository.py:32).

### Model `FiscalPeriod` (`__tablename__ = "fiscal_period"`, schema `ref`) — governed period dimension

`__table_args__` (lines 94–97): `UniqueConstraint("fiscal_year","period",
name="fiscal_period_year_period")` + `{"schema":"ref"}`.

| Column | Python type | DB type (mig 0014 L76–81) | Null | Constraints |
|--------|-------------|---------------------------|------|-------------|
| `id` | `uuid.UUID` | `uuid` (PG_UUID) | NOT NULL | **PK** `pk_fiscal_period` |
| `fiscal_year` | `int` | `Integer` | NOT NULL | UNIQUE `fiscal_period_year_period` (with `period`) |
| `period` | `int` | `Integer` | NOT NULL | UNIQUE (with `fiscal_year`) |
| `quarter` | `int` | `Integer` | NOT NULL | — |
| `begin_date` | `date` | `Date` | NOT NULL | — |
| `end_date` | `date` | `Date` | NOT NULL | — |
| `weeks` | `int` | `Integer` | NOT NULL | — |

**WHY:** This is the governed period grain other tables FK to (the model docstring, lines 84–91).
It mirrors the authoritative 4-3-3-3 Kroger fiscal calendar shipped as data
(`app/fiscal/data/kroger_fiscal_periods.csv`) and the typed library `app.fiscal.calendar.FiscalPeriod`.
A fiscal year carries **exactly 13** four-week periods grouped 4-3-3-3 into four quarters; **period 13
of a 53-week year carries a 5th week** (`weeks=5`) — which is exactly WHY `weeks` is a stored column
and not a constant. The row set is **seeded by migration 0014** (`op.bulk_insert`, 0014 L89), all 273
rows (FY16..FY36, contiguous; 0014 docstring L8–13). `UNIQUE(fiscal_year, period)` is the natural key.
**What breaks without it:** `bid.bid_line.fiscal_period_id` (migration 0015) has nothing governed to
reference; the flat-13 fan-out (`period_fanout.py`) loses its calendar backbone. **Cross-check
verified:** the ORM column set (fiscal_year, period, quarter, begin_date, end_date, weeks) matches
migration 0014 `op.create_table` columns L76–81 exactly, and the UNIQUE name matches (0014 L83).

**LAYER-1 contribution (ref):** ORM↔table map is `Client→ref.client`, `Commodity→ref.commodity`,
`FiscalPeriod→ref.fiscal_period`. **No value transformation** happens in this file — it is pure schema
declaration. The only "transformation" of note is the **tenant stamping** that happens one layer up
(service.py): request body (no client_id) → row (client_id = context tenant). Mapped to file:line in
§1.5.

## 1.3 `ref/repository.py` — census row 126 (2214 B, 65 lines)

**File WHY:** The application-layer half of defence-in-depth tenant isolation (docstring + security/
PLAN §1): every read of a tenant-scoped entity injects `WHERE client_id = :ctx_tenant`; there is **no
un-scoped read path** to governed data, and the tenant comes from request context, never the caller.
Postgres RLS is the DB-layer backstop (Platform&Data M10). **What breaks without it:** services would
issue raw cross-tenant queries; the tenant-isolation guarantee would live nowhere.

### class `CommodityRepository(session, tenant_id)` — tenant-scoped queries over `ref.commodity`
- `__init__(self, session: Session, tenant_id: uuid.UUID)` — stores session + the **bound tenant**.
  Side-effects: none. WHY the tenant is a constructor arg, not a per-call arg: it cannot be forgotten
  or overridden per call — every method is scoped by construction.
- `list() -> Sequence[Commodity]` — `select(Commodity).where(client_id == tenant_id).order_by(
  commodity_code)`. In: none. Out: scoped, code-ordered list. Side-effects: read. Errors: none
  (empty list if none). **Edge:** a tenant with zero commodities → `[]` (not an error).
- `get_by_code(code) -> Commodity | None` — `where(client_id == tenant_id, commodity_code == code)`,
  `scalar_one_or_none()`. **Edges:** miss → `None`; **a duplicate (code) across tenants cannot return
  the other tenant's row** because the `client_id` predicate is always present — the isolation proof.
  `scalar_one_or_none` would raise `MultipleResultsFound` if two same-code rows existed within the
  tenant, but the `uq_commodity_code_per_client` UNIQUE makes that impossible — so in practice it is
  one-or-none.
- `add(commodity) -> None` — `session.add(commodity); session.flush()`. **This is the add+flush, NEVER
  commit pattern (PLAN §7).** Side-effect: stages the row and flushes so `commodity.id` is populated
  (server default round-trips) — but does **not** commit; the unit of work owns the transaction. WHY:
  the change and its audit event must land in the *same* transaction (see §1.5).

### class `ClientRepository(session)` — the tenant registry (NOT itself tenant-scoped)
- `__init__(self, session)` — no tenant bound. WHY: `ref.client` is the registry of tenants; scoping
  it *by* a tenant would be circular. This is the deliberate exception to "every read is scoped".
- `get(tenant_id) -> Client | None` — `session.get(Client, tenant_id)` (PK lookup).
- `get_by_code(code) -> Client | None` — `select(Client).where(client_code == code)`,
  `scalar_one_or_none()`. **Edge:** miss → `None`. WHY this exists: an inbound request authenticates a
  tenant by its stable `client_code`; this resolves it to the `id` used everywhere else.

**Dependencies:** `app.domain.ref.models.{Client,Commodity}`, SQLAlchemy `select`, `Session`.

## 1.4 `ref/schemas.py` — census row 127 (1169 B, 44 lines)

**File WHY:** The Pydantic request/response boundary. The load-bearing rule (docstring + PLAN §5):
**tenant is ambient (from context), so it NEVER appears on a request body** — the create schemas carry
**no `client_id`**; the service stamps it. This is a security property expressed as a schema shape: a
caller *cannot* assert a tenant. **What breaks without it:** the API could accept a client-supplied
`client_id` and write cross-tenant data.

- `CommodityCreate(BaseModel)` — fields: `commodity_code: str (max_length=40)`,
  `commodity_name: str (max_length=120)`, `abbreviation: str|None (default=None, max_length=20)`.
  No `client_id`. The `max_length` values **mirror the DB column widths** (40/120/20 — schema.sql
  L92–96) so Pydantic rejects an over-length value before it reaches Postgres (validation_error, not
  a DB error). **Edge:** `abbreviation` omitted → `None` (nullable column).
- `CommodityRead(BaseModel)` — `model_config = from_attributes=True` (ORM→schema). Fields: `id: UUID`,
  `client_id: UUID|None`, `commodity_code`, `commodity_name`, `active_flag: bool`. WHY `client_id` is
  on the *read* but not the *create*: a read surfaces which tenant owns the row (for admin views); a
  create must not let the caller choose it. `active_flag` (DB name) is surfaced verbatim — **no rename**
  in the read model (the Read mirrors the column).
- `ClientRead(BaseModel)` — `from_attributes=True`; `id`, `client_code`, `client_name`, `is_active`.
  For admin surfaces (the tenant registry). **No `ClientCreate`** — tenants are provisioned out of band,
  not via a client-facing create (an explained absence, not a gap).

**Dependencies:** pydantic `BaseModel/ConfigDict/Field`, `uuid`.

## 1.5 `ref/service.py` — census row 128 (2552 B, 66 lines) — THE add+flush+audit reference

**File WHY:** The single concrete demonstration of the governed-mutation pattern the other seven layers
follow (docstring): stamp `client_id` from context (never the body), emit a domain event for the audit
writer, stage the row; the unit of work owns the commit so the change and its audit event land in the
**same transaction** (security/PLAN §3). **What breaks without it:** there is no worked example of
"mutation + audit in one txn, tenant from context" — the pattern would be unproven.

### class `CommodityService(session, tenant: TenantContext, principal: Principal)`
- `__init__` (lines 25–30): stores session, tenant, principal; builds
  `CommodityRepository(session, tenant.tenant_id)` and `AuditWriter(session)`. Side-effects: none.
  WHY it takes `TenantContext` AND `Principal`: the tenant scopes the data; the principal supplies the
  audit `actor`/`source` (provenance of *who* mutated).
- `create(data: CommodityCreate) -> Commodity` (lines 32–65). **Inputs:** a validated
  `CommodityCreate`. **Output:** the staged `Commodity` (with `.id` populated by the flush).
  **Side-effects:** stages one `ref.commodity` row + one `audit.event_log` row, both un-committed.
  **The full branch/edge trace:**
  1. **Duplicate-code guard (lines 38–43):** `if self._repo.get_by_code(data.commodity_code) is not
     None:` → `raise AppError(code=ErrorCode.CONFLICT, message="A commodity with this code already
     exists for the tenant.", status_code=409)`. This is the **reuse-by-natural-key / conflict** edge:
     the natural key is `(tenant, commodity_code)`; a second create with the same code is a **409
     CONFLICT**, surfaced as an error envelope (taxonomy.py `ErrorCode.CONFLICT`, status 409), never a
     silent overwrite. This pre-empts the DB `uq_commodity_code_per_client` UNIQUE so the caller gets a
     clean typed error instead of an `IntegrityError`. WHY check-then-insert (not rely on the UNIQUE):
     a friendly typed envelope + same-txn semantics; the UNIQUE remains the DB backstop against a race.
  2. **Construct (lines 45–50):** `Commodity(client_id=self._tenant.tenant_id, commodity_code=...,
     commodity_name=..., abbreviation=...)`. **THE TENANT STAMP** — `client_id` is taken from the
     context tenant (`tenant.tenant_id`), **never from `data`** (which has no such field). This is the
     transformation that makes the nullable `client_id` column always non-null on the live path.
  3. **add + flush (line 51):** `self._repo.add(commodity)` → `session.add(); session.flush()`;
     comment "add + flush -> commodity.id populated". No commit.
  4. **Audit append (lines 53–64):** `self._audit.append(DomainEvent(event_type=EventType.CREATED,
     client_id=tenant.tenant_id, entity_type="ref.commodity", entity_id=commodity.id,
     actor=principal.actor, source=principal.source, before=None, after={"code":...,"name":...}))`.
     `before=None` because it is a create. `after` carries the canonical state the writer hashes. The
     writer (`AuditWriter.append`, writer.py:106) does **NOT commit** (writer.py:108–111) — it
     row-locks the tenant's chain head (`SELECT ... FOR UPDATE`, writer.py:96–101), computes
     `seq=last_seq+1`, hashes `before`/`after`, computes the chained `event_hash`, and `INSERT`s the
     `audit.event_log` row in the caller's txn. So **commodity row + audit row are atomic** — the
     decision (security/PLAN §3) is enforced at writer.py:108–160 + service.py:51–64.
  5. **Return (line 65):** the staged `Commodity`. The HTTP/unit-of-work layer commits; on any later
     failure the whole txn (row + audit) rolls back together.
  **Errors raised:** `AppError(CONFLICT, 409)` on duplicate; nothing else explicitly (a Pydantic
  validation_error happens earlier, at the schema; a DB constraint trip surfaces as the txn rolls back).

**Decision enforcement (ref):**
- **PLAN §7 (add+flush, never commit):** repository.py:49–50, service.py:51, writer.py:108–111. ✔
- **security/PLAN §1 (tenant from context, every read scoped):** repository.py:32/40, service.py:46. ✔
- **security/PLAN §3 (mutation + audit same txn, hash chain):** service.py:53–64 + writer.py:96–160. ✔
- **security/PLAN §5 (tenant never on request body):** schemas.py CommodityCreate (no client_id). ✔
- **R-PD5 (client_id nullable now, NOT NULL+RLS later):** models.py:69–75 + schema.sql L92. ✔ (drift
  is *intended* and documented, not an unplanned gap.)

**Dependencies:** `app.core.audit.events.{DomainEvent,EventType}`, `app.core.audit.writer.AuditWriter`,
`app.core.errors.taxonomy.{AppError,ErrorCode}`, `app.core.security.principal.Principal`,
`app.core.security.tenant.TenantContext`, `app.domain.ref.models.Commodity`,
`app.domain.ref.repository.CommodityRepository`, `app.domain.ref.schemas.CommodityCreate`.

---

# PART 2 — `domain/cyc` (the cycle keystone + satellites)

## 2.1 `cyc/__init__.py` — census row 114 (72 B, 1 line)

- **What:** A single line: `"""Cycle layer (`cyc` schema) — present-but-empty stub (PLAN §2)."""`
- **Detailed WHY this is NOT a D19 violation:** the *package* `__init__` is intentionally thin — it
  carries no re-exports because, unlike `ref`, the cyc layer's models are imported directly from
  `app.domain.cyc.models` by the engine runner and tests (there is no service/repo trio to surface).
  The word "stub" here labels the **package init**, not the layer: `models.py` (281 lines, 16 mapped
  classes) is fully built. **What breaks without it:** `app.domain.cyc` would not be a package; the
  `from app.domain.cyc.models import ...` imports the runner relies on would fail. So it is a required
  package marker, explained — not an empty placeholder screen.
- **Census note:** row 114 marks it owned `y`, 72 bytes — consistent.

## 2.2 `cyc/models.py` — census row 115 (12619 B, 281 lines) — ORM for the `cyc` schema

**File WHY:** Maps the `cyc.*` tables the application reads/writes outside raw SQL. Two groups:
**(a)** the additive **kickoff satellites** shipped by migrations 0002 (kickoff) + 0003 (safety) —
the net-new tables the ORM *owns*; **(b)** a **partial map** of the baseline cyc spine
(`cycle_round`, `cycle_timeframe`, `cycle_lot`, `cycle_item_scope`, `cycle_lot_item`,
`cycle_projected_volume`) — only the columns the **engine runner** reads by key, the rest managed by
SQL (the same partial-map rule the bid/ref models follow; docstring lines 156–162). **Grain anchor:**
`cyc.cycle.cycle_id` is `varchar(36)` in the M0 baseline (schema.sql L332), so every satellite FKs that
type and these classes use `cycle_id: Mapped[str]`. **What breaks without it:** the engine has no typed
handle to the round/timeframe/lot/demand grain it aggregates; the kickoff satellites have no ORM.

**Base wiring:** `CycBase = SchemaBase("cyc")` (line 32), same `TYPE_CHECKING`→`Base` alias as ref.
Imports `Numeric, Date, DateTime, Text, func` etc. — note this file uses **raw `Numeric(...)`** (not
the `Money` helper) because cyc carries case-counts (18,3) and term values (18,2), distinct precisions.

### Group (a) — Kickoff satellites (migrations 0002 + 0003)

**`CycleObjective`** (`cycle_objective`) — mirrors 0002 (L73–82).
- PK = composite `(cycle_id varchar(36) FK→cyc.cycle.cycle_id, objective_code text)`.
- `is_primary boolean NOT NULL default False`; `objective_note text NULL`.
- **WHY:** a cycle has multiple objectives, exactly one primary. **The "exactly one primary" rule is
  enforced in the DB, not the ORM:** 0002 L84 `CREATE UNIQUE INDEX uq_cycle_objective_one_primary ...`
  (a partial unique index on `is_primary=true`). The ORM models the columns but **not** that partial
  index — DRIFT noted: the ORM cannot, by itself, prevent two primaries; the DB does. Also DDL-only:
  `ck_cycle_objective_code CHECK(objective_code IN (...))` (0002 L79) — the ORM `objective_code` is a
  free `Text` (no enum), DB-validated.

**`CyclePricing`** (`cycle_pricing`) — mirrors 0002 (L92–109). PK = `cycle_id` alone (**one row per
cycle** — the ONE pricing render contract, **D9/D12**, docstring line 49).
- `pricing_basis text NOT NULL`, `duration_cadence text NOT NULL`, `cadence_n int NULL`,
  `baseline_then_negotiate boolean NOT NULL default False`, `volume_split_rule text NULL`,
  `routing_basis text NULL`, `sourcing_region_per_period text NULL`.
- **WHY one-per-cycle:** D9/D12 — pricing is a single render contract per cycle, not per-line; PK on
  `cycle_id` enforces it. **DDL-only CHECKs the ORM does not carry:** `ck_cycle_pricing_basis
  (pricing_basis IN FIXED/INDEX/HYBRID)` (0002 L102), `ck_cycle_pricing_cadence` (L103),
  `ck_cycle_pricing_routing` (L106), `ck_cycle_pricing_cadence_n_positive (cadence_n IS NULL OR >0)`
  (L108). The ORM leaves these as free `Text`/`Integer` — Postgres is the validator. **Decision D9/D12
  enforced at:** PK `cycle_id` (models.py:53; 0002 L101).

**`CycleScopeItem`** (`cycle_scope_item`) — mirrors 0002 (L120–128). PK = `(cycle_id, subcommodity_code
text, gtin_code text default "")`.
- `participates boolean NOT NULL default False` — **D9 product-level participation** (docstring L66).
- `lot_id varchar(36) NULL` — "unconstrained until persistent norm.lot lands (M2/G8)" (comment L76).
- `projected_volume Numeric(18,3) NULL` — case-count precision.
- **WHY `gtin_code` defaults to "":** it is part of the PK; an empty-string default lets a subcommodity-
  level (no-GTIN) participation row exist with a stable, non-null PK component (a NULL PK component is
  illegal). **Value note:** `projected_volume` is **18,3** (cases, 3 decimals) — the standard demand
  precision used everywhere in cyc/bid.

**`CyclePbaTerm`** (`cycle_pba_term`) — mirrors 0002 (L136–142). PK `(cycle_id, metric text)`.
`threshold text NOT NULL`, `enforcement text NULL`. **WHY:** PBA (performance-based-agreement)
governance terms, multi per cycle keyed by `metric`. No CHECK in DDL.

**`CycleCommercialTerm`** (`cycle_commercial_term`) — mirrors 0002 (L148–158). PK `(cycle_id,
term_type text)`. `target_value text NULL`, `benefit_value Numeric(18,2) NULL`, `treatment text NULL`,
`note text NULL`. **WHY `benefit_value` is 18,2** (not 18,3/18,6): it is a money-ish benefit *amount*,
2-decimal currency precision — distinct from case-counts (18,3) and per-case pricing (18,6).
**DDL-only CHECK:** `ck_cycle_commercial_term_type CHECK(term_type IN (...))` (0002 L156) — ORM free.

**`CycleRfiQuestion`** (`cycle_rfi_question`) — mirrors 0002 (L164–173). PK `(cycle_id, question_code
text)`. `question_text text NOT NULL`, `answer_type text NULL`, `seq int NOT NULL`. **WHY `seq`
NOT NULL:** RFI questions render in a stable order; the order is data, not row insertion order.
**DDL-only CHECK:** `ck_cycle_rfi_answer_type` (0002 L171).

**`CycleTimelineEvent`** (`cycle_timeline_event`) — mirrors 0002 (L179–188). PK `(cycle_id, event_seq
int)`. `event_name text NOT NULL`, `event_date date NULL`, `is_leadership_gate boolean NOT NULL default
False`, `round_no int NULL`, `bcg_support_needed boolean NOT NULL default False`. **WHY:** the
"Next Steps" rail (**E-16**, docstring L124). `is_leadership_gate` flags a leadership decision gate on
the timeline; `round_no` ties an event to a round; `bcg_support_needed` flags advisory support.

**`CycleNarrative`** (`cycle_narrative`) — mirrors 0002 (L194–207). PK `(cycle_id, narrative_type text,
version int default 1)`. `body_richtext text NOT NULL`, `authored_by varchar(120) NULL`,
`authored_at timestamptz NOT NULL server_default now()`. **WHY versioned + rich text "never
field-ified":** narrative blocks (background, strategy, etc.) are kept as versioned rich-text rather
than parsed into fields — the version in the PK lets a block be re-authored without losing history.
**DDL-only CHECKs:** `ck_cycle_narrative_type CHECK(narrative_type IN BACKGROUND/DATA_DIVE/.../
APPENDIX_LINK)` (0002 L203) and `ck_cycle_narrative_version_positive (version>0)` (0002 L206) — ORM
free `Text`/`Integer`.

**`CycleSafety`** (`cycle_safety`) — mirrors 0003 (L42–68). PK `(cycle_id FK→cyc.cycle, safety_type
text)`. **A per-RFP pricing-safety CONTRACT term (D13 / ADR-0014; docstring L257) — TERMS ONLY, the
engine does NOT consume these** (docstring L260). Columns grouped by safety type:
| Column | Type (0003) | Null | For safety type |
|--------|-------------|------|-----------------|
| `cap` | `Numeric(18,6)` | NULL | COLLAR (upside protection on a hike) |
| `floor` | `Numeric(18,6)` | NULL | COLLAR (downside protection) |
| `lookback_weeks` | `Integer` | NULL | ROLLING_MIDPOINT |
| `reset_cadence_weeks` | `Integer` | NULL | ROLLING_MIDPOINT |
| `band` | `Numeric(18,6)` | NULL | TOLERANCE_BAND |
| `min_duration_weeks` | `Integer` | NULL | TOLERANCE_BAND |
| `reprice_window_weeks` | `Integer` | NULL | TOLERANCE_BAND |
| `reverts_to_contract` | `Boolean` | NOT NULL default True | DISASTER / INVERSE_DISASTER |
| `notes` | `Text` | NULL | all |
- **WHY 18,6** on cap/floor/band: these are per-case price collars/bands — same 6-decimal precision as
  bid pricing, so a collar compares apples-to-apples with a constructed price. **WHY engine ignores
  them:** D13/ADR-0014 — safety is a *contract* term (what happens to price after award under a
  disaster/collar), not a scoring input; the engine scores on bids, the safety terms are rendered in
  the deliverable. **DDL-only CHECKs (ORM does not carry):** `ck_cycle_safety_type CHECK(safety_type
  IN (5 ratified values))` (0003 L59), `ck_cycle_safety_weeks_positive` (L61),
  `ck_cycle_safety_collar_ordered` (cap≥floor, L66). **Decision D13 enforced at:** the table's
  existence + `safety_type` CHECK (0003 L59); the ORM is the read/write handle (models.py:256–280).

### Group (b) — Baseline cyc spine (PARTIAL map — only engine-read columns)

**`CycleRound`** (`cycle_round`) — mirrors baseline (schema.sql L373–390). Mapped: `round_id
varchar(36) PK`, `cycle_id varchar(36) NOT NULL`, `round_number int NOT NULL`, `status varchar(40)
NOT NULL`, `round_status text NULL`, `is_final boolean NOT NULL default False`. **NOT mapped (managed
by SQL):** `invite_due_at`, `bid_due_at`, `meeting_due_at` (timestamps) — the runner doesn't read them.
**WHY partial:** the engine runner needs only the round it seals the analysis for (docstring L156–162);
mapping more would invite ORM/SQL drift. **DDL-only:** UNIQUE `uq_round_number_per_cycle`,
`uq_round_cycle_pair`, CHECK `ck_round_number_positive(round_number>0)` (schema.sql L383–386).

**`CycleTimeframe`** (`cycle_timeframe`) — mirrors baseline (schema.sql L355–371). Mapped: `tf_id
varchar(36) PK`, `cycle_id varchar(36) NOT NULL`, `tf_code varchar(20) NOT NULL`, `tf_name varchar(120)
NOT NULL`, `start_date date NOT NULL`, `end_date date NOT NULL`, `week_count int NOT NULL`, `rationale
text NULL`. **WHY:** maps the runner's `tf_id ↔ tf_code` period token (docstring L176). **DDL-only:**
UNIQUE `uq_tf_code_per_cycle`/`uq_tf_cycle_pair`, CHECK `ck_tf_week_count_positive(week_count>0)`,
`ck_tf_date_range_positive(end_date>start_date)` (schema.sql L365–368).

**`CycleLot`** (`cycle_lot`) — mirrors baseline (schema.sql L415–426). `lot_id varchar(36) PK`,
`cycle_id NOT NULL`, `lot_code varchar(40) NOT NULL`, `lot_name varchar(120) NOT NULL`, `rationale text
NULL`, `active_flag boolean NOT NULL default True`. **DDL-only:** UNIQUE `uq_lot_code_per_cycle`/
`uq_lot_cycle_pair`.

**`CycleItemScope`** (`cycle_item_scope`) — mirrors baseline (schema.sql L392–413). **PK `(cycle_id,
item_id)`** (composite — docstring L206). `commodity_id varchar(36) NOT NULL`, `subcommodity_id
varchar(36) NULL`, `inclusion_status text NOT NULL`, `rationale text NULL`, `added_at DateTime NOT
NULL`, `added_by varchar(120) NOT NULL`. **WHY composite PK:** an item is in/out of scope **per cycle**;
the pair is the identity. **NOTE — `added_at` is `DateTime` (no tz) in the ORM** (models.py:216) while
the DDL is `timestamp` (no tz) (schema.sql L399) — they agree (both naive); contrast the satellites'
`timestamptz`. The baseline has 6 composite-identity FKs on this table (scope_cycle_commodity,
scope_cycle_subcom, scope_item_commodity, scope_item_subcom, + two single — schema.sql L401–411); the
ORM models **none** of them (partial map) — DB-enforced.

**`CycleLotItem`** (`cycle_lot_item`) — mirrors baseline (schema.sql L429–444). `lot_item_id varchar(36)
PK`, `cycle_id NOT NULL`, `lot_id NOT NULL`, `item_id NOT NULL`, `required_flag boolean NOT NULL default
True`, `sort_order int NOT NULL default 0`. **WHY:** the lot↔item link, **one lot per item** (DDL UNIQUE
`uq_one_lot_per_item_per_cycle (cycle_id,item_id)`, schema.sql L439); the runner **aggregates
item-grain demand up to the engine's lot-grain cell** via this link (docstring L222–224). **This is a
key data-flow hop** — see Layer-1 §4.

**`CycleProjectedVolume`** (`cycle_projected_volume`) — mirrors baseline (schema.sql L446–470). `volume_id
varchar(36) PK`, `cycle_id NOT NULL`, `dc_id NOT NULL`, `item_id NOT NULL`, `tf_id NOT NULL`,
`volume_input_method text NOT NULL`, `projected_weekly_cases Numeric(18,3) NULL`,
`projected_period_cases Numeric(18,3) NOT NULL`, `growth_override_pct Numeric(9,6) NULL`,
`normalization_run_id varchar(36) NULL`. **WHY the precisions (load-bearing):**
- `projected_weekly_cases` / `projected_period_cases` = **Numeric(18,3)** — case counts at 3 decimals.
- `growth_override_pct` = **Numeric(9,6)** — a *fraction/percentage* override at 6 decimals (e.g.
  0.025000 = 2.5%); the wider scale (6) but narrower precision (9) marks it as a ratio, not a count.
- **The runner aggregates this DC×item×TF demand to the engine's (dc, lot, tf) cell grain** (docstring
  L236–238) — another key flow hop (Layer-1 §4). **DDL-only:** UNIQUE `uq_volume_cell
  (cycle,dc,item,tf)`, CHECK `ck_volume_method_consistency` (WEEKLY_X_WEEKS⇒weekly NOT NULL;
  DIRECT_PERIOD_CASES⇒weekly NULL, schema.sql L463), CHECK `ck_volume_period_nonneg(period≥0)` (L465).
  The ORM models none of these — DB-enforced. **NOTE:** the FK `normalization_run_id →
  norm.normalization_run` is deferred in the DDL (cross-schema cycle break, schema.sql L468–470); the
  ORM column is a plain nullable `varchar(36)` (a logical reference), consistent with that deferral.

**LAYER-2 process note (cyc):** this file declares no functions — it is pure ORM. All "process" for cyc
lives in the engine runner (out of slice) which *reads* these classes. The decisions visible here are
**D9** (participation/one-pricing — CycleScopeItem.participates, CyclePricing one-per-cycle), **D12**
(period-grain pricing — CyclePricing per cycle, period carried via tf), **D13/ADR-0014** (CycleSafety),
**E-16** (CycleTimelineEvent). Each is enforced by the **table shape (PK/CHECK) in the migration**, and
the ORM is the typed read/write handle — the enforcement file:line is the migration, cited above.

---

# PART 3 — `domain/bid` (the intake / template round-trip module)

The bid layer is the **round-trip core (D20)**: ONE owned template schema (`template_schema.py`)
written by the generator (`template_generator.py`) and read back by the ingester (`bid_ingester.py`),
so the two ends cannot drift ("the engine ingests the files it itself creates"). Plus: `template_preset`
(compose-from-superset), `period_fanout` (flat-13 fan-out), `legacy_adapter` (migration bridge),
`models.py` (the write target). This is the heaviest slice; every value transformation is mapped below.

## 3.1 `bid/__init__.py` — census row 106 (70 B, 1 line)

- **What:** `"""Bid layer (`bid` schema) — present-but-empty stub (PLAN §2)."""`
- **WHY (same as cyc):** thin package marker; the bid modules are imported directly
  (`from app.domain.bid.bid_ingester import ...`). "Stub" labels the init, not the layer — the layer is
  fully built (1900+ lines across 7 modules). **What breaks without it:** `app.domain.bid` is not a
  package; the ingester/generator imports fail. An explained package marker, not a placeholder.

## 3.2 `bid/models.py` — census row 109 (7797 B, 135 lines) — ORM for the `bid` schema

**File WHY:** The intake module's write target + the engine's read source. `BidLine` maps
`bid.bid_line` (schema.sql L721) **PLUS** the engine cost-component columns added by **migration 0007**
(`delivery_surcharge_case`, `vegcool_surcharge_case`, `lot_discount_case`, `price_basis_resolved`),
**plus** `transit_days` (mig 0011), **plus** `fiscal_period_id` (mig 0015). **Grain = the identity
octuple** — one row per submission×DC×lot×item×TF (and via the submission: supplier×round×cycle)
(docstring L4–7). Column alignment mirrors `bid.bid_line` verbatim (partial map — only intake/engine
columns) so the ORM round-trips against the migration. **What breaks without it:** the ingester has no
ORM to persist parsed lines to; the engine has no typed read of the cost stack.

**Precision constants (load-bearing, lines 25–37):**
- `_Cases = Numeric(18, 3)` — case-count precision (whole-ish cases, 3 decimals) — comment L25–26:
  "the case-count precision the capacity tables use ... Distinct from `_Money`."
- `_Money = Numeric(18, 6)` — per-case dollars, 6 decimals (matches `app/core/db/types.Money`).
- **WHY two constants:** a case count and a per-case dollar must not share precision — 6-decimal money
  vs 3-decimal cases keeps each value honest at its own grain (CLAUDE.md §3 data fidelity).
- `BidBase = BidBaseT` (line 35) re-exports the base under a legacy name some callers/alembic expect.

### Model `BidLine` (`__tablename__ = "bid_line"`, schema `bid`)

| Column | Python type | DB type | Null | Source | WHY |
|--------|-------------|---------|------|--------|-----|
| `bid_line_id` | str | varchar(36) | NOT NULL | baseline | **PK** `pk_bid_line` |
| `submission_id` | str | varchar(36) | NOT NULL | baseline | part of submission FK; the bid header |
| `cycle_id` | str | varchar(36) | NOT NULL | baseline | identity octuple |
| `round_id` | str | varchar(36) | NOT NULL | baseline | identity octuple |
| `supplier_id` | str | varchar(36) | NOT NULL | baseline | identity octuple |
| `dc_id` | str | varchar(36) | NOT NULL | baseline | identity octuple |
| `lot_id` | str | varchar(36) | NOT NULL | baseline | identity octuple |
| `item_id` | str | varchar(36) | NOT NULL | baseline | identity octuple |
| `tf_id` | str | varchar(36) | NOT NULL | baseline | identity octuple (period) |
| `fiscal_period_id` | str\|None | varchar(36) | **NULL** | **mig 0015** | the flat-13 period the line records against (INTAKE §1a); NULL on pre-fan-out (pilot/timeframe-only) rows; logical reference like tf_id (model L54–56) |
| `currency_code` | str | varchar(3) | NOT NULL | baseline | ISO currency |
| `price_basis` | str | text | NOT NULL | baseline | which §7 branch produced price |
| `submitted_all_in_case` | Decimal\|None | numeric(18,6) | NULL | baseline | engine IN_Bids All-In (primary). DDL CHECK `ck_bid_all_in_positive(>0)` |
| `fob_case` | Decimal\|None | numeric(18,6) | NULL | baseline | §7 fallback FOB. DDL CHECK `ck_bid_fob_positive(>0)` |
| `volume_minimum_cases` | Decimal\|None | numeric(18,3) | NULL | baseline | offered-volume coverage feed (cases) |
| `delivery_surcharge_case` | Decimal\|None | numeric(18,6) | NULL | **mig 0007** | §7 fallback component |
| `vegcool_surcharge_case` | Decimal\|None | numeric(18,6) | NULL | **mig 0007** | §7 fallback component (cold-chain) |
| `lot_discount_case` | Decimal\|None | numeric(18,6) | NULL | **mig 0007** | §7 fallback-only discount |
| `price_basis_resolved` | str\|None | text | NULL | **mig 0007** | ALL_IN vs COMPONENT_FALLBACK |
| `transit_days` | int\|None | integer | NULL | **mig 0011** | supplier-stated lane transit (origin→DC); blank ⇒ no proxy (model L71–73) |
| `commercial_conditions_text` | str\|None | text | NULL | baseline | free text |
| `exclusivity_required_flag` | bool | boolean | NOT NULL default False | baseline | — |
| `effective_date_start` | date\|None | date | NULL | baseline | — |
| `effective_date_end` | date\|None | date | NULL | baseline | — |
| `validity_status` | str | text | NOT NULL | baseline | — |
| `source_row_number` | int\|None | integer | NULL | baseline | provenance back to the sheet row |
| `created_at` | datetime | timestamp (naive) | NOT NULL | baseline | — |
| `bid_line_status` | str\|None | text | NULL | baseline | — |
| `is_scoreable` | bool | boolean | NOT NULL default False | baseline | engine eligibility |
| `is_awardable` | bool | boolean | NOT NULL default False | baseline | award eligibility |
| `incomplete_reason_code` | str\|None | text | NULL | baseline | why a line is incomplete |

**Columns in the baseline table NOT mapped (managed by SQL — partial map):** `freight_case`,
`fuel_case`, `accessorial_case`, `item_discount_case`, `shrink_case`, `moq_cases`,
`loading_location_id`, `leverage_signal_flag`, `leverage_signal_reason`, `best_in_class_signal_flag`,
`follow_up_recommended_flag` (schema.sql L735–757). **WHY mapped subset only:** the ORM carries exactly
the columns the intake writes + the engine §7 reads; the rest are engine-output/signal columns owned by
the analysis SQL. **THE LOAD-BEARING DB CHECK** the ingester guards in Python:
`ck_bid_line_no_double_discount` (mig 0007 L65–71): `submitted_all_in_case IS NULL OR lot_discount_case
IS NULL OR lot_discount_case = 0` — i.e. an All-In and a Lot Discount cannot coexist. The ingester
pre-empts this at `construct_price` (bid_ingester.py:301–302) so a bad row **quarantines** instead of
tripping the DB CHECK mid-txn. **Decision D20/D21 enforced:** the octuple identity columns +
`uq_bid_line_identity_full`/`uq_bid_line_cell_per_submission` UNIQUEs (schema.sql L759–760) are the
keyed grain the round-trip lands on.

### Model `CapacityStatement` (`__tablename__ = "capacity_statement"`, schema `bid`) — E-38

Mirrors `bid.capacity_statement` (schema.sql L806) verbatim — the per-supplier-per-round header that
owns the per-cell constraints. Columns: `capacity_statement_id varchar(36) PK`, `cycle_id NOT NULL`,
`round_id varchar(36) NULL`, `supplier_id NOT NULL`, `submission_id varchar(36) NULL`,
`source_artifact_id varchar(36) NOT NULL`, `status text NOT NULL`, `effective_at DateTime NOT NULL`,
`notes text NULL`. **WHY it rides the SAME `norm.source_artifact` + `bid.bid_submission`** as the bids
(model docstring L91–95): the capacity sheet is part of the one returned template file, so the FK chain
is shared and provenance is honest. `status` is free text (no DB CHECK): "SUBMITTED" on import, flipped
to "SUPERSEDED" when a later submission for the same (cycle, round, supplier) replaces it (append-only,
never deleted — model L105–107) — the **reuse-by-natural-key / supersede** edge. **DDL-only:** FKs
`fk_capacity_stmt_round_in_cycle`, `fk_capstmt_artifact_*`, `fk_capstmt_submission_identity`, CHECK
`ck_capstmt_submission_requires_round (submission_id IS NULL OR round_id IS NOT NULL)`, UNIQUE
`uq_capstmt_id_cycle` (schema.sql L815–827). ORM is the read/write handle.

### Model `CapacityConstraint` (`__tablename__ = "capacity_constraint"`, schema `bid`) — E-38

Mirrors `bid.capacity_constraint` (schema.sql L832) verbatim. Columns: `capacity_constraint_id
varchar(36) PK`, `capacity_statement_id NOT NULL`, `cycle_id NOT NULL`, `scope_type text NOT NULL`,
`dc_id varchar(36) NULL`, `lot_id varchar(36) NULL`, `tf_id varchar(36) NULL`, `max_weekly_cases
Numeric(18,3) NULL`, `max_period_cases Numeric(18,3) NULL`, `conditions_text text NULL`. **WHY five
scope types but the ingester writes only CELL** (model docstring L116–121): five exist in the baseline
(CELL / DC_TF / LOT_TF / SUPPLIER_TF / TOTAL_CYCLE); the ingest path emits **CELL** rows (dc+lot+tf all
set) — the grain the engine award is keyed on, so allocation-vs-capacity is a direct per-cell compare.
**THE TWO DB CHECKS the ingester guards:** `ck_capacity_scope_field_match` (schema.sql L845–851 — for
CELL, dc/lot/tf all NOT NULL) and `ck_capacity_has_a_max (max_weekly OR max_period NOT NULL)` (L852);
also `ck_capacity_weekly_nonneg`/`ck_capacity_period_nonneg (>= 0)` (L853–854). The ingester only emits
rows with at least one non-negative max so these CHECKs never trip (model L119–121; guarded in
`_parse_capacity_row`, bid_ingester.py:726–735). **Value note:** capacity maxes are **18,3 cases** —
same grain as the demand/coverage so a per-cell capacity compares directly to a per-cell allocation.

**Dependencies:** SQLAlchemy column types, `app.core.db.base.{Base,SchemaBase}`.

## 3.3 `bid/template_schema.py` — census row 113 (12591 B, 289 lines) — THE owned contract

**File WHY:** The single place the template shape is declared — written by the generator, read by the
ingester, so they **cannot drift** (D20; docstring L1–7). **D17:** our own multi-sheet design, NOT a
copy of the reference's 14-tab workbook. **D21:** explicit key IDs at every grain (the join identity is
the surrogate UUID, names are display-only). **"NO real data here — pure structure"** (docstring L33;
ADR-0001 §4). **What breaks without it:** generator and ingester would each hardcode headers and
silently diverge — the round-trip guarantee collapses.

**Module constants & their WHY:**
- `TEMPLATE_VERSION = "kr-bid-template/v1"` (L43) — stamped into every generated template, asserted on
  ingest; bump on any header/grain change so an old file against a new reader is caught, not silently
  mapped (L42). **Drift guard.**
- `TEMPLATE_PROTECT_PASSWORD = "kr-rfp-bid"` (L48) — soft Excel form-protection password; usability
  guard only — "the keyed re-ingest remains the real check (D21)" (L47). **Not a security control.**
- `BID_STATUS_HEADER = "Bid Status"` (L53) — a LOCKED generator-owned formula column (traffic light),
  appended after `BID_HEADERS`, **NOT part of the ingested contract** (the ingester never reads it).
- `SHEET_INSTRUCTIONS/SHEET_BIDS/SHEET_CAPACITY` (L56–58) — stable sheet identifiers.
- `TITLE_ROW=1, HEADER_ROW=2, BODY_START_ROW=3` (L62–64) — **our** layout (row-1 title band, row-2
  headers, row-3 body). WHY explicit: the reference put headers at row 4/17; reading **by header name**
  off a known header row (not by position) is what makes the round-trip robust (docstring L20–22, L61).

**`class BidColumn(StrEnum)` (L67–105)** — canonical header strings for the `Bids` sheet; the **string
VALUE is the literal cell text** the generator writes and the ingester matches on. Groups:
- **Key IDs (D21, locked, the join identity):** `CYCLE_ID="Cycle ID"`, `ROUND_ID="Round ID"`,
  `TF_ID="TF ID"`, `LOT_ID="Lot ID"`, `ITEM_ID="Item ID"`, `DC_ID="DC ID"`, `SUPPLIER_ID="Supplier ID"`.
- **Display names (attributes, NOT the key):** `ROUND="Round"`, `BID_TYPE="Bid Type"`,
  `SUPPLIER="Supplier"`, `DC="DC Name"`, `LOT="Lot"`, `ITEM="Item Description"`, `TF="TF"`.
- **Pricing components (supplier-owned, blank in a fresh template; D12 period-grain):**
  `ALL_IN="All-In $/case"`, `FOB="FOB $/case"`, `DELIVERY_SURCHARGE`, `VEGCOOL_SURCHARGE`,
  `LOT_DISCOUNT`, `TRANSIT_DAYS="Transit Days"`, `PRICING_COMMENTS`.
- **Volume (supplier-owned):** `WEEKLY_VOL_OFFERED`, `TOTAL_VOL_OFFERED`, `INVESTED_R1="Invested? (R1)"`.

**Column-set tuples (the grain/order contract):**
- `KEY_ID_COLUMNS` (L111–119) = (CYCLE, ROUND, TF, LOT, ITEM, DC, SUPPLIER) — **the grain tuple order
  used by the key validator + the round-trip assertion.** This ordering IS the identity; any reorder
  silently breaks validation, so it lives once here.
- `DISPLAY_SCOPE_COLUMNS` (L122–130) — the human columns the generator pre-fills.
- `SCOPE_COLUMNS = (*KEY_ID_COLUMNS, *DISPLAY_SCOPE_COLUMNS)` (L133) — all system-owned columns.
- `PRICE_COLUMNS` (L136–147) — the supplier-owned superset (blank in a fresh template).
- `BID_HEADERS = tuple(c.value for c in (*SCOPE_COLUMNS, *PRICE_COLUMNS))` (L150) — full ordered header
  list (scope first, then pricing).

**`class CapacityColumn(StrEnum)` (L153–176)** — Capacity-sheet headers; same D21 discipline. Key IDs
`CYCLE/SUPPLIER/DC/LOT/ITEM/TF`; display `SUPPLIER/DC/ITEM/TF`; supplier-entry `MAX_WEEKLY_CASES`,
`MAX_TOTAL_CASES`, `CAPACITY_NOTES`. `CAPACITY_KEY_ID_COLUMNS` (L182–189) = (CYCLE, SUPPLIER, DC, LOT,
ITEM, TF). **WHY LOT_ID is carried on a DC×item×TF capacity grain** (L180–181): the persisted
`bid.capacity_constraint` CELL grain is dc×lot×tf — the engine-award grain — so the lot is derived from
the item via the cycle scope and embedded. `CAPACITY_HEADERS`/`CAPACITY_ENTRY_COLUMNS` (L191–198).

**`@dataclass(frozen=True) ScopeRow` (L204–248)** — one supplier×DC×lot×item×TF×round cell; the
generator emits one `Bids` row per ScopeRow. Carries the surrogate KEY IDs (`round_id`, `tf_id`,
`supplier_id`, `dc_id`, `lot_id`, `item_id`) + display labels (`supplier_label`, `dc_label`,
`lot_label`, `item_label`, `tf_code`) + `round_code`/`bid_type`.
- `key_grain(cycle_id) -> (cycle_id, round_id, tf_id, lot_id, item_id, dc_id, supplier_id)` (L233–248)
  — **the exact identity the ingester reconstructs and validates**, in `KEY_ID_COLUMNS` order.
  Inputs: cycle_id. Output: the 7-tuple. Side-effects: none. **This method is the single definition of
  the embedded-key tuple — both ends call it (generator via scope, ingester via `by_key`).**

**`@dataclass(frozen=True) CycleScope` (L251–289)** — a cycle's scope: `cycle_id`, `cycle_code`,
`cycle_name`, `window_label`, `template_version=TEMPLATE_VERSION`, `rows: tuple[ScopeRow,...]`.
- `key_set() -> frozenset[7-tuple]` (L266–274) — **the allow-list the ingester validates each row's
  embedded keys against.** A row whose keys are not in this set is quarantined (UNKNOWN_KEY /
  KEY_MISMATCH), never guessed back from display names (D21).
- `capacity_key_set() -> frozenset[6-tuple]` (L276–288) — `(cycle_id, supplier_id, dc_id, lot_id,
  item_id, tf_id)` per row, **deduped across rounds** (capacity is round-independent). The allow-list
  for the Capacity-sheet ingest.

**Dependencies:** stdlib `dataclasses`, `enum`. **No I/O, no ORM** — pure structure (D17/ADR-0001 §4).

## 3.4 `bid/template_preset.py` — census row 112 (4403 B, 107 lines)

**File WHY:** EXP-INTAKE-TEMPLATE §1 — compose a leaner template from the `PRICE_COLUMNS` superset. A
`BidTemplatePreset` is a named, reusable selection of supplier-entry columns; the generator emits
exactly those. **Scope columns (keys D21 + names D23) are ALWAYS included** — a preset only chooses the
supplier-entry columns. Because the ingester reads by header NAME and tolerates absent optional columns
(`.get()`), a preset-built template round-trips for the columns it carries — "the preset IS the saved
mapping (no re-inference)" (docstring L11–14). **What breaks without it:** every cycle would ship the
full column superset; no lean per-cycle template.

- Module guards `_USABLE_PRICE = (ALL_IN, FOB)`, `_VOLUME = (WEEKLY_VOL_OFFERED, TOTAL_VOL_OFFERED)`
  (L29–30) — a complete/scoreable bid needs one of each.
- **`@dataclass(frozen=True) BidTemplatePreset`** — `name`, `description`, `entry_columns:
  tuple[BidColumn,...]`.
  - `__post_init__` (L42–54) **validation branches (all raise `ValueError`):**
    1. any entry column **not in `PRICE_COLUMNS`** → "columns not in the entry superset" (L43–48).
    2. **duplicate** entry columns → "duplicate entry columns" (L49–50).
    3. **no usable price** (neither ALL_IN nor FOB) → "must include a usable price" (L51–52).
    4. **no volume** (neither weekly nor total) → "must include a volume" (L53–54).
    **WHY:** a preset that cannot yield a complete bid is a configuration error caught at construction,
    not at generate/ingest time.
  - `bid_headers() -> tuple[str,...]` (L56–59) — `(*SCOPE_COLUMNS, *entry_columns)` values: scope first
    then this preset's entries. The generator and the traffic-light formula both key off this order.
- **Built-in presets:** `FULL_PRESET` (all `PRICE_COLUMNS`), `ALL_IN_PRESET` ("all_in_simple": ALL_IN +
  transit + comments + weekly + total + invested), `COMPONENTS_PRESET` ("components": FOB + delivery +
  vegcool + lot_discount + transit + comments + weekly + total + invested). `PRESETS` dict keyed by name.
- `get_preset(name) -> BidTemplatePreset` (L101–106) — resolve by lowercased/stripped name; **None or
  unknown → `FULL_PRESET`** (the safe superset fallback, never an error). **Edge:** an unrecognized
  preset name silently widens to full, not a 404 — deliberate (a template should never fail to generate
  because of a typo'd preset; the full superset is always valid).

**Dependencies:** `app.domain.bid.template_schema.{PRICE_COLUMNS, SCOPE_COLUMNS, BidColumn}`.

## 3.5 `bid/template_generator.py` — census row 111 (13204 B, 314 lines) — GENERATE end

**File WHY:** The GENERATE end of the round-trip (D20) / our design (D17). From a `CycleScope` produce a
multi-sheet xlsx: `Instructions` (identity + window + rules + version), `Bids` (one pre-filled scope row
per cell, blank price cells), `Capacity` (one row per supplier×DC×item×TF, blank capacity cells). File
IO via openpyxl is fine here — "a service, not the pure engine" (docstring L10–11). **What breaks
without it:** no template artifact for suppliers; nothing for the ingester to round-trip.

**Styling constants (L47–53):** `_ENTRY_FILL` (pale-yellow "enter here"), `_UNLOCKED =
Protection(locked=False)`, `_STATUS_RULES` (Complete=green, Incomplete=amber, Not bid=grey).

**Functions (each: signature · what · WHY · side-effects):**
- `_protect_form(ws)` (L56–63) — set sheet protection on with `TEMPLATE_PROTECT_PASSWORD`,
  `selectLockedCells`/`selectUnlockedCells` true, `formatCells=False`. **WHY:** make the sheet a true
  FORM — only unlocked entry cells stay editable. Side-effect: mutates `ws.protection`.
- `_unlock_entry_cells(ws, header_index, entry_headers, n_rows)` (L66–76) — for each entry column ×
  body row, set `cell.protection=_UNLOCKED` and `cell.fill=_ENTRY_FILL`. **WHY:** the only editable
  cells are the supplier-owned ones, visibly highlighted. **Note:** openpyxl writes through locks (L46
  comment), so the automated fill/ingest path is unaffected by protection.
- `_hide_columns(ws, header_index, headers)` (L79–83) — set `column_dimensions[letter].hidden=True`.
  **WHY (D23):** hide the raw key-ID columns so a supplier sees **names, not UUIDs**. The keys remain in
  the cells (the join identity) but are not shown.
- `_INSTRUCTION_RULES` (L87–109) — the (label, value) rule rows: Template version/Cycle/Window (filled
  from scope), Pricing (**"Enter EITHER an All-In ... OR the components ... Do not enter both an All-In
  and a Lot Discount"** — the human statement of the §7 double-subtract guard), No Bid ("Leave ALL price
  cells blank ... Do not enter 0"), Volume, Grain ("One row per DC × Lot × Item × TF. Prices are per
  period (TF)"). **WHY here:** the supplier instructions are the human side of the rules the ingester
  enforces in code — keeping them in one tuple keeps form text and code behavior aligned.
- `_write_headers(ws, title, headers)` (L112–117) — row-1 title band + row-2 header row.
- `_build_instructions(ws, scope)` (L120–133) — title + the rule rows (version/cycle/window filled from
  scope), written from row 3 down.
- `_scope_cell_values(row, cycle_id) -> dict[BidColumn,str]` (L136–161) — **THE key-embedding map:** the
  7 KEY-ID columns ← the surrogate UUIDs (`CYCLE_ID←cycle_id`, `ROUND_ID←row.round_id`, etc.) + the
  display columns ← the human labels. **WHY (D21):** both are system-owned/locked, but only the keys are
  the validated identity; the names are attributes (a mismatch warns, never re-resolves).
- `_add_bid_status_column(ws, status_col, n_rows, preset)` (L164–219) — append the per-row readiness
  **traffic light** as a LOCKED Excel formula (NOT ingested). Builds, per row, an
  `=IF(AND(NOT(any_price),NOT(any_vol)),"Not bid",IF(AND(has_price,has_vol),"Complete","Incomplete"))`
  formula referencing the preset's price/volume columns by letter, then attaches conditional formatting
  per `_STATUS_RULES`. **WHY:** a live in-Excel readiness indicator for the supplier; generator-owned so
  it never enters the ingest contract. **Edge:** built only from columns present in the preset
  (`if c in preset.entry_columns`), so a lean preset's traffic light only references its own columns.
- `_build_bids(ws, scope, preset)` (L222–237) — write headers (preset order), one row per `scope.rows`
  via `_scope_cell_values` (price cells left blank), then form treatment: `_unlock_entry_cells`,
  `_hide_columns(KEY_ID_COLUMNS)`, `_add_bid_status_column`, freeze panes at body start, `_protect_form`.
- `_build_capacity(ws, scope)` (L240–280) — write `CAPACITY_HEADERS`, then **dedupe the bid scope on the
  full IDENTITY** `(supplier_id, dc_id, lot_id, item_id, tf_id)` (L252–258) — "**not display names, so
  two cells that share a name never collapse**" (L244–245; CLAUDE.md §3 fidelity). For each unique cell:
  embed the 6 key IDs + the display names, increment row. Then unlock entry cells, hide
  `CAPACITY_KEY_ID_COLUMNS`, protect. **Edge:** capacity is round-independent, so two rounds' rows for
  the same cell collapse to one capacity row (correct — a capacity statement is per cell, not per round).
- `build_template_workbook(scope, preset=FULL_PRESET) -> Workbook` (L283–304) — repurpose the default
  sheet as `Instructions` (+ protect), create `Bids` + `Capacity`. Returns the in-memory workbook.
- `generate_template_bytes(scope, preset=FULL_PRESET) -> bytes` (L307–313) — save the workbook to a
  `BytesIO` and return the bytes. **WHY bytes, not a file:** CLAUDE.md §4 NO server-side file storage —
  the artifact streams to the caller / DB, never written to disk.

**Dependencies:** openpyxl (`Workbook`, styles, `CellIsRule`, `get_column_letter`),
`template_preset.{FULL_PRESET, BidTemplatePreset}`, `template_schema.*`.

## 3.6 `bid/bid_ingester.py` — census row 107 (30396 B, 751 lines) — INGEST end (D20/D21)

**File WHY:** The INGEST end of the round-trip. Reads OUR owned template (NOT arbitrary legacy layouts —
D20: "no universal-format guessing for the live product"). **D21 — KEY-VALIDATED load, never a name
resolve** for our template: each generated `Bids` row embeds the surrogate KEY IDs; ingest READS those
keys and VALIDATES the full key tuple against `CycleScope.key_set()` (exact match → accept, keys carry
identity DIRECTLY; blank → MISSING_KEY; unknown/tampered → UNKNOWN_KEY/KEY_MISMATCH — **never** fall
back to guessing identity from names). Names are at most a WARNING cross-check. The legacy
name-resolution path is retained ONLY for the migration bridge (`legacy_adapter`). Output is an
in-memory `IngestResult`; persisting to the DB is the caller's unit of work (CLAUDE.md §4). **What
breaks without it:** the generated template cannot become `bid.bid_line` rows; the D20/D21 round-trip
proof has no ingest end.

**Type aliases (L57–60):** `KeyGrain = 7-tuple` (KEY_ID_COLUMNS order); `CapacityKeyGrain = 6-tuple`.

**Enums:**
- `Completeness(StrEnum)` (L63–68): `BID` (usable price present), `NO_BID` (every price/volume cell
  blank — a **declined** cell, NOT a zero price), `INCOMPLETE` (partial price intent, not enough to
  construct). **WHY a declined cell ≠ zero:** CLAUDE.md §3 — a blank is "no statement", a 0 would be a
  fabricated price.
- `QuarantineReason(StrEnum)` (L71–87): **D21 key reasons** `MISSING_KEY`, `UNKNOWN_KEY`, `KEY_MISMATCH`
  (alias of UNKNOWN_KEY); **legacy name reasons** `UNRESOLVED_{SUPPLIER,DC,LOT,ITEM,TF}`,
  `MISSING_IDENTITY`; **shared** `DOUBLE_SUBTRACT` (All-In + discount footgun), `BAD_NUMERIC`
  (non-numeric/negative price cell). **WHY an enum:** quarantine reasons are a closed, auditable set —
  we quarantine, never guess.

**Dataclasses:** `ResolvedIdentity` (L90–108: the system-owned key IDs a parsed row carries; for our
template these are the embedded+validated keys, for legacy the resolved ids — `cycle_id/round_id/tf_id`
default `""` so the legacy path is unaffected; `tf_code` is the engine's TF period token).
`IdentityResolver(Protocol)` (L111–124: resolve supplier/dc/lot/item/tf label→canonical id or None;
the real impl queries `ref.*_alias`). `StubIdentityResolver` (L127–159: a dict-backed resolver for
tests/prototype; `_norm` = case/space-fold matching the alias layer's `normalized_alias_text`).
`ParsedComponents` (L162–171: all_in, fob, delivery_surcharge, vegcool_surcharge, lot_discount — maps
1:1 to the engine §7). `ParsedBidLine` (L173–196: the costed line — round_code, bid_type, identity,
components, `landed_cost_per_case`, `price_basis`, weekly/total vol, invested_r1, pricing_comments,
transit_days, completeness, source_row_number). `QuarantinedRow` (L198–206: source row, reason, detail,
raw dict — kept verbatim). `NameMismatchWarning` (L208–220: row/column/expected/found — the row STILL
loads on keys; we only warn). `IngestResult` (L222–240: lines + quarantined + name_warnings, with
`bid_count`/`no_bid_count`/`incomplete_count` properties).

**THE VALUE-TRANSFORMATION FUNCTIONS (formula + file:line):**
- `_to_decimal(value) -> Decimal | None` (L248–265) — **the coercion hop.** None/blank → None; a string
  is `.strip()`-ed then `Decimal(stripped)`, raising `ValueError` on `InvalidOperation`; **`bool` is
  explicitly rejected** (L261–262: bool is an int subclass but is never a price); int/float/Decimal →
  `Decimal(str(value))`. **WHY `Decimal(str(float))`:** stringifying the float first avoids binary
  float drift entering the Decimal — CLAUDE.md §3 no value alteration. A non-numeric cell becomes a
  `ValueError` → quarantined `BAD_NUMERIC` (never coerced to 0).
- `_to_bool(value) -> bool | None` (L268–274) — None/blank/"-" → None; else True iff in
  {y,yes,true,1,invested}. Used for `Invested? (R1)`.
- `_header_index(ws) -> dict[str,int]` (L277–285) — map header text → 1-based column from the template's
  header row **by NAME** (§2 rule — never by position). **WHY:** the reference's trailing-width
  inflation taught not to trust `max_column` (docstring + L278).
- **`construct_price(components) -> (price, basis, error)` (L288–317) — THE §7 cost-construction hop +
  double-subtract guard:**
  - If `all_in is not None`: **if `lot_discount != 0` → return `(None, None, "All-In present together
    with a Lot Discount (double-subtract risk)")`** (L301–302) — the **DOUBLE_SUBTRACT** guard: do NOT
    recompute, do NOT silently drop the discount, surface for quarantine (the DB
    `ck_bid_line_no_double_discount` is the persistence backstop). Else `(all_in, "ALL_IN", None)` —
    **All-In taken verbatim** (already net of discounts).
  - Elif `fob is not None`: `price = construct_price_from_parts(None, fob, delivery, vegcool,
    lot_discount)` (L307–313) → **the canonical §7 formula `FOB + delivery + vegcool − lot_discount`**
    (defined once in `app/engine/formulas.py:21–42`, shared by engine + ingest so the arithmetic lives
    in exactly one place). Returns `(price, "COMPONENT_FALLBACK", None)`.
  - Else `(None, None, None)` — no All-In, no FOB → nothing to construct (no-bid/incomplete).
  **THIS is the FOB→landed transformation hop the audit standard demands named with formula + file:line:
  `bid_ingester.py:307–313` calling `formulas.py:41` → `fob + delivery_surcharge + vegcool_surcharge −
  lot_discount`.** No rounding is applied here — `Decimal` arithmetic preserves the operands' scale; the
  6-decimal (18,6) DB column stores it without re-rounding.
- `_classify(components, price, weekly, total) -> Completeness` (L320–341) — **bid/no_bid/incomplete:**
  `has_any_price_intent` = any of all_in/fob present or any surcharge/discount ≠ 0; `has_vol` = weekly
  or total present. **If `price is not None and price > 0` → BID** (L337); **elif not price-intent and
  not vol → NO_BID** (L339); **else INCOMPLETE** (L341). **WHY `price > 0`:** a non-positive constructed
  price is not a usable bid (mirrors the engine's `<=0` drop); a partially-filled row that can't yield a
  positive price is INCOMPLETE, surfaced — not silently dropped (CLAUDE.md §3).
- `_iter_body_rows(data) -> list[(row_no, raw-dict)]` (L344–363) — load the `Bids` sheet
  (`data_only=True, read_only=True`); **raise `ValueError` if `SHEET_BIDS` missing** (L349–350); skip
  fully-blank rows (L359–360). **Edge:** a file without a `Bids` sheet is a hard error (it is not our
  template).

**THE TWO PUBLIC INGEST ENTRY POINTS:**
- **`ingest_template(data, scope) -> IngestResult` (L366–390) — the LIVE, key-validated path.** Builds
  `valid_keys = scope.key_set()` and `by_key = {row.key_grain(cycle_id): row for row in scope.rows}`,
  then per body row calls `_parse_keyed_row`; a `QuarantinedRow` → `result.quarantined`, else the
  `(line, warnings)` → `result.lines` + `result.name_warnings`.
- **`ingest_template_resolved(data, resolver) -> IngestResult` (L393–410) — LEGACY-ONLY name-resolve.**
  Per row calls `_parse_resolved_row`. Banner (L394–400): retained solely for the migration bridge; the
  live product never reaches here.

**THE PARSE HELPERS (every branch):**
- `_row_to_dict(row_cells, headers)` (L413–423) — build `{header: stringified-stripped value}` keyed by
  header names (None → ""). 
- `_cell(raw, column)` (L426–427) — `raw.get(column.value, "").strip()`.
- `_parse_pricing_and_build(raw, row_number, identity)` (L430–475) — **the shared tail** (identical for
  keyed + legacy; never touches identity again): build `ParsedComponents` via `_to_decimal` (surcharges
  default to `Decimal("0")` when blank — L443–447), read weekly/total/transit; **on `ValueError` →
  `QuarantinedRow(BAD_NUMERIC)`** (L452–453). Then `construct_price`; **if `price_error` →
  `QuarantinedRow(DOUBLE_SUBTRACT)`** (L456–457). Classify completeness, build the `ParsedBidLine`
  (transit cast to `int` when present — L472). 
- `_KEY_TO_NAME_COLUMN` (L479–484) — the (key, name) display columns cross-checked warn-only.
- **`_parse_keyed_row(raw, row_number, cycle_id, valid_keys, by_key)` (L487–535) — D21 validation, every
  branch:**
  1. Read embedded keys `keys = tuple(_cell(raw, col) for col in KEY_ID_COLUMNS)` (L497) — **tuple order
     MUST match `key_grain()`**.
  2. **Blank key cell → `QuarantinedRow(MISSING_KEY, "blank {col}")`** (L499–503) — a locked identity
     cell was cleared/tampered.
  3. **`embedded_cycle != cycle_id OR keys not in valid_keys` → `QuarantinedRow(UNKNOWN_KEY, "embedded
     keys not in cycle scope: {keys}")`** (L506–514) — unknown/tampered/foreign key; **NEVER guess from
     names**.
  4. Accepted: unpack keys into `ResolvedIdentity` (identity carried DIRECTLY; `tf_code` = the display
     TF token) (L516–527).
  5. `warnings = _name_cross_check(raw, row_number, by_key.get(keys))` (L530) — warn-only.
  6. `_parse_pricing_and_build`; if quarantined return it, else return `(line, warnings)`.
- `_name_cross_check(raw, row_number, scope_row)` (L538–561) — for each (key,name) column, if the found
  display name is non-blank, the expected is non-blank, and they differ → append a `NameMismatchWarning`.
  **The row STILL loads on its keys** — names are attributes (D21). `scope_row is None` → no warnings.
- **`_parse_resolved_row(raw, row_number, resolver)` (L564–605) — LEGACY name resolution, every branch:**
  read 5 labels (supplier/dc/lot/item/tf_code); **any blank → `MISSING_IDENTITY`** (L580–584); then
  resolve each via the resolver — **each None → the matching `UNRESOLVED_*`** (L586–600); on success
  build `ResolvedIdentity` (with `tf_code = resolved_tf`) and `_parse_pricing_and_build`.

**CAPACITY INGEST (E-38, same D21 discipline):**
- `ParsedCapacityLine` (L613–634) — cycle/supplier/dc/lot/item/tf keys + tf_code + `max_weekly_cases` +
  `max_period_cases` (the sheet's "Max Total Cases" = total over the TF, the apples-to-apples compare to
  the engine's per-cell period allocation, L617–621) + notes + source_row_number. **Only a cell with a
  max becomes a line (a blank cell is no statement, not a zero).**
- `CapacityIngestResult` (L637–642) — lines + quarantined.
- **`ingest_capacity(data, scope) -> CapacityIngestResult` (L645–664)** — `valid_keys =
  scope.capacity_key_set()`; per row `_parse_capacity_row`; a None outcome (no max) is skipped. **The
  Capacity sheet is OPTIONAL — a file without it yields an empty result (no capacity is NOT an error).**
- `_iter_capacity_rows(data)` (L667–689) — load the `Capacity` sheet; **missing sheet → `[]`** (L675–677
  — optional, contrast `_iter_body_rows` which raises for a missing Bids sheet); skip blank rows.
- **`_parse_capacity_row(raw, row_number, cycle_id, valid_keys) -> line | QuarantinedRow | None`
  (L692–750), every branch:** read 6 keys; **blank → `MISSING_KEY`** (L706–710); **`cycle_k != cycle_id
  OR keys not in valid_keys` → `UNKNOWN_KEY`** (L713–719); read maxes via `_to_decimal`, **`ValueError`
  → `BAD_NUMERIC`** (L724–725); **negative max → `BAD_NUMERIC("negative ...")`** (L727–731 — guards the
  DB nonneg CHECKs so a bad cell quarantines cleanly, never aborts the txn); **both maxes None → return
  `None`** (no statement — L734–735); else build the `ParsedCapacityLine`.

**Dependencies:** openpyxl, `template_schema.*`, **`app.engine.formulas.construct_price_from_parts`**
(the single shared §7 definition). **Decision enforcement (bid_ingester):** D20 round-trip (reads our
template only), D21 key-validation (`_parse_keyed_row` L487–535, `_parse_capacity_row` L692–719), §7 +
double-subtract (`construct_price` L298–303 + formulas.py:41), §4 no-bid (`_classify` L320–341), E-38
capacity (ingest_capacity + CELL-grain) — each at the file:lines cited.

## 3.7 `bid/legacy_adapter.py` — census row 108 (5714 B, 138 lines) — migration bridge ONLY

**File WHY:** D20 — our owned template is the LIVE contract; messy reference formats (.xlsb, 14-tab
legacy) are TEST/REFERENCE inputs only. This adapter reads a **SYNTHETIC, our-own** legacy-shaped
workbook (NOT the quarantined real files), maps its columns onto our owned `Bids` grain, and hands the
normalized bytes to the ingester. **D21 boundary — this is the ONLY place name resolution lives**
(legacy inputs predate embedded keys), so it calls `ingest_template_resolved` (the LEGACY-ONLY entry),
NOT the live `ingest_template`. Anything it cannot map flows through to quarantine (never guess).
**What breaks without it:** no proof that a foreign layout produces the same parsed grain or quarantines
cleanly — the migration-resilience claim is unbacked.

- `LEGACY_TO_OWNED: dict[str, BidColumn]` (L44–60) — maps reference wording (e.g. `"FOB $/Case
  (Corrugate)"→FOB`, `"Lot_ID"→LOT`, `"Product Description"→ITEM`, `"Comments"→PRICING_COMMENTS`,
  `"Weekly Vol Cap"→WEEKLY_VOL_OFFERED`) to our owned columns. Unmapped legacy columns (trailing
  inflation) **fall away — dropped, not guessed** (L104).
- `LEGACY_NO_BID = "No Bid"` (L63) — the legacy decline token, normalized to a blank price cell.
- **`adapt_legacy_to_owned(legacy_bytes, *, sheet_name, legacy_header_row) -> bytes` (L66–118)** —
  **the shape-bridge transformation:** read the legacy sheet's headers at `legacy_header_row` (NOT
  trusted to be our row 2 — the reference uses row 4/17, L70–76); build a fresh `Workbook` with title
  "Bids (migrated from legacy)" and our `BID_HEADERS` on `HEADER_ROW`; for each legacy body row, for
  each mapped legacy header, copy the stripped value into the owned column — **`"No Bid"` → ""** (a
  decline → blank price cell, which the ingester then flags `no_bid`, L107–108); only emit a dest row if
  any value was written. Returns the owned-template bytes. **Edge:** a fully-`No Bid`/empty legacy row
  writes nothing (no dest row). **Value note:** this hop changes only **shape** (layout/headers), never
  numbers — values are copied verbatim except the `No Bid`→blank normalization (CLAUDE.md §3 honesty).
- **`ingest_legacy(legacy_bytes, resolver, *, sheet_name, legacy_header_row) -> IngestResult`
  (L121–137)** — adapt to owned bytes, then `ingest_template_resolved(owned_bytes, resolver)`. **The
  only sanctioned caller of `ingest_template_resolved`** — the live product key-validates (L131–132).

**Dependencies:** openpyxl (`Workbook`, `load_workbook`), `bid_ingester.{IdentityResolver, IngestResult,
ingest_template_resolved}`, `template_schema.{BID_HEADERS, BODY_START_ROW, HEADER_ROW, SHEET_BIDS,
TITLE_ROW, BidColumn}`.

## 3.8 `bid/period_fanout.py` — census row 110 (3203 B, 79 lines) — flat-13 fan-out

**File WHY:** INTAKE_TEMPLATE_DESIGN §1a — storage stays **flat at the 13 periods**, but a supplier
prices a handful of **timeframes** (contiguous spans of fiscal periods); intake **fans out** each
timeframe's price to EVERY fiscal period it covers, so each of the 13 periods carries the timeframe's
payload verbatim while the supplier filled only a few cells. **PURE logic — no DB, no ORM, no
`app.domain.*` imports** (docstring L9–11) so it is unit-testable in isolation; builds on
`app.fiscal.calendar.expand_to_periods`. **What breaks without it:** the flat-13 grain cannot be
realized from timeframe-grain bids; the engine's per-period model has gaps.

- `@dataclass(frozen=True) FannedPrice` (L23–38) — `fiscal_period: FiscalPeriod`, `payload:
  Mapping[str,object]` (opaque — whatever price/volume/component dict the caller priced the timeframe
  with, **copied verbatim** onto each period; this module never inspects or hardcodes bid column names —
  L26–29). `period_key` property → `(fiscal_year, period)` (unique within a year).
- **`fan_out(timeframe, payload) -> list[FannedPrice]` (L41–51) — THE fan-out hop:** for each period in
  `expand_to_periods(timeframe)` (`app/fiscal/calendar.py:221–228` → `get_period(fy, p)` for each p in
  `timeframe.period_numbers`), emit a `FannedPrice` with a **`copy.copy(payload)` shallow copy** (L49)
  so callers cannot mutate shared state across records. **Value note:** the payload is copied
  **verbatim** — NO value change, NO renormalization at this hop; the timeframe's price lands on each
  period unchanged (CLAUDE.md §3 — no flattening/coercion). One record per period, in period order.
- **`fan_out_all(groups) -> list[FannedPrice]` (L54–78) — multi-timeframe, with overlap guard:** for
  each `(timeframe, payload)`, fan out; **if a period_key is already `seen` → raise `ValueError("period
  {p} of FY{fy} is covered by more than one timeframe; each period must get at most one price.")`**
  (L67–73) — **the no-double-coverage edge:** a period must not receive two prices. Then sort by
  period_key. **WHY the guard:** overlapping timeframes would double-count a period's spend — surfaced as
  an error, never silently resolved (CLAUDE.md §3).

**Dependencies:** stdlib `copy`, `collections.abc`, `dataclasses`; `app.fiscal.calendar.{FiscalPeriod,
Timeframe, expand_to_periods}`.

---

# LAYER-1 contributions (data model + data-flows) from this slice

## Tables these ORM classes map (schema · table · source)
- `ref.client` (schema.sql L74) ← `Client`; `ref.commodity` (L90) ← `Commodity`; `ref.fiscal_period`
  (mig 0014) ← `FiscalPeriod`.
- `cyc.cycle_objective/cycle_pricing/cycle_scope_item/cycle_pba_term/cycle_commercial_term/
  cycle_rfi_question/cycle_timeline_event/cycle_narrative` (mig 0002) + `cyc.cycle_safety` (mig 0003) ←
  the cyc satellites; `cyc.cycle_round/cycle_timeframe/cycle_lot/cycle_item_scope/cycle_lot_item/
  cycle_projected_volume` (schema.sql L355–470) ← the partial-mapped spine.
- `bid.bid_line` (schema.sql L721 + mig 0007/0011/0015) ← `BidLine`; `bid.capacity_statement` (L806) ←
  `CapacityStatement`; `bid.capacity_constraint` (L832) ← `CapacityConstraint`.

## Value transformations / decimal hops in this slice (formula + file:line)
1. **Cell→Decimal coercion** — `bid_ingester._to_decimal` (L248–265): str→`Decimal(stripped)`,
   float→`Decimal(str(float))` (drift-free), bool rejected, blank→None, non-numeric→ValueError→
   quarantine BAD_NUMERIC. **No rounding.**
2. **§7 price construction (FOB→landed)** — `bid_ingester.construct_price` (L298–317) →
   `formulas.construct_price_from_parts` (`app/engine/formulas.py:41`): `price = fob + delivery_surcharge
   + vegcool_surcharge − lot_discount`. All-In branch returns All-In **verbatim** (no arithmetic).
   Stored at **numeric(18,6)** (`bid.bid_line.submitted_all_in_case`/`fob_case`/component columns); no
   re-round on store.
3. **Double-subtract guard** — `construct_price` L301–302 (All-In + non-zero Lot Discount → block →
   QuarantinedRow DOUBLE_SUBTRACT); DB backstop `ck_bid_line_no_double_discount` (mig 0007 L65–71).
4. **Completeness classification** — `_classify` (L320–341): `price>0`→BID; no price-intent & no vol→
   NO_BID; else INCOMPLETE. A non-positive price is never stored as a bid.
5. **Flat-13 fan-out** — `period_fanout.fan_out` (L41–51): timeframe payload **copied verbatim**
   (`copy.copy`) onto each fiscal period from `expand_to_periods` (`calendar.py:221–228`). **No value
   change**; overlap → ValueError (`fan_out_all` L67–73).
6. **Legacy shape bridge** — `legacy_adapter.adapt_legacy_to_owned` (L66–118): layout/header remap only;
   values verbatim except `"No Bid"`→blank (L107–108). **No numeric change.**
7. **Tenant stamp** — `ref/service.create` (L46): request (no client_id) → row `client_id = context
   tenant`. (Identity transformation, not numeric.)
8. **Capacity grain** — maxes read at **numeric(18,3)** (`_parse_capacity_row` L722–723); negative→
   quarantine (L727–731); CELL-scoped (dc+lot+tf) persistence (`bid.capacity_constraint`).

## Precision inventory (this slice)
- **numeric(18,6)** = per-case money: `bid.bid_line.submitted_all_in_case/fob_case/
  delivery_surcharge_case/vegcool_surcharge_case/lot_discount_case`; `cyc.cycle_safety.cap/floor/band`.
- **numeric(18,3)** = case counts: `bid.bid_line.volume_minimum_cases`;
  `bid.capacity_constraint.max_weekly_cases/max_period_cases`;
  `cyc.cycle_projected_volume.projected_weekly_cases/projected_period_cases`;
  `cyc.cycle_scope_item.projected_volume`.
- **numeric(18,2)** = currency amounts: `cyc.cycle_commercial_term.benefit_value`.
- **numeric(9,6)** = a ratio/percentage: `cyc.cycle_projected_volume.growth_override_pct`.

---

# LAYER-2 process / edge-case index (this slice)

| Process | Happy path | Edges enumerated (file:line) |
|---------|-----------|-------------------------------|
| Commodity create | stamp tenant, add+flush, audit (service.py:45–65) | duplicate code → 409 CONFLICT (38–43); validation_error at schema (over-length); DB UNIQUE backstop |
| Live bid ingest (D21) | keyed validate → cost → classify (ingest_template 366–390) | blank key→MISSING_KEY (499–503); foreign/tampered key→UNKNOWN_KEY (506–514); name mismatch→WARN only (538–561); bad numeric→BAD_NUMERIC (452–453); All-In+discount→DOUBLE_SUBTRACT (456–457); all-blank→NO_BID (339); partial→INCOMPLETE (341); missing Bids sheet→ValueError (349–350); blank row skipped (359–360) |
| Legacy ingest (bridge) | adapt shape → name-resolve (ingest_legacy 121–137) | blank scope cell→MISSING_IDENTITY (582–584); each unresolved label→UNRESOLVED_* (586–600); No Bid→blank (107–108); unmapped col dropped (104) |
| Capacity ingest (E-38) | keyed validate → read maxes (ingest_capacity 645–664) | missing sheet→[] optional (675–677); blank key→MISSING_KEY (706–710); foreign key→UNKNOWN_KEY (713–719); bad/negative max→BAD_NUMERIC (724–731); no max→skip None (734–735) |
| Period fan-out | verbatim copy per period (fan_out 41–51) | overlap→ValueError (67–73) |
| Preset compose | validate at construct (BidTemplatePreset.__post_init__ 42–54) | not-in-superset / duplicate / no-price / no-volume → ValueError; unknown preset name→FULL fallback (get_preset 101–106) |
| Capacity supersede | SUBMITTED→SUPERSEDED on replacement (models.py:105–107) | append-only, never deleted (reuse-by-natural-key) |

---

# Decision → enforcement map (this slice)

| Decision / Epic | What | Enforced at (file:line) | Drift? |
|-----------------|------|-------------------------|--------|
| D9 (participation / one pricing) | participates flag; one pricing render | cyc/models.py CycleScopeItem.participates (75); CyclePricing PK cycle_id (53) + mig 0002 L101 | no |
| D12 (period-grain pricing) | price per TF/period | CyclePricing (one/cycle) + TF on bid_line/scope rows | no |
| D13 / ADR-0014 (pricing safety) | safety as CONTRACT term, engine ignores | cyc/models.py CycleSafety (256–280) + mig 0003 | no |
| D17 (our own template) | multi-sheet owned design | template_schema.py (whole), template_generator.py | no |
| D18 (strategy-driven generation) | scope-driven, nothing hardcoded | template_schema.CycleScope (251–289) | no |
| D20 (round-trip ingest) | engine ingests files it creates | template_schema (one contract) + generator + ingest_template (366) | no |
| D21 (explicit keys, key-validated load) | keys are identity, names are display | KEY_ID_COLUMNS (111); _parse_keyed_row (487–535); _parse_capacity_row (692–719) | no |
| D23 (hide raw key IDs) | supplier sees names not UUIDs | template_generator._hide_columns (79–83), used L234/279 | no |
| §7 + double-subtract | one price formula, block double-subtract | formulas.py:41 (shared); construct_price (298–303) + DB ck (mig 0007 L65) | no |
| §4 (no-bid handling) | blank ≠ 0; declined surfaced | _classify (320–341); legacy No Bid→blank (107) | no |
| E-16 (Next Steps rail) | timeline events | cyc/models.py CycleTimelineEvent (123–136) + mig 0002 | no |
| E-38 (capacity) | stated capacity, CELL grain | bid/models.py Capacity* (88–134); ingest_capacity (645) | no |
| INTAKE §1a (flat-13 fan-out) | timeframe→13 periods verbatim | period_fanout.fan_out (41–51) + fiscal_period_id (mig 0015) | no |
| PLAN §7 (add+flush, no commit) | UoW owns commit | repository.add (46–50); service (51); writer (108–111) | no |
| security/PLAN §1/§3/§5 | tenant from ctx; mutation+audit one txn; tenant off body | repository (32/40); service (46,53–64)+writer (96–160); schemas (no client_id) | no |
| R-PD5 | client_id nullable now, NOT NULL+RLS later | models.py:69–75 + schema.sql L92 | **intended** (documented) |

**Sub-drifts noted (ORM does not carry a DDL CHECK — DB is the backstop, by the partial-map rule, not a
bug):** `ck_client_code_not_empty`, `ck_commodity_code_not_empty`, `uq_cycle_objective_one_primary`
(partial unique), all the `cyc.cycle_pricing`/`narrative`/`safety`/`volume`/`commercial_term`/`rfi`
CHECKs, `ck_bid_all_in_positive`/`ck_bid_fob_positive`, the capacity scope/has-a-max/nonneg CHECKs. Each
is enforced in Postgres (cited above); the ingester additionally pre-guards the double-subtract and
capacity-nonneg CHECKs in Python so a bad row quarantines cleanly instead of aborting the txn.

---

# GAPS / UNVERIFIABLE / NOTES (honest)
1. **No `read.py` in any of the three trees** (prompt listed "read" as a layer). Verified absent by
   `find`. cyc & bid intentionally do not ship the service/repository/schemas trio (PLAN §2): `ref` is
   the reference impl; cyc is models-only; bid ships intake/template modules. Explained, not a missing
   file.
2. **Partial ORM maps are intentional** (cyc spine, bid_line): only engine/intake-read columns are
   mapped; the rest are SQL-managed. Listed the unmapped columns explicitly (cyc §2.2, bid §3.2) so the
   gap is named, not silent.
3. **The cyc `__init__` and bid `__init__` say "present-but-empty stub"** in their own docstrings — the
   word "stub" refers to the package init only; the layers' models are fully built. Not a D19 violation.
4. **R-PD5 nullable `client_id`** is a planned migration-window state (NOT NULL + RLS pending Security
   ratification), documented in code and here — not unplanned drift.
5. The 13 `__pycache__/*.pyc` are generated bytecode caches — counted in bulk (§0), not per-file
   audited, not in the census (which tracks owned source).
6. **Decimal rounding:** verified there is **no rounding** in this slice's value path — `_to_decimal`
   and §7 arithmetic preserve operand scale; the 18,6 / 18,3 columns store without re-rounding. Any
   rounding to display precision happens downstream (engine/render), out of this slice.
