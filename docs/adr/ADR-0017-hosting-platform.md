# ADR-0017 — Hosting platform: GCP (Cloud Run + Cloud SQL for PostgreSQL)

- **Status:** Accepted (2026-06-21) — sponsor delegated the choice to the decision methodology with the constraints below
- **Deciders:** Sponsor (Ed), PM, Solution Architect, DevOps
- **Relates:** DEP-4 (hosting/cloud + IdP); ADR-0003 (execution model — two runtimes: web console + MCP harness); ADR-0002 (frontend stack — Next.js/Node 20, Python 3.12); D30 (per-run isolated DBs); DEP-6 (USDA key → secret store); the CI image build (`.github/workflows/ci.yml`); gaps G-C/G-J (RBAC/tenancy → future IdP)

## Context

The platform is ready to choose where it runs (resolving the hosting half of DEP-4). The system is
**FastAPI + SQLAlchemy + Alembic + PostgreSQL 16** (the governed system of record, including the
audit hash-chain) with a **Next.js** console; CI already **builds a container image**. The sponsor
set the frame and delegated the pick to our decision methodology:

- **Hard exclusion:** *not Azure.*
- **"Best for longevity"** — a durable vendor and low lock-in / a clean exit path.
- **Budget:** *"modest monthly OK for reliability"* — reliability over absolute-cheapest; cost-aware,
  not free-tier-only.
- **Standing principle:** full functionality with the **least margin for error** (operational
  simplicity, managed durability for the governed data).

## Decision

**Host on Google Cloud Platform: the web console as a container on Cloud Run, backed by Cloud SQL
for PostgreSQL 16, with Secret Manager for secrets and Artifact Registry for images.**

- **Compute — Cloud Run** runs the CI-built container image directly (no rearchitecting; matches
  ADR-0003 and the existing image build). It **scales to zero** between pilot runs → near-zero idle
  cost, and a small always-warm `min-instances=1` is the "modest monthly for reliability" dial when
  we want no cold starts.
- **Database — Cloud SQL for PostgreSQL 16**, managed, with **automated backups + point-in-time
  recovery** — the durability the governed system of record and the audit hash-chain require. The
  MCP harness's **per-run isolated DBs (D30)** are provisioned as separate logical databases on the
  same instance (cheap), keeping the two-runtime model intact.
- **Secrets — Secret Manager** for the USDA MARS key (DEP-6), the session-signing key, and vault
  git credentials — never in chat/repo (matches the DEP-6 rule).
- **Images — Artifact Registry**, deployed by digest from CI on push to `main` (the commented
  main-only stanza in `ci.yml` becomes build-push + deploy-to-staging).
- **Identity (the IdP half of DEP-4) — deferred, not chosen now.** Phase 1 is single-operator and
  keeps our own auth + TOTP 2FA. When tenancy/RBAC (G-C/G-J) is built, **Google Identity Platform**
  is the native path; this ADR does not commit to it.

### Methodology — criteria → options

Criteria weighted by the sponsor's frame (longevity and least-margin-for-error lead; cost is a
"modest monthly" floor, not "minimize"):

| Criterion (weight) | A. GCP — Cloud Run + Cloud SQL | B. AWS — App Runner/Fargate + RDS | C. PaaS — Render / Fly.io |
|---|---|---|---|
| **Longevity / low lock-in** (high) | ✅ Tier-1 hyperscaler; Cloud Run = Knative (open standard → portable) | ✅ Tier-1 hyperscaler; portable containers | ⚠️ Smaller vendors — real continuity risk |
| **Not Azure** (hard) | ✅ | ✅ | ✅ |
| **Least margin for error / ops simplicity** (high) | ✅ Simplest container→prod among hyperscalers; managed DB | ◐ ECS/Fargate heavier; App Runner simpler but newer | ✅ Simplest overall |
| **Managed Postgres durability** (high) | ✅ Cloud SQL: backups + PITR | ✅ RDS: backups + PITR | ◐ Managed PG, lighter PITR/SLAs |
| **Cost at pilot scale** ("modest monthly") | ✅ Scale-to-zero idle; pay-per-use | ◐ App Runner no true scale-to-zero | ✅ Lowest flat cost |
| **Fit to CI image + 2 runtimes** (high) | ✅ Runs the image as-is; per-run DBs as logical DBs | ✅ Comparable | ◐ Workable; per-run DBs less clean |
| **Future IdP for tenancy/RBAC** (med) | ✅ Identity Platform | ✅ Cognito | ❌ Bring-your-own |

**GCP wins** on the two highest-weighted criteria (longevity + least-margin-for-error) without
giving up managed durability or cost discipline, and it runs our container with the least change.

## Consequences

- DevOps stands up: Artifact Registry, a Cloud SQL Postgres 16 instance (private IP + automated
  backups/PITR), Cloud Run services for the console, Secret Manager entries (USDA key, session key,
  vault credentials), and the `main`-branch build-push → deploy-to-staging continuation of `ci.yml`.
- `DATABASE_URL` stays the single connection variable (DevOps PLAN §2); only host/creds differ.
- **DEP-4 hosting half = resolved (GCP);** IdP half stays open, deferred to the tenancy/RBAC work
  (G-C/G-J), with Identity Platform as the documented forward option.
- Prod is a **manual promotion** of the staging-validated digest (workflow_dispatch behind an
  environment approval), never automatic — unchanged from `ci.yml`'s intent.
- Low exit cost preserved: the app is a standard container + standard Postgres, so a move to AWS
  (the runner-up) is a redeploy + a Postgres dump/restore, not a rewrite.

## Rejected

- **Azure** — hard-excluded by the sponsor.
- **AWS (App Runner/Fargate + RDS)** — equally durable and the **documented fallback**, but chosen
  against on operational simplicity + idle cost for a pilot (App Runner has no true scale-to-zero;
  Fargate/ECS is heavier to operate). The low-lock-in design keeps this a cheap future switch.
- **Managed PaaS (Render / Fly.io)** — lowest cost and simplest, but **fails "best for longevity"**
  (smaller-vendor continuity risk) and offers a weaker IdP/RBAC path for the multi-tenant future.
- **Self-managed VMs / k8s** — maximum control, maximum operational surface; violates
  least-margin-for-error for a pilot with one operator.
