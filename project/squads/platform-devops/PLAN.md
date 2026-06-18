---
doc: Platform Engineering / DevOps Squad Plan
id: SQUAD-DEVOPS-001
version: 1.0
status: Draft
created: 2026-06-18
owner: Platform Engineering / DevOps squad lead
depends_on: ADR-0001, ADR-0002, ADR-0003, project/02_WAYS_OF_WORKING, project/05_MILESTONE_ROADMAP,
            project/01_TEAM_STRUCTURE_AND_RACI, audit/04_RISKS_DECISIONS_ROADMAP,
            squads/architecture/PLAN, squads/platform-data/PLAN
epics: E-00, E-02, E-27(support); RACI A on "Environments & CI/CD"
---

# Platform Engineering / DevOps — Squad Plan

We own the running ground: environments (dev/stage/prod), CI/CD, IaC, secrets, the DB-migration
pipeline, observability, release management, and performance/sizing. We do **not** own the schema
(Platform & Data), the engine (Engine & Domain), or RBAC/tenancy policy (Security) — we provide the
pipeline that proves all three on every commit. The CI gates the program's non-negotiables in code:
lint, type, test, **migration roundtrip**, the **`reference/`-import guard**, and the frontend build.

This plan is concrete enough to scaffold this session (ADR-0003 plan-then-scaffold). It is explicitly
provider-neutral where the sponsor has not yet chosen (DEP-4: cloud + IdP); those forks are flagged in §4.

---

## 1. Environments

Three tiers, one image, config-by-environment. Parity is a control: stage must differ from prod only
in scale and data, never in topology, so a green stage is evidence for prod.

| Aspect | dev (local) | staging | prod |
|---|---|---|---|
| Runtime | docker-compose on the laptop | container platform (DEP-4) | same platform, separate project/account |
| Postgres | container `postgres:15` | **managed** Postgres 15+, small | **managed** Postgres 15+, HA + PITR |
| Backend/worker | hot-reload container | built image, 1–2 replicas | built image, 2+ replicas |
| Frontend | `next dev` (Phase F) | built image / SSR host | built image / SSR host |
| Secrets | `.env` (gitignored) | secret store (DEP-4) | secret store, tighter scope |
| Data | synthetic fixtures + seed | pilot dataset (Phase B), classified | real, full classification + retention |
| Auth | dev stub principal | real IdP, test tenant | real IdP (DEP-4) |
| Migrations | `make migrate` by hand | auto on deploy, gated (§7) | auto on deploy, gated + approval |

**Promotion path:** PR → merge to `main` → image built once → deploy to **staging** → smoke +
migration verify → manual gate → **prod**. The same immutable image digest is promoted; no rebuild
between stage and prod.

**DB-per-tenant vs shared-schema — input, not a decision (coordinate w/ Security).** The architecture
ratifies tenancy *in the schema* (`ref.client` + `client_id` columns + Postgres RLS, ADR-0004). For the
stated scale (§6) and the governance model (one writer, RLS backstop), **a single shared-schema database
with RLS is the recommended default**: it keeps "open last cycle" a single query, keeps migrations
singular (one roundtrip, not N), and matches the modest workload. DB-per-tenant buys hard physical
isolation and per-tenant PITR at the cost of N migration runs and cross-tenant reporting friction.
**OPEN QUESTION for Security/Sponsor:** does the commercial/PII classification of bid+award data
mandate physical per-tenant isolation, or is RLS + app-filter defense-in-depth sufficient? This is the
single biggest fork in our IaC; we need it answered before staging hardens. Our pipeline is built so the
answer is a deploy-topology change, not a code change.

---

## 2. Local dev

One command to a working store. Everything below is scaffolded in Phase 0.

**`docker-compose.yml` (in `infra/`)** — three services on a private network:
- `db`: `postgres:15`, named volume, healthcheck (`pg_isready`), `POSTGRES_*` from `.env`.
- `backend`: built from `backend/Dockerfile`, mounts source for hot-reload, `depends_on: db` (healthy),
  runs `uvicorn app.main:app --reload`; exposes `:8000`.
- `adminer`: lightweight DB UI on `:8080` (pgAdmin is the heavier alternative; adminer is the default —
  one container, no config). Frontend (`web`) is added as a fourth service at Phase F (ADR-0002).
- `worker` shares the backend image (async entry) — reserved seam, off by default in early phases.

**`Makefile` targets** (thin wrappers; the contract every squad and CI shares):

| Target | Does |
|---|---|
| `make up` / `make down` | compose up -d / down; `up` waits on db health |
| `make migrate` | `alembic upgrade head` in the backend container |
| `make migrate-down` | `alembic downgrade -1` (and `roundtrip` chains up→base→up, the CI check) |
| `make revision m="…"` | `alembic revision --autogenerate` |
| `make seed` | load synthetic reference + a sample cycle into the running store |
| `make test` | `pytest` (unit + service tests against the compose Postgres) |
| `make lint` | `ruff check` + `ruff format --check` |
| `make type` | `mypy backend/app` |
| `make check` | lint + type + test + roundtrip + import-guard (the full local CI mirror) |
| `make fmt` | `ruff format` (write) |

**Env management.** A committed **`.env.example`** documents every variable with safe placeholder
values; the real **`.env` is gitignored** and never committed (Security owns the classification rule,
ADR-0001 §4 / ADR-0015). Settings load through one typed `pydantic-settings` object (architecture §7);
no literals in code. CI and prod inject the same variable names from their secret store, so the only
difference between environments is the *values*, never the *shape*. A `.gitignore` entry for `.env`,
`*.env.local`, and `reference/samples/` is part of the scaffold.

---

## 3. CI/CD pipeline

GitHub Actions, one workflow `.github/workflows/ci.yml`. The job graph below is the contract; the final
YAML is authored in the scaffold (E-00). Jobs run in parallel where independent and fan into a single
required `ci-pass` gate so branch protection has one status to require.

**Triggers.** `on: pull_request` (all branches → `main`) and `on: push` to `main`. PRs run the full
graph; `main` runs the full graph **plus** image build/push and the deploy-to-staging job.

**Jobs (each = a separate Actions job):**

1. **lint** — checkout → setup-python 3.12 → cache pip → `ruff check` + `ruff format --check`. Fast, no DB.
2. **type** — `mypy backend/app`. No DB.
3. **reference-guard** — the clean-room invariant (ADR-0001). Fails if `backend/` imports from
   `reference/`. Implemented as a grep/AST scan over `backend/` for `import reference`,
   `from reference`, and `reference.` references; non-zero match → fail. Cheap, runs on every PR; this
   gate is a program non-negotiable, not a lint nicety.
4. **test** — `services: postgres:15` (Actions service container) → `make migrate` → `pytest` (unit +
   service tests against real Postgres, per architecture §7 — no SQLite, R8). Coverage reported.
5. **migration-roundtrip** — the WAYS-OF-WORKING §3 requirement. Against a fresh Postgres service:
   `alembic upgrade head` → dump schema → `alembic downgrade base` → `alembic upgrade head` → dump
   again → assert the two dumps are **byte-identical**, then `alembic check` asserts **no model drift**.
   Also asserts the constraint-count floor Platform & Data specify (≥46 composite FKs, the de-no-op'd
   CHECK count) so M0 fidelity is gated, not hoped (R-PD2).
6. **frontend-build** — Phase F onward (ADR-0002): setup-node → `npm ci` → typecheck → `next build` →
   (generated OpenAPI client check: types regenerate clean from the backend contract). Skipped via path
   filter until `frontend/` exists, so it is a no-op early without red X's.
7. **ci-pass** — `needs: [lint, type, reference-guard, test, migration-roundtrip, frontend-build]`;
   the single required check for branch protection.

**Skeleton (illustrative, not the final file):**

```yaml
name: ci
on:
  pull_request: { branches: [main] }
  push: { branches: [main] }
jobs:
  lint:               # ruff check + format --check
  type:               # mypy backend/app
  reference-guard:    # fail if backend/ imports reference/
  test:               # postgres service -> alembic upgrade -> pytest
  migration-roundtrip:# up->down->up byte-identical + alembic check + constraint floor
  frontend-build:     # next build + generated-client check (path-filtered until Phase F)
  ci-pass:            # needs: [all above] -> the one required status
  # main-only, gated on ci-pass:
  build-push:         # build image, tag :sha + :main, push to registry
  deploy-staging:     # deploy digest, run migrations (gated, §7), smoke
```

**Branch protections (on `main`).** No direct pushes (already program policy); require PR + **review by
the owning squad lead** (WoW §3); require `ci-pass`; require branch up-to-date; linear history;
dismiss stale approvals on new commits. Breaking-migration PRs (G1/G2) additionally require Architect +
Platform & Data review (§7).

**What runs where.** *PR:* jobs 1–7 (the gate). *main:* the gate **+** `build-push` + `deploy-staging`.
Prod deploy is a manual promotion of the staging-validated digest (a `workflow_dispatch` or a protected
`deploy-prod` job behind an environment approval), not automatic.

---

## 4. IaC & hosting approach

**Target: container-based, managed Postgres, provider-neutral until DEP-4.** The architecture is four
containers + a database (architecture §6); we host them as containers and keep Postgres **managed** (we
do not run our own HA Postgres — PITR, failover, and patching are the managed service's job; this is a
system of record and durability is the point).

- **Recommendation (pending DEP-4):** a managed container runtime + managed Postgres on the sponsor's
  chosen cloud. The default, decisive recommendation if the choice is left to us: **AWS — ECS Fargate (or
  App Runner) + RDS for PostgreSQL 15 + ECR + Secrets Manager**, because it gives managed Postgres with
  PITR, IAM-scoped secrets, and a small ops surface. The design is portable: Azure (Container Apps +
  Flexible Server + Key Vault) or GCP (Cloud Run + Cloud SQL + Secret Manager) are drop-in equivalents.
  Nothing in the app couples to a provider (architecture §4.2: IdP-neutral at the edge).
- **IaC.** Terraform under `infra/terraform/`, one module per concern (network, db, service, secrets),
  per-environment `.tfvars` (`dev`/`stage`/`prod`). State in a remote backend (chosen at DEP-4). dev needs
  no Terraform — it is compose only. Scaffold ships the module layout + a `README`; the real provider
  blocks land when DEP-4 resolves.
- **Secrets management.** No secret in git, ever (ADR-0001 §4). dev: `.env` (gitignored). stage/prod:
  the cloud secret store, injected as env vars at runtime under the **same variable names** as
  `.env.example`. CI secrets (registry creds, deploy role) live in GitHub Actions encrypted secrets /
  OIDC-federated role — no long-lived cloud keys in the repo. Secret rotation is the secret store's job.
- **Image build/push.** One backend image (API + worker, selected by entrypoint); a separate frontend
  image at Phase F. Built once on `main`, tagged `:<git-sha>` (immutable) and `:main` (moving),
  pushed to the registry. The **digest** is what deploys — stage and prod run the identical digest.
- **Deploy strategy.** Rolling deploy with health-gated cutover (readiness probe must pass before old
  tasks drain); migrations run as a **pre-deploy step** gated per §7. Rollback = redeploy the previous
  digest (and, for additive migrations, no down-migration needed; for breaking ones, §7 governs).
  Blue/green is reserved for the breaking-migration releases. **DEP-4 (cloud + IdP) is sponsor-pending**;
  until it lands, stage/prod IaC is scaffolded-but-not-applied and we run dev + CI only.

---

## 5. Observability

Three signals + audit, with tenant/request correlation everywhere (the store is multi-tenant; a log line
without a tenant is a bug).

- **Structured logging.** JSON logs (one event per line), every line carrying `request_id`, `tenant`
  (`client_id`), `principal`, `route`, `status`, `latency_ms`. No secrets or raw commercial data in logs
  (Security classification). Correlation id is generated at the edge and threaded through services and the
  worker. Log level by env (DEBUG dev, INFO stage/prod).
- **Health / readiness endpoints.** `GET /healthz` (liveness — process up, no dependencies) and
  `GET /readyz` (readiness — DB reachable, migrations at head, engine-impl selected). The orchestrator
  routes traffic only when `/readyz` is green; `/readyz` failing on "migrations not at head" is how a
  half-applied deploy is caught before it serves.
- **Metrics.** Prometheus-style metrics endpoint (`/metrics`): request rate/latency/error by route,
  DB pool saturation, migration status gauge, engine-run duration, import row counts + quarantine rate.
  Scraped by the platform's metrics stack (managed offering at DEP-4). The seam is reserved in the
  scaffold (architecture §7 leaves "metrics seam for DevOps").
- **Audit-event sink (coordinate w/ Security).** The `audit.event_log` is **not** an observability
  concern — it is the live, hash-chained, in-transaction governance record owned by Security (G11,
  architecture §4.3). DevOps's responsibility is to (a) **never** treat it as a log target we can sample
  or drop, (b) ensure its table is in the PITR/backup scope as a first-class durable asset, and (c)
  surface a **metric** (events/sec, chain-verify pass/fail) without reading payloads. Operational logs
  and the audit log are different systems; we keep them separate by design. **OPEN with Security:**
  confirm the audit log stays in-Postgres (our recommendation — it must be in the same transaction as the
  change it records) versus any external sink.
- **Error tracking.** An error-aggregation service (e.g. Sentry-class; provider at DEP-4) captures
  unhandled exceptions with the same correlation ids, scrubbed of PII/commercial fields. Errors page on
  rate, not on single occurrences (this is system-of-record scale, not high-traffic).

---

## 6. Performance / sizing

The workload is **modest and bounded** — this is a system of record, so we **design for clarity,
correctness, and auditability, not throughput.** Stated scale: tens of categories, dozens of DCs,
hundreds of lots, single-digit-thousand bids per cycle.

- **Data volume.** A cycle is ~10³ bids × a handful of price/landed-cost/eligibility rows each ≈ low tens
  of thousands of rows per cycle. Feeds (iTrade receipts) are the largest table — receipt-grain over
  history — but still comfortably in the millions-of-rows range over years, trivial for Postgres with the
  right indexes (Platform & Data own the index design). The whole store fits on the smallest production
  managed-DB tier with headroom; we **size up only on measured need.**
- **Compute.** One engine run scores ~10³ bids and computes 7 scenarios — sub-second to low-seconds of
  in-process compute (pure library, no I/O during compute, architecture §3). Synchronous request handling
  is fine through Phase E; the worker seam exists for long imports + document generation, promoted to a
  real queue only if a measurement says so (architecture §9). **2 small backend replicas** cover prod
  availability; this is concurrency-of-a-handful-of-analysts, not public traffic.
- **The binding NFR is not throughput — it is "open last cycle" < 2s** (roadmap Phase A gate). That is an
  indexing + query-shape problem (the `round_analysis_snapshot` anchor + the event trail), not a scaling
  problem; we hold it as a CI/perf-smoke assertion, not a capacity plan.
- **Sizing posture:** start at the smallest sensible tier in every environment; the only thing we
  over-provision is **durability** (managed Postgres HA + PITR + backups in prod), because losing the
  record is the one unacceptable failure for a system of record. Everything else scales on evidence.

---

## 7. Migration safety (the two breaking migrations, G1/G2)

Every migration is roundtrip-gated in CI (§3 job 5) — that protects *correctness*. The two **breaking**
migrations (M-G1 split-award, M-G2 scenario-generalize; Platform & Data §2) additionally need
*deployment* safety, because they touch the solver core and every read that assumes one winner.

- **Feature-flagged, shipped together.** Both land behind `feature.split_award` and
  `feature.scenario_lenses` (Platform & Data §2; Ed's reconciliation — G1+G2 ship as one increment with
  E-18). The schema change deploys **flag-off**: the new grain exists, the old behavior is preserved
  (auto scenario still defaults to one supplier per DC — permit-not-force) until the flag flips. Flag
  state is config, set per environment, so prod enables only after stage proves it.
- **Sequenced after the Phase-B pilot.** These migrations are blocked from `main` until the additive
  store is proven on real data (Phase B gate, R1). The pipeline enforces ordering by phase label, not by
  hope.
- **Pipeline gating.** A PR carrying a migration labeled `breaking` triggers extra required reviewers
  (Architect + Platform & Data, §3 branch protection) and an **expand/contract** discipline in the
  roundtrip job: the migration must be additive-then-cutover (expand: add the new grain alongside the old;
  contract: a later, separate migration removes the old) so a rollback never strands data. The roundtrip
  job additionally asserts the **forward data-migration** of any seeded scenario rows (Platform & Data §2)
  and the rewritten capacity-arithmetic CHECK before the flag can be enabled.
- **Deploy choreography.** Breaking releases deploy blue/green (not rolling): new code + flag-off goes
  live, migration runs in expand mode, smoke + chain-verify pass, then the flag flips in a config-only
  change (no redeploy). Rollback before flag-flip = redeploy previous digest; the expand migration is
  non-destructive so no down-migration is needed in the hot path. The contract (old-grain removal) ships
  only after the flagged behavior is confirmed in prod.

---

## 8. Risks (squad-owned)

- **R-DO1 (High) — DEP-4 unresolved (cloud + IdP).** Stage/prod IaC, the secret store, the error/metrics
  vendors, and the auth edge all fork on it. *Mitigation:* provider-neutral design (§4); dev + CI fully
  functional without it; Terraform module layout scaffolded so DEP-4 is a values change, not a rewrite.
- **R-DO2 (High) — tenancy topology fork (§1).** DB-per-tenant vs shared-schema+RLS changes the entire
  deploy/migration model. *Mitigation:* default to shared-schema+RLS, hold it as an OPEN question to
  Security/Sponsor, keep the pipeline so the answer is a topology change not a code change.
- **R-DO3 (Med) — breaking-migration blast radius (§7).** G1/G2 touch the solver core. *Mitigation:*
  flag-off deploy, expand/contract, blue/green, extra reviewers, post-pilot sequencing.
- **R-DO4 (Med) — CI gate erosion.** A roundtrip or reference-guard turned "advisory" silently lets a
  non-negotiable through. *Mitigation:* the gates are *required* checks via the single `ci-pass` status;
  removing one requires a branch-protection change (auditable), not a quiet skip.
- **R-DO5 (Med, shared) — secret leakage / sample-data classification.** `.env` and `reference/samples/`
  must never be committed (ADR-0001 §4, Security). *Mitigation:* `.gitignore` + a secret-scanning step in
  CI; Security owns the classification rule, we own the enforcement.

---

## 9. What this plan defers

- **Concrete cloud, IdP, secret store, metrics/error vendor** — all gated on DEP-4 (sponsor). Design is
  neutral; values land when it clears.
- **The tenancy topology** — recommended (shared-schema + RLS) but a Security/Sponsor call (§1).
- **Async/queue promotion** — the worker seam exists; promotion to a real queue is evidence-driven (§6).
- **The final `ci.yml` and Terraform provider blocks** — authored in the Phase 0 scaffold (E-00/E-02),
  designed here.

---

## Changelog

| Version | Date | Author | Change Summary |
|---------|------|--------|----------------|
| 1.0 | 2026-06-18 | DevOps lead | Initial platform & CI/CD plan: environments, local dev, CI job graph + branch protection, IaC/hosting recommendation, observability, sizing, G1/G2 migration safety. |
