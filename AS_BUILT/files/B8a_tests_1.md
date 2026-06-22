---
doc: AS-BUILT AUDIT — SLICE B8a — backend API / auth / pilot tests + test fixtures (Layer 2, test surface)
id: ASBUILT-B8a-TESTS-1
status: COMPLETE (read-only audit; nothing modified)
scope: backend/tests/api/**, backend/tests/auth/** (does not exist — see GAP-1), backend/tests/pilot/**,
       backend/tests/conftest.py, backend/tests/__init__.py
contract: /CLAUDE.md ABSOLUTE REQUIREMENTS injected; honored literally. AUDIT_STANDARD.md Layer-2 bar.
census_rows: 181 (tests/__init__.py), 182–194 (tests/api/*), 214 (tests/conftest.py), 233–240 (tests/pilot/*)
method: find over the three dirs + conftest; cross-checked every path against AS_BUILT/FILE_CENSUS.md;
        read EVERY file end-to-end; enumerated EVERY def (test fn + helper). Function counts verified by grep.
---

# SLICE B8a — the test surface for the REST API, auth, and the pilot core

> **What this slice IS.** The automated regression suite that guards the backend's HTTP surface
> (`app.api.v1.*`), the auth/session contract (`app.auth.*`), and the pilot orchestration core
> (`app.pilot.*`). It is the executable specification of the "no-MVP, full-capability, data-faithful,
> no-server-side-storage, governed-and-auditable" contract: each test asserts a behavior the running
> RFP system MUST exhibit, and names (in its docstring) the regression it prevents.
>
> **Two runtimes guarded.** The repo runs two runtimes (CLAUDE.md / AUDIT_STANDARD Layer-1): the
> **stateless web console** (one shared Postgres, identity in `pilot.run`, NO server-side files) and
> the **MCP-harness file-vault** (per-run isolated DB, files on disk in a git vault). These tests
> guard BOTH: the `api/**` tests exercise the console HTTP surface against the shared DB with an empty
> temp vault; the `pilot/**` tests exercise `PilotService` in both console mode (`db_runs=True`,
> `persist_outputs=False`) and harness mode (files written to a temp vault, per-run DB provisioned).

## How to read this document

Per AUDIT_STANDARD Layer-2, every file gets: path · ext · empty? · what · **detailed WHY** (what
behavior/contract it guards, what regression it prevents) · **every test function** (name, scenario it
sets up, what it asserts, the decision/requirement it protects) · whether it needs a **live DB** vs is
**pure** · its census cross-ref. The shared fixtures (`client`, `db_session`, `seed_user`, `vault_root`,
`engine`, `database_url`, `seed_tenants`) and the **rolled-back-transaction isolation pattern** are
documented once, up front, since every integration test depends on them.

---

## 0. SCOPE RECONCILIATION vs FILE_CENSUS.md

`find` over the three directories + the named conftest yields exactly the files below; each is present
in `AS_BUILT/FILE_CENSUS.md` at the cited row. The `__pycache__/*.pyc` are compiled artifacts (not
owned source) and are excluded from the per-file audit as a vendored/generated tree, counted here as
**~30 `.pyc` files under `tests/api/__pycache__` and `tests/pilot/__pycache__`** (CPython bytecode for
the `.py` we audit — regenerated on every test run; never edited).

| census row | path | ext | bytes | empty? | audited below |
|---|---|---|---|---|---|
| 181 | `backend/tests/__init__.py` | py | 0 | **YES** | §1.1 |
| 214 | `backend/tests/conftest.py` | py | 2535 | no | §1.2 |
| 182 | `backend/tests/api/__init__.py` | py | 102 | no | §1.3 |
| 183 | `backend/tests/api/conftest.py` | py | 2605 | no | §1.4 |
| 185 | `backend/tests/api/test_auth.py` | py | 5996 | no | §2.1 |
| 188 | `backend/tests/api/test_cors.py` | py | 3637 | no | §2.2 |
| 192 | `backend/tests/api/test_runs.py` | py | 6294 | no | §2.3 |
| 186 | `backend/tests/api/test_bids.py` | py | 22619 | no | §2.4 |
| 184 | `backend/tests/api/test_alignment.py` | py | 17164 | no | §2.5 |
| 191 | `backend/tests/api/test_post_award.py` | py | 8776 | no | §2.6 |
| 187 | `backend/tests/api/test_comms.py` | py | 14092 | no | §2.7 |
| 189 | `backend/tests/api/test_downloads.py` | py | 5668 | no | §2.8 |
| 190 | `backend/tests/api/test_finalize.py` | py | 6171 | no | §2.9 |
| 193 | `backend/tests/api/test_strategy.py` | py | 4382 | no | §2.10 |
| 194 | `backend/tests/api/test_version_save.py` | py | 2856 | no | §2.11 |
| 233 | `backend/tests/pilot/__init__.py` | py | 98 | no | §3.1 |
| 235 | `backend/tests/pilot/test_pilot_cycle_e2e.py` | py | 26895 | no | §3.2 |
| 236 | `backend/tests/pilot/test_pilot_setup.py` | py | 13049 | no | §3.3 |
| 234 | `backend/tests/pilot/test_deliverables.py` | py | 7553 | no | §3.4 |
| 239 | `backend/tests/pilot/test_run_repo.py` | py | 7135 | no | §3.5 |
| 237 | `backend/tests/pilot/test_run_isolation.py` | py | 2284 | no | §3.6 |
| 238 | `backend/tests/pilot/test_run_persistence.py` | py | 2301 | no | §3.7 |
| 240 | `backend/tests/pilot/test_vault_autopush.py` | py | 3935 | no | §3.8 |

- **GAP-1 (scope vs reality).** The slice brief names `backend/tests/auth/**`. **No such directory
  exists.** The auth test surface lives at `backend/tests/api/test_auth.py` (§2.1), which IS audited
  here. There is no orphaned/missing `tests/auth/` tree — it was never created; auth was folded under
  `api/`. (`app/auth/` the package — `security.py`, `models.py`, `session.py` — is NOT a test path and
  is out of this slice's scope; it is tested *through* `test_auth.py` and `api/conftest.py`.)
- **Counts.** 18 test files + 4 dunder/conftest files = 22 owned `.py` in scope. **114 test functions**
  total (80 in `api/**`, 34 in `pilot/**`), plus 22 module-level/nested helper functions. Verified by
  `grep -cE '^def test_|^    def test_'` per file (see appendix table).
- **Marker registration.** `backend/pyproject.toml` `[tool.pytest.ini_options]` registers exactly one
  custom marker: `integration: tests that require a real Postgres database (deselect with -m 'not
  integration')`. `testpaths = ["tests"]`, `python_files = ["test_*.py"]`. So the suite splits cleanly:
  `pytest -m "not integration"` = PURE (no DB); `pytest` = full (needs `DATABASE_URL` → live Postgres).

---

## 1. SHARED FIXTURES, THE ROLLED-BACK-TRANSACTION PATTERN, AND THE PACKAGE MARKERS

### 1.0 The rolled-back-transaction isolation pattern (the spine of every DB test)

Every integration test in this slice obtains DB isolation **without truncating tables** via a
nested-connection/transaction-rollback pattern defined in `tests/conftest.py`:

1. **`engine` (session-scoped).** One SQLAlchemy `Engine` for the whole run, built from
   `get_settings().database_url`, `pool_pre_ping=True`. On creation it runs `SELECT 1`; **any**
   connection failure → `pytest.skip(...)` (NOT an error). This is the "green pure run on a box with
   no Postgres" guarantee — integration tests *skip*, they don't *fail*, when no DB is reachable.
2. **`db_session` (function-scoped).** For each test: open a fresh `connection`, `begin()` a
   transaction, bind a `Session(expire_on_commit=False)` to that connection, `yield` the session, and
   in `finally` **`session.close()` → `trans.rollback()` → `connection.close()`**. Every row the test
   (or the app code under test) wrote is rolled back at teardown. Tests therefore never see each
   other's data and the DB is left pristine — no per-test cleanup SQL, no truncation, no fixtures
   leaking across tests. `expire_on_commit=False` keeps ORM objects usable after the app's
   service-layer `commit()`s inside the same outer transaction.
3. **The `client` override (api/conftest).** `app.dependency_overrides[get_db]` is replaced with a
   generator that simply `yield`s the SAME `db_session`. So the FastAPI request handlers write to the
   exact transaction the test owns and rolls back — the HTTP surface and the test share one isolated
   session. The override deliberately **does NOT commit/close** (the `db_session` fixture owns the
   lifecycle); it is popped in `finally`.

This is the load-bearing pattern that lets the api tests drive multi-step governed flows
(create→setup→import→analyze→freeze→adjust→finalize) end-to-end while staying perfectly isolated.

### 1.1 `backend/tests/__init__.py` — ext `py` · **EMPTY (0 bytes)** · census 181
- **What.** An empty package marker for the `tests` package.
- **Detailed WHY it exists / why empty.** Pytest's `rootdir`/import model and the project's
  `from tests.pilot.test_pilot_cycle_e2e import ...` cross-imports (used by `test_bids.py`,
  `test_alignment.py`, `test_strategy.py`, etc.) require `tests`, `tests.api`, and `tests.pilot` to be
  importable packages. The file is empty because a package marker needs no code; its mere presence makes
  the directory a package so the sibling test modules can be imported by dotted path. **What breaks
  without it:** the cross-module helper imports (`from tests.pilot...`, `from tests.api...`) fail with
  `ModuleNotFoundError`, collapsing most of the `api/**` suite, which reuses the pilot synthetic builders.
- **DB?** Pure (no code).

### 1.2 `backend/tests/conftest.py` — ext `py` · 77 lines · census 214
- **What.** The root pytest fixture module: the integration DB plumbing shared by every DB test.
- **Detailed WHY.** Centralizes the "real Postgres, never SQLite" rule (PLAN §7, quoted in its
  docstring) and the rollback isolation so no individual test re-implements it. It is the single place
  that decides "skip vs run" for the whole integration suite. **What breaks without it:** every
  integration test loses `engine`/`db_session`/`seed_tenants`; the suite can't isolate or skip cleanly.
- **Fixtures defined (all the spine pieces):**
  - `database_url()` — *session scope*. Returns `get_settings().database_url`. The single source of the
    integration target; also consumed directly by `test_run_isolation.py` to decide skip-if-no-DB.
  - `engine(database_url)` — *session scope*. Builds the engine; `SELECT 1` probe → `pytest.skip` on any
    failure. **DB-gating fixture.**
  - `db_session(engine)` — *function scope*. The rolled-back-transaction session (see §1.0).
  - `seed_tenants(db_session)` — inserts two `ref.Client` tenants (A, B) with random unique
    `client_code`s, `flush`es, returns `{"a": id, "b": id}`. WHY: used by tenant-isolation tests
    (outside this slice — `tests/test_tenant_isolation.py`) but defined at root so it shares the same
    rolled-back session; randomized codes avoid UNIQUE collisions across repeated runs.
- **DB?** The fixtures are DB-touching; the module itself is imported for every run (pure import).

### 1.3 `backend/tests/api/__init__.py` — ext `py` · 1 line · census 182
- **What.** Package marker for `tests.api` with a one-line docstring: *"Tests for the REST API
  foundation (auth + runs) — FastAPI TestClient against a real Postgres."*
- **Detailed WHY.** Makes `tests.api` an importable package so `test_comms.py`/`test_downloads.py`/etc.
  can do `from tests.api.test_alignment import _seed_sealed_run, _login, _create_run`. **Breaks without
  it:** those intra-package helper imports fail.
- **DB?** Pure.

### 1.4 `backend/tests/api/conftest.py` — ext `py` · 69 lines · census 183
- **What.** The API-layer fixtures: a `TestClient` wired to the rolled-back session + a temp vault +
  a seeded console user. The bridge between the HTTP surface and the isolated DB.
- **Detailed WHY.** This is where the console's FastAPI app is connected to the test's transaction and
  to an empty per-test vault so the api tests can run governed flows in isolation and assert the
  no-server-side-storage contract. **Breaks without it:** the entire `api/**` suite has no client, no
  user to log in as, and no vault redirection (tests would hit the real vault root / real `get_db`).
- **Fixtures defined (the four named in the brief, fully documented):**
  - **`vault_root(tmp_path, monkeypatch)`** → `Path`. Creates `tmp_path/"vault"`, then
    `monkeypatch.setattr("app.api.v1.pilot_common._vault_root", lambda: root)`. WHY: the runs+bids
    routers resolve their `PilotService` vault through the shared, normally `lru_cache`d
    `pilot_common._vault_root`; redirecting it to a fresh temp dir per test means (a) tests never touch
    the real vault, and (b) the NFS tests can assert "no file was written under `vault_root/runs/<slug>`".
  - **`client(db_session)`** → `Iterator[TestClient]`. Overrides `get_db` to yield `db_session` (the
    shared rolled-back session); builds `TestClient(app, base_url="https://testserver")`. WHY the
    **https** base_url: the session cookie is `Secure`, and httpx withholds Secure cookies over plain
    http — so an http TestClient would silently drop the cookie and every authed follow-up would 401.
    Using `https://testserver` mirrors prod-behind-TLS so the cookie round-trips. The override is popped
    in `finally`. The override **does not commit** (the `db_session` fixture owns the txn lifecycle).
  - **`seed_user(db_session)`** → dict. Inserts an `AppUser` (`username="admin"`,
    `password_hash=hash_password("s3cret-pw")`, `is_active=True`, `totp_enabled=False`), `flush`es,
    returns `{"username","password","user"}`. WHY: a known active console user with a real argon2 hash
    so login tests exercise the genuine verify path; `totp_enabled=False` so the default login path is
    single-factor (the 2FA path is opted into per-test by setting `totp_secret`/`totp_enabled`).
- **DB?** `vault_root` is pure (filesystem + monkeypatch); `client`/`seed_user` are DB-touching.

---

## 2. `tests/api/**` — the REST API / auth surface (80 test functions across 11 files)

> All `api/**` integration tests share the same arc: `seed_user` + `client` (rolled-back session,
> https TestClient) + `vault_root` (empty temp vault). The `_login(client, seed_user)` helper posts
> valid creds and asserts 200 before the test's own assertions; many files import the alignment seed
> helpers (`_create_run`, `_seed_sealed_run`) to reach a sealed/frozen state through pure HTTP.

### 2.1 `backend/tests/api/test_auth.py` — 164 lines · census 185 · 8 test fns
- **What.** The login / session / 2FA contract over `/api/v1/auth/*` plus one pure password-hash unit
  test. Constants imported: `TWO_FACTOR_REQUIRED_DETAIL` (the distinct, UI-detectable 2FA-prompt
  string) and `SESSION_COOKIE_NAME`.
- **Detailed WHY.** Guards the *entire* authentication contract the console relies on: argon2 hashing,
  opaque 401s (no user enumeration), the distinct 2FA-required signal the UI branches on, the session
  cookie lifecycle (set on login, cleared on logout), and TOTP enroll→verify. A regression here would
  silently weaken auth (e.g. leaking whether a username exists, or accepting a login without 2FA).
- **Test functions:**
  1. **`test_password_hash_roundtrip()` — PURE (no DB).** Asserts `hash_password("correct-horse")`
     verifies the right password, rejects `"wrong"`, and `verify_password("anything","not-a-real-hash")`
     is `False` (a malformed stored hash never crashes/never accepts). Protects: argon2 round-trip +
     graceful-reject-of-garbage-hash, the bedrock of credential checking. **Needs no DB** — the only
     pure test in the file (the rest are `@integration`).
  2. **`test_login_success_sets_cookie(client, seed_user)` — INTEGRATION.** Posts correct
     username+password → asserts 200, body `user.username == "admin"`, `totp_enabled is False`, an `id`
     present, `SESSION_COOKIE_NAME in resp.cookies`; then `GET /me` returns the same user. Protects:
     the happy-path login issues a working session that `/me` honors.
  3. **`test_login_wrong_password_401(client, seed_user)` — INTEGRATION.** Wrong password → 401, NO
     cookie set, and `detail != TWO_FACTOR_REQUIRED_DETAIL`. Protects: a credential failure is a plain
     401 distinct from the 2FA prompt (the UI must not show "enter your code" for a bad password).
  4. **`test_login_unknown_user_401(client, seed_user)` — INTEGRATION.** Unknown username → the SAME
     opaque 401. Protects: **no user enumeration** — an attacker can't tell "wrong password" from "no
     such user".
  5. **`test_login_2fa_required_path(client, seed_user, db_session)` — INTEGRATION.** Enables TOTP on
     the seeded user (`pyotp.random_base32()`, `totp_enabled=True`, `flush`). Then: password-only →
     401 with `detail == TWO_FACTOR_REQUIRED_DETAIL`, no cookie; a wrong code `"000000"` → still the
     2FA-required 401; the valid current `pyotp.TOTP(secret).now()` → 200 + cookie + `totp_enabled True`.
     Protects: the three-state 2FA login (need-code / bad-code / good-code) and the distinct detail the
     UI keys on.
  6. **`test_me_requires_session_401(client)` — INTEGRATION.** `GET /me` with no cookie → 401.
     Protects: `/me` is authenticated (no anonymous identity leak).
  7. **`test_logout_clears_cookie(client, seed_user)` — INTEGRATION.** Login, then `POST /logout` → 204;
     a follow-up `GET /me` → 401. Protects: logout truly invalidates the session client-side.
  8. **`test_2fa_enroll_then_verify(client, seed_user)` — INTEGRATION.** Login, `POST /2fa/enroll` →
     200 with `secret` + an `otpauth://totp/...` URI containing the `KR RFP`/`KR%20RFP` issuer label;
     `POST /2fa/verify {code: TOTP(secret).now()}` → 200 with `totp_enabled True`. Protects: the
     enrollment ceremony issues a valid provisioning URI and a real code flips 2FA on.
- **DB?** 1 pure, 7 integration.

### 2.2 `backend/tests/api/test_cors.py` — 86 lines · census 188 · 4 test fns
- **What.** The CORS preflight + header-exposure contract for the cross-origin browser console. Builds
  the app straight from `create_app()` (no fixtures) since CORSMiddleware short-circuits before any
  route/DB.
- **Detailed WHY.** The Next.js console is a separate origin calling with credentials (the session
  cookie). The API must (a) answer preflights for configured origins, echoing the *exact* origin with
  credentials enabled, (b) refuse unknown origins (so the browser blocks them), (c) expose
  `Content-Disposition` cross-origin so the console can read download filenames, and (d) keep CORS
  headers even on a 500 so the console reads the real error instead of a misleading CORS failure. A
  regression here breaks the console's ability to talk to the API at all, or leaks the API to evil
  origins. **All four are PURE** (middleware-only, no DB).
- **Test functions (all PURE):**
  1. **`test_preflight_allows_configured_origin_with_credentials()`.** First asserts
     `http://localhost:3000 ∈ get_settings().cors_allow_origins` (so the test stays meaningful if the
     default changes), then `OPTIONS /api/v1/auth/login` with that Origin → 200,
     `access-control-allow-origin == that origin`, `allow-credentials == "true"`. Protects: the
     credentialed-CORS happy path for the real console origin.
  2. **`test_preflight_does_not_allow_unknown_origin()`.** Preflight with `Origin:
     https://evil.example.com` → NO `access-control-allow-origin` header. Protects: the allowlist truly
     gates — an unconfigured origin is rejected (browser blocks the call).
  3. **`test_actual_response_exposes_content_disposition()`.** An unauthenticated `GET
     /api/v1/auth/me` with the allowed Origin → carries `access-control-allow-origin` AND lists
     `content-disposition` in `access-control-expose-headers`. Protects: cross-origin download filename
     readability (run-file + zip downloads send the name on `Content-Disposition`).
  4. **`test_unexpected_500_carries_cors_for_allowed_origin()`.** Registers a throwaway `/api/v1/_boom`
     route that raises; `TestClient(..., raise_server_exceptions=False)` → 500 that STILL carries
     `access-control-allow-origin` + `allow-credentials`. Protects: the explicit header-echo in the
     catch-all 500 handler (which runs in `ServerErrorMiddleware`, *outside* CORSMiddleware) so the
     console sees the error, not a CORS wall.
- **DB?** All 4 pure.

### 2.3 `backend/tests/api/test_runs.py` — 166 lines · census 192 · 7 test fns
- **What.** The Runs API: the auth gate, create-then-list/read against a temp vault, rehearsal flagging,
  404 for unknown slug, and DB-resolved identity (a run as a `pilot.run` row with NO vault folder).
- **Detailed WHY.** Encodes ADR-0018 (run identity is the DB row, NOT the vault folder) and the
  no-server-side-storage contract: a console-created run scaffolds NO folder. Every test (except the
  401 gate) logs in first. Guards: auth on every runs route; the RunDetail/RunSummary shapes (incl. the
  4-bucket kanban); rehearsal marking; and the two "folderless run" behaviors Slices 3/6 introduced.
- **Test functions (all INTEGRATION):**
  1. **`test_runs_requires_auth(client, vault_root)`.** `GET /runs` no session → 401. Protects: every
     runs route is authenticated.
  2. **`test_runs_list_empty_when_authed(client, seed_user, vault_root)`.** Login → `GET /runs` → 200
     and `== []`. Protects: an authed user with an empty vault gets an empty list (not an error).
  3. **`test_create_run_then_appears_in_list(client, seed_user, vault_root)`.** `POST /runs
     {commodity:"Field Tomatoes", label:"Console E2E", rehearsal:false}` → 201 RunDetail; asserts
     `commodity`/`label`/`rehearsal`, a non-empty `stage`, and the full kanban `{Done,Doing,Next,Waiting
     on you}` with `"Run folder created" ∈ Done`; then the run lists as a RunSummary and reads back by
     slug (`kanban` present). Protects: the create→list→read identity round-trip + the canonical kanban
     shape the UI renders.
  4. **`test_create_rehearsal_run_marks_synthetic(client, seed_user, vault_root)`.** `rehearsal:true` →
     `rehearsal is True` in both the create detail and the list summary. Protects: rehearsal runs are
     flagged synthetic everywhere (the dress-rehearsal "looked live" finding).
  5. **`test_get_unknown_run_404(client, seed_user, vault_root)`.** Unknown slug → 404 (not 500 / empty
     detail). Protects: clean not-found semantics.
  6. **`test_run_resolves_from_db_with_no_folder(client, seed_user, vault_root, db_session)`.** Inserts
     a `pilot.run` row directly via `create_run_record(...)` (empty temp vault, no folder) → the run
     LISTS (`has_cycle is False`) and READS BACK by slug with the full kanban — entirely from the DB
     row. Protects: **Slice 3** DB-resolved identity — the console surfaces a run with no vault folder.
  7. **`test_created_run_scaffolds_no_vault_folder(client, seed_user, vault_root, db_session)`.**
     `POST /runs` → asserts `not (vault_root/"runs"/slug).exists()` yet the run lists + reads back.
     Protects: **Slice 6 / ADR-0018 / CLAUDE.md req #4** — a console-created run writes NO folder; its
     identity is the `pilot.run` row only.
- **DB?** All 7 integration.

### 2.4 `backend/tests/api/test_bids.py` — 540 lines · census 186 · 17 test fns
- **What.** The bids + run-input-chain surface: auth gates; the full input chain end-to-end
  (create→download setup→ingest setup→generate template→strict import→list bids); the flexible
  propose/confirm path; the run-archive zip; the no-server-side-storage proof across the whole chain;
  cross-run isolation; and a battery of guard branches (path traversal, unknown run, gate-before-setup,
  out-of-range round, second-setup conflict, bad mode). Reuses the pilot synthetic builders
  (`_build_filled_setup`, `_fill_bid_template`) so the routes exercise the REAL ingest path.
- **Detailed WHY.** This is the heart of the buyer's intake loop and the strictest test of the
  data-fidelity + no-storage + isolation contracts. It proves: uploads stream to ingest (nothing on
  disk), the strict path is key-validated, the flexible path proposes without writing then confirms via
  the strict path, two parallel runs in one shared DB never cross-contaminate (cycle/round scoping), and
  every error is a clean problem-detail (gate_required / validation_error / conflict / 404 / 422), never
  a 500. `_disk_files()`/`_cycle_id()` helpers assert the on-disk emptiness and DB identity.
- **Helpers:** `_login`, `_create_run`, `_ingest_setup` (asserts cycle_id + kanban), `_generate_template`,
  `_build_messy_supplier_file(view)` (a supplier's own messy sheet — odd headers, shuffled, no keys, 8
  priced rows), `_disk_files(vault_root, slug)`, `_cycle_id(db_session, slug)`, `_import_round1`.
- **Test functions:**
  - **auth gates (INTEGRATION):**
    1. **`test_bids_import_requires_auth`** — `POST /bids/import` no session → 401.
    2. **`test_bids_list_requires_auth`** — `GET /bids` no session → 401.
    3. **`test_run_files_requires_auth`** — `GET /runs/{slug}/files` no session → 401.
       Protects: every bids/files route is authenticated.
  - **the full input chain (INTEGRATION):**
    4. **`test_input_chain_e2e(client, seed_user, vault_root)`.** create → `GET /files` (the created run
       carries the setup workbook in inputs/, all `kind ∈ {input,output}`, all `size_bytes>0`) →
       download the setup (xlsx content-type, `attachment` + name in Content-Disposition, payload starts
       `PK`) → ingest filled setup → generate Round-1 template (name == `02_round1_bid_template.xlsx`,
       lists + downloads) → fill + strict import → asserts `ingested == 8` (2 DCs×2 lots×1 TF×2
       suppliers) + the 4-bucket kanban → `GET /bids` returns 8 rows at the identity grain, each
       carrying the reviewer columns (`bid_line_id, supplier_id, dc_id, lot_id, item_id, tf_id,
       currency_code, submitted_all_in_case, fob_case, volume_minimum_cases, validity_status,
       is_scoreable, is_awardable`), `currency_code=="USD"`, `is_scoreable is True`,
       `submitted_all_in_case is not None`. Protects: the WHOLE intake chain end-to-end + the exact
       8-row identity-grain output and its reviewer-facing schema (data fidelity, CLAUDE.md req #3).
  - **flexible propose/confirm (INTEGRATION):**
    5. **`test_flexible_propose_then_confirm(client, seed_user, vault_root, db_session)`.** Builds a
       messy supplier sheet against the persisted cycle's known names (via `load_cycle(db_session,
       cycle_id)`). `confirm=false` → a `proposal` (`is_confident True`, `header_row==2`, mappings ⊇
       `{supplier,dc,lot,all_in,volume}`, `mappings.dc.confidence=="high"`, a `summary`) and asserts NO
       new file written + `GET /bids == []` (nothing ingested). `confirm=true` → `ingested == 8` and the
       list now has 8. Protects: flexible inference proposes without side-effects, then confirm ingests
       via the strict key-validated path (D-flex behavior; no silent writes on a proposal).
    6. **`test_flexible_propose_failure_cleans_scratch(client, seed_user, vault_root)`.** Posts garbage
       bytes as a "workbook"; wraps the call in `contextlib.suppress(Exception)`; asserts the file set
       is unchanged and no `raw_supplier_drop` orphan remains. Protects: the route's `try/finally`
       removes the temp scratch upload even when inference RAISES — no orphan temp files leak into
       inputs/ on every failed drop.
  - **archive (INTEGRATION):**
    7. **`test_download_run_archive_zip(client, seed_user, vault_root)`.** `GET /runs/{slug}/archive` →
       `application/zip`, `{slug}.zip` in Content-Disposition; the zip namelist is EXACTLY
       `[f"{slug}/01_setup_kickoff.xlsx"]` for a fresh run and the entry bytes start `PK`. Protects:
       **Slice 5** — the archive is a projection of `enumerate_deliverables` (rendered on request), NOT a
       scan of the vault folder; a fresh run carries exactly the setup book.
  - **no-server-side-storage across the chain (INTEGRATION):**
    8. **`test_uploads_leave_no_file_on_disk(client, seed_user, vault_root, db_session)`.** Drives
       create → ingest setup (upload) → generate template → strict import (upload) → flexible confirm
       (upload + normalized template) and asserts `_disk_files(vault_root, slug) == set()` at EVERY step.
       Protects: **Slice 4+6 / ADR-0018 / CLAUDE.md req #4** — the entire intake chain writes NOTHING to
       the run's vault folder; the run is a `pilot.run` row only. (The single most direct test of the
       no-server-side-storage requirement.)
  - **cross-run isolation (INTEGRATION):**
    9. **`test_two_runs_do_not_cross_contaminate(client, seed_user, vault_root)`.** Two runs each ingest
       the same synthetic 8 bids in ONE shared DB (`isolate_db=False`); asserts each lists exactly 8
       (never 16) and `ids_a.isdisjoint(ids_b)`. Protects: isolation by scoping every bid query to the
       run's own `cycle_id+round_id` — a scoping regression would surface as 16 rows or overlapping ids.
       (Directly guards the shared-DB-but-isolated guarantee the web console depends on.)
  - **guards / error branches (INTEGRATION):**
    10. **`test_download_path_traversal_refused`** — encoded traversal names (`..%2f..%2fconftest.py`,
        `%2e%2e%2f...NOTES.md`, `nope.xlsx`) → 404 each, never a read above the run folder. Protects:
        path-traversal safety (only exact deliverable names match).
    11. **`test_unknown_run_404_everywhere`** — an unknown slug → 404 on files, file-download, setup,
        template, import, and list. Protects: uniform not-found across the bids/runs surface.
    12. **`test_template_before_setup_is_gated`** — template before setup → 400 `code=="gate_required"`.
        Protects: the gate is a clean problem-detail, not a 500.
    13. **`test_import_before_setup_is_gated`** — import before a cycle exists → 400 `gate_required`.
    14. **`test_run_has_cycle_flips_after_setup`** — `has_cycle` false on a fresh run, true after ingest.
        Protects: the durable post-setup signal the intake UI gates on (Codex P2) — a returning user who
        ingested setup but not a template keeps the later steps unlocked without re-uploading.
    15. **`test_template_out_of_range_round_is_validation_error`** — after setup, round 99 → 400
        `validation_error` (NOT gate_required). Protects: the Codex P2 fix — an out-of-range round must
        not wrongly tell the user to redo setup; the round is pre-validated.
    16. **`test_second_setup_post_is_conflict`** — a 2nd `POST /setup` on a run that already has a cycle →
        409 `code=="conflict"`. Protects: setup is once-per-run; the prior cycle is never silently
        orphaned by a re-pointed `cycle_id.txt`.
    17. **`test_import_bad_mode_is_422`** — `mode:"bogus"` → 422 (request validation) before any work.
        Protects: unknown modes fail at the schema boundary.
- **DB?** All 17 integration.

### 2.5 `backend/tests/api/test_alignment.py` — 400 lines · census 184 · 11 test fns
- **What.** The web alignment / scenario-slice surface (PLAN §5) — "which lens" decision + the read
  layer. The full path (analysis → list → 7-lens compare with B recommended → B detail with per-cell
  suppliers → freeze B), gate/error paths, and a **consistency** test that the web read layer matches
  the Excel workbook's gather. It is the source of the canonical seed helpers reused across the slice.
- **Detailed WHY.** This is the buyer's decision surface and the strongest guard of "the web can never
  diverge from the Excel" (CLAUDE.md req #2/#3 — auditability + data fidelity). Freeze is a governed,
  immutable decision; the tests prove a typo'd scenario writes nothing, the FROZEN audit event lands,
  and the seven lenses + per-cell min/recommended flags are exactly right.
- **Shared seed helpers (exported, reused by 6 other api files):** `_login`, `_create_run`,
  **`_seed_sealed_run(client, slug)`** = create→ingest setup→template→strict import (asserts 8)→`POST
  /rounds/1/analysis` → returns `analysis_run_id`. `_XLSX` mimetype constant.
- **Test functions:**
  1. **`test_analysis_routes_require_auth(client, vault_root)` — INTEGRATION.** Each of `POST .../analysis`,
     `GET .../analysis`, `GET .../analysis/run-1/scenarios`, `GET .../scenarios/B`, `POST .../awards/freeze`
     with no session → 401. Protects: every alignment route is authenticated.
  2. **`test_alignment_full_path_e2e(client, seed_user, vault_root)` — INTEGRATION.** Seeds a sealed run,
     then a 2nd analysis → `version==2`, `round_number==1`, `scenario_count==7`, `sealed_at`, an `.xlsx`
     filename. `GET /analysis` lists both oldest-first `[1,2]` with engine_version. `GET /scenarios` →
     exactly `[A,B,C,D,E,F,G]`, exactly `[B]` recommended; every lens carries
     `{code,label,description,total_spend,delta_vs_a,savings_vs_incumbent_pct,savings_vs_stly_pct,
     supplier_count,cell_count,cap_breach_count}` with `total_spend>0` and `cell_count==4`; lens A has
     `delta_vs_a==0.0`. `GET /scenarios/B` → per-cell: each cell names dc/lot/tf + incumbent, has
     suppliers, exactly one `is_min`, exactly one `is_recommended` (single-winner B) with
     `volume_share>0`, the `recommended.supplier` matches that pick and carries a `rec_type`, and
     `min_price == min(supplier prices)`. `POST /awards/freeze {B}` → an `award_id`, `scenario_code=="B"`.
     Protects: the whole alignment decision surface AND the per-cell min/recommended/min_price invariants.
  3. **`test_freeze_emits_frozen_audit_event(client, seed_user, vault_root, db_session)` — INTEGRATION.**
     Freezes B, then SQL-counts `audit.event_log` for `event_type='FROZEN', entity_type='awd.award',
     entity_id=award_id` → exactly 1. Protects: freezing through HTTP lands the governed FROZEN audit
     event (auditability, CLAUDE.md req #2).
  4. **`test_freeze_unknown_scenario_rejected_and_writes_nothing(...)` — INTEGRATION.** Freeze scenario
     `"Z"` → 400 `validation_error`; SQL-asserts `awd.award` count for that code == 0. Protects: the
     Codex P2 fix — the scenario's rows are read BEFORE any write, so a typo can't leave a bogus
     zero-line FROZEN (immutable!) award or a spurious FROZEN event.
  5. **`test_analysis_before_setup_is_gated`** — `POST .../analysis` before setup → 400 `gate_required`.
  6. **`test_scenarios_before_any_sealed_run_is_gated`** — scenario read before any sealed run → 400
     `gate_required` (not a 500/empty list).
  7. **`test_list_analysis_is_empty_before_seal`** — `GET /analysis` before any seal → 200 `[]` (the LIST
     is never a gate). Protects: list-vs-read gating asymmetry is intentional.
  8. **`test_unknown_run_404_on_alignment_routes`** — unknown slug → 404 on every alignment route.
  9. **`test_unknown_analysis_run_404`** — real run, unknown `analysis_run_id` → 404 (never another run's
     analysis). Protects: analysis reads are scoped to the run's cycle.
  10. **`test_unknown_scenario_code_is_validation_error`** — valid sealed run, lens `"Z"` → 400
      `validation_error`. Protects: unknown lens code is a clean validation error, not a 404/500.
  11. **`test_read_layer_matches_workbook_gather(tmp_path, db_session)` — INTEGRATION.** Drives a run
      directly through `PilotService(tmp_path, isolate_db=False)` (start→ingest setup→template→
      ingest_bids→run_round), then calls the workbook's `_gather_scenario_rollups(...)` DIRECTLY (ground
      truth) and the web read layer's `scenario_comparison(...)`, asserting per lens A–G that
      `total_spend`, `delta_vs_a`, `savings_vs_incumbent_pct` (== gather `savings_vs_baseline_frac`),
      `savings_vs_stly_pct` (== `savings_vs_stly_frac`), `supplier_count`, `cell_count`,
      `cap_breach_count` all match (via `pytest.approx`). Protects: **the web read layer can never
      diverge from the Excel** — the single most important data-fidelity/auditability guard in the slice.
      (Note: this test uses `db_session` directly without `client`/`seed_user` — it bypasses HTTP to
      compare the two computation paths.)
- **DB?** All 11 integration.

### 2.6 `backend/tests/api/test_post_award.py` — 237 lines · census 191 · 6 test fns
- **What.** The post-award surface: read a frozen award (list + detail) and record append-only
  adjustment LAYERS, with scope/cell validation, the layered effective price, and the CREATED audit
  event. Defines the `_freeze_b(...)` helper reused by comms/finalize/downloads tests; `_VALID_CHANGE`
  is a syntactically-valid but off-award cell payload.
- **Detailed WHY.** Encodes the append-only, governed post-award model (E-?? / D-post-award): a frozen
  award is immutable; price changes are NEW layers, each a governed decision with an audit event;
  invalid changes (off-award cell, duplicate cell, empty changes, unknown award) write NOTHING. Guards
  the actor attribution (the authenticated user, not a "pilot" default).
- **Test functions (all INTEGRATION):**
  1. **`test_award_routes_require_auth(client, vault_root)`.** `GET /awards`, `GET /awards/a-1`, and
     `POST /awards/a-1/adjustments` (valid body) with no session → 401. Protects: every award route is
     authenticated (valid body so the only failure is auth).
  2. **`test_award_read_and_adjustment_e2e(client, seed_user, vault_root, db_session)`.** Pre-freeze
     `GET /awards == []` (never a gate). Freeze B → list shows one award (`latest_version==0`,
     `line_count>0`); detail lines carry both cell-key ids and names (`dc_id,lot_id,tf_id,supplier_id,
     dc,supplier`), all `delta==0`, `versions==[0]`, `frozen_by == "admin"`, `versions[0].created_by ==
     "admin"`. Record a +$5 `MARKET_HIKE` on the first cell → `version_no==1`, `.xlsx` filename. Re-read:
     exactly one line has `delta!=0`, its `effective_price ≈ new_price`, `versions==[0,1]`,
     `latest_version==1`, `versions[1].created_by=="admin"`. SQL-asserts exactly 1 CREATED
     `audit.event_log` for `awd.award_adjustment`. Protects: the full read+layer lifecycle, the layered
     effective price, the authenticated-actor attribution, and the governed CREATED event.
  3. **`test_adjustment_unknown_cell_is_validation_error(...)`.** A change with off-award ids
     (`_VALID_CHANGE`) → 400 `validation_error`; SQL-asserts `awd.award_adjustment` count == 0.
     Protects: an off-award cell writes NO layer.
  4. **`test_adjustment_duplicate_cell_is_validation_error(...)`.** Same cell twice in one layer → 400
     `validation_error`; count == 0. Protects: one DB line per cell; a duplicate writes nothing.
  5. **`test_adjustment_unknown_award_404(...)`.** Real run+cycle, unknown award id → 404. Protects:
     adjustments scoped to the run's cycle.
  6. **`test_adjustment_empty_changes_rejected(...)`.** `changes: []` → 422 (request validation).
     Protects: an empty layer is rejected at the schema boundary.
- **DB?** All 6 integration.

### 2.7 `backend/tests/api/test_comms.py` — 303 lines · census 187 · 12 test fns
- **What.** Supplier comms (E-37): award-notification, round-feedback, and rejection email DRAFTS over
  HTTP — one template-merge draft per relevant supplier, draft-only (no send). Reuses the alignment
  seed helpers + `_freeze_b`. Defines `_fill_bid_template_bumped(...)` to resubmit a round at higher
  prices (exercising the supersede / sealed-run-sourcing path).
- **Detailed WHY.** Comms are merged from GOVERNED data, so the tests guard: every placeholder token is
  filled (no visible `[#...]` holes), the machine-routing subject tags (`[RFP:`, `[SUP:`), the
  authenticated user as the draft's buyer (with `BuyerTitle` left for the buyer to complete), and — the
  subtle one — that each draft attaches the supplier's OWN award-id-stamped guide and that a SEALED
  run's feedback draft is byte-for-byte stable even after a later resubmission. These guard real
  regressions Codex flagged (a fixed-name guide overwritten per freeze; drafts re-reading current rows).
- **Helper:** `_fill_bid_template_bumped(template_bytes, bump)` — refills the round template like the
  e2e seed but adds `bump` to every All-In/FOB price (so a resubmission materially differs and supersedes).
- **Test functions (all INTEGRATION):**
  1. **`test_award_comms_requires_auth`** — `GET /awards/a-1/comms/award` no session → 401.
  2. **`test_award_comms_drafts_one_per_awarded_supplier(...)`.** Freeze B → ≥1 award draft;
     each: `email_type=="Award Notification"`; subject starts `[RFP:`, contains `[SUP:` + `Award
     Notification –`; body has `Dear {supplier},` + `selected for award` + `Awarded Locations:`; no
     `[#AwardedDCCount]`/`[#AwardedLotCount]`/`[#AwardFileName]` holes; `AwardFileName ∉ missing`; body
     references `award_guide` (the supplier's OWN guide) and NOT `supplier_guides` (the combined book,
     which would leak every supplier's awards); the authed `username` appears in the body; `BuyerTitle
     ∈ missing`. Protects: data-filled, leak-free, correctly-attributed award drafts.
  3. **`test_award_comms_guide_is_not_stale_across_awards(...)`.** Freeze B (`AWD-B`) then A (`AWD-A`);
     award-B drafts reference the EARLIER award's stamped guide (`awd_b`) and never `awd_a`. Protects:
     the per-award, award-code-stamped guide — a 2nd freeze can't shadow the 1st award's files (the
     fixed-name-overwrite regression).
  4. **`test_award_comms_guide_unique_when_award_codes_collide(...)`.** Two awards sharing award_code
     `DUP-CODE` get distinct guides keyed by the unique `award_id` (slugified) — B's drafts reference
     B's id, never A's. Protects: filename uniqueness via the PK even when human award codes collide.
  5. **`test_award_comms_unknown_award_404`** — unknown award → 404.
  6. **`test_feedback_comms_requires_auth`** — `GET /analysis/run-1/comms/feedback` no session → 401.
  7. **`test_feedback_comms_drafts_above_benchmark_suppliers(...)`.** A sealed round → ≥1 round-feedback
     draft per above-benchmark supplier; each: `email_type=="Round Feedback"`; subject `[RFP:`/`[SUP:`/
     `Feedback –`, no `[#RoundNumber]`; body has `Dear {supplier},` + the three sections (`DC Summary`,
     `Items Requiring Action`, `Additional Improvement Opportunities`); all table tokens
     (`[#DCSummaryTable]`/`[#HardAskTable]`/`[#SoftAskTable]`) expanded; authed user present;
     `BuyerTitle ∈ missing`. Protects: every supplier above the market-low gets a fully-merged feedback
     draft (the synthetic seed splits lots so both suppliers qualify on their weaker lot).
  8. **`test_feedback_comms_unknown_run_404`** — unknown analysis run → 404.
  9. **`test_feedback_comms_sealed_after_resubmit(...)`.** Capture the sealed run's feedback drafts;
     resubmit round 1 at +$5.00 (supersedes the scored rows); re-fetch → `after == before` (byte-for-byte
     unchanged). Protects: the **sealed-run sourcing fix** — the draft reads the SEALED run's own
     `bid_score`→`bid_line` rows, so a later resubmission can't move its benchmarks/premiums.
  10. **`test_rejection_comms_requires_auth`** — `GET /awards/a-1/comms/rejection` no session → 401.
  11. **`test_rejection_comms_drafts_per_lost_lot(...)`.** Freeze B → ≥1 non-selection draft per
      supplier with a lost lot; each: `email_type=="RFP Results"`; subject `[RFP:`/`[SUP:`/`RFP Results
      –`; body `Dear {supplier},` + `not selected for award` + `Evaluation Summary`; the
      `[#RejectionReasonTable]` expanded with `Benchmark Price`; authed user present; `BuyerTitle ∈
      missing`. Protects: each supplier's lost lots are itemized (price, market-low benchmark, % gap,
      reason) with no visible holes.
  12. **`test_rejection_comms_unknown_award_404`** — unknown award → 404.
- **DB?** All 12 integration.

### 2.8 `backend/tests/api/test_downloads.py` — 137 lines · census 190 · 1 test fn
- **What.** The download endpoints (`/files`, `/files/{name}`, `/archive`) render on request from the
  DB with an EMPTY vault `outputs/` (NFS Slice 5). Reuses the alignment seed helpers. Helpers:
  `_sheet_data(data)` (every sheet's cell values — the data-identity basis, E-39), `_outputs_files(...)`
  (what's actually on disk), `_cycle(...)`.
- **Detailed WHY.** Proves CLAUDE.md req #4 end-to-end for downloads: the console persists no generated
  files (ADR-0018) — analysis/freeze/record-adjustment do governed DB writes ONLY, and the download
  endpoints are projections of `enumerate_deliverables` rendered on request. The render must be
  DATA-identical to a direct registry render (date-stamped provenance lines differ across days, so the
  comparison is on cell DATA, not raw bytes — E-39).
- **Test function (INTEGRATION):**
  1. **`test_downloads_render_from_db_with_empty_outputs(client, seed_user, vault_root, db_session)`.**
     Seeds a sealed run, freezes B, records one `MARKET_HIKE` post-award layer; asserts `outputs/` stays
     EMPTY. `GET /files` lists the normalized names: `01_setup_kickoff.xlsx`,
     `04_round1_alignment_v1.xlsx`, `08_award_booking_guide.xlsx`, `08_award_supplier_guides.xlsx`,
     `09_post_award_v1.xlsx` (all `size_bytes>0`). For three sampled deliverables, `GET /files/{name}`
     → 200, xlsx content-type, name in Content-Disposition, and `_sheet_data(resp) ==
     _sheet_data(registry.render(db_session))` (DATA-identical). Unknown name → 404. `GET /archive` zips
     every deliverable under `{slug}/...`, each a real `PK` xlsx; `outputs/` still empty. Protects: the
     whole render-on-request download surface, the empty-outputs invariant, and data-identity to the
     registry ground truth.
- **DB?** 1 integration (the other 3 defs are pure helpers).

### 2.9 `backend/tests/api/test_finalize.py` — 148 lines · census 190 · 6 test fns
> (Census cross-ref verified against FILE_CENSUS.md: `test_downloads.py` = row 189, `test_finalize.py`
> = row 190; both match the §0 reconciliation table.)
- **What.** The run's terminal governed close-out (`POST /runs/{slug}/finalize`). Reuses the alignment
  seed helpers + `_freeze_b`. Helper `_closed_event_count(db_session, cycle_id)` counts CLOSED audit
  events for the cycle.
- **Detailed WHY.** Finalize is the design's "Finalize & close run" step — a governed, idempotent,
  audited close-out. It guards: finalize-after-freeze CLOSES the run and emits EXACTLY ONE CLOSED event
  (entity = the cycle, actor = the authed user) and surfaces won/not-won notice counts that EQUAL the
  drafts the console renders; finalize without a frozen award is refused (409, no CLOSED event);
  re-finalize is idempotent (same summary, no 2nd event); unknown run → 404.
- **Test functions (all INTEGRATION):**
  1. **`test_finalize_requires_auth`** — `POST /x/finalize` no session → 401.
  2. **`test_finalize_unknown_run_404`** — unknown run → 404 `code=="not_found"`.
  3. **`test_finalize_without_frozen_award_is_conflict(...)`.** Sealed analysis, nothing frozen →
     finalize → 409 `conflict`; SQL-asserts 0 CLOSED events. Protects: can't close out without a frozen
     award.
  4. **`test_finalize_before_setup_is_conflict`** — no cycle yet → finalize → 409 `conflict` (not 500).
  5. **`test_finalize_after_freeze_closes_and_surfaces_notices(...)`.** Freeze B; assert 0 CLOSED events
     pre-finalize; finalize → 200 `closed True`, `award_id` matches, `won_suppliers>=1` &
     `not_won_suppliers>=1`. The summary counts EQUAL `len(award comms)` and `len(rejection comms)`. SQL-
     asserts exactly 1 CLOSED `cyc.cycle` event with `actor == "admin"`. Protects: the governed,
     attributed, in-txn close-out and the notice-count consistency with the rendered drafts.
  6. **`test_finalize_is_idempotent(...)`.** Finalize twice → both 200, `second.json()==first.json()`,
     `award_id` stable, still exactly 1 CLOSED event. Protects: re-finalize is a clean no-op; the audit
     chain isn't forked.
- **DB?** All 6 integration.

### 2.10 `backend/tests/api/test_strategy.py` — 116 lines · census 193 · 4 test fns
- **What.** The strategy panel: GET/PUT the run's engine strategy (the named weight preset + the four
  engine safeties), persisted onto `cyc.cycle`. Reuses the alignment `_login`/`_create_run` + the pilot
  `_build_filled_setup`. `_FULL` is a complete valid payload; `_ingest_setup` reaches a cycle.
- **Detailed WHY.** Persists the SAME fields the setup workbook seeds and that `run_round` layers over
  the default config — so a strategy set here is exactly what the next analysis runs under (no new
  store, no engine change). Guards: auth; the gate before a cycle exists; the GET→PUT→GET round-trip
  persisting; preset remap (price_focus weights) echoed in the response; and input validation
  (unknown preset → 400 validation_error; out-of-range safety → 422 schema bound).
- **Test functions (all INTEGRATION):**
  1. **`test_strategy_requires_auth`** — GET + PUT `/x/strategy` no session → 401.
  2. **`test_strategy_gate_before_cycle`** — GET strategy before a cycle → 400 `gate_required`.
  3. **`test_strategy_get_then_set_roundtrips(...)`.** GET → the effective strategy contains
     `{weight_preset,weight_price,premium_ceiling,coverage_floor,conc_thresh,max_sup_dc}`, `max_sup_dc>=1`,
     each of the three fractional safeties in `(0,1]`. PUT `price_focus` + new safeties → echoes
     `weight_preset=="price_focus"`, `weight_price ≈ PRESET_WEIGHTS[price_focus].weight_price`,
     `coverage_floor≈0.75`, `max_sup_dc==3`. A fresh GET persists those (`premium_ceiling≈0.10`,
     `max_sup_dc==3`). Protects: GET/PUT round-trip, preset→weight remap, persistence onto `cyc.cycle`.
  4. **`test_strategy_rejects_bad_input(...)`.** Unknown preset `"bogus"` → 400 `validation_error`;
     `coverage_floor:"1.5"` → 422 (schema bound). Protects: bad strategy is rejected at the right layer.
- **DB?** All 4 integration.

### 2.11 `backend/tests/api/test_version_save.py` — 68 lines · census 194 · 4 test fns
- **What.** The version-savepoint surface (E-43): name a sealed alignment version via `PATCH
  /runs/{slug}/analysis/{id}` (sets `eng.analysis_run.label`). Reuses the alignment seed helpers.
- **Detailed WHY.** Encodes the deliberate decoupling of "name a version" (a lightweight savepoint —
  NO audit event, NO award) from "freeze" (the only governed seal). Guards that naming does NOT freeze,
  the name shows in the list, and the validation bounds (empty → 422 by Pydantic min_length;
  whitespace-only → 400 validation_error after the service strips it).
- **Test functions (all INTEGRATION):**
  1. **`test_name_version_requires_auth`** — `PATCH /x/analysis/y` no session → 401.
  2. **`test_name_version_sets_label_without_freezing(...)`.** Seal a run; PATCH label "Balanced
     baseline" → 200, body `{analysis_run_id, label, version==1}`; the list reflects the name; `GET
     /awards == []` (naming did NOT freeze). Protects: savepoint ≠ governed seal.
  3. **`test_name_version_unknown_run_is_404`** — unknown analysis run → 404 `not_found`.
  4. **`test_name_version_rejects_empty(...)`.** `label:""` → 422 (Pydantic min_length=1);
     `label:"   "` → 400 `validation_error` (service strips whitespace). Protects: the two-layer
     validation (schema bound vs service rule).
- **DB?** All 4 integration.

---

## 3. `tests/pilot/**` — the pilot orchestration core (34 test functions across 7 files)

> These drive `PilotService` directly (no HTTP) with SYNTHETIC data (clean-room, ADR-0001). They guard
> the full cycle loop, the setup template/ingest round-trip, the DB-backed run identity (ADR-0018), the
> deliverable registry parity, per-run DB isolation (D30), vault-carried DB persistence, and vault
> auto-push (D34). `pytestmark = pytest.mark.integration` at module level marks whole files; otherwise
> per-function `@pytest.mark.integration`. The synthetic builders here are the single source of truth
> reused by the api tests.

### 3.1 `backend/tests/pilot/__init__.py` — ext `py` · 1 line · census 233
- **What.** Package marker for `tests.pilot` with docstring *"Tests for the pilot core (`app.pilot`) —
  synthetic data only, real Postgres for DB paths."*
- **Detailed WHY.** Makes `tests.pilot` importable so the api tests can `from
  tests.pilot.test_pilot_cycle_e2e import _build_filled_setup, _fill_bid_template, _first_award_cell,
  _latest_run_id`. **Breaks without it:** those cross-package imports (the synthetic-builder reuse the
  whole api suite depends on) fail. **DB?** Pure.

### 3.2 `backend/tests/pilot/test_pilot_cycle_e2e.py` — 574 lines · census 235 · 11 test fns
- **What.** PART B — the WHOLE cycle loop end-to-end through `PilotService`, on a real Postgres. Also
  the canonical home of the synthetic builders (aliased from `app.pilot.synthetic`:
  `_build_filled_setup = build_filled_setup`, `_fill_bid_template = fill_bid_template`) and the DB
  helpers `_latest_run_id`, `_first_award_cell` reused across the slice. Plus a pure inference unit test.
- **Detailed WHY.** The single most comprehensive guard of the decision-support loop and the
  data-fidelity contract (CLAUDE.md req #1/#3). It proves: setup ingest → governed cycle (right counts),
  template gen → normalized filename, bid ingest → 8 priced cells, the OPTION-B flat-13 period fan-out
  (8 logical cells × 4 fiscal periods = 32 storage rows) with supersede partitioning (latest scoreable,
  prior superseded — never deleted, never double-counted), run_round → scored cells + in-file version
  headings + LIVE/SYNTHETIC provenance stamping, freeze → booking guides, post-award adjustment →
  layered doc, history/run_data.json snapshot (names not keys, D23), FEEDBACK.md distillation, and the
  close-out zip + purge. The synthetic scope is deliberately the platform minimum (2 rounds — the
  `cyc.cycle` round_count CHECK requires 2..6).
- **Helpers:** `_fake_cycle_view()` (a tiny in-memory `CycleView` with known names — no DB),
  `_all_cell_text(path)` (every string cell joined — for provenance assertions),
  `_build_messy_supplier_file(view)`, `_latest_run_id(db_session, cycle_id)`,
  `_first_award_cell(db_session, award_id)`.
- **Test functions:**
  1. **`test_infer_bid_mapping_on_messy_sheet()` — PURE (no DB).** Builds a messy supplier sheet (title
     band + odd headers `Warehouse/Vendor/Product/Delivered Price/Cases per Week` in a different order)
     and asserts `infer_bid_mapping(bytes, _fake_cycle_view())` finds `header_row==2`, maps each field
     to the right source header, and locks DC + supplier by VALUE match against the cycle's known names
     (`confidence=="high"`, `is_confident`). Protects: the flexible-ingest column inference (D-flex) —
     a supplier's own format maps correctly without keys. **The only pure test here.**
  2. **`test_resubmission_supersedes_prior(tmp_path, db_session)` — INTEGRATION.** Ingests round-1 bids
     twice (a corrected re-send); asserts `ingested==8` both times, then SQL-asserts the period fan-out:
     `scoreable == 8*4`, `superseded == 8*4`, distinct identity cells (`supplier,dc,lot,item,tf`) == 8;
     "superseded" appears in NOTES (never silent); `run_round` scores exactly 8 (no doubling). Protects:
     the dress-rehearsal double-count edge — a resubmission supersedes (is_scoreable=false), never
     double-counts; the LOGICAL grain stays 8 despite the 13-period storage fan-out (CLAUDE.md req #3:
     no collapsing/no double-count, reconcile to the numbers at each step).
  3. **`test_full_cycle_loop_e2e(tmp_path, db_session)` — INTEGRATION (no marker → runs in pure set too?
     NO: it needs `db_session`, which `skip`s if no DB, so it's effectively DB-gated even without the
     marker).** The full loop: start_run → ingest setup (cycle_id, 2 DCs/2 lots/2 suppliers/2 rounds) →
     generate_bid_template(1) (name `02_round1_bid_template.xlsx`; RUN.md updated) → fill + ingest (8
     lines) → run_round(1) (`04_round1_alignment_v1.xlsx`; Summary banner carries "Analysis v1"/"Round
     1"/"LIVE CYCLE DATA", never "SYNTHETIC") → freeze B (`08_award_booking_guide.xlsx` +
     `08_award_supplier_guides.xlsx`) → record_adjustment (`09_post_award_v1.xlsx`; "Version 1" banner)
     → history() (1 analysis run v1, 1 award with versions {0,1}, the two output files present) →
     run_data.json (cycle name "E2E Tomatoes Cycle", `scope.dcs` contains "Atlanta DC" — names not keys
     D23, `bid_lines_by_round==[{round:1,bid_lines:8}]`, analysis v1, award `AWD-E2E-1` versions {0,1},
     award suppliers ⊆ the synthetic names) → FEEDBACK.md (four sections) → add_memory →
     close_run (zip holds inputs/outputs/memory/NOTES.md/run_data.json/FEEDBACK.md/alignment_v1/
     post_award_v1) → purge_run (folder gone, archive intact, DB records remain). Protects: the entire
     orchestrated loop AND the governed-data snapshot fidelity (names, counts, versions).
     *Note:* the assert at L282 reads `run_data["cycle"]["name"] == "E2E Tomatoes Cycle"`, while the
     setup workbook in `test_pilot_setup.py` uses the label "Test Tomatoes Cycle" — the synthetic
     builder in `app.pilot.synthetic` sets "E2E Tomatoes Cycle" (the two builders differ; see GAP-2).
  4. **`test_rehearsal_run_stamps_synthetic_provenance(tmp_path, db_session)` — INTEGRATION.** A
     `rehearsal=True` run carries the `.rehearsal` sentinel (`is_rehearsal(paths)`); after the loop the
     alignment workbook + booking guides are stamped "SYNTHETIC" and NEVER "LIVE CYCLE DATA"/"real names
     & prices"; the sentinel rides the close-out zip. Protects: the dress-rehearsal finding — a
     rehearsal can never be mistaken for a live cycle.
  5. **`test_apply_cycle_safeties_layers_over_preset()` — PURE.** With no safeties set,
     `_apply_cycle_safeties(base, cv) is base` (nothing to override); setting `premium_ceiling=0.15` +
     `max_sup_dc=3` overrides only those, leaving `coverage_floor`/`conc_thresh` at the preset. Protects:
     per-RFP safeties layer over the preset; blank fields keep the preset (no accidental zeroing).
  6. **`test_setup_engine_safeties_flow_to_engine_config(tmp_path, db_session)` — INTEGRATION.** A setup
     workbook with `premium_ceiling=0.15` (not the 0.12 preset) persists onto the cycle, loads into the
     CycleView (`premium_ceiling==0.15`, `coverage_floor==0.80`, `conc_thresh==0.40`, `max_sup_dc==2`),
     and `_apply_cycle_safeties(_DEFAULT_CONFIG, view)` yields `global_premium_threshold==0.15`.
     Protects: the finding where the setup ingester DROPPED the Cycle-tab safeties and the engine
     silently ran the preset default.
  7. **`test_apply_cycle_preset_remaps_weights()` — PURE.** No preset → config unchanged; `price_focus`
     → `preset==PRICE_FOCUS`, `weight_price==0.50`, `weight_continuity==0.14`; `custom` → keeps the
     explicit weights. Protects: a named preset swaps in its weight vector; CUSTOM preserves weights.
  8. **`test_setup_weight_preset_flows_to_engine_config(tmp_path, db_session)` — INTEGRATION.** A setup
     workbook with `weight_preset="risk_averse"` persists; `_apply_cycle_preset` → `RISK_AVERSE`,
     `weight_zrisk==0.18`, `weight_price==0.20`. Protects: the buyer's preset remaps the engine weights.
  9. **`test_setup_rejects_unknown_weight_preset(tmp_path, db_session)` — INTEGRATION.** A setup with
     `weight_preset="cheapest_wins"` → `ingest_setup` raises `SetupIngestError` mentioning "Weight
     Preset". Protects: an unknown preset is rejected at ingest, never silently ignored (data fidelity).
  10. **`test_failed_start_leaves_no_orphan_run(tmp_path, monkeypatch)` — PURE (monkeypatches
      `build_setup_workbook` to raise).** A `start_run` that blows up after the scaffold tears the
      partial run down — `runs/` has no leftover folder. Protects: the dress-rehearsal finding #2 —
      orphan run folders/DBs left by an aborted start; `start_run` now wraps post-scaffold steps in a
      cleanup. (No DB needed — the failure is before any DB write.)
  11. **`test_ingest_any_flexible_roundtrip(tmp_path, db_session)` — INTEGRATION.** `ingest_any(...,
      confirm=False)` → a `MappingProposal` (`is_confident`), nothing ingested; `confirm=True` → an int
      count > 0 and `03_round1_bids_normalized.xlsx` written. Protects: the propose-then-confirm flexible
      ingest at the service layer (the api `test_bids.py` flexible tests guard the same through HTTP).
- **DB?** 4 pure (1,5,7,10), 7 integration (2,3,4,6,8,9,11). (Function 3 lacks an explicit marker but is
  DB-gated via `db_session`.)

### 3.3 `backend/tests/pilot/test_pilot_setup.py` — 337 lines · census 236 · 8 test fns
- **What.** PART A — the run vault scaffold, the setup template/ingest round-trip, notes/memory, kanban,
  and the once-per-run + unresolved-rows guards. Carries its OWN `_build_filled_setup()` (a richer,
  tab-by-tab builder using the real template tab/header constants) distinct from the
  `app.pilot.synthetic` one. Helpers `_header_col`, `_write_rows` fill the generated template in-memory.
- **Detailed WHY.** Guards the scaffold IDENTITY (every run folder structurally identical — longevity +
  drift reduction), the normalized stage filenames, the setup template's tabs/dropdowns, and the
  full template→fill→ingest→load_cycle round-trip reconstructing the scope with EXACT counts (data
  fidelity). Plus the two governance guards: second-setup refusal (409, no orphan) and unresolved-row
  reporting (a volume row pointing at an unknown DC is surfaced, never silently dropped — CLAUDE.md
  req #3 quarantine-not-fudge).
- **Test functions:**
  - **PURE:**
    1. **`test_stage_filename_normalized()`.** `stage_filename(1,"setup_kickoff")=="01_setup_kickoff.xlsx"`,
       `(4,"round1_alignment",version=1)=="04_round1_alignment_v1.xlsx"`,
       `(9,"post_award",version=2)=="09_post_award_v2.xlsx"`, `(2,"round1_bid_template",ext="csv")=="02_round1_bid_template.csv"`.
       Protects: the normalized stage-filename convention (numeric prefix, version suffix, ext override).
    2. **`test_start_run_creates_identical_scaffold(tmp_path)`.** Every dir/manifest exists
       (inputs/outputs/memory/notes_md/run_md/cycle_id_file); the setup workbook is written under the
       stage name and starts `PK`; slug shape `<commodity-slug>-<YYYYMMDD>-<short>`; the vault is a git
       repo (`.git` exists, run committed); RUN.md carries the four kanban buckets. Protects: the
       identical scaffold + git-tracked vault (the harness runtime's identity).
    3. **`test_two_runs_are_structurally_identical(tmp_path)`.** Two runs (different commodities) have
       the same relative file/dir shape (modulo content, ignoring `.git`/`.gitkeep`); `list_runs()==2`.
       Protects: structural identity across runs (drift reduction).
    4. **`test_remember_and_add_memory_append_notes(tmp_path)`.** `remember(...)` appends to NOTES.md;
       `add_memory(...)` writes the memory file AND links its name + caption in NOTES. Protects: the
       notes/memory capture loop (buyer asks are durable + linked).
    5. **`test_setup_template_has_all_tabs_and_dropdowns()`.** The generated workbook has all 7 tabs
       (Cycle/DCs/Lots/Suppliers/Volumes/Incumbents/Timeframes); the Lots tab carries the Product Type
       closed-domain dropdown (a data-validation containing "Conventional"). Protects: the setup
       template's structure + a closed-domain dropdown (input fidelity at the source).
  - **INTEGRATION:**
    6. **`test_setup_roundtrips_to_cycle(tmp_path, db_session)`.** Upload the filled setup → ingest →
       cycle_id; `cycle_id.txt` + RUN.md carry the link; `load_cycle` reconstructs EXACT counts (2 DCs,
       2 lots, 2 items, 1 TF, 2 rounds, 2 suppliers), 4 projected-volume cells, 4 incumbent baselines
       all `==11.20`; the kanban shows "Cycle created" in Done and a bid step in Next (buyer terms).
       Protects: the full setup round-trip with reconciled counts + the incumbent baseline value
       (data fidelity).
    7. **`test_second_setup_ingest_is_refused(tmp_path, db_session)`.** A 2nd `ingest_setup` raises
       `AppError` with `code==CONFLICT`, `status_code==409`; the original `cycle_id.txt` is untouched.
       Protects: once-per-run setup; re-ingest would strand the prior cycle's bids/analyses/awards.
    8. **`test_setup_ingest_reports_unresolved_rows(tmp_path, db_session)`.** A volume row pointing at
       "Nonexistent DC" → `ingest_setup_workbook` raises `SetupIngestError` whose `.problems` names
       "Nonexistent DC". Protects: cross-reference integrity — a dangling row is SURFACED (quarantine),
       never silently dropped (CLAUDE.md req #3).
- **DB?** 5 pure (1–5), 3 integration (6–8).

### 3.4 `backend/tests/pilot/test_deliverables.py` — 178 lines · census 234 · 3 test fns
- **What.** The DB-backed deliverable registry (NFS Slice 1): `enumerate_deliverables` is a faithful
  projection of the MCP-harness on-disk write path. `pytestmark = pytest.mark.integration` (whole file
  DB-gated). Reuses the e2e synthetic builders + DB helpers. Helpers `_disk_filenames`, `_sheet_data`
  (E-39 data-identity), `_cycle_id`.
- **Detailed WHY.** This is the bridge proving the web's render-on-request registry (ADR-0018) produces
  EXACTLY the files the harness writes to disk — name-for-name AND data-for-data. Without it, the
  console's downloads could silently diverge from the canonical harness outputs (breaking auditability +
  no-storage parity).
- **Test functions (all INTEGRATION via pytestmark):**
  1. **`test_enumerate_matches_harness_filenames(tmp_path, db_session)`.** Drives a full harness run
     (setup → both round templates [round 1 also filled+ingested] → run_round → freeze B → adjustment),
     then asserts `enumerated == disk` (exact set parity), and spot-checks the expected normalized names
     (`01_setup_kickoff`, `02_round1_bid_template`, `05_round2_bid_template`, `04_round1_alignment_v1`,
     `08_award_booking_guide`, `08_award_supplier_guides`, `09_post_award_v1`) plus ≥1 per-supplier guide
     `award_guide_awd_deliv_1*`. Protects: the registry produces every file the harness wrote and nothing
     extra (name parity).
  2. **`test_render_is_data_identical_to_stored(tmp_path, db_session)`.** For the alignment workbook +
     the booking guide, `registry.render(db_session)` reproduces the STORED workbook's sheet cell DATA
     (`_sheet_data` equality). Protects: data-identity of the on-request render (E-39; date-stamped
     provenance lines are intentionally excluded by comparing DATA not raw bytes).
  3. **`test_no_cycle_enumerates_only_setup(tmp_path, db_session)`.** A run with no ingested setup (no
     cycle) enumerates exactly `["01_setup_kickoff.xlsx"]` and its render is a real `PK` xlsx produced
     with NO DB read. Protects: the no-cycle base case (the registry never over- or under-enumerates).
- **DB?** All 3 integration.

### 3.5 `backend/tests/pilot/test_run_repo.py` — 163 lines · census 239 · 7 test fns
- **What.** The DB-backed run identity (NFS Slice 2): the `pilot.run` repo CRUD, the console-mode
  dual-write, the harness-mode no-write, the console no-folder scaffold, console delete, rehearsal flag,
  and the backfill of a pre-existing folder. `pytestmark = pytest.mark.integration`. Reuses
  `_build_filled_setup`.
- **Detailed WHY.** These are the building blocks Slice 3 flips the console reads onto (ADR-0018: run
  identity is the `pilot.run` row, not the folder). Guards the dual-write contract (console writes the
  row + sets cycle_id while harness mode stays untouched) and the no-server-side-storage scaffold
  (console mode writes only the row, no folder).
- **Test functions (all INTEGRATION via pytestmark):**
  1. **`test_repo_crud_round_trips(db_session)`.** create→get→list→set_cycle→delete on the rolled-back
     session; `set_run_cycle` on an unknown slug → `ValueError` (clean error, never silent no-op);
     delete is idempotent. Protects: the repo CRUD + error semantics.
  2. **`test_console_service_dual_writes_run_row(tmp_path, db_session)`.** `PilotService(..., db_runs=True)`:
     `start_run(session=...)` inserts the row (`cycle_id None`); `ingest_setup` sets its `cycle_id`
     (and the vault `cycle_id.txt` matches). Protects: the console dual-write linking the cycle.
  3. **`test_harness_mode_writes_no_run_row(tmp_path, db_session)`.** `db_runs` default False →
     `get_run` is `None` after start_run. Protects: the harness is untouched by the DB-runs feature.
  4. **`test_console_start_run_scaffolds_no_folder(tmp_path, db_session)`.** `db_runs=True,
     persist_outputs=False` → the row exists but `paths.root` does NOT. Protects: Slice 6 — console
     start writes only the DB row, no vault folder.
  5. **`test_console_delete_run_removes_row(tmp_path, db_session)`.** `delete_run` removes the row;
     idempotent. Protects: console close-out deletes the identity row.
  6. **`test_rehearsal_dual_write_flags_synthetic(tmp_path, db_session)`.** A rehearsal run's row carries
     `rehearsal=True`. Protects: rehearsal provenance on the DB identity.
  7. **`test_backfill_seeds_existing_vault_folder(tmp_path, db_session)`.** A harness-mode folder (no DB
     row) is backfilled: `backfill_run` inserts a row deriving commodity/label/rehearsal/cycle from the
     files; idempotent (2nd backfill → False, cycle link kept). Protects: pre-Slice-2 folders surface in
     the console without vanishing (migration safety).
- **DB?** All 7 integration.

### 3.6 `backend/tests/pilot/test_run_isolation.py` — 56 lines · census 237 · 1 test fn
- **What.** Per-run data isolation (D30): provisions TWO run databases and writes the SAME
  globally-unique `ref.dc` code (DC01) into each. Needs Postgres AND a role with CREATEDB (skips cleanly
  otherwise); drops both DBs after. `_INSERT_DC01` is a raw INSERT of DC01.
- **Detailed WHY.** This is the COMPLIANCE regression for the harness runtime's database-per-run model:
  in a shared DB, two DC01s collide on the global UNIQUE; with a DB per run they must NOT — each run
  holds its own DC01 and can never see the other's. A regression collapsing to a shared store would
  surface as a unique-violation or cross-contamination.
- **Test function (INTEGRATION):**
  1. **`test_two_runs_get_isolated_databases(database_url)`.** Provisions two run DBs (skips with a
     clear message if the role lacks CREATEDB), inserts DC01 with region EAST into run A and WEST into
     run B via `run_unit_of_work`, then asserts the DB names differ AND each DB holds ONLY its own DC01
     (`SELECT region` → `["EAST"]` / `["WEST"]`); a `finally` drops both DBs. Protects: D30 per-run
     database isolation (no cross-run leakage of globally-unique reference data).
- **DB?** Integration (needs CREATEDB role; skips otherwise).

### 3.7 `backend/tests/pilot/test_run_persistence.py` — 62 lines · census 238 · 1 test fn
- **What.** Vault-carried DB persistence: a run's governed isolated Postgres DB survives a wiped
  (ephemeral) container by being dumped into the vault git and restored on session start.
- **Detailed WHY.** The web runtime is reclaimed between sessions, so a run's isolated DB is gone next
  time. The vault carries a per-run SQL dump; this proves the full provision→write→dump→DROP→restore
  round-trip leaves the governed data intact — the run resumes exactly where it was (longevity, the #1
  decision-weighting criterion).
- **Test function (INTEGRATION):**
  1. **`test_run_db_dump_drop_restore_round_trips(tmp_path)`.** Provision a fresh migrated isolated DB;
     insert a `ref.client` sentinel (a random marker); `dump_run_database` to a vault-like path
     (`runs/<slug>/db/run_db.sql`, asserts the file exists + non-empty); `drop_run_database` (the wipe);
     `restore_run_database` from the dump; assert the sentinel survived (`SELECT client_name` == marker)
     and `run_db_name` starts `kr_rfp_run_`; `finally` drops the DB. Protects: vault-carried DB
     persistence end-to-end (the ephemeral-container resume guarantee).
- **DB?** Integration.

### 3.8 `backend/tests/pilot/test_vault_autopush.py` — 94 lines · census 240 · 3 test fns
- **What.** Vault auto-push (D34): the write side of vault-carried persistence — a governed commit only
  PERSISTS in the ephemeral runtime if it reaches the vault's REMOTE; `RFP_VAULT_AUTOPUSH` turns pushing
  on (off for local/tests). Uses real `git` subprocesses against a bare remote. Helpers `_git`,
  `_vault_with_remote`.
- **Detailed WHY.** In the reclaimed web runtime the local clone is discarded between sessions, so a
  commit that doesn't reach the remote is lost. These tests prove the opt-in actually pushes (and the
  default does not), including the tricky first-write-no-upstream case. A regression would silently lose
  governed writes on the next wipe.
- **Test functions (all PURE — no DB, but spawn `git`):**
  1. **`test_commit_pushes_to_remote_when_autopush_enabled(tmp_path, monkeypatch)`.** With a vault clone
     + established upstream and `RFP_VAULT_AUTOPUSH=1`, a governed change committed via `git_commit_run`
     advances the bare remote's HEAD. Protects: the opt-in push reaches the remote (survives the wipe).
  2. **`test_commit_pushes_to_empty_vault_with_no_upstream(tmp_path, monkeypatch)`.** An EMPTY bare
     remote (no commits, no branch → clone has no upstream) + autopush on: the first governed write must
     still reach it (`push -u origin HEAD`); asserts remote HEAD == vault HEAD. Protects: the
     first-write-no-upstream edge (a brand-new vault still persists).
  3. **`test_commit_does_not_push_when_autopush_disabled(tmp_path, monkeypatch)`.** With autopush unset,
     the commit exists locally but the remote did NOT advance. Protects: pushing is opt-in (local/tests
     don't push).
- **DB?** All 3 pure (git subprocess only).

---

## 4. CROSS-CUTTING OBSERVATIONS & GAPS

### 4.1 Live-DB vs pure split (the marker contract, verified)
- **Pure (run under `pytest -m "not integration"`, no DB):** `test_auth.py::test_password_hash_roundtrip`;
  all 4 of `test_cors.py`; `test_pilot_cycle_e2e.py::{test_infer_bid_mapping_on_messy_sheet,
  test_apply_cycle_safeties_layers_over_preset, test_apply_cycle_preset_remaps_weights,
  test_failed_start_leaves_no_orphan_run}`; `test_pilot_setup.py::{test_stage_filename_normalized,
  test_start_run_creates_identical_scaffold, test_two_runs_are_structurally_identical,
  test_remember_and_add_memory_append_notes, test_setup_template_has_all_tabs_and_dropdowns}`;
  all 3 of `test_vault_autopush.py` (git subprocess, no DB). **≈17 pure tests.**
- **Integration (need a live Postgres; `skip` when unreachable):** everything else (**≈97 tests**),
  including the entire `api/**` suite except the one auth hash unit + the four CORS middleware checks.
- **Special DB needs:** `test_run_isolation.py` additionally needs a **CREATEDB** role (skips with a
  clear message otherwise); `test_run_persistence.py` exercises `pg_dump`/restore of an isolated DB.
- The split is enforced by the single registered marker in `backend/pyproject.toml` and the
  `engine`/`db_session` skip-on-no-DB fixtures — so a dev box with no Postgres still gets a green pure run.

### 4.2 The fixtures named in the brief — where each is defined / consumed
- **`db_session`** — defined in `tests/conftest.py` (the rollback-isolation session); consumed by ~all
  integration tests directly and indirectly via `client`.
- **`client`** — defined in `tests/api/conftest.py`; the https TestClient bound to `db_session`;
  consumed by every `api/**` integration test.
- **`seed_user`** — defined in `tests/api/conftest.py`; the active console user (`admin`/`s3cret-pw`);
  consumed by every authed `api/**` test (and mutated in `test_login_2fa_required_path`).
- **`vault_root`** — defined in `tests/api/conftest.py`; redirects `pilot_common._vault_root` to a temp
  dir; consumed by every `api/**` test (always passed so the real vault is never touched, and so NFS
  tests can assert on-disk emptiness).
- Also: `engine`, `database_url`, `seed_tenants` (root conftest); the `pilot/**` tests use only
  `db_session`/`database_url` + `tmp_path`/`monkeypatch` (no `client`/`seed_user`/`vault_root`), since
  they drive `PilotService` directly.

### 4.3 Gaps / discrepancies (flagged, not "fixed" — read-only audit)
- **GAP-1 (scope path mismatch).** The brief's `backend/tests/auth/**` does not exist; auth is tested at
  `backend/tests/api/test_auth.py` (audited). No missing/orphaned `tests/auth/` tree. *(Already noted §0.)*
- **GAP-2 (two synthetic-setup builders, different cycle labels).** `test_pilot_setup.py` defines its OWN
  `_build_filled_setup()` (tab-by-tab, cycle label "Test Tomatoes Cycle"), while
  `test_pilot_cycle_e2e.py` aliases `app.pilot.synthetic.build_filled_setup` (cycle label "E2E Tomatoes
  Cycle", per the L282 assertion). The api tests import the LATTER. This is intentional (the e2e/api
  builder is the pytest-free single source reusable by `deploy/gcp/seed.py`), but it means the repo has
  TWO synthetic setup builders with different cycle names — a minor duplication/drift risk worth noting
  (the `test_pilot_setup.py` local copy could in principle drift from the shared one; only the shared one
  is reused outside its module). Not a defect; flagged per the exhaustiveness bar.
- **GAP-3 (`test_full_cycle_loop_e2e` lacks an explicit `@pytest.mark.integration`).** It is nonetheless
  DB-gated because it requires the `db_session` fixture (which `skip`s with no DB). So under
  `pytest -m "not integration"` it would still be COLLECTED (the marker filter doesn't deselect it) but
  would SKIP at fixture setup if no DB is present, and RUN (touching the DB) if a DB happens to be
  reachable. Every other DB-touching test in the file carries the marker explicitly; this one is the
  lone exception. Worth a one-line marker add for consistency (the pure suite should be DB-free by
  construction, not by happenstance of no reachable DB). *Flagged only; not changed.*
- **No empty test files, no placeholder/stub tests, no skipped-by-default `xfail`/`skip` decorators**
  found anywhere in scope — consistent with CLAUDE.md req #1 (no stubs/placeholders). The only `skip`s
  are the deliberate environment gates (no DB / no CREATEDB role) in fixtures + `test_run_isolation`.

### 4.4 Appendix — verified per-file function counts (grep `^def test_|^    def test_`)
api/test_alignment=11 · api/test_auth=8 · api/test_bids=17 · api/test_comms=12 · api/test_cors=4 ·
api/test_downloads=1 · api/test_finalize=6 · api/test_post_award=6 · api/test_runs=7 · api/test_strategy=4 ·
api/test_version_save=4  → **API subtotal 80**.
pilot/test_deliverables=3 · pilot/test_pilot_cycle_e2e=11 · pilot/test_pilot_setup=8 ·
pilot/test_run_isolation=1 · pilot/test_run_persistence=1 · pilot/test_run_repo=7 ·
pilot/test_vault_autopush=3  → **pilot subtotal 34**.  **GRAND TOTAL = 114 test functions** (+22 helper
defs). All accounted for above.
