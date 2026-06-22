# Deploying KR_RFP to GCP — Cloud Run + Cloud SQL (RUNBOOK)

This deploys the KR_RFP web console to **Google Cloud Run** (two services: a FastAPI backend and a
Next.js frontend) backed by **Cloud SQL for PostgreSQL**, with secrets in **Secret Manager** and
images in **Artifact Registry**. Hosting decision: ADR-0017; storage model (stateless, no
server-side files): ADR-0018 / D40 / D41.

One script does the whole thing — [`deploy.sh`](deploy.sh) — idempotently (create-if-not-exists, so
re-running reconciles). The seed lives in [`seed.py`](seed.py).

---

## 1. Prerequisites

- A **GCP project with billing enabled**.
- The **`gcloud` CLI** installed and on your PATH (`gcloud --version`).
- **`openssl`** (used to generate the random secrets) — standard on macOS/Linux.
- Permission to act on the project (see roles below).

> You do **not** need Docker locally: images build in the cloud via `gcloud builds submit`
> (Cloud Build). Docker is only needed for the local compose verification (see §7).

### IAM roles (the service-account / operator path)

The identity that runs `deploy.sh` needs these roles on the project:

| Role | Why |
|---|---|
| `roles/run.admin` | create/deploy Cloud Run services + jobs |
| `roles/cloudsql.admin` | create the Cloud SQL instance, database, user |
| `roles/artifactregistry.admin` | create the image repo |
| `roles/secretmanager.admin` | create secrets + grant access |
| `roles/iam.serviceAccountUser` | let Cloud Run/Build act as the runtime service account |
| `roles/cloudbuild.builds.editor` | submit Cloud Build builds |
| `roles/serviceusage.serviceUsageAdmin` | enable the required APIs |

The script also grants the **Cloud Run runtime service account** (the project's Compute default SA,
`PROJECTNUMBER-compute@developer.gserviceaccount.com`) `roles/secretmanager.secretAccessor` (to read
the DB password + app key) and `roles/cloudsql.client` (to reach Cloud SQL) — automatically.

---

## 2. The two access paths

Pick one to authenticate `gcloud` before running the script:

**(a) Operator login (interactive).**
```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

**(b) Service-account key (CI / automation).**
```bash
gcloud auth activate-service-account --key-file=/path/to/key.json
gcloud config set project YOUR_PROJECT_ID
```
The service account must hold the roles in §1.

---

## 3. Parameters

Set these as environment variables before running (only `PROJECT_ID` and `SEED_ADMIN_PASSWORD` are
required):

| Var | Required | Default | Meaning |
|---|---|---|---|
| `PROJECT_ID` | **yes** | — | your GCP project id |
| `SEED_ADMIN_PASSWORD` | **yes (for the seed)** | — | the `admin` console login password |
| `REGION` | no | `us-central1` | the Cloud Run + Cloud SQL region |
| `APP_PREFIX` | no | `kr-rfp` | names every resource (`<prefix>-backend`, `<prefix>-sql`, …) |
| `DB_TIER` | no | `db-f1-micro` | Cloud SQL machine tier |
| `DB_NAME` | no | `kr_rfp` | the application database name |
| `DB_USER` | no | `kr_rfp_app` | the application DB user |
| `MIN_INSTANCES` | no | `0` | set `1` for the "always warm" reliability dial (ADR-0017) |
| `RUN_SEED` | no | `1` | set `0` (or pass `--no-seed`) to skip seeding |

The DB password and the app JWT/secret-key are **auto-generated** into Secret Manager on first run —
you never type or store them. (You can rotate them later by adding a new secret version and
re-running.)

---

## 4. One-command deploy

```bash
export PROJECT_ID=your-gcp-project
export SEED_ADMIN_PASSWORD='choose-a-strong-password'
# optional: export REGION=us-east1  APP_PREFIX=kr-rfp  MIN_INSTANCES=1

./deploy/gcp/deploy.sh
```

What it does, in order (each step is idempotent and echoes what it's doing):

1. **Enable APIs** — run, sqladmin, artifactregistry, secretmanager, cloudbuild.
2. **Artifact Registry** — create the `<prefix>-images` Docker repo.
3. **Secret Manager** — create `<prefix>-db-password` + `<prefix>-auth-secret-key` (random values).
4. **Cloud SQL** — create the Postgres 16 instance + `kr_rfp` database + the app user (password from
   the secret).
5. **Grant runtime IAM** — secret accessor + `cloudsql.client` to the Cloud Run runtime SA.
6. **Build + push the backend image** (Cloud Build).
7. **Deploy the backend** Cloud Run service — `--add-cloudsql-instances`, `DATABASE_URL` over the
   `/cloudsql/<conn>` **unix socket**, `AUTH_SECRET_KEY` from Secret Manager.
8. **Run migrations** — `alembic upgrade head` against Cloud SQL via a one-off **Cloud Run job**.
9. **Build + push the frontend image** with `NEXT_PUBLIC_API_BASE_URL` = the backend URL (it is
   inlined at build time, so this must happen *after* the backend is up).
10. **Deploy the frontend** Cloud Run service.
11. **Wire CORS** — set the backend's `CORS_ALLOW_ORIGINS` to the frontend URL.
12. **Seed** (unless `--no-seed`) — admin user + TOMATO + POTATO cycles via a Cloud Run job.

At the end it prints the **frontend URL**. Open it and log in as `admin` with your
`SEED_ADMIN_PASSWORD`.

Reprint the URLs any time:
```bash
PROJECT_ID=your-gcp-project ./deploy/gcp/deploy.sh --print-urls
```

---

## 5. Seeding (separately, if you skipped it)

The seed creates: an `admin` console user, the **TOMATO** synthetic cycle, and the **POTATO**
real-data cycle — both driven through the real `PilotService` to a **FROZEN award**, so the runs
list and the Awards screens render. It is committed (the dry-run script rolls back; the seed
commits).

Re-run the seed job:
```bash
gcloud run jobs execute kr-rfp-seed --region us-central1 --project YOUR_PROJECT_ID --wait
```
Or run it locally against any database by pointing `DATABASE_URL` at it:
```bash
DATABASE_URL='postgresql+psycopg://user:pw@host:5432/kr_rfp' \
  SEED_ADMIN_PASSWORD='...' python deploy/gcp/seed.py
# flags: --admin-only | --skip-tomato | --skip-potato | --admin-username NAME
```

---

## 6. Rough cost

Smallest sensible tier (pilot posture, scale-to-zero):

| Resource | Approx monthly |
|---|---|
| Cloud SQL `db-f1-micro` (shared vCPU, ~10GB) | ~$8–15 (it runs 24/7 — the main cost) |
| Cloud Run (both services, scale-to-zero) | ~$0 idle; cents per active hour |
| Artifact Registry + Secret Manager | <$1 |
| **Total** | **~$10–20/month** at pilot usage |

Set `MIN_INSTANCES=1` for an always-warm backend (no cold starts) — adds a small steady Cloud Run
charge. Bump `DB_TIER` for production durability/throughput.

---

## 7. Local full-stack verification (no GCP needed)

Before deploying, prove the exact container shape locally with the repo-root
[`docker-compose.yml`](../../docker-compose.yml) (Docker required):

```bash
docker compose up --build -d          # postgres + migrate + backend + frontend
docker compose run --rm seed          # admin + the two cycles (set SEED_ADMIN_PASSWORD)
# backend:  http://localhost:8000/api/v1/health  +  /api/v1/ready
# frontend: http://localhost:3000   (log in as admin)
docker compose down -v                # stop + wipe
```

This is the de-risk harness: it wires the services together exactly as the two Cloud Run services
are (frontend `NEXT_PUBLIC_API_BASE_URL` → backend; backend `DATABASE_URL` → postgres; a migrate
step before serving; the same seed). It differs from prod only where it must: a local DB password,
`AUTH_COOKIE_SECURE=false` (plain http on localhost), and HTTP instead of HTTPS.

---

## 8. Teardown

Delete everything the script created (replace the prefix/region if you changed them):

```bash
PROJECT=YOUR_PROJECT_ID; REGION=us-central1; P=kr-rfp
gcloud run services delete  $P-backend  --region $REGION --project $PROJECT -q
gcloud run services delete  $P-frontend --region $REGION --project $PROJECT -q
gcloud run jobs delete      $P-migrate  --region $REGION --project $PROJECT -q
gcloud run jobs delete      $P-seed     --region $REGION --project $PROJECT -q
gcloud sql instances delete $P-sql      --project $PROJECT -q          # deletes the DB + data
gcloud artifacts repositories delete $P-images --location $REGION --project $PROJECT -q
gcloud secrets delete $P-db-password     --project $PROJECT -q
gcloud secrets delete $P-auth-secret-key --project $PROJECT -q
```

> Deleting the Cloud SQL instance is irreversible and removes all data. Export/back up first if you
> need to keep anything.
