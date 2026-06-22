---
doc: AS-BUILT EXHAUSTIVE AUDIT — SLICE B6 (auth · comms · output · fiscal · cycle + top-level app)
id: ASBUILT-B6
status: DONE
bar: AUDIT_STANDARD.md (3 layers; nothing skipped; detailed WHY; every transformation/decimal with formula+file:line; every edge case)
contract: /CLAUDE.md (ABSOLUTE REQUIREMENTS injected)
scope: backend/app/auth/** · backend/app/comms/** · backend/app/output/** · backend/app/fiscal/** · backend/app/cycle/** · backend/app/main.py · backend/app/__init__.py
census_rows: 45 (app/__init__.py), 59–81 (auth + comms), 96–98 (cycle), 138–155 (fiscal, main, output)
---

# SLICE B6 — auth, comms, output, fiscal, cycle, + remaining top-level `app/**`

## 0. SCOPE RECONCILIATION (cross-check vs FILE_CENSUS.md + the slice boundaries)

`find backend/app -maxdepth 2 -type f` (ignoring `__pycache__/*.pyc`, which are vendored/generated
Python bytecode — counted, never per-file audited) gives the complete top-level inventory. Mapping
every entry to its owning slice so **nothing in `backend/app` is missed across B1–B6**:

| Path | Owning slice | In B6? |
|------|--------------|:------:|
| `app/__init__.py` (census #45) | top-level — **B6** ("any remaining top-level files NOT covered by engine/pilot/domain/api/core") | ✅ |
| `app/main.py` (census #141) | top-level — **B6** | ✅ |
| `app/api/**` | B5 | — |
| `app/core/**` | B5 | — |
| `app/domain/**` | B3 / B4 | — |
| `app/engine/**` | B1 | — |
| `app/pilot/**` | B2 | — |
| `app/auth/**` (census #59–63) | **B6** | ✅ |
| `app/comms/**` (census #64–81) | **B6** | ✅ |
| `app/cycle/**` (census #96–98) | **B6** | ✅ |
| `app/fiscal/**` (census #138–140) | **B6** | ✅ |
| `app/output/**` (census #142–155) | **B6** | ✅ |

The ONLY top-level (`maxdepth 1`) files under `app/` are `__init__.py` and `main.py`; the other
top-level `__init__.py` markers (`api/__init__.py`, `core/__init__.py`, `domain/__init__.py`,
`engine/__init__.py`, `pilot/__init__.py`) live under packages owned by B1–B5 and are out of scope
here. **No B6 file is empty** — every census row for this slice has a non-zero byte count and a
`y` owned-flag; there are no `EMPTY`-flagged files in this slice (the 18 empty files live elsewhere).

**B6 file count: 31 owned files** (5 auth + 5 comms `.py` + 7 comms `.txt` + 2 cycle + 2 fiscal `.py`
+ 1 fiscal `.csv` + 7 output `.py` + 1 `app/__init__.py` + 1 `app/main.py`). All read end-to-end.

Note the census `created/modified` timestamps differ from the live `stat` by a few minutes
(census recorded earlier in the same hour); the per-file metadata below uses the census row as the
authoritative cross-ref.

---

## 1. TOP-LEVEL `app/**`

### 1.1 `backend/app/__init__.py` — census #45 · py · 82 B · not empty
**What:** the `app` package docstring marker: `"""Kroger Produce RFP / Sourcing — system-of-record
backend (package `app`)."""`. One line, no code.
**Detailed WHY:** Python needs `app/` to be an importable package so `from app.x import y` resolves;
the one-line docstring names the package's role (system-of-record backend) for any reader who opens
it. **What breaks without it:** with no `__init__.py` the directory is at best an implicit namespace
package (fragile under the project's editable install + test runner); the canonical `app.*` import
root the entire backend depends on would not reliably resolve. It is intentionally code-free — a
package marker, not a module.

### 1.2 `backend/app/main.py` — census #141 · py · 4430 B · not empty
**What:** the FastAPI application factory (`create_app`) + the module-level `app = create_app()` the
ASGI server imports. Mounts the `/api/v1` router, registers uniform exception handlers, wires the
immutability-guard listeners, installs a **tenant-context middleware STUB**, and adds CORS.
**Detailed WHY:** every request enters here; this is where the app is assembled and where the verified
**principal/tenant is established on `request.state`** for the downstream security dependencies. It is
deliberately a factory (not a bare module-level app) so tests can build an app with overridden
settings. **What breaks without it:** no ASGI entrypoint, no router, no auth context, no CORS — the
backend cannot serve.

**Functions / structure (every one):**
- `_DEV_TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")` (L31) — a STABLE dev tenant id
  so local requests resolve to a consistent tenant; **WHY the literal value:** it matches the
  migration's seeded `ref.client` on a freshly migrated DB, so dev work lands on real seeded data.
- `_dev_principal(settings) -> Principal` (L34–47) — builds a non-production principal holding
  `frozenset({Role.ANALYST, Role.CAT_MAN, Role.APPROVER})`, subject/email `"dev@local"`, tenant
  `_DEV_TENANT_ID`, `tenant_code=settings.default_tenant_code`. **WHY all three roles:** so local work
  can exercise every guarded route without an IdP. Side-effects: none (pure construction). It is a
  scaffold convenience, **never a production path**.
- `create_app() -> FastAPI` (L50–103) — reads `get_settings()`; constructs `FastAPI(title=…,
  version="0.1.0", openapi_url=f"{settings.api_v1_prefix}/openapi.json")`; calls
  `register_exception_handlers(app)` and `register_immutability_guards()`; defines the
  `@app.middleware("http")` **tenant_context_middleware**; conditionally adds `CORSMiddleware`;
  `app.include_router(api_router, prefix=settings.api_v1_prefix)`; returns the app.
  - **tenant_context_middleware** (L64–81): sets `request.state.request_id =
    request.headers.get("x-request-id", str(uuid.uuid4()))` (request correlation) and
    `request.state.principal = None`; THEN, **only when `settings.env is not Environment.PRODUCTION`**,
    sets `request.state.principal = _dev_principal(settings)`. In production it leaves the principal
    `None`, so the security dependencies deny protected routes (until the DEP-4 IdP adapter lands).
    **Edge case enforced:** tenant is ALWAYS derived from the verified principal, **never from the
    request body** (the "no tenant-from-input" rule).
  - **CORS** (L83–100): `cors_origins = [o.strip() for o in settings.cors_allow_origins.split(",") if
    o.strip()]`; if non-empty adds `CORSMiddleware(allow_origins=cors_origins,
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
    expose_headers=["Content-Disposition"])`. **WHY added LAST / outermost:** so preflight `OPTIONS`
    are short-circuited before the tenant middleware and CORS headers ride on EVERY response
    (including errors). **WHY explicit origins, never `"*"`:** a credentialed response cannot use a
    wildcard origin. **WHY `expose_headers=["Content-Disposition"]`:** the browser console reads the
    download filename for run-file/zip downloads off that header, which a browser only exposes
    cross-origin when listed.
- `app = create_app()` (L106) — the module-level ASGI app instance.

**Layer-2 STUB flag / drift note:** `main.py` is explicitly labelled a **STUB** for the
tenant-context middleware (the IdP token-verification adapter is **DEP-4**, not yet landed). This is
NOT an MVP cut of a shipped capability — production requests are left *unauthenticated by design*
(deny-by-default at the security dependencies), and the dev principal is gated to non-production. The
docstring names the exact production replacement. Recorded as a **known pending dependency (DEP-4)**,
not silent drift.

---

## 2. `app/auth/**` — web-console authentication (username/password + TOTP-2FA)

A self-contained auth surface for the REST console, **separate from the eight governed domain
layers** (its own `auth` schema). WHY separate: the governed data spine must never depend on who is
logged into the console.

### 2.1 `auth/__init__.py` — census #59 · py · 447 B · not empty
**What:** package docstring describing the auth surface: an `auth.app_user` table in its own `auth`
schema, argon2 password hashing, a signed session JWT in an httpOnly `kr_session` cookie, and TOTP
2FA enrol/verify. No code. **WHY:** package marker + the one-paragraph contract of the package; names
that `app/api/v1/auth.py` wraps these primitives and `app/auth/deps.py` exposes `get_current_user`.
**Breaks without it:** `app.auth` would not be a guaranteed package.

### 2.2 `auth/models.py` — census #62 · py · 1721 B · not empty
**What:** the SQLAlchemy mapped class `AppUser` → table `auth.app_user`.
**Detailed WHY:** the credential record behind the console login; lives in its **own `auth` schema**
(`__table_args__ = {"schema": "auth"}`) so it is isolated from the governed `ref/cyc/bid/eng/awd/…`
layers. PK mirrors the `ref` spine convention (a server-generatable UUID via `uuid_pk()`, stable
`pk_app_user` name) so it round-trips like the other governed tables. **Breaks without it:** no ORM
mapping for the login user — `get_current_user`, the seed CLI, and the auth router cannot load/create
users.
**Columns (name · type · nullability · default · WHY):**
- `id: uuid.UUID` = `uuid_pk()` — server-generatable UUID PK; WHY: matches the ref-spine round-trip.
- `username: str` = `mapped_column(Text, nullable=False, unique=True)` — login handle; **UNIQUE**
  enforces one account per username (the `upsert_user` lookup key).
- `password_hash: str` = `Text, nullable=False` — the argon2 hash string (never the plaintext).
- `totp_secret: str | None` = `Text, nullable=True` — base32 TOTP shared secret; **NULL until the
  user enrols**; only honoured once `totp_enabled` flips true (the enrol→verify two-step).
- `totp_enabled: bool` = `Boolean, nullable=False, default=False` — 2FA-active flag.
- `is_active: bool` = `Boolean, nullable=False, default=True` — soft-disable; `get_current_user`
  denies an inactive user.
- `created_at: datetime` = `created_at_column()` — server-defaulted creation timestamp.

### 2.3 `auth/security.py` — census #63 · py · 3779 B · not empty
**What:** the pure auth primitives — argon2 hashing, the session JWT, and TOTP helpers. No FastAPI,
no DB. **Detailed WHY:** keeps the credential arithmetic in one pure place so the routers AND the
seed CLI call the same functions; secrets/TTL come from settings; the **cookie name is fixed here**
(`SESSION_COOKIE_NAME = "kr_session"`, L20) so the issuer (login) and the reader (`get_current_user`)
always agree. **Breaks without it:** login, session validation, and 2FA have no implementation.
**Constants:** `SESSION_COOKIE_NAME = "kr_session"`; `TOTP_ISSUER = "KR RFP"` (the label authenticator
apps display); `_JWT_ALG = "HS256"` (symmetric HMAC — matches the single shared `auth_secret_key`);
`_pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")` — **argon2 only**, the modern
memory-hard default; passlib's `verify()` is constant-time.
**Functions (every one — signature · WHY · transformation):**
- `hash_password(password) -> str` (L32) — `str(_pwd_context.hash(password))`; argon2 hash for storage.
- `verify_password(password, password_hash) -> bool` (L38) — `bool(_pwd_context.verify(...))` inside
  `try/except (ValueError, TypeError): return False`. **Edge case:** a malformed/empty stored hash
  reads as "does not verify", **never raises** (so a corrupt row can't 500 a login).
- `create_session_token(user_id, *, username) -> str` (L51) — signs a JWT with claims
  `{"sub": user_id, "username": username, "iat": int(now.timestamp()), "exp":
  int((now + timedelta(minutes=settings.auth_token_ttl_minutes)).timestamp())}` via
  `jwt.encode(payload, settings.auth_secret_key, algorithm="HS256")`. **Transformation/precision:**
  `iat`/`exp` are integer epoch seconds (`int(...)`); `now = datetime.now(UTC)` (tz-aware UTC).
- `decode_session_token(token) -> dict | None` (L65) — `jwt.decode(token, secret, algorithms=["HS256"])`
  inside `try/except jwt.PyJWTError: return None`. **Edge case:** ANY decode failure (bad signature,
  expired, malformed) collapses to `None` — the dependency turns that into a uniform 401.
- `session_cookie_max_age_seconds() -> int` (L76) — `auth_token_ttl_minutes * 60`; **WHY:** so the
  cookie Max-Age and the JWT `exp` expire **together** (no zombie cookie outliving its token).
- `generate_totp_secret() -> str` (L85) — `pyotp.random_base32()`; a fresh (not-yet-enabled) secret.
- `totp_provisioning_uri(secret, *, username) -> str` (L91) —
  `pyotp.TOTP(secret).provisioning_uri(name=username, issuer_name="KR RFP")`; the `otpauth://` URI.
- `verify_totp(secret, code) -> bool` (L97) — `if not secret or not code: return False`; else
  `pyotp.TOTP(secret).verify(code.strip(), valid_window=1)`. **Edge case / precision:**
  `valid_window=1` tolerates ±1 time-step (±30s) clock skew; `code.strip()` drops stray whitespace.

**Cookie attributes (samesite/secure) — WHERE:** `security.py` only fixes the cookie NAME and the
Max-Age helper; the actual `samesite`/`secure`/`httponly` flags are set on the `Response.set_cookie`
call in the auth router (`app/api/v1/auth.py`, B5 scope), which is the issuer. **Cross-slice note for
B5:** the cookie is httpOnly per the package docstring ("httpOnly `kr_session` cookie"); the
SameSite/Secure attributes are emitted at the set-cookie site (B5) — verify there.

### 2.4 `auth/deps.py` — census #61 · py · 2115 B · not empty
**What:** the `get_current_user` FastAPI dependency + the `CurrentUser` Annotated alias.
**Detailed WHY:** the single gate the runs API depends on so **every runs route is authenticated**;
it reads+validates the session cookie and loads the active user. **Breaks without it:** the protected
API has no way to identify the caller; runs routes would be open.
**Functions:**
- `_unauthenticated(detail) -> AppError` (L24) — builds `AppError(code=ErrorCode.UNAUTHENTICATED,
  message=detail, status_code=401)`; **WHY a single helper:** every failure path returns the SAME
  uniform 401 envelope (no information leak about which check failed).
- `get_current_user(request, db) -> AppUser` (L28) — flow + **every branch**:
  1. `token = request.cookies.get(SESSION_COOKIE_NAME)`; **no cookie → 401** (`_unauthenticated()`).
  2. `claims = decode_session_token(token)`; **None → 401** "Session is invalid or expired."
  3. `subject = claims.get("sub")`; **not a `str` → 401**.
  4. `user_id = uuid.UUID(subject)` inside `try/except ValueError: raise … from None` — **non-UUID
     subject → 401**.
  5. load `AppUser` by id; **`None` or `not user.is_active` → 401**.
  6. else return the user.
  **WHY uniform 401 on every failure:** an attacker learns nothing about which step failed.
- `CurrentUser = Annotated[AppUser, Depends(get_current_user)]` (L60) — the reusable dependency type.

### 2.5 `auth/create_user.py` — census #60 · py · 1713 B · not empty
**What:** the seed/upsert CLI — `python -m app.auth.create_user <username> <password>`.
**Detailed WHY:** the operational bootstrap so the FIRST admin can log in before any UI exists; the
user enrols TOTP later through the API. Runs inside the standard unit of work (DB is the source of
truth). **Breaks without it:** no way to create the initial console account (chicken-and-egg).
**Functions:**
- `upsert_user(username, password) -> str` (L19) — inside `with unit_of_work() as session`: SELECT
  the user by username; if absent, INSERT a new `AppUser(password_hash=hash_password(password),
  is_active=True, totp_enabled=False)`, flush; if present, RESET `password_hash = hash_password(...)`
  and force `is_active=True`, flush; return `str(user.id)`. **Edge case:** idempotent — re-running
  resets the password rather than erroring (a password-reset path), and the new user is created
  **without 2FA** (enrol later).
- `main(argv) -> int` (L42) — arg-count guard: `if len(argv) != 2: print(usage, file=sys.stderr);
  return 2`; else upsert and print `upserted user '<u>' (id=<id>)`; return 0.
- `if __name__ == "__main__": raise SystemExit(main(sys.argv[1:]))` (L52).

---

## 3. `app/comms/**` — supplier communications (E-37), DETERMINISTIC template-merge (NOT LLM)

Decision: the buyer authors plain-text email templates with `[#PlaceholderName]` tokens; this package
**parses and FILLS them from governed data** — a mail-merge, the same reproducible/auditable pattern
as the workbook generators. **No AI/LLM** anywhere in this package (verified: no anthropic/openai/etc.
imports; pure stdlib + sqlalchemy + pydantic).

### 3.1 `comms/__init__.py` — census #64 · py · 346 B · not empty
**What:** package docstring: deterministic template-merge email drafts; `merge` is the pure engine,
the resolvers + draft surface build on top. No code. **WHY:** package marker + the "NOT AI" contract.

### 3.2 `comms/merge.py` — census #65 · py · 3262 B · not empty — THE PURE MERGE ENGINE
**What:** the scalar placeholder parser+filler. Pure stdlib (`re`, `Mapping`, `dataclass`) — no DB,
no app imports — so it is trivially testable and reusable by every touchpoint.
**Detailed WHY:** one definition of the merge arithmetic so every email path fills the same way and a
draft never goes out with an invisible gap. **Breaks without it:** every resolver would re-implement
placeholder substitution and drift.
**The token regex (L24):** `_TOKEN = re.compile(r"\[#([A-Za-z0-9_]+)\]")` — a `[#Name]` token is a
leading `#` then `[A-Za-z0-9_]+` inside square brackets with `]` immediately after the name.
**Edge cases (left as-is, NOT tokens):** `[plain]`, `[# spaced]`, `[#]` — none match, so they pass
through unchanged. WHY this exact shape: lets a subject carry literal `[RFP:…]`/`[SUP:…]` routing
wrappers without them being treated as placeholders.
**`MergeResult` dataclass (frozen):** `text: str`, `used: tuple[str,...]` (filled names, first-seen
order), `missing: tuple[str,...]` (present-but-unfillable names, left in the text).
**`placeholders(template) -> list[str]` (L38):** distinct placeholder names in first-seen order — for
showing the buyer which fields a template needs before any merge.
**`merge(template, context) -> MergeResult` (L53):** for each `[#Name]` match, `value =
context.get(name)`; **a placeholder is "filled" ONLY when the value is not None AND not `""`**
(L68). On fill: append to `used` (dedup), return `value`. On miss (unknown name, `None`, or empty
string): append to `missing` (dedup) and return `match.group(0)` — i.e. **leave the literal `[#Name]`
in place** (L74). **WHY a visible hole, not a silent blank:** the caller can refuse to mark a draft
ready/SENT while `missing` is non-empty. **Determinism:** same template + context → identical result.

### 3.3 `comms/render.py` — census #66 · py · 3859 B · not empty — TABLE-AWARE RENDER
**What:** adds the two structures the buyer's authored templates use on top of the scalar `merge`:
a **subject line with machine-readable bracket tags first**, and **table/block placeholders** that
expand to a header + one row per record.
**Detailed WHY:** `merge` only fills scalars; touchpoints need subjects a downstream router (Power
Automate) can parse on a stable tag even if human wording changes, and need per-row tables (e.g. the
incomplete-bid list). **Breaks without it:** no subject/table rendering — only flat scalar bodies.
**Dataclasses (frozen):**
- `TableSpec` — `name` (body placeholder e.g. "IncompleteBidTable"), `columns: tuple[str,...]`
  (header labels), `row: str` (per-row template e.g. `"[#DC] | [#Lot] | [#Item]"`).
- `CommsTemplate` — `email_type`, `subject`, `body`, `tables: tuple[TableSpec,...] = ()`.
- `EmailDraft` — `subject`, `body`, `missing: tuple[str,...]`.
**`_render_table(spec, rows) -> (text, missing)` (L54):** builds `header = " | ".join(spec.columns)`,
`separator = "-" * len(header)`. **Empty-rows edge case:** if `not rows`, returns
`f"{header}\n{separator}\n(none)"` (an explicit `(none)` line, never a blank table). Else for each
row `merge(spec.row, row)`, collect any per-row `missing` (dedup), append the merged line.
**`render(template, context, tables=None) -> EmailDraft` (L75):** ORDER OF OPERATIONS —
1. **tables expand first**: for each `spec in template.tables`, render the block and
   `body = body.replace(f"[#{spec.name}]", rendered)`; collect table `missing` (dedup).
2. then scalar `merge(body, context)` and `merge(template.subject, context)`.
3. union all `missing` (subject + body + tables), dedup, first-seen order.
**WHY tables before scalars:** a row template's `[#DC]` etc. must merge against the per-row dict, not
the scalar context; expanding first prevents the scalar pass from "missing" the row tokens.

### 3.4 `comms/templates.py` — census #68 · py · 4986 B · not empty — THE 7 AUTHORED TEMPLATES
**What:** the registry of the seven supplier-comms touchpoints, each a `CommsTemplate` pairing a
machine-readable subject with the buyer's authored body (loaded VERBATIM from a `.txt` data file) +
the specs for its `[#XxxTable]` blocks.
**Detailed WHY bodies are `.txt`, not Python strings (L6):** so the prose is never reflowed by code
formatters and the buyer can edit it directly; templates are versioned DATA (like the workbook
generators). **Breaks without it:** the resolvers have no templates to fill.
**Subject standard (L25):** `_TAGS = "[RFP:[#CycleID]] [SUP:[#SupplierID]]"` — routing tags FIRST so
a downstream parser routes on a stable tag even if the human wording moves. `_subject(infix)` →
`f"{_TAGS} {infix} – [#CycleName]"`. `_body(filename)` → `(_TEMPLATE_DIR / filename).read_text(
encoding="utf-8").rstrip("\n")` (trailing newline trimmed).
**`EmailType(StrEnum)` (L40) — the 7 touchpoints (value = the machine tag in the subject):**
`INVITATION="Invitation"`, `TEMPLATE="Template"`, `INCOMPLETE_BID="Incomplete Bid"`,
`ROUND_FEEDBACK="Round Feedback"`, `AWARD="Award Notification"`, `NON_SELECTION="RFP Results"`,
`PBA="PBA Transmittal"`.
**The 7 `CommsTemplate` definitions + their TableSpecs (every one):**
1. `_INVITATION` — subject infix `"Invitation"`, body `invitation.txt`, no tables.
2. `_TEMPLATE` — subject `"Template – Round [#RoundNumber]"`, body `template.txt`, no tables.
3. `_INCOMPLETE_BID` — body `incomplete_bid.txt`; **table `IncompleteBidTable`** cols
   `("DC","Lot","Item","Timeframe","Missing Fields")`, row
   `"[#DC] | [#Lot] | [#Item] | [#Timeframe] | [#MissingFields]"`.
4. `_ROUND_FEEDBACK` — subject `"Round [#RoundNumber] Feedback"`, body `round_feedback.txt`; **THREE
   tables**: `DCSummaryTable` (cols DC/Lots Above Target/Avg $ Premium/Avg % Premium/Estimated Weekly
   Impact; row `[#DC] | [#LotsAboveTarget] | [#AvgDollarPremium] | [#AvgPercentPremium] |
   [#EstWeeklyImpact]`), `HardAskTable` (DC/Lot/Issue/Current Value/Required Improvement; row
   `[#DC] | [#Lot] | [#IssueReason] | [#CurrentMetric] | [#TargetMetric]`), `SoftAskTable`
   (DC/Lot/Premium %/Market Benchmark/Improvement Opportunity; row `[#DC] | [#Lot] | [#PremiumPct] |
   [#BenchmarkPrice] | [#SuggestedTarget]`). **Docstring caveat (L11):** the `DCSummaryTable` columns
   are INFERRED (the author specified only the Hard/Soft ask tables) — a recorded authorship gap.
5. `_AWARD` — subject `"Award Notification"`, body `award.txt`, no tables.
6. `_NON_SELECTION` — subject `"RFP Results"`, body `non_selection.txt`; **table
   `RejectionReasonTable`** cols `("DC","Lot","Submitted Price","Benchmark Price","Difference %",
   "Reason")`, row `"[#DC] | [#Lot] | [#BidPrice] | [#BenchmarkPrice] | [#PremiumPct] | [#ReasonCode]"`.
7. `_PBA` — subject `"PBA Transmittal"`, body `pba.txt`, no tables.
**`REGISTRY: dict[EmailType, CommsTemplate]` (L133)** maps all 7; **`get_template(email_type)` (L144)**
returns the authored template (KeyError if an unknown type — caller passes an `EmailType`).

### 3.5 `comms/resolvers.py` — census #67 · py · 23154 B · not empty — THE PER-TOUCHPOINT RESOLVERS
**What:** builds the merge CONTEXT from the governed store for a given touchpoint and renders ONE
draft per supplier. **Draft-only** — nothing here sends; the buyer reviews/edits/sends.
**Detailed WHY:** the pure render core fills placeholders from a context; the resolvers are where the
context is sourced from `awd.*` / `eng.*` / `bid.*` / `cyc.*` records, supplier-by-supplier, with
each supplier seeing ONLY their own data (never a competitor's name or price). **Breaks without it:**
the templates have no governed data to fill — they'd be empty shells.

**THE 3/7 ROUTED-vs-UNROUTED FINDING (load-bearing, verified):** `resolvers.py` implements governed-
data resolvers for **only 3 of the 7** touchpoints — `award_drafts` (AWARD), `feedback_drafts`
(ROUND_FEEDBACK), and `rejection_drafts` (NON_SELECTION). These 3 are the **routed** touchpoints:
each is wired into `app/pilot/service.py` (imports at L33–37; calls at L2234/L2261/L2287) and
surfaced to the console via `app/api/v1/runs.py` (imports `SupplierEmailDraft` at L30). The other 4 —
**INVITATION, TEMPLATE, INCOMPLETE_BID, PBA** — exist as authored templates (`templates.py`/`.txt`)
with their TableSpecs, but have **NO resolver and no router/service caller** that pulls governed data
to fill them. They are the **unrouted** touchpoints: render-ready (covered by `tests/comms/
test_render.py`), but not yet wired to a data source or an endpoint. **WHY this is a known gap, not
silent drift:** the prompt itself flags "the 3/7 routed vs unrouted"; the 3 award-cycle-terminal
touchpoints (award/feedback/non-selection) are the ones the pilot run produces, and the 4 process-
front touchpoints (invite/template/incomplete-bid/PBA) await their resolver increment. Flagged here
as **DRIFT/PENDING: 4 of 7 comms touchpoints are template-only (no governed-data resolver wired).**

**Module constants:** `_ZERO = Decimal("0")`; `_DEFAULT_PREMIUM_CEILING = Decimal("0.12")` and
`_DEFAULT_COVERAGE_FLOOR = Decimal("0.80")` (mirror the pilot's engine-eligibility defaults when the
cycle sets no override); `_Cell = tuple[str, str, str]` (dc_id, lot_id, tf_id).
**`SupplierEmailDraft(BaseModel)`** — `supplier_id`, `supplier_name`, `email_type`, `subject`,
`body`, `missing: list[str]` (the visible `[#Name]` holes the buyer completes).

**Formatting helpers (every value transformation / decimal — formula + file:line):**
- `_fmt_date(value) -> str` (L60): `value.strftime("%b %d, %Y")` or `""` if None — e.g. "Jun 22, 2026".
- `_money(value, *, cents=True) -> str` (L145): `f"${value:,.2f}"` (cents) or `f"${value:,.0f}"`
  (whole) — thousands separators; 2-decimal money or 0-decimal whole dollars.
- `_pct(value) -> str` (L149): `f"{value * 100:.1f}%"` — a FRACTION → 1-decimal percent (0.123 → "12.3%").
- `_delivery_window(session, cycle_id) -> (str, str)` (L64): min `start_date` / max `end_date` over
  `cyc.cycle_timeframe` for the cycle, each via `_fmt_date`; `("", "")` when no timeframes.

**`award_drafts(...)` (L77) — AWARD touchpoint:**
- Reuses cycle-scoped `award_detail(session, cycle_view, award_id)` (raises ValueError → router 404 if
  the award isn't this run's). Groups `detail.lines` by supplier into `won_dcs`/`won_lots` (sets of
  distinct dc_id/lot_id). **Only awarded suppliers appear** (a not-awarded supplier is the
  non-selection touchpoint).
- Per supplier context: `AwardedDCCount = str(len(won_dcs[sup]))`, `AwardedLotCount =
  str(len(won_lots[sup]))`, delivery window from `_delivery_window`, plus SupplierName/ID,
  CycleName/ID, BuyerName/Title.
- **Per-supplier file safety (L122–126):** `AwardFileName` is set ONLY from
  `award_files.get(supplier_id)` (THIS supplier's own guide). If absent, `[#AwardFileName]` is left a
  visible `missing` hole — **never names another supplier's/award's file** (data-isolation rule).
- Renders `get_template(EmailType.AWARD)`; drafts sorted by `supplier_name`.

**Round-feedback path (L142–437) — ROUND_FEEDBACK touchpoint:**
- `_round_id_and_number(session, run_id) -> (round_id, 1-based number)` (L153): joins
  `eng.analysis_run` → `cyc.cycle_round`; **ValueError if the run is unknown**.
- `_constructed_price(all_in, fob, delivery, vegcool, lot_discount) -> Decimal|None` (L169): builds a
  `BidComponents` and calls the engine's §7 `construct_price` via a `BidInput` whose
  `landed_cost_per_case = comp.all_in or comp.fob or _ZERO`. **WHY:** comms uses EXACTLY the engine's
  price construction (no parallel arithmetic) — a component-basis bid (All-In NULL) still counts.
- `_round_prices(session, run_id) -> {cell: {supplier_id: price}}` (L199): joins `eng.bid_score` to
  the exact `bid.bid_line` it scored (by `bid_line_id`) and constructs each price. **WHY source the
  sealed run's OWN rows, not "current scoreable":** keeps the draft consistent with the rendered
  analysis even after a later resubmission supersedes those rows.
- `_eligibility(session, run_id)` (L228): per (supplier, dc, lot, tf) → `(is_eligible,
  COALESCE(gate_flags,''))` from `eng.bid_score`.
- `_weekly_volume(session, cycle_id)` (L243): per (dc, lot, tf) → `SUM(projected_weekly_cases)` from
  `cyc.cycle_projected_volume` joined to `cyc.cycle_lot_item` (item→lot remap). **Transformation:**
  this is the item→lot aggregation (sum over a lot's items) onto the engine cell grain.
- `_hard_ask_rows(flags, prem_pct, ceiling, floor)` (L258): **one row PER breached HARD gate** —
  GATE_PREMIUM → ("Price premium exceeds threshold", `_pct(prem_pct)`, "at or below `_pct(ceiling)`");
  GATE_COVERAGE → ("Insufficient volume offered", "below `_pct(floor)` of requirement", "at least
  `_pct(floor)`"). **Edge case:** if neither matched, a generic fallback row ("Not eligible for
  award", `_pct(prem_pct)`, "review submission"). WHY both: premium and coverage can fire together;
  the supplier sees EVERY change needed to regain eligibility.
- `feedback_drafts(...)` (L285): the orchestrator. **Threshold resolution (L309–320):** `ceiling`/
  `floor` use `cycle_view.premium_ceiling`/`coverage_floor` **`is not None`** (NOT truthiness) so a
  cycle that explicitly sets a `0` ceiling/floor quotes that 0, not the default. Per cell:
  `market_low = min(sup_prices.values())`; **skip cells with `market_low <= 0`** (no defined
  premium). Per supplier in the cell: `is_elig, flags`; `above = price > market_low`. **Branches:**
  (a) eligible AND at/below low → nothing to ask (continue); (b) **ineligible** → HARD ask rows
  (regardless of price position — a coverage gate can hit even the market-low bidder); (c) eligible
  but above → SOFT ask row. **Decimals:** `prem_dollar = premium_dollars(price, market_low)` (price −
  low), `prem_pct = premium_vs_low(price, market_low) or _ZERO` ((price−low)/low). Per-DC summary
  (`dc_agg`, L373–387) aggregates **above-benchmark lots only** (count/dollar/pct/impact);
  `impact = weekly_impact(prem_dollar, weekly_cases)` (premium $/case × weekly cases). Output per
  supplier: DCSummaryTable rows with `AvgDollarPremium = _money(dollar/count)`,
  `AvgPercentPremium = _pct(pct/count)`, `EstWeeklyImpact = _money(impact, cents=False)`; Hard/Soft
  tables sorted by (DC, Lot). A draft is emitted for **any supplier with a hard OR soft ask**.

**`rejection_drafts(...)` (L440–571) — NON_SELECTION touchpoint:**
- `_LostLot` dataclass accumulates a supplier's averaged standing on a (dc, lot) they did NOT win,
  across its timeframes (`bid_sum`, `low_sum`, `count`, `ineligible`, `flags`).
- `_rejection_reason(ineligible, flags)` (L454): if ineligible → GATE_NO_PRICE "No valid price
  submitted" / GATE_PREMIUM "Price premium above ceiling" / GATE_COVERAGE "Insufficient volume
  offered" / else "Did not meet eligibility criteria"; if eligible-but-lost → "Not selected (lower
  competitive rank)".
- `rejection_drafts` (L468): keyed on the **frozen award** (the settled who-won-what). Loads the
  `Award` (ValueError if not this cycle's → 404). `prices = _round_prices(run)`; `eligibility`;
  `awarded = {(dc, lot, tf, sup) from awd.award_line}`. Per cell with `market_low > 0`, per supplier
  NOT in `awarded` for that cell: accumulate into `_LostLot` (bid+low+count, ineligible flag, flags).
  **Per (dc,lot) averaging (L537–540):** `avg_bid = bid_sum/count`, `avg_low = low_sum/count`,
  `prem_pct = premium_vs_low(avg_bid, avg_low) or _ZERO`. Row cols: BidPrice `_money(avg_bid)`,
  BenchmarkPrice `_money(avg_low)`, PremiumPct `_pct(prem_pct)`, ReasonCode `_rejection_reason(...)`.
  **Edge case:** a supplier awarded EVERY cell they bid gets NO draft (they got the award notice).
  Each supplier sees only their own bid + an anonymous benchmark — **never a competitor's name/price.**

### 3.6 The 7 template `.txt` data files (census #69–75) — every one, verbatim structure
Each `.txt` is the buyer's authored email BODY (plain text, `[#Placeholder]` / `[#XxxTable]` tokens,
LF-terminated, loaded with trailing `\n` trimmed). All seven end with the same sign-off block:
`Best Regards,` / blank / `[#BuyerName]` / `[#BuyerTitle]` / `The Kroger Co.`. **Why `.txt` not code:**
buyer-editable, never reflowed (see §3.4). None empty.
- **`award.txt`** (#69, 672 B): award notification; placeholders SupplierName, CycleName,
  AwardedDCCount, AwardedLotCount, DeliveryStartDate, DeliveryEndDate, AwardFileName, BuyerName/Title.
- **`incomplete_bid.txt`** (#70, 486 B): intake-validation incomplete notice; SupplierName, CycleName,
  `[#IncompleteBidTable]`, **`[#CorrectionDueDate]`** (an unrouted scalar — no resolver fills it yet).
- **`invitation.txt`** (#71, 632 B): event invitation; CycleName, ProcessStartDate, BidDueDate,
  RoundCount, EstimatedAwardDate, DeliveryStartDate/EndDate (all unrouted — no resolver).
- **`non_selection.txt`** (#72, 519 B): RFP-results; SupplierName, CycleName, `[#RejectionReasonTable]`.
- **`pba.txt`** (#73, 495 B): Produce Buying Agreement transmittal; EffectiveDate, ExpirationDate,
  PBAFileName (unrouted).
- **`round_feedback.txt`** (#74, 520 B): round feedback; RoundNumber, CycleName, and the three blocks
  `[#DCSummaryTable]` / `[#HardAskTable]` / `[#SoftAskTable]`.
- **`template.txt`** (#75, 512 B): bid-template transmittal; RoundNumber, CycleName, BidDueDate,
  TemplateFileName (unrouted).

---

## 4. `app/output/**` — the client-workbook / deliverable generators

Extracted out of `demo/run_cycle_demo.py` so any feature (the pilot, not just the demo) reuses the
generators from a `CycleView`. **The app layer never imports from the demo.** Render-on-request: the
bytes builders are the no-file-storage path; the `*_xlsx` disk wrappers are the MCP-harness vault path.

### 4.1 `output/__init__.py` — census #142 · py · 686 B · not empty
**What:** re-exports `write_scenario_workbook_xlsx`, `CycleView`, `Entity`, `SeededCycle`
(`__all__`). **WHY:** one import surface for the output layer; documents that the app reuses the
demo's presentation language from ONE place and never imports the demo.

### 4.2 `output/types.py` — census #149 · py · 2400 B · not empty — THE RESOLVED CYCLE VIEW
**What:** `Entity(id, code, name)` (frozen) and `CycleView` (mutable dataclass) — the in-memory,
name-resolved view of a cycle's scope every generator reads.
**Detailed WHY:** the generators must run IDENTICALLY for a synthetic demo cycle and a real persisted
cycle, so the scope is abstracted into one structure buildable two ways (demo `seed_cycle` OR
`app.cycle.loader.load_cycle`). **Breaks without it:** the generators would each query the DB
differently and drift between demo and live.
**`CycleView` fields (every one):** `cycle_id/code/name`, `client_id`, `commodity_id`,
`dcs/lots/items/tfs/rounds/suppliers: list[Entity]` (**`items[i]` belongs to `lots[i]`** and
**`rounds[i].code == "R{i+1}"`** — the index alignment the generator relies on),
`incumbent_by_dc_lot: dict[(dc_id,lot_id)->supplier_id]`, `incumbent_routing:
dict[(dc_id,lot_id)->Decimal]` (routing baseline), `period_cases_by_cell: dict[(dc_id,lot_id,tf_id)->
Decimal]`, `commodity_name=""`, `horizon_weeks=0` (sum of TF week counts — the real horizon), and the
per-RFP engine safeties `premium_ceiling/coverage_floor/conc_thresh: Decimal|None`, `max_sup_dc:
int|None`, `weight_preset: str|None` (**None = use the strategy-preset default**). `SeededCycle =
CycleView` (back-compat alias for the demo's call sites).

### 4.3 `output/formatting.py` — census #145 · py · 8357 B · not empty — THE D24 STYLING PASS
**What:** the shared presentation language for EVERY client-openable xlsx: titled header block, bold
white-on-color header row, column widths, `$`/`%` number formats, thin borders, freeze panes, a TOTAL
row, AutoFilter. **NOT a raw CSV-like dump (D24).**
**Detailed WHY:** one place so every workbook (booking guide, scenario workbook, post-award doc) reads
in the same visual language; **breaks without it:** each generator re-styles inconsistently.
**Number-format constants (the decimal vocabulary — every output number routes through one of these):**
`NUMFMT_MONEY = "$#,##0.00"` (2-dp money), `NUMFMT_PCT = "0.0%"` (a FRACTION → 1-dp %; 0.05→"5.0%"),
`NUMFMT_PCT_WHOLE = "0.0%"`, `NUMFMT_INT = "#,##0"` (thousands-grouped integer). Brand palette fills
(navy header `1F3864`, title `2E5496`, total band `D9E1F2`) + accent fills (min/best green `C6EFCE`,
Scenario-A benchmark peach `FCE4D6`, Scenario-B rec blue `DDEBF7`, rec-pick `BDD7EE`, incumbent amber
`FFF2CC`, cap-breach red `FFC7CE`). `DECISION_SUPPORT_STRAP = "DECISION-SUPPORT — recommends, does
not assert"` (ADR-0006) — the provenance strap every surface carries.
**`Col(header, width=16, number_format=None, total="")` (frozen):** one column spec; `total="sum"` →
a `=SUM(...)` cell in the TOTAL row.
**`_title_block(ws, *, title, subtitle_lines, span, start_row=1) -> int` (L69):** writes the merged
banner (row 1 = title in `_TITLE_FONT`/`_TITLE_FILL`, height 22; following rows = italic subtitle
lines; whole block merged across `span` columns), returns the next free row after a blank spacer.
**`format_table(...) -> dict[str,int]` (L107):** the full styling pass over a sheet whose body is
ALREADY written (caller writes data at `header_row+1`). Steps + edge cases:
- title banner (computes `header_row` from banner height if not passed);
- header row bold white-on-color, centered/wrapped/bordered; **formula-injection guard (L143):** if a
  header text starts with `= + - @`, force `cell.data_type = "s"` so Excel doesn't treat the label as
  a formula and "repair" the file;
- body number formats + borders + alignment (`_CENTER` for numeric cols, `_LEFT` for text);
- **TOTAL row** only `if add_total and n_body_rows > 0`: for `total=="sum"` cols, writes
  `=SUM({letter}{body_start}:{letter}{body_end})` with the col's number_format (or `NUMFMT_INT`);
- freeze panes directly under the header;
- **AutoFilter** only `if add_autofilter and n_body_rows > 0`, spanning `A{header_row}:{last}{body_end}`
  (excludes the title banner and the total row);
- returns `{header_row, body_start, body_end, total_row}` (total_row falls back to body_end if none).

### 4.4 `output/synthetic.py` — census #148 · py · 2697 B · not empty — SYNTHETIC region/transit model
**What:** DEMO-illustrative region/transit/freight attributes derived deterministically so BOTH the
demo seed AND the generator read them from ONE place and produce identical results. **SYNTHETIC ONLY**
(no schema column yet). **WHY here, not inline:** so the demo's fill and the workbook's read can't drift.
**Constants/derivations (with the exact synthetic numbers):** `WEEKS_PER_TF = 13` (weeks per timeframe;
drives projected volumes AND the Controls horizon AND the capacity-check weekly divisor);
`DC_NAMES` (Atlanta/Dallas/Denver with ATL/DAL/DEN codes); `LOT_PRODUCT_TYPE =
("Conventional","Conventional","Organic","Organic")` (per-lot product type for the Award-Summary
split); `DC_REGION_GROUP = {ATL:East, DAL:South, DEN:West}`; `REGION_FREIGHT = {East:1.40,
South:1.85, West:2.40}` (per-region delivery $/case); `VEGCOOL_SURCHARGE_CASE = 0.35`;
`_dc_region(dc_index)` (region by seed index); `_transit_days(sup_index, dc_index) =
2 + (sup_index*2 + dc_index*3) % 5` (deterministic 2–6 day lane transit); `FRESHNESS_WATCH_DAYS = 4`
(transit beyond this flags a freshness/lead-time watch — the hidden cost on perishable produce).
**Decimal WHY:** these decompose the synthetic All-In into FOB + Delivery (by region) + VegCool so the
LANDED price the engine scores is UNCHANGED but the freight is transparent on the FOB tab.

### 4.5 `output/capacity_check.py` — census #144 · py · 7430 B · not empty — E-38 capacity evaluator
**What:** "never recommend an award beyond a supplier's STATED capacity." Pure `evaluate_capacity`
+ the sealed-record reader `load_active_capacity`. **Decision-support only — FLAGS over-capacity,
never changes an award (ADR-0006).**
**Detailed WHY:** the accuracy core's safety question; **breaks without it:** the workbook's Capacity
Check tab has nothing to compute and the buyer could book beyond stated supply.
**Grain:** per supplier × dc × lot × tf (the engine award's grain). Two comparisons: **PERIOD**
(allocated total over the TF vs `max_period_cases`) and **WEEKLY** (allocated/weeks vs
`max_weekly_cases`, weeks = `WEEKS_PER_TF`); a cell flags if EITHER is exceeded. When a (supplier,
cell) has multiple stated constraints, the **TIGHTEST (MIN) of each ceiling is taken INDEPENDENTLY**
(weekly and period min'd separately) — conservative, never understates.
**`StatedCapacity(max_weekly_cases, max_period_cases)`** (either/both may be None, at least one set);
**`CapacityCheckRow`** carries `allocated_cases` (= period_cases × volume_share), `allocated_weekly_
cases` (= allocated / weeks_per_tf), the ceilings, `has_statement`, `over_period`, `over_weekly`, plus
`over_capacity` (= over_period or over_weekly) and `status` ("No stated capacity" / "OVER CAPACITY" /
"Within capacity") properties.
**`evaluate_capacity(award_cells, capacity_by_cell, *, weeks_per_tf) -> list[CapacityCheckRow]` (L87):**
- **Edge case (fails LOUD):** `if weeks_per_tf <= 0: raise ValueError` — the weekly check is undefined
  without a week count; it must fail rather than silently treat a real weekly overage as in-capacity.
- per cell: `allocated = awarded_cases(c.period_cases, c.volume_share)` (period × share);
  `weekly = allocated / weeks_per_tf`. **No-statement branch:** `cap is None` → a row with
  `has_statement=False`, never flagged. **Statement branch:** `over_period = max_period_cases is not
  None and allocated > max_period_cases`; `over_weekly = max_weekly_cases is not None and weekly >
  max_weekly_cases`.
**`load_active_capacity(session, cycle_id) -> dict[CellKey, StatedCapacity]` (L154):** reads
`bid.capacity_constraint` JOIN `bid.capacity_statement` WHERE `cycle_id=:c AND cs.status <>
'SUPERSEDED' AND cc.scope_type = 'CELL'`, `MIN(max_weekly_cases)`, `MIN(max_period_cases)` GROUP BY
(supplier, dc, lot, tf). **WHY status<>'SUPERSEDED':** a re-submission supersedes its predecessor so
the latest ceilings win. **WHY MIN of each independently:** conservative on both dimensions.

### 4.6 `output/booking_guide.py` — census #143 · py · 14965 B · not empty — THE POST-AWARD BOOKING GUIDE
**What:** the LAST step of the loop (D22) — generated FROM THE FROZEN AWARD (never off a scenario):
the buyers/pricing internal master, the per-supplier guides in one workbook, and the per-supplier
SEPARATE files for E-37 attachment.
**Detailed WHY:** pricing uses the internal master to update the system (D9); each supplier gets ONLY
its own awarded data (a supplier's award email must never expose another supplier's awards). The award
is described STRUCTURALLY (`BookingAwardView`/`BookingCellView` Protocols) so the demo's concrete
types and a pilot award assembled from `awd.award_line` both satisfy it without this module depending
on them. **Names not keys (D23):** every readable cell renders the resolved NAME; a trailing key-ref
column trails for traceability. **Breaks without it:** no post-award deliverable.
**Protocols:** `BookingCellView` (dc/lot/item/tf/supplier ids + `volume_share`, `awarded_price`,
`period_cases`, `routing_baseline`), `BookingAwardView` (`scenario_code`, `scenario_label`, `cells`).
**`_provenance_line(synthetic)` (L90):** "SYNTHETIC — names & prices invented" vs "LIVE CYCLE DATA —
real names & prices".
**`build_booking_guide_internal_bytes(cycle, award, *, synthetic=False) -> bytes` (L100):** one row per
awarded **DC × lot × item × TF**. **Columns (13) + formats:** DC, Lot, Item, Timeframe, Awarded
Supplier (all text/NAME), **Volume Share** (`NUMFMT_PCT`), **FOB $/case** (`NUMFMT_MONEY`), **Landed
$/case** (`NUMFMT_MONEY`), **Awarded Period Cases** (`NUMFMT_INT`, total=sum), **Line Spend**
(`NUMFMT_MONEY`, total=sum), **Routing Baseline $/case** (`NUMFMT_MONEY`), **Savings vs Baseline**
(`NUMFMT_PCT`), Key ref (DC·lot·sup). **Value transformations per row (formula+line):**
`savings_frac = savings_fraction(c.routing_baseline, c.awarded_price)` (L147; (base−price)/base, 0 if
base≤0); `cases = awarded_cases(c.period_cases, c.volume_share)` (L148; period×share);
`line_spend(c.awarded_price, cases)` (L163; price×cases). **Precision note:** every Decimal is cast to
`float(...)` at the cell-write boundary (e.g. L158–166) so openpyxl stores a number and the cell's
`number_format` renders the displayed precision; the underlying Decimal arithmetic is exact and the
float cast is only for the spreadsheet cell. **Demo note (L159):** the demo uses All-In as BOTH the
FOB and the landed basis (placeholders) — both columns show `awarded_price`.
**`write_booking_guide_internal_xlsx(...)` (L188):** disk wrapper (mkdir + write_bytes).
**`build_supplier_award_guides_bytes(...)` (L203):** one SHEET per awarded supplier (sorted by name),
each showing ONLY that supplier's cells. **Columns (8):** DC, Lot, Item, Timeframe, Volume Share
(PCT), Awarded Period Cases (INT, sum), Awarded $/case (MONEY), Line Spend (MONEY, sum). Drops the
default empty sheet once a real one is added.
**`write_supplier_award_guides_xlsx(...)` (L283):** disk wrapper.
**`supplier_guide_label(award_id, award_code, supplier_name, supplier_id) -> str` (L307):** the
`stage_filename` LABEL = `f"award_guide_{award_code}_{supplier_name}_{supplier_id[:6]}_{award_id}"`.
**WHY the award_id suffix:** award codes aren't enforced unique, so the unique award PK keeps two
awards' per-supplier files from colliding and a draft from pointing at the wrong award's guide.
**`write_supplier_award_guide_files(..., paths_by_supplier, ...)` (L322):** one SEPARATE one-sheet
workbook per supplier (reusing the renderer over a `_SingleSupplierAward` view). **WHY separate files,
not the combined workbook:** the combined one exposes every supplier's volumes/prices — unsafe to
attach to a single supplier's email. **Edge case:** a supplier with no awarded cells is skipped.
**`build_supplier_award_guide_bytes(cycle, award, supplier_id, ...)` (L350):** the single-supplier
slice for the web console's render-on-request path; returns None if the supplier is unawarded.
**`_sheet_title(name)` (L370):** Excel-safe (`<=31` chars, strips `[]:*?/\`) sheet title; falls back
to "Supplier".

### 4.7 `output/post_award_doc.py` — census #146 · py · 13611 B · not empty — POST-AWARD ADJUSTMENTS doc
**What:** renders the versioned post-award adjustment picture for a frozen award (ADR-0014
freeze-and-layer): version history v0→vN, the current effective price per cell at a chosen version,
and the per-cell changes that version introduced. Three tabs. **Reads, never mutates.**
**Detailed WHY:** the frozen baseline (`awd.award_line`) is the immutable raw award; the effective
price is that baseline overlaid by the append-only versioned layers (`awd.award_adjustment` /
`awd.award_adjustment_line`). The doc carries a PROMINENT "which version" heading (PILOT step 5).
**Breaks without it:** no post-award change record/deliverable.
**Constants:** `VERSION_SUBTITLE = "Version {n} · as of {effective_date}"`; `BANNER_TITLE =
"POST-AWARD ADJUSTMENTS — {award_code}"`.
**`_Names`** (dc/supplier/lot/tf name dicts) + `cell_label((dc,lot,tf,supplier)) -> (DC, Lot,
Supplier, TF)` names (D23). **`_resolve_names(session, award)` (L77):** DCs/suppliers from `ref.dc` /
`ref.supplier` (`canonical_name`) via `text()` (not ORM-mapped), lots/TFs from `cyc.cycle_lot` /
`cyc.cycle_timeframe` (ORM) by `award.cycle_id`. All reads keyed (D21), rendered by name (D23).
**`build_post_award_adjustments_bytes(session, *, award_id, as_of_version=None) -> bytes` (L107):**
loads the `Award` (`scalar_one()`); `history = award_versions(...)`; `latest_version = max(version_no,
default=0)`; **`version_n = min(as_of_version or latest, latest)`** (clamps an out-of-range as-of to
the latest). Heading effective date = the as-of version's effective date (v0 = `frozen_at`). Writes
the three tabs.
**`_write_versions_tab` (L169):** cols Version (INT), Type, Effective Date, Reason, Recorded By,
Recorded At, # Cells Changed (INT); the reason/type come from the STORED rows (D28: no hardcoded
reasons); dates formatted `%Y-%m-%d` / `%Y-%m-%d %H:%M`; `add_total=False`; `_bold_subtitle`.
**`_write_effective_tab` (L214):** per cell — Frozen Baseline $/case (`AwardLine.frozen_price`),
Effective $/case (v{n}) (`effective_award(...)`), **Cumulative Δ $/case = `price_delta(eff, base)`**
(eff − base, L263). `eff = effective.get(key, base)` (baseline if no layer touched the cell).
**`_write_changes_tab` (L279):** the per-cell prior→new for version N (only `if version_n >= 1`),
reading `awd.award_adjustment_line` joined to `awd.award_adjustment` WHERE version_no=N; cols Prior /
New / Δ $/case (the stored `delta`). **Empty-version edge case (L342):** if no changes, writes a note
"No per-cell price changes recorded for this version (v0 = frozen baseline)."
**`_sorted_cells` (L362):** deterministic order by resolved (DC,Lot,Supplier,TF) names.
**`_bold_subtitle(ws, span)` (L368):** re-styles banner row 2 (the `Version N · as of …` line) BOLD so
the which-version line stands out (PILOT step 5).

### 4.8 `output/scenario_workbook.py` — census #147 · py · 183077 B · not empty — THE 18-TAB ALIGNMENT WORKBOOK
**What:** the team-alignment / comparison Scenario Workbook (D26/D27) generated from a SEALED engine
run + a `CycleView` + an `EngineConfig`. Reads ONLY governed sealed records (`eng.*`, `bid.bid_line`,
`awd.*`, `cyc.*`) — never the demo. The award is structural (`AwardView`/`AwardCellView` Protocols).
**Detailed WHY:** this is the surface buyers/category/sourcing work through to DECIDE in the alignment
call — manipulable (pivot/drill/filter/live, D27), not fixed tables. Every readable cell is a NAME
(D23); decision-support only (ADR-0006). **Breaks without it:** no alignment deliverable. This is the
single largest module in B6 (4280 lines); read end-to-end.

**`CellInfo`** (the per-(DC×lot×item×TF) competitive picture: names, `volume`, `baseline_price`,
`incumbent_name`, `eligible_suppliers`, `rec_supplier`, `rec_score`, `price_by_supplier`,
`score_by_supplier`, `transit_by_supplier`, `rec_type`) — the unit the Supplier Comparison + Custom
tabs are built on.

**Gather functions (every value transformation / SQL with WHY):**
- `_transit_by_lane(session, cycle_id)` (L198): real supplier→DC transit from `bid.bid_line.transit_
  days`, `MAX(...)` over `is_scoreable = true` rows GROUP BY (supplier, dc). **WHY MAX + is_scoreable:**
  a superseded submission's transit must not win the MAX; fan-out is a non-issue (period rows replicate
  the value). Only lanes with a value appear (no synthetic proxy).
- `_line_price(all_in, fob, delivery, vegcool, lot_discount) -> Decimal|None` (L219): wraps
  `construct_price_from_parts(...)` — **the canonical §7 price** (All-In verbatim if present, else
  FOB + delivery + vegcool − lot_discount). **WHY route EVERY price read through this:** reading raw
  `submitted_all_in_case` alone DROPPED component-basis bids (All-In NULL) the engine scored, making
  them vanish from grids/stats/coverage/FOB while awards used the constructed price.
- `_gather_cells(...)` (L240): **Option-B de-fan (L272–282):** bids are STORED flat at the 13 fiscal
  periods (≤13 identical rows per cell); the competitive grid is TIMEFRAME-grain, so the SQL uses
  `DISTINCT ON (supplier_id, dc_id, lot_id, tf_id) … ORDER BY …, fiscal_period_id NULLS LAST,
  bid_line_id` over `is_scoreable = true` rows to collapse to ONE price per cell. **WHY:** the fanned
  rows are identical, so the deduped read is byte-identical to the pre-fan-out timeframe grain (and
  a superseded re-submission can't leak a stale price). Eligibility + RecScore from `eng.bid_score`;
  the B pick from `award.cells`; the engine's authoritative per-cell `rec_type` from
  `eng.analysis_scenario_award` JOIN scenario WHERE `scenario_code='B'` (D28: render the engine's
  reason, never hardcode). **Dropdown/edge logic (L350–356):** always include the rec pick even if
  gated elsewhere; if no eligible names, fall back to anyone who priced (dropdown never empty); dedup.

- `ScenarioRollup` + `_gather_scenario_rollups(...)` (L418): rolls each lens A–G to spend/deltas/
  savings/counts/breaches. **`_STLY_UPLIFT = Decimal("1.04")`** (L415) — prior-year actual-paid modeled
  ~4% over this year's incumbent-routing baseline (a clearly-labelled SYNTHETIC reference, D11/D26).
  `baseline_total = Σ line_spend(incumbent_routing[(dc,lot)], cases)`; `stly_total = (baseline_total *
  1.04).quantize(Decimal("0.01"))` (L444 — **the one explicit quantize: STLY rounded to cents**). Per
  award row: `line = line_spend(price, awarded_cases(cases, share))`; `delta_vs_a = spend − a_spend`;
  `savings_vs_baseline_frac = savings_fraction(baseline_total, spend)`; `savings_vs_stly_frac =
  savings_fraction(stly_total, spend)`.
- `AwardDetail` + `_gather_award_details(...)` (L548): one fully-resolved line per (scenario × DC ×
  lot × item × TF × supplier). `cases = awarded_cases(vol_by_cell[cell], share)`; `spend =
  line_spend(price, cases)`; `baseline_spend = line_spend(baseline, cases)`; `savings_vs_baseline =
  savings_dollars(baseline_spend, spend)`; `premium_vs_baseline_frac = delta_vs_historical(price,
  baseline) or 0` ((price−base)/base); the five factor scores + RecScore joined from `eng.bid_score`;
  `relationship = "Preserve" if is_incumbent else "Create"`.

**Tabs written (every tab, its columns, its number formats, its conditional formatting):**
The orchestrator `build_scenario_workbook_bytes` (L4044) writes them in this order (`wb.calculation.
fullCalcOnLoad = True` so Excel resolves the live cross-tab formulas on open):
1. **Summary / Overview** (`_write_summary_tab`, L651): banner = "MID-CYCLE ALIGNMENT ANALYSIS"
   with the run version heading (`Analysis v{seq}`, round, `sealed {…:%Y-%m-%d %H:%M}`). 2-col
   Item/Value table: Cycle, Scope, Strategy (preset + weights), **Headline (A vs B)** computed as
   `delta_pct = (rec.total_spend − bench.total_spend)/bench.total_spend*100` with above/below
   direction and `savings_vs_baseline_frac*100:.1f%`, and a How-to-use line. Then `_write_kpi_band`
   (the four-lens scorecard: Savings `${:,.0f}`, Savings % `{:.1%}`, Avg transit `{:.1f}`, Freshness
   watches, Preserved/Created, Incumbent-vs-field move) and `_augment_summary_index` (the banded tab
   index — the front door).
2. **Controls** (`_write_controls_tab`, L2726): key/value cockpit banded by section (Cycle / Scope /
   Baselines / Engine weights / Engine rules). `total_weeks = horizon_weeks or len(tfs)*WEEKS_PER_TF`;
   `rec_savings = baseline_total − rec_spend`. Weights/thresholds shown as `NUMFMT_PCT`, counts as
   `NUMFMT_INT`, money as `NUMFMT_MONEY`. Note line labels what's schema-backed vs modeled.
3. **Award Summary (Sign-off)** (`_write_award_summary_tab`, L2841): per DC, Incumbent → Recommended.
   Cols: DC, Incumbent, Recommended, Cells (INT,sum), Rec spend (MONEY,sum), Incumbent baseline
   (MONEY,sum), Savings vs incumbent $ (MONEY,sum), Savings vs incumbent % (PCT), Savings vs STLY $
   (MONEY,sum), Negotiation R1→Final $ (MONEY,sum). `sav_inc = baseline_spend − rec_spend`;
   `sav_inc_pct = sav_inc/baseline_spend`; `stly_spend += baseline_spend * _STLY_UPLIFT`. **TOTAL-row
   blended % (L2932):** `=G{total}/F{total}` (total savings / total baseline — a sum of % is
   meaningless). CF: savings $ green>0 / red<0 on cols G,I,J. Product-type split (Conventional/Organic
   via `LOT_PRODUCT_TYPE`).
4. **Scenario Comparison** (`_write_scenario_comparison_tab`, L1063): rows A–G + a **LIVE Custom row**
   (formulas off the Custom Scenario tab). Cols: Lens, Scenario (label), Total Spend (MONEY), Δ vs A
   (MONEY), Savings vs Baseline (PCT), Savings vs STLY* (PCT), # Suppliers (INT), # Cap-Breaches (INT),
   # Cells (INT). Custom row formulas: total `={Custom!$K$total}`; Δ vs A `=total−$C$bodystart`;
   savings `=IF(base=0,0,(base−total)/base)` and the STLY analog; # suppliers a distinct-count
   SUMPRODUCT/COUNTIF over the Custom supplier column. A/B rows tinted (peach/blue). Then the
   **EXPANDABLE DRILL** (`_write_scenario_drill` + `_write_custom_drill`, outline levels 0/1/2,
   `summaryBelow=False`, opens collapsed) and the **PER-DC MATRIX** (DCs down × scenarios across →
   spend + supplier-mix sub-row).
   - `_DRILL_HEADERS` (L787): Scenario/DC/Supplier, Spend (MONEY), Volume (INT), Savings vs Baseline
     (MONEY), # Suppliers / $/case (MONEY), Volume share (PCT), Premium vs Baseline (PCT), Flags.
   - `_custom_refs(n_cells)` (L959): deterministic A1 ranges into the Custom tab (header_row=6 fixed),
     so the live Custom column references it by address.
5. **Lowest-Cost Check** (`_write_lowest_cost_check_tab`, L1971): per cell the rec vs market-low.
   Cols: DC, Lot, Item, Timeframe, Recommended, Rec $/case (MONEY), Market-low $/case (MONEY), Premium
   vs Low (PCT), Is Lowest?, Why not lowest. `prem = (rec_price − min_price)/min_price`; `is_lowest =
   abs(rec_price − min_price) < Decimal("0.005")` (a half-cent tolerance, L2005). `_rec_type_reason`
   (L1942) RENDERS the engine's authoritative `rec_type` (Lowest cost / Coverage advantage /
   Comparable / Defensible / Risk-adjusted) — never re-derives it (D28). CF: premium > 0.07 amber.
6. **Supplier Comparison** (THE CENTERPIECE, `_write_supplier_comparison_tab`, L1243): one row per
   cell; lead cols DC/Lot/Item/Timeframe/Demand(INT,sum)/Baseline $/case(MONEY)/Incumbent/Incumbent
   $/case(MONEY); then **one $/case col PER SUPPLIER** (MONEY, blank if no bid); then Min $/case
   (MONEY)/Recommended/RecScore(INT); then **one cost-impact col PER SUPPLIER** (PCT). Per-row impact
   `=(p − baseline_price)/baseline_price` when baseline>0. **CF:** per-row MIN highlighted green
   (`FormulaRule` `AND(cell<>"", cell=MIN(row range))`, L1353); impact > `config.global_premium_
   threshold` red (`CellIsRule greaterThan`, L1365). Rec-pick cell tinted blue+bold, incumbent amber.
7. **Landed & Hidden Costs (FOB)** (`_write_fob_analysis_tab`, L3072; data `_gather_fob`, L3013): per
   (lot × DC × supplier) FOB → +Delivery → +VegCool → = All-In decomposition (constructed via
   `_line_price`), `freight = delivery + vegcool`, `freight_pct = freight/all_in`, transit + freshness
   watch (transit > `FRESHNESS_WATCH_DAYS`). Cheapest landed per (lot,DC) green. Cols incl. FOB/+
   Delivery/+VegCool/=All-In (all MONEY), Freight % of All-In (PCT), Transit (INT), Freshness.
   Regional freight summary (avg Delivery $/case by region).
8. **Share & Relationships** (`_write_share_relationships_tab`, L3385): per-supplier % share of total
   spend in EVERY scenario (heatmap `ColorScaleRule` white→`conc_thresh`→0.6 red), relationship
   (Preserve/Create), `Max share`, Dependency flag (`max >= conc_thresh`). `sh = spend[(code,sup)]/
   scen_total[code]`. Relationship ledger (preserved / created / dropped) for the recommendation.
9. **Incumbent Retention** (`_write_incumbent_retention_tab`, L3270; data `_gather_incumbent_
   retention`, L3214): per incumbent cell the $ cost to keep them vs the rec. Status = Retained-
   recommended / Eligible-not-pick / Gated-by-premium / No-bid. `premium_per_case = inc_price −
   rec_price`; `premium_period = premium_per_case * volume`; `premium_pct = premium_per_case/
   rec_price`. Premium-to-retain $ (MONEY, total=sum → the "RELATIONSHIP BUDGET"). Gated rows amber.
10. **Negotiation Dynamics** (`_write_negotiation_dynamics_tab`, L3589; data `_gather_negotiation`,
    L3524): per supplier the R1→final concession (`avg_move_frac`), avg premium vs low, sustainability
    flags (Z<−2 count), and a game-theoretic "read". DataBar on the concession col. Fairness verdict
    from `gap = inc_move − chal_move` (>0.005 leaning on tenure / <−0.005 defending competitively /
    else in line).
11. **Coverage** (`_write_coverage_tab`, L2228; data `_gather_coverage`, L2139): per (supplier × cell)
    offered vs required cases → `ratio = offered/required` → band (Critical<50% / Short<80% / Partial
    <100% / Full≤120% / Surplus>120%; As-Needed if req≤0). Cols incl. Cover Ratio (PCT). CF: ratio <
    `config.coverage_floor` red. Same Option-B `DISTINCT ON` de-fan as `_gather_cells`.
12. **Capacity Check** (`_write_capacity_check_tab`, L2346; data `_gather_capacity_check`, L2306):
    allocation vs stated capacity via `evaluate_capacity(..., weeks_per_tf=WEEKS_PER_TF)`. Over-
    capacity rows sort first; Status col CF `="OVER CAPACITY"` red. Allocated/wk = allocated ÷
    `WEEKS_PER_TF`.
13. **Detailed Scoring** (`_write_detailed_scoring_tab`, L2047; data `_gather_score_detail`, L1836):
    per scored bid the five factors + the market stats that explain them — Mkt Min/Avg, Prem vs Low,
    **Z-Score = (price − avg)/std**, # Bidders. `_stats` computes `avg = Σvals/n`, `var = Σ(v−avg)²/n`,
    `std = var.sqrt() if var>0 else 0` (population std on Decimal, L1893–1894). Same Option-B de-fan
    (so the bid COUNT isn't inflated ≤13×).
14. **TF Comparison** (`_write_tf_comparison_tab`, L2421) — **only if `len(tfs) > 1`**: per DC×lot the
    rec supplier+price in each TF side by side + a SPLIT flag when TFs award differently.
15. **Round Evolution** (`_write_round_evolution_tab`, L2556; data `_gather_round_evolution`, L2496) —
    **only if `len(rounds) > 1`** and a cell is priced in ≥2 rounds: per (supplier × cell) the $/case
    per round + `delta = last − first`, `pct = delta/first`, direction (↓/↑/→). Reads ALL rounds
    (`is_scoreable`), not just the final.
16. **Data Quality** (`_write_data_quality_tab`, L2601): no-bid cells (Σ `max(0, n_sup −
    len(price_by_supplier))`), thin-competition (<3 bidders), advisory gate-flag count, ineligible
    count — all **surfaced, non-blocking** (ADR-0006).
17. **Custom Scenario** (THE INTERACTIVE TAB, `_write_custom_scenario_tab`, L1438): one row per cell
    with a data-validation **Supplier dropdown** (list = the cell's eligible suppliers by NAME) and
    LIVE formulas — `$/case = SUMIFS(_Prices!$D, _Prices!$A, CellKey&"@"&Supplier)`; vs Min/Incumbent/
    Baseline % (SUMIFS against the `_Prices` reference grid); `Volume` literal; `Line Spend = price ×
    volume`; transit `=SUMIFS(...)`. Pre-filled with Scenario B. LIVE summary block (Total/Baseline/
    Savings $/%) + a per-DC distinct-supplier cap-breach block (`SUMPRODUCT((dc=…)/COUNTIFS(...))` vs
    `max_sup_dc`). Cols incl. `$/case (live)`/`Line Spend (live)` (MONEY), the three vs-% (PCT),
    Volume (INT), Transit (INT).
18. **Custom Dashboard** (`_write_custom_dashboard_tab`, L3773): the four lenses computed LIVE off the
    Custom Scenario rows (spend/savings/transit/share) beside the recommended B, via Excel formulas so
    the whole dashboard recomputes as the buyer changes a dropdown.
19. **Data (pivot me)** (`_write_data_pivot_tab`, L1708): the flat manipulable dataset — one row per
    (scenario × DC × lot × item × TF × awarded-supplier) with all 27 cols (`_DATA_COLUMNS`, L1677),
    registered as a REAL Excel Table (`Table(displayName="AwardData")`, `TableStyleMedium2`) so the
    buyer drops a native PivotTable on it. Money cols MONEY, score cols INT, shares PCT.
20. **_Prices (hidden)** (`_write_prices_helper`, L1376): the supplier×cell price grid (Match Key =
    `cell_key&"@"&supplier`, $/case, Transit) + a per-cell reference grid (Cell Key | Min | Incumbent
    | Baseline) the live formulas SUMIFS against; `sheet_state="hidden"`.

**Provenance restamp (`_stamp_real_provenance`, L4019):** on a real run (`synthetic=False`) it replaces
the literal SYNTHETIC/SYNTHESIZED strap tokens with LIVE/MODELED across every string cell. **WHY:** the
generator's demo lineage writes "SYNTHETIC"; a real run must not mislabel real names/prices.
**`_run_version` (L3973):** the mid-cycle alignment version = the 1-based ordinal of THIS sealed run
among the cycle's runs (by `run_started_at`), + a per-round ordinal, + the round number, + this run's
`run_finished_at`. **WHY:** surfaces the version (D26) from already-sealed history — never mints it.
**Disk wrapper `write_scenario_workbook_xlsx` (L4250):** bytes builder + write (default
`OUTPUT_DIR/SCENARIO_WORKBOOK.xlsx`); the web console calls the bytes builder and streams (no disk).

---

## 5. `app/cycle/**` — cycle-scope reconstruction (loader / scope)

### 5.1 `cycle/__init__.py` — census #96 · py · 173 B · not empty
**What:** re-exports `load_cycle` (`__all__ = ["load_cycle"]`). **WHY:** the one import surface for
reconstructing a `CycleView` from governed records.

### 5.2 `cycle/loader.py` — census #97 · py · 7869 B · not empty — THE INVERSE OF THE DEMO SEED
**What:** `load_cycle(session, cycle_id) -> CycleView` — reads the SAME governed tables the demo's
`seed_cycle` writes and assembles the name-resolved `CycleView` the generators are built on.
**Detailed WHY:** makes every generator runnable for a REAL persisted cycle, not just the synthetic
seed (the "wired to real data" requirement). **Names are DISPLAY names (D23); keys JOIN.** **Breaks
without it:** the pilot could never produce deliverables for a persisted cycle.
**Reads + transformations (every one):**
- cycle row from `cyc.cycle` LEFT JOIN `ref.commodity` (`m.id::text = c.commodity_id`) → code/name/
  commodity + the five engine safeties (`engine_premium_ceiling/coverage_floor/conc_thresh/
  max_sup_dc/weight_preset`).
- DCs: `ref.dc` JOIN `cyc.cycle_projected_volume` (the DCs the cycle carries volume for), ORDER BY
  `dc_code`.
- Lots+items: `cyc.cycle_lot` JOIN `cyc.cycle_lot_item` JOIN `ref.item`, ORDER BY `lot_code` →
  `lots[i]`↔`items[i]` index alignment; `item_to_lot[item_id] = lot_id` (the one-item-per-lot grain).
- TFs: `cyc.cycle_timeframe` ORDER BY `tf_code`; `horizon_weeks = Σ int(week_count)` (skips NULLs) —
  **the real horizon transformation.**
- Rounds: `cyc.cycle_round` ORDER BY `round_number`; **code synthesized** `f"R{round_number}"`, name
  `f"Round {n}"` + " — Final" when `is_final` (no name column in the table).
- Suppliers: `cyc.cycle_invited_supplier` JOIN `ref.supplier` (the submitted-vs-missing denominator),
  ORDER BY `canonical_name`; code synthesized `f"SUP-{i:02d}"`.
- Projected volumes: `cyc.cycle_projected_volume` at (dc, **item**, tf) → **remapped to the engine's
  (dc, lot, tf) cell grain** via `item_to_lot` (L137–141); `Decimal(str(period_cases))`. **Edge
  case:** an item not in any in-scope lot is skipped (shouldn't happen for a well-formed cycle).
- Incumbents + routing: `perf.historical_award_assignment` (incumbent_flag) LEFT JOIN
  `perf.historical_awarded_price_basis` (`preferred_basis_flag = true` — the iTrade baseline, D11) →
  `(dc, lot)->supplier` and `(dc, lot)->routing`; routing `Decimal(str(...))` or `Decimal("0")`.
- Returns a `CycleView` with `client_id=""` (not needed by the generator) and every Decimal-typed
  engine safety cast `Decimal(str(x)) if x is not None else None`.

### 5.3 `cycle/scope.py` — census #98 · py · 2752 B · not empty — THE BID-TEMPLATE SCOPE BUILDER
**What:** `build_scope_from_cycle(cycle, round_no) -> CycleScope` — the inverse companion to the
loader: builds the intake `CycleScope` (one `ScopeRow` per **DC × lot × item × TF × supplier** cell)
carrying the system-owned surrogate KEY IDs (D21) the bid-template generator embeds and the ingester
validates.
**Detailed WHY:** recreates the demo's `build_scope` against a `CycleView` so the bid-template
generator runs identically for the synthetic seed and a real persisted cycle. **Breaks without it:**
no bid template for a persisted cycle.
**Edge case (L27):** `round_no` is 1-based; `if not (1 <= round_no <= len(cycle.rounds)): raise
ValueError` — **never silently picks a default round.** Selects `cycle.rounds[round_no - 1]`. The
nested loops (dc → item/lot by index → tf → supplier) build the full Cartesian scope; each `ScopeRow`
carries both the KEY ids (round/tf/supplier/dc/lot/item) and the display LABELS (D23). Lot↔item grain
is one item per lot (`lots[i]`↔`items[i]`).

---

## 6. `app/fiscal/**` — the 4-3-3-3 fiscal calendar library + CSV data

### 6.1 `fiscal/__init__.py` — census #138 · py · 539 B · not empty
**What:** package docstring naming `app.fiscal.calendar` for the period↔date lookups, the timeframe
presets, and the intake fan-out; states the period spans come from the sponsor's conversion CSV
(nothing derived by a date rule) so **a future calendar quirk is a data update, not a code change**
(INTAKE_TEMPLATE_DESIGN §1a). No code. **WHY:** package marker + the data-driven contract.

### 6.2 `fiscal/calendar.py` — census #139 · py · 8259 B · not empty — THE AUTHORITATIVE 13-PERIOD REFERENCE
**What:** the period↔date lookups, the timeframe grouping presets, and the intake fan-out
(`expand_to_periods`).
**Detailed WHY:** Kroger runs a **4-3-3-3** retail fiscal calendar — every FY has EXACTLY 13 four-week
periods in four quarters (Q1=P1-4, Q2=P5-7, Q3=P8-10, Q4=P11-13); a 53-week leap year (~every 5-6
years) gives **Period 13 a 5th week**. Period spans are therefore NOT always 28 days, so this module
**never assumes a fixed length** — all dates come from the CSV. This is the canonical grain the
flat-13 intake model records against (every offer lands in exactly ONE of the 13 periods). **Breaks
without it:** intake has no period grain, no timeframe grouping, no fan-out.
**Constants:** `PERIODS_PER_YEAR = 13`; **`QUARTER_OF_PERIOD`** (L30) — the fixed 4-3-3-3 split
(1-4→Q1, 5-7→Q2, 8-10→Q3, 11-13→Q4), "verified across every FY in the table" (confirmed below in §6.3).
**Dataclasses (frozen):**
- `FiscalPeriod(fiscal_year, period, quarter, begin, end, weeks)` + `days` property
  (`(end−begin).days + 1`) + `label` property (`f"P{period:02d}-{fiscal_year%100:02d}"`, e.g. "P05-26").
- `Timeframe(label, fiscal_year, start_period, end_period, begin, end)` + `period_numbers` property
  (`tuple(range(start, end+1))`).
**`_load()` (L85, `@lru_cache(maxsize=1)`):** reads the CSV once via `csv.DictReader`, building
`FiscalPeriod` per row; `int(...)` for fiscal_year/period/quarter/weeks, `date.fromisoformat(...)` for
begin/end. **Edge case (CRLF):** the file is CRLF; opened with `newline=""` so `csv` strips the line
terminator and `int(r["weeks"])` receives a clean value.
**Lookups (every one, with edge cases):**
- `all_periods()` / `fiscal_years()` — the full ordered set / ascending distinct FYs.
- `periods_in_year(fy)` (L118): the 13 periods of a FY; **raises ValueError if the FY is outside the
  table** (names the FY16..FY36 range).
- `get_period(fy, period)` (L128): the single period; **raises ValueError if period out of 1..13.**
- `period_for_date(day)` (L137): the period a date falls in; **raises ValueError if outside the
  calendar** (names the covered date range). Linear scan of the contiguous spans.
**Timeframe grouping + fan-out:**
- `group_periods(fy, spans, labels=None)` (L153): groups the 13 periods into contiguous timeframes.
  **Edge cases:** `if not spans: raise`; **`flat = [p for s,e in spans for p in range(s,e+1)]` MUST ==
  `list(range(1,14))`** else raise ("contiguous and cover periods 1..13 exactly once") — guarantees no
  gap/overlap/duplication; `labels` length must match `spans`. Each TF's begin/end come from its
  first/last period's authoritative dates.
- `fiscal_quarters(fy)` (L193): `[(1,4),(5,7),(8,10),(11,13)]` labelled Q1-Q4 (the 4-3-3-3 split).
- `fiscal_halves(fy)` (L199): `[(1,7),(8,13)]` H1/H2 (aligned to quarter boundaries).
- `fiscal_year_timeframe(fy)` (L205): `[(1,13)]` "FY" (a flat-year, one price for all 13 periods).
- `per_period(fy)` (L211): each period its own timeframe (the supplier prices all 13).
- `expand_to_periods(timeframe)` (L221): **the intake flat-13 fan-out** — `tuple(get_period(fy, p) for
  p in timeframe.period_numbers)`. **WHY:** a timeframe priced once is recorded against EACH of its
  periods, so the DB stays flat at the 13-period grain while the supplier filled only a few cells.
  (This is the upstream of the Option-B `DISTINCT ON` de-fan the scenario workbook does on read.)

### 6.3 `fiscal/data/kroger_fiscal_periods.csv` — census #140 · csv · 9420 B · not empty
**What:** the sponsor's authoritative period→date conversion table. **CRLF-terminated**, header
`fiscal_year,period,quarter,begin_date,end_date,weeks`, **273 data rows = 21 fiscal years (FY2016..
FY2036) × 13 periods**, fully contiguous.
**Detailed WHY:** the calendar is DATA, not code — a future calendar quirk is a CSV update. **Breaks
without it:** `_load()` raises and every fiscal lookup fails.
**VERIFIED INVARIANTS (run during this audit):**
- **Row count:** 273 data rows (21 × 13). ✅
- **Years:** FY2016..FY2036 contiguous (21 years). ✅
- **`weeks` distribution:** 269 rows = 4 weeks; **4 rows = 5 weeks** — exactly the 53-week leap years,
  all on **Period 13**: `2017,13,4,2017-12-31,2018-02-03,5`; `2023,13,4,2023-12-31,2024-02-03,5`;
  `2028,13,4,2028-12-31,2029-02-03,5`; `2034,13,4,2034-12-31,2035-02-03,5` (each a 35-day P13). This
  confirms the docstring's "Period 13 gets a 5th week in a 53-week year." ✅
- **Quarter mapping:** every (period→quarter) pair across the file is EXACTLY the 4-3-3-3 split and
  matches `QUARTER_OF_PERIOD`. ✅
- **Contiguity:** 0 gaps/overlaps — every `end_date` is exactly one day before the next `begin_date`,
  across all 273 rows (verified programmatically). ✅ This is what makes `period_for_date`'s linear
  scan exhaustive and unambiguous.

---

## 7. LAYER-1 CONTRIBUTIONS — value transformations / decimal precision in B6 (formula + file:line)

Every B6 number routes through `app/engine/formulas.py` (the single "table of calcs", pure Decimal) or
one of the local helpers; the decimal's journey ends at a `float(...)` cast at the openpyxl cell-write
boundary, where the cell's `number_format` (`NUMFMT_MONEY`/`NUMFMT_PCT`/`NUMFMT_INT`) renders the
DISPLAY precision. The arithmetic itself stays exact Decimal until that boundary.

| Transformation | Formula | Source (file:line) |
|---|---|---|
| §7 price construction | All-In if present, else FOB+delivery+vegcool−lot_disc(−all_lot_disc) | formulas.py:21,45; scenario_workbook.py:219 (`_line_price`); resolvers.py:169 (`_constructed_price`) |
| premium vs market low (%) | (price − low)/low; None if low≤0 | formulas.py:69; used resolvers.py:346, scenario_workbook.py:2004 |
| premium $ | price − low | formulas.py:142; resolvers.py:345 |
| delta vs historical/baseline (%) | (price − base)/base; None if base≤0 | formulas.py:100; scenario_workbook.py:609 |
| awarded cases | period_cases × volume_share | formulas.py:114; booking_guide.py:148, capacity_check.py:110 |
| line spend | price × cases | formulas.py:120; booking_guide.py:163, scenario_workbook.py:468 |
| savings $ | baseline_spend − actual_spend | formulas.py:126; scenario_workbook.py:633 |
| savings fraction (%) | (base − actual)/base; 0 if base≤0 | formulas.py:132; booking_guide.py:147, scenario_workbook.py:484 |
| weekly impact $ | premium $/case × weekly cases | formulas.py:148; resolvers.py:374 |
| price delta (post-award) | current − baseline | formulas.py:154; post_award_doc.py:263 |
| STLY proxy total | baseline_total × 1.04, quantized to $0.01 | scenario_workbook.py:415,444 |
| allocated weekly cases | allocated ÷ weeks_per_tf (raises if ≤0) | capacity_check.py:104,111 |
| Z-score | (price − avg)/std (population std = sqrt(Σ(v−avg)²/n)) | scenario_workbook.py:1886-1894,1911 |
| coverage ratio + band | offered/required → band thresholds 50/80/100/120% | scenario_workbook.py:2196-2208 |
| cover floor / premium ceiling display | `_pct(x)` = x×100, 1-dp | resolvers.py:149 |
| item→lot volume aggregation | SUM(projected_weekly_cases) over a lot's items | resolvers.py:243; loader.py:137 |
| timeframe→13-period fan-out | one DB row per covered period (identical payload) | calendar.py:221 |
| 13-period→timeframe de-fan (read) | DISTINCT ON (sup,dc,lot,tf) … ORDER BY fiscal_period_id NULLS LAST | scenario_workbook.py:272-282, 1867-1877, 2176-2187 |
| money display | `$#,##0.00` (2-dp) or `f"${:,.2f}"`/`f"${:,.0f}"` | formatting.py:26; resolvers.py:145-146 |
| percent display | `0.0%` on a FRACTION (1-dp) | formatting.py:27 |
| integer display | `#,##0` | formatting.py:29 |

---

## 8. LAYER-2 CONTRIBUTIONS — edge cases / decisions enforced / DRIFT flags

**Decisions enforced (decision → enforcing file:line):**
- D19 NO-MVP — the 4 unrouted comms touchpoints are render-ready templates, the 3 routed ones are
  fully wired; flagged as a pending resolver increment, not a shipped stub (see DRIFT below).
- D21 keys join / D23 names display — every generator reads by KEY, renders by NAME
  (loader.py throughout; post_award_doc.py:77; booking_guide.py:112-119; scenario_workbook.py:255-261).
- D24 presentation (not CSV dump) — formatting.py:107 `format_table` applied by every workbook.
- D26/D27 alignment + manipulable — scenario_workbook.py (drill outline, live formulas, Data table).
- D28 render the engine's reason, never hardcode — rec_type sourced from `eng.analysis_scenario_award`
  (scenario_workbook.py:310); post-award reason/type from stored rows (post_award_doc.py:16,196).
- ADR-0006 decision-support — `DECISION_SUPPORT_STRAP` on every surface (formatting.py:56); capacity
  check FLAGS, never changes the award (capacity_check.py:6-8).
- ADR-0014 freeze-and-layer — post_award_doc.py reads baseline + append-only layers, never mutates.
- INTAKE §1a flat-13 — calendar.py fan-out + the workbook de-fan reads.
- No-file-storage — every generator exposes a bytes builder (render-on-request) + a thin `*_xlsx` disk
  wrapper for the MCP vault only (booking_guide.py:188, post_award_doc.py:146, scenario_workbook.py:4250).

**Edge cases / branches mapped (per process):**
- auth: no-cookie / bad-token / non-str sub / non-UUID sub / unknown-or-inactive user → uniform 401
  (deps.py); malformed stored hash → verify False, never raise (security.py:43); TOTP ±1 window;
  cookie Max-Age == JWT exp (security.py:79).
- main.py: production leaves principal None → deny-by-default; tenant never from input.
- merge: unknown/None/empty → visible `[#Name]` hole + collected in `missing`; non-token brackets pass
  through.
- render: empty table → `(none)` line; tables expand before scalars.
- resolvers: award not this run's → ValueError→404; per-supplier file isolation (never another's);
  threshold `is not None` (honours an explicit 0); ineligible hard-ask fires regardless of price
  position; one hard row per breached gate; awarded-every-cell supplier → no rejection draft;
  market_low≤0 cells skipped; sealed-run-own-rows (not "current scoreable").
- capacity_check: weeks_per_tf≤0 → raise (fail loud); no-statement cell reported not flagged; multi-
  constraint → MIN each dimension independently; superseded statements excluded.
- scenario_workbook: Option-B de-fan on every per-cell read (else counts/std inflate ≤13×);
  rec-pick always in dropdown even if gated; dropdown never empty (fall back to anyone who priced);
  TF Comparison only if >1 TF; Round Evolution only if >1 round and ≥2 priced rounds; provenance
  restamp on real runs; as_of_version clamped to latest (post_award_doc).
- cycle/scope: round_no out of range → ValueError (never a default); item not in scope → skipped.
- fiscal: every lookup raises on out-of-range FY/period/date; group_periods rejects non-contiguous /
  non-covering / mismatched-labels spans.

**DRIFT / PENDING (flag, not silent):**
1. **comms 3/7 routed:** INVITATION, TEMPLATE, INCOMPLETE_BID, PBA have authored templates + (for
   incomplete-bid) a TableSpec, but **no governed-data resolver and no service/router caller**
   (resolvers.py implements only award/feedback/rejection; pilot/service.py wires only those 3;
   api/v1/runs.py imports only `SupplierEmailDraft`). The 4 unrouted templates reference scalars
   (CorrectionDueDate, ProcessStartDate, RoundCount, EstimatedAwardDate, EffectiveDate,
   ExpirationDate, PBAFileName, TemplateFileName, RoundNumber for the template) that nothing currently
   fills. **Pending: their resolvers (an E-37 increment).**
2. **main.py tenant middleware STUB** — production auth-edge IdP adapter is **DEP-4**, not yet landed
   (production requests intentionally unauthenticated/deny-by-default until then).
3. **round_feedback `DCSummaryTable` columns INFERRED** — templates.py:11 records that the author
   specified only the Hard/Soft ask tables; the DC-summary columns were inferred.
4. Synthetic/demo-illustrative attributes (region/transit/freight in synthetic.py; STLY 1.04 uplift;
   product-type split) are clearly LABELLED synthetic/modeled in every surface and restamped on real
   runs — not real-data drift, but recorded as modeled-pending-feed.

---

## 9. CENSUS CROSS-REF

All 31 B6 files map to census rows 45, 59–81, 96–98, 138–155; none empty; none claimed by another
slice. Vendored/generated bytecode under each `__pycache__/` is counted (not ours), never per-file
audited, per the exhaustiveness rule. Nothing in `backend/app` is missed across B1–B6.
