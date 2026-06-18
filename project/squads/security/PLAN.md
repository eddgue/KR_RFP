---
doc: Security & Compliance Squad Plan — the net-new enterprise layer
id: SQUAD-SEC-001
version: 1.0
status: Draft
created: 2026-06-18
owner: Security & Compliance squad lead
depends_on: audit/01_DOCUMENT_AUDIT ([D-4],[D-7]), audit/02_GAP_ANALYSIS (G9,G11,G12,net-new), audit/04_RISKS_DECISIONS_ROADMAP (R7), specs/original-engine/BUILD_02 (Layer 8 audit), specs/rfp-engine/BUILD_02 (audit.event_log), intake/SESSION-01, SESSION-02, SESSION-04, project/04_PROGRAM_BACKLOG (E-03,E-04,E-05,E-17,E-24), ADR-0001
epics: E-03, E-04, E-05, E-17, E-24
owns_adrs: ADR-0004 (tenancy), ADR-0005 (audit-chain), ADR-0009 (RBAC), ADR-0015 (classification/retention)
---

# Security & Compliance — Squad Plan

We own the layer neither original package contained (`01 [D-4]`, `02` net-new, R7): multi-tenant
isolation, identity/RBAC, the **live** audit hash-chain (G11), the two governance gates (G12 in,
G9 out), data protection, the threat model, and the security NFR acceptance criteria for the phase
gates. We also own the clean-room CI rule (`backend/` must never import `reference/`, ADR-0001).

**Inheritance rule applied to security:** shape/intent from the BRIEF (client as a first-class
entity, portfolio sign-off, draft→sent as a gate, live event log), constraint discipline from the
AS-BUILT (composite-identity FKs, the hash-chain *design*, app+DB double enforcement). We never
weaken an as-built control; we make the scaffolded ones operative and add the missing layer.

We model **policy and enforcement points**; Platform & Data models the columns/migrations we
specify (their M1 audit-live, M10 client-tenant), Engine wires the guards into services, DevOps
provides the IdP/secret-store (DEP-4). No application code appears in this document.

---

## 1. Tenancy model (E-03 · ADR-0004)

**`ref.client` is a first-class reference entity** (Session 1: "Clients … its own home"). One row per
governed tenant (a Kroger sourcing org / business unit). It is created before any breadth hardens the
schema (D5 — cheap now, expensive later), and it sits in `ref` beside `supplier`/`dc`/`commodity`.

| Column | Note |
|---|---|
| `id` (uuid PK) | canonical tenant id |
| `code` (unique) | short stable handle, used in logs/correlation |
| `name`, `status` (ACTIVE/SUSPENDED) | lifecycle; SUSPENDED denies all access, retains data |
| `data_residency`, `classification_ceiling` | drives §5 handling rules per tenant |
| `created_at` / `created_by` | provenance |

**Row-level tenant isolation — the strategy.** Every tenant-scoped table carries a non-null
`client_id` FK to `ref.client`. "Tenant-scoped" = everything cycle-derived: all of `cyc/bid/eng/awd`,
the `perf` feeds, `norm.item_lot_map` and cycle-local scope, and `audit.event_log`. Pure global
reference (`commodity`, `dc`, `fiscal_calendar`, `zip_centroid`) is **not** tenant-scoped — it is
shared master data; `supplier`/`item` are global identities but their *bids/awards* are tenant-scoped.
This split is published as the **tenancy classification table** (deliverable, Phase 0) so no table's
scope is ambiguous.

Isolation is **defence-in-depth, two independent layers** (one layer is a convention, two is a control):

1. **Application layer (primary).** A request-scoped **tenant context** is set at the auth edge from
   the verified principal's claim — **never** from a request body, query param, or header the client
   controls (the #1 cross-tenant leak vector). Every repository is tenant-aware: the base query class
   injects `WHERE client_id = :ctx_tenant` and every write stamps `client_id` from context. There is no
   un-scoped read path to governed data; cross-tenant access requires an explicit, permissioned,
   audited "admin cross-tenant" capability that no standard role holds.
2. **Database layer (backstop).** PostgreSQL **Row-Level Security** policies on every tenant-scoped
   table, keyed to a `SET LOCAL app.current_tenant` GUC the unit-of-work sets per transaction from the
   same context. If an app-layer filter is ever forgotten, RLS still denies the row. The app connects
   as a non-superuser, non-`BYPASSRLS` role so RLS cannot be silently skipped. (Lands in Platform &
   Data's M10; we own the policy set.)

**Composition with the as-built's composite-identity FKs.** The as-built guarantees lot∈cycle,
item∈lot, tf∈cycle, the submission identity quad, the calc-run identity (46 composite FKs — KEEP).
Tenancy composes by **prepending `client_id` to those composite keys** where the entity is
tenant-scoped: a cycle is identified by `(client_id, cycle_id)` and every child FK carries `client_id`
forward, so the database itself forbids a child of tenant A from referencing a parent of tenant B —
cross-tenant referential leakage is structurally impossible, not merely filtered. Global reference
entities keep their existing single-tenant-free keys. This makes tenancy an *extension* of the
as-built's integrity discipline, not a parallel mechanism.

**Leakage prevention checklist (tested invariants, not hopes):** tenant from token only; RLS denies by
default; connection role cannot bypass RLS; composite FKs carry `client_id`; generated documents and
exports stamp + filter by tenant; audit events carry `client_id`; error envelopes never echo another
tenant's identifiers; "open last cycle" is tenant-scoped at the query root.

---

## 2. Identity, authn & RBAC (E-03/E-04 · ADR-0009)

**AuthN — delegated to an external IdP (DEP-4).** We do **not** build a password store. The backend
trusts a verified principal at the edge: an OIDC/SAML IdP (the sponsor's SSO — Okta/Entra/Ping class)
issues a signed token; an auth middleware validates signature, issuer, audience, and expiry, and
extracts `(subject, tenant, roles, email)`. The architecture stays **provider-neutral** — one
verification adapter, swappable — so the choice of IdP (DEP-4, sponsor/IT) does not couple the build.
Service accounts (importers, the worker) authenticate via client-credentials with a dedicated
non-interactive role. MFA, session lifetime, and lockout are the IdP's responsibility; we require them
via the NFR criteria (§7), we do not reimplement them.

**Actor / role model.** Roles are assigned **per tenant** (a user may be Analyst in tenant A and have
no access to tenant B). Permissions are the atomic unit; roles are named bundles. The principal carries
roles; services receive an already-authorized principal and never re-derive authz.

**Role catalog (the bundles):**

| Role | Who | Holds (headline) |
|---|---|---|
| **Sourcing Analyst** | runs the cycle day-to-day | create/edit cycle (pre-gate), import bids, run engine, build scenarios, draft awards & documents. **Cannot** approve a gate or send. |
| **Category Manager (Cat Man)** | owns the category | everything Analyst has **+** select/promote a scenario to award, author the in-gate request, mark documents ready-to-send. Still **cannot** ratify a gate alone. |
| **Leadership / Approver** | the gate authority | **approve the Stage-0 in-gate (G12)** and the **portfolio sign-off out-gate**, and authorize **draft→SENT (G9)**. Read-everything; cannot edit operational data (separation of duties — the approver is not the author). |
| **Admin (tenant)** | tenant administration | manage users↔roles within the tenant, manage `ref.client` settings, manage RFI/term templates. **No** access to another tenant; **no** ability to mutate sealed runs, frozen awards, or the audit log. |
| **Auditor (read-only)** | compliance/IA | read-only across the tenant **including the audit log + verify chain**; can export evidence; cannot write anything. |
| **Platform Admin (cross-tenant)** | break-glass ops | the only role with the gated cross-tenant capability; every action heavily audited; held by a tiny set, MFA-mandatory. |
| **Service account** | importers / worker | scoped to ingestion + run execution for a named tenant; no gate, no send, no user management. |

**Permission matrix vs the lifecycle.** Columns are the lifecycle transitions; an approval transition is
a *distinct permissioned verb*, never a side-effect of a GET or a run (architecture §5):

| Capability | Analyst | Cat Man | Approver | Admin | Auditor |
|---|:--:|:--:|:--:|:--:|:--:|
| Kickoff: create/edit cycle (draft) | ✔ | ✔ | – | – | – |
| **Stage-0 in-gate approve (G12)** | – | request | **✔** | – | – |
| Import feeds / bids | ✔ | ✔ | – | – | – |
| Run engine (sealed run) | ✔ | ✔ | – | – | – |
| Build/edit scenarios | ✔ | ✔ | – | – | – |
| **Select → promote to award** | – | **✔** | – | – | – |
| **Freeze award (at sign-off)** | – | – | **✔** | – | – |
| **Portfolio sign-off approve** | – | – | **✔** | – | – |
| **Draft → SENT (G9)** | – | request | **✔** | – | – |
| Generate documents (draft) | ✔ | ✔ | – | – | – |
| Manage users / roles (in tenant) | – | – | – | ✔ | – |
| Read audit log / verify chain | ✔ | ✔ | ✔ | ✔ | **✔** |
| Cross-tenant access | – | – | – | – | – |

Rule encoded above: **the author cannot approve their own gate.** Analyst/Cat Man produce; Approver
ratifies. This is the separation of duties the governance gates exist to provide.

**API authz approach.** AuthZ is an explicit boundary in `app/core/security/`: dependency-injected
route guards declare the required permission; the guard reads the principal from context and the tenant
from context, and denies with a uniform problem envelope (no information leak about other tenants'
existence). Object-level checks (this award belongs to this tenant and this cycle) run at the repository
boundary via the tenant filter, so a valid token for tenant A can never address tenant B's object id.
The engine and domain services never see an unauthorized or untenanted call.

---

## 3. The live audit hash-chain (E-05 · G11 · ADR-0005)

We finish the as-built's `audit_event` design (`01 [D-7]`, `02 G11`) — its before/after + prev/this
hash structure is *stronger* than the brief's jsonb log — and make it **operative and write-only**. We
do not rebuild it as the brief's simpler table; we promote the brief's "must be live" onto the
as-built's better structure.

**`audit.event_log` row (per state change):**

| Field | Content |
|---|---|
| `id`, `client_id`, `occurred_at` | identity, tenant, time |
| `actor` (subject + role), `source` (api/worker/import) | who/what |
| `event_type` | CREATED / SEALED / FROZEN / SUPERSEDED / SIGNED_OFF / SENT / GATE_APPROVED / IMPORTED |
| `entity_type`, `entity_id`, `cycle_id` | what changed, anchored to a cycle for "open last cycle" |
| `before_state_hash`, `after_state_hash` | sha256 of the canonical-serialized entity pre/post |
| `prev_event_hash`, `event_hash` | chain link: `event_hash = sha256(this row's fields ‖ prev_event_hash)` |
| `seq` | per-tenant monotonic sequence (gap = evidence of tampering) |

**Population — not the caller's job to remember.** Services emit a domain event on every governed
mutation; a **single audit writer** subscribes and writes the chained row **inside the same
transaction** as the change it records (so a change without its audit event cannot commit, and an audit
event without its change cannot exist). The writer computes both state hashes and links the chain by
reading the tenant's current head under a row lock (serialized per tenant). This is wired once, in
`app/core/audit/`, not sprinkled across services.

**Write-only enforcement — app + DB.**
- **App.** No service exposes update/delete on `event_log`; the writer is the only producer and it only
  appends.
- **DB.** A `BEFORE UPDATE OR DELETE` trigger on `event_log` raises unconditionally; no role is granted
  `UPDATE`/`DELETE` on the table; the app's DB role has `INSERT`+`SELECT` only. (Platform & Data's M1
  ships the triggers + grants to our spec.) This is the as-built's `calc_run_guards` discipline applied
  to the log itself.

**Tamper-evidence.** Any edit/delete/reorder breaks the chain: a recomputed `event_hash` will not match
the stored next link, or `seq` will gap. A **`verify_chain(tenant, [from,to])`** routine (Auditor-
callable) walks the chain and reports the first break. The chain head per tenant is the integrity
anchor; we periodically snapshot the head hash to an append-only location for external attestation.

**"Open last cycle" reads it.** The capability that separates a system of record from a pile of
generators (Session 1) is a **tenant-scoped query** across `cycle → rounds → bids → runs → scenarios →
awards`, with `event_log` joined to prove the *order and authorship* of every state change. The audit
log is not a side-file; it is the spine the reopen query reads to reconstruct the full story.

---

## 4. Governance gates (E-17 G12 in · E-24 G9 out)

Both gates are **approval objects with approver + timestamp**, gated by the Approver permission — never
channel side-effects, never auto-asserted by the engine (the engine still "never auto-asserts an award";
a human promotes). Each approval emits a `GATE_APPROVED` / `SENT` audit event.

**Stage-0 in-gate (G12).** "A real cycle on real data requires a Stage-0 governance sign-off that is not
implemented" (`02 G12`). We model `cyc.cycle_ingate_approval` (cycle_id, approver, approved_at,
decision, note, classification acknowledged). The enforced control: **a cycle cannot transition out of
DRAFT to an OPEN/operational state — and no real feed may bind to it — without an in-gate approval by an
Approver.** The cycle's status machine refuses the transition; the API guard refuses the call. Cat
Man requests; Approver ratifies (separation of duties §2).

**Draft → SENT (G9).** "Sent is a governance gate, not a channel" (Session 1, Discrepancy #2): sent
means *official, left the building, recorded with approver + timestamp*. We add a `sent` lifecycle state
(approver, sent_at, channel-is-metadata) to **feedback, awards, and generated documents**. The control:
the draft→sent transition requires the send permission, writes a `SENT` audit event, and is irreversible
(a correction is a new superseding draft→sent, never an edit of the sent record). We **keep** the
as-built's `BANNED_DECISION_WORDS` guard on the *recommendation* surface — the two are compatible: the
engine never asserts an award; a human, permissioned, promotes a draft to official.

**Portfolio sign-off (the out-gate, supports E-22).** Session 4: one sign-off spans many categories/
clients in a single leadership meeting ("$5.0M across categories"). The sign-off approval is therefore
**portfolio-level** — it references a set of cycle awards (possibly across categories, within the
tenant's portfolio) and freezes them together. Our control: sign-off approve is Approver-only, freezes
every referenced award (`frozen_at`), and emits one `SIGNED_OFF` event per award plus a portfolio
roll-up event. Post-freeze changes go only to `award_layer` (immutability, owned with Engine/Plat&Data).

---

## 5. Data protection (ADR-0015)

**Classification scheme (every entity tagged, Phase 0 deliverable).** Four tiers:

| Tier | Examples | Handling |
|---|---|---|
| **C3 — Commercial-Sensitive** | bid prices, landed cost, awarded prices, supplier scorecards, savings-vs-STLY, sign-off financials | encrypted at rest + in transit; tenant-scoped + RLS; no export without an audited action; **never** committed to the repo or pasted into logs/issues |
| **C2 — Internal** | cycle config, objectives, scope, RFI sets, kickoff narrative | tenant-scoped; internal-only |
| **C1 — PII (limited)** | supplier/internal contact names, emails, approver identities | minimized, masked in logs, retained per policy, access-logged |
| **C0 — Public/Reference** | commodity codes, DC list, fiscal calendar, zip centroids | shared master data; not tenant-scoped |

Note: PII here is light (this is commercial, not consumer data) — the dominant risk is **C3 commercial
leakage**, not personal data. Logs and error envelopes carry **no C3 values and no cross-tenant ids**;
structured logs reference entity ids, not prices.

**Retention.** Governed records are **append-only and effectively permanent within the tenant** — the
system's entire reason for being is the long memory ("open last cycle"); we do **not** auto-purge cycle/
award/audit data. Retention policy therefore governs *deletion on tenant offboarding* (full tenant
export then cryptographic-erase of that tenant's encryption scope) and *log/PII minimization* (operational
logs rotate; the audit log never does). The audit chain is immutable and exempt from purge by design.

**The reference/samples rule (we own it — ADR-0001 §4).** Real commercial values must be classified and
handled, never committed casually. Concretely: a real iTrade pull, bid workbook, or sign-off deck is
**C3** the moment it lands. Rule: (1) sample files live under `reference/samples/` with a provenance +
classification header; (2) **C3 sample files are git-ignored and never committed** — they are referenced
by hash/manifest, not stored in the repo; (3) CI runs a **secret/commercial-value scanner** that fails
the build if a price-shaped or PII-shaped value, or an un-headered sample, is staged; (4) the
reference-intake agent (ADR-0001) emits only the *schema* and a *digest* — never raw commercial rows —
across the quarantine boundary. We publish a one-page intake checklist the sponsor follows when
uploading.

**Clean-room CI rule (we own it).** `backend/` must never import from `reference/` (ADR-0001). We own
the CI gate: a static import check (AST/grep over `backend/`) that fails on any `reference` import, plus
a path check that `reference/` is input-only. This runs in the same CI stage as the commercial-value
scanner.

---

## 6. Threat model (STRIDE, concise)

Scope: the governed system of record + the net-new web app. Top threats and the control that retires each:

| STRIDE | Threat (this system) | Primary control |
|---|---|---|
| **Spoofing** | forged/replayed token; a tenant impersonating another | IdP-signed tokens validated at edge (sig/iss/aud/exp); tenant from token only; short token TTL; service accounts scoped |
| **Tampering** | edit a sealed run, frozen award, or the audit log; alter a price post-sign-off | app+DB immutability (no UPDATE/DELETE grant; triggers); hash-chain detects log tampering; freeze-and-layer for awards |
| **Repudiation** | "I didn't approve that gate / send that award" | every gate/send/select writes an actor-stamped, chained audit event; approver identity is non-repudiable in the chain |
| **Information disclosure** | cross-tenant read; C3 prices in logs/exports/errors; a leaked sample file | RLS + app filter (defence-in-depth); composite `client_id` keys; log/error scrubbing; C3 git-ignore + CI scanner |
| **Denial of service** | runaway import/engine run; oversized upload | rate limits + payload caps at the edge; runs are bounded + sealed; worker isolation; (sizing is modest per `02` — design accordingly, not for hyperscale) |
| **Elevation of privilege** | Analyst self-approves a gate; app role bypasses RLS; cross-tenant via Platform Admin | separation of duties (author≠approver); non-`BYPASSRLS` DB role; cross-tenant capability gated + heavily audited + MFA |

**Trust boundaries:** browser↔API (token-validated edge), API↔DB (RLS + scoped role), API↔external
feeds (importers validate, quarantine on doubt), and the **clean-room boundary** (`reference/` is
input-only, CI-enforced). The sponsor's existing repo is **not a runtime actor** — it is offline,
isolated reference (ADR-0001).

---

## 7. NFR security acceptance criteria (the phase gates)

Security criteria that gate the milestone roadmap (PM-005). IDs continue the program's S-series (S1 =
"open last cycle <2s", S2 = engine reproduces v3 — already referenced); ours are **S7+**:

| ID | Acceptance criterion | Gate (phase) |
|---|---|---|
| **S7** | **Tenant isolation enforced.** A token for tenant A cannot read or write any tenant-B row via any endpoint; RLS denies even with the app filter removed (negative test); cross-tenant requires the gated capability. | A |
| **S8** | **RBAC enforced.** Every endpoint declares a required permission; an under-privileged token is denied with the uniform envelope; the author≠approver separation holds (an Analyst token cannot approve a gate). | A |
| **S9** | **Audit log is live + write-only.** Every governed state change emits one chained event in-transaction; UPDATE/DELETE on `event_log` is rejected at the DB; `verify_chain` passes on a clean run and pinpoints an injected tamper. | A |
| **S10** | **"Open last cycle" reads the chain.** A reopened cycle reconstructs the full ordered story from `event_log`, tenant-scoped, < 2s (composes with S1). | A/B |
| **S11** | **Stage-0 in-gate enforced (G12).** A cycle cannot bind real feeds or leave DRAFT without an Approver in-gate approval; the transition is refused otherwise and the refusal is audited. | C |
| **S12** | **Draft→SENT enforced (G9).** Sent requires the send permission, is irreversible, writes a `SENT` event; the engine still never auto-asserts (BANNED_DECISION_WORDS guard intact). | E |
| **S13** | **Data classification + sample rule.** Every entity carries a classification; CI fails on a staged C3/PII value or an un-headered sample; no C3 in logs/errors (scanner green). | 0/A |
| **S14** | **Clean-room boundary.** CI fails if `backend/` imports `reference/`. | 0 |
| **S15** | **IdP integration.** Tokens are validated (sig/iss/aud/exp); an invalid/expired token is rejected at the edge; MFA + session policy confirmed enforced at the IdP. | A/F |

Each is a **tested invariant** (QA squad runs them in CI), not a document assertion — directly retiring
R7 ("commercial data with no RBAC/PII/retention is an enterprise non-starter").

---

## 8. What we need from the sponsor (DEP-4 + sample intake)

| # | Need | Unblocks | Priority |
|---|---|---|---|
| 1 | **IdP / SSO details** — which provider (Okta/Entra/Ping/other), OIDC vs SAML, the claims it issues (subject, email, groups→roles mapping), and a non-prod tenant for integration | DEP-4; S8/S15; the authn adapter | **Top** |
| 2 | **Hosting/cloud + secret-store** decision (with DevOps) — where the store runs, KMS for at-rest encryption + the per-tenant key scope | DEP-4; C3 at-rest; residency | **Top** |
| 3 | **The org's data-classification & retention policy** (if one exists) — so our C0–C3 scheme and the offboarding/erase rule align to corporate policy, not just ours | ADR-0015; S13 | High |
| 4 | **The role→person mapping** — who in Sourcing is Analyst vs Cat Man vs Leadership/Approver, and the separation-of-duties expectation for gates | ADR-0009; the role catalog | High |
| 5 | **Confirmation of the tenant grain** — is a "client" a Kroger BU, or are external clients in scope? (changes the residency/classification ceiling) | ADR-0004 `ref.client` | Med |
| 6 | **A real sample set, classified on arrival** (iTrade pull, bid workbook, sign-off deck) — needed by other squads; we need them to validate the C3 handling + sample rule end-to-end | S13; the intake checklist | Med (with Plat&Data's list) |

---

## 9. Sequencing & ownership boundaries

- **Phase 0:** author ADR-0004/0009/0015, the tenancy classification table, the data-classification
  scheme, the clean-room CI rule (S14) and the commercial-value scanner (S13). Start E-03/E-04.
- **Phase A:** `ref.client` + RLS policy set (with Plat&Data M10), the authn adapter + RBAC guards
  (S7/S8/S15), the live audit chain wired + write-only triggers (S9/S10, with Plat&Data M1).
- **Phase C:** Stage-0 in-gate enforced (S11, E-17).
- **Phase E:** draft→SENT enforced (S12, E-24); portfolio sign-off freeze (with Engine/Plat&Data).
- **Phase F:** API hardening review; confirm IdP/session/MFA in the deployed environment.

**Boundaries.** We model policy + enforcement points and own the gates, the chain, tenancy isolation,
classification, and the clean-room rule. **Platform & Data** ships the columns/migrations/triggers we
specify (M1, M10). **Engine** wires guards into services and keeps the engine non-asserting. **DevOps**
provides the IdP, secret-store, and runs the CI we author. **QA** runs the S-series as CI invariants.

---

## Changelog

| Version | Date | Author | Change Summary |
|---|---|---|---|
| 1.0 | 2026-06-18 | Security & Compliance lead | Net-new security/tenancy/NFR layer: tenancy model + RLS, RBAC catalog + matrix, live audit hash-chain, G12/G9 gates, data classification + sample rule, STRIDE, S7–S15 acceptance criteria, sponsor asks. |
