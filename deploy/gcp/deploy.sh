#!/usr/bin/env bash
# ============================================================================================
# deploy/gcp/deploy.sh — one-command, idempotent deploy of KR_RFP to GCP Cloud Run + Cloud SQL.
#
# Deploys TWO Cloud Run services (backend FastAPI + frontend Next.js) backed by a Cloud SQL
# Postgres instance, with secrets in Secret Manager and images in Artifact Registry. Every step is
# CREATE-IF-NOT-EXISTS, so re-running it is safe (it reconciles, never duplicates) and echoes what
# it is doing.
#
# Hosting decision: ADR-0017 (GCP Cloud Run + Cloud SQL) / ADR-0018 (stateless, no server-side
# files). The containers persist nothing to disk — Postgres is the system of record.
#
# Prerequisites + IAM roles + the access paths are in README.md (this directory). In short:
#   gcloud auth login        # or: gcloud auth activate-service-account --key-file=KEY.json
#   export PROJECT_ID=my-gcp-project
#   export SEED_ADMIN_PASSWORD='a-strong-password'      # for the post-deploy seed
#   ./deploy/gcp/deploy.sh
#
# Parameters (env vars):
#   PROJECT_ID            (required) the GCP project id
#   REGION               (default: us-central1)
#   APP_PREFIX           (default: kr-rfp)   names every resource: <prefix>-backend, etc.
#   DB_TIER              (default: db-f1-micro)   Cloud SQL machine tier
#   DB_NAME              (default: kr_rfp)
#   DB_USER              (default: kr_rfp_app)
#   SEED_ADMIN_PASSWORD  (required for --seed) the console admin password
#   RUN_SEED             (default: 1)  set 0 to skip the post-deploy seed
#   MIN_INSTANCES        (default: 0)  set 1 for the "always warm" reliability dial (ADR-0017)
#
# Usage:
#   ./deploy.sh            full deploy (APIs -> registry -> SQL -> secrets -> build -> deploy -> migrate -> seed)
#   ./deploy.sh --no-seed  skip the seed step
#   ./deploy.sh --print-urls   just print the current service URLs and exit
# ============================================================================================
set -euo pipefail

# --------------------------------------------------------------------------------------------
# parameters
# --------------------------------------------------------------------------------------------
PROJECT_ID="${PROJECT_ID:-}"
REGION="${REGION:-us-central1}"
APP_PREFIX="${APP_PREFIX:-kr-rfp}"
DB_TIER="${DB_TIER:-db-f1-micro}"
DB_NAME="${DB_NAME:-kr_rfp}"
DB_USER="${DB_USER:-kr_rfp_app}"
RUN_SEED="${RUN_SEED:-1}"
MIN_INSTANCES="${MIN_INSTANCES:-0}"

# Derived resource names (all deterministic from the prefix, so re-runs reconcile).
AR_REPO="${APP_PREFIX}-images"
SQL_INSTANCE="${APP_PREFIX}-sql"
BACKEND_SVC="${APP_PREFIX}-backend"
FRONTEND_SVC="${APP_PREFIX}-frontend"
SECRET_DB_PASSWORD="${APP_PREFIX}-db-password"
SECRET_APP_KEY="${APP_PREFIX}-auth-secret-key"

# Repo root = two parents up from this script (deploy/gcp/deploy.sh).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# --------------------------------------------------------------------------------------------
# small helpers
# --------------------------------------------------------------------------------------------
say()  { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
info() { printf '    %s\n' "$*"; }
die()  { printf '\033[1;31mERROR: %s\033[0m\n' "$*" >&2; exit 1; }

require_tools() {
  command -v gcloud >/dev/null 2>&1 || die "gcloud is not installed (https://cloud.google.com/sdk)."
}

require_project() {
  [ -n "${PROJECT_ID}" ] || die "PROJECT_ID is not set. export PROJECT_ID=your-gcp-project"
}

# --print-urls fast path -------------------------------------------------------------------
print_urls() {
  local be fe
  be="$(gcloud run services describe "${BACKEND_SVC}"  --region "${REGION}" --project "${PROJECT_ID}" --format='value(status.url)' 2>/dev/null || true)"
  fe="$(gcloud run services describe "${FRONTEND_SVC}" --region "${REGION}" --project "${PROJECT_ID}" --format='value(status.url)' 2>/dev/null || true)"
  echo "backend : ${be:-<not deployed>}"
  echo "frontend: ${fe:-<not deployed>}"
}

# --------------------------------------------------------------------------------------------
# 1. enable the needed APIs (idempotent — enabling an already-enabled API is a no-op)
# --------------------------------------------------------------------------------------------
enable_apis() {
  say "Enabling required APIs"
  gcloud services enable \
    run.googleapis.com \
    sqladmin.googleapis.com \
    artifactregistry.googleapis.com \
    secretmanager.googleapis.com \
    cloudbuild.googleapis.com \
    --project "${PROJECT_ID}"
  info "run, sqladmin, artifactregistry, secretmanager, cloudbuild enabled."
}

# --------------------------------------------------------------------------------------------
# 2. Artifact Registry repo (Docker)
# --------------------------------------------------------------------------------------------
ensure_artifact_registry() {
  say "Ensuring Artifact Registry repo '${AR_REPO}'"
  if gcloud artifacts repositories describe "${AR_REPO}" \
       --location "${REGION}" --project "${PROJECT_ID}" >/dev/null 2>&1; then
    info "repo exists."
  else
    gcloud artifacts repositories create "${AR_REPO}" \
      --repository-format=docker \
      --location "${REGION}" \
      --description "KR_RFP container images" \
      --project "${PROJECT_ID}"
    info "repo created."
  fi
}

# --------------------------------------------------------------------------------------------
# 3. Cloud SQL Postgres instance + database + user
# --------------------------------------------------------------------------------------------
ensure_cloud_sql() {
  say "Ensuring Cloud SQL instance '${SQL_INSTANCE}' (Postgres 16)"
  if gcloud sql instances describe "${SQL_INSTANCE}" --project "${PROJECT_ID}" >/dev/null 2>&1; then
    info "instance exists."
  else
    info "creating instance (this takes several minutes the first time) ..."
    gcloud sql instances create "${SQL_INSTANCE}" \
      --database-version=POSTGRES_16 \
      --tier="${DB_TIER}" \
      --region="${REGION}" \
      --storage-auto-increase \
      --project "${PROJECT_ID}"
    info "instance created."
  fi

  say "Ensuring database '${DB_NAME}'"
  if gcloud sql databases describe "${DB_NAME}" --instance "${SQL_INSTANCE}" --project "${PROJECT_ID}" >/dev/null 2>&1; then
    info "database exists."
  else
    gcloud sql databases create "${DB_NAME}" --instance "${SQL_INSTANCE}" --project "${PROJECT_ID}"
    info "database created."
  fi

  say "Ensuring database user '${DB_USER}'"
  # The password is whatever we stored in Secret Manager (created/ensured below before this runs).
  local db_password
  db_password="$(gcloud secrets versions access latest --secret "${SECRET_DB_PASSWORD}" --project "${PROJECT_ID}")"
  if gcloud sql users list --instance "${SQL_INSTANCE}" --project "${PROJECT_ID}" --format='value(name)' | grep -qx "${DB_USER}"; then
    info "user exists — resetting its password to the stored secret (idempotent)."
    gcloud sql users set-password "${DB_USER}" \
      --instance "${SQL_INSTANCE}" --password "${db_password}" --project "${PROJECT_ID}"
  else
    gcloud sql users create "${DB_USER}" \
      --instance "${SQL_INSTANCE}" --password "${db_password}" --project "${PROJECT_ID}"
    info "user created."
  fi

  # The instance connection name "project:region:instance" — the /cloudsql socket path on Cloud Run.
  SQL_CONNECTION_NAME="$(gcloud sql instances describe "${SQL_INSTANCE}" \
    --project "${PROJECT_ID}" --format='value(connectionName)')"
  info "connection name: ${SQL_CONNECTION_NAME}"
}

# --------------------------------------------------------------------------------------------
# 2.5 Secret Manager — DB password + the app JWT/secret-key. Created BEFORE Cloud SQL so the user
#     password comes from the secret (single source of truth). Both are auto-generated if absent.
# --------------------------------------------------------------------------------------------
ensure_secret() {
  local name="$1" generate="$2"
  if gcloud secrets describe "${name}" --project "${PROJECT_ID}" >/dev/null 2>&1; then
    info "secret '${name}' exists."
  else
    info "creating secret '${name}' ..."
    gcloud secrets create "${name}" --replication-policy=automatic --project "${PROJECT_ID}"
    if [ "${generate}" = "generate" ]; then
      # 32 random bytes -> base64; a strong default the operator never has to type.
      openssl rand -base64 32 | tr -d '\n' \
        | gcloud secrets versions add "${name}" --data-file=- --project "${PROJECT_ID}"
      info "generated an initial version for '${name}'."
    fi
  fi
}

ensure_secrets() {
  say "Ensuring secrets in Secret Manager"
  ensure_secret "${SECRET_DB_PASSWORD}" generate
  ensure_secret "${SECRET_APP_KEY}"     generate
}

# --------------------------------------------------------------------------------------------
# grant the Cloud Run runtime service account read access to the secrets + the Cloud SQL client role
# (idempotent — re-adding a binding is a no-op).
# --------------------------------------------------------------------------------------------
grant_runtime_iam() {
  say "Granting the Cloud Run runtime SA access to secrets + Cloud SQL"
  local project_number sa
  project_number="$(gcloud projects describe "${PROJECT_ID}" --format='value(projectNumber)')"
  # Cloud Run services run as the Compute default SA unless overridden.
  sa="${project_number}-compute@developer.gserviceaccount.com"
  info "runtime service account: ${sa}"

  for secret in "${SECRET_DB_PASSWORD}" "${SECRET_APP_KEY}"; do
    gcloud secrets add-iam-policy-binding "${secret}" \
      --member="serviceAccount:${sa}" \
      --role="roles/secretmanager.secretAccessor" \
      --project "${PROJECT_ID}" >/dev/null
  done
  gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
    --member="serviceAccount:${sa}" \
    --role="roles/cloudsql.client" >/dev/null
  info "secret accessor + cloudsql.client granted."
}

# --------------------------------------------------------------------------------------------
# 4. build + push BOTH images via Cloud Build (no local docker needed)
# --------------------------------------------------------------------------------------------
image_uri() { echo "${REGION}-docker.pkg.dev/${PROJECT_ID}/${AR_REPO}/$1:latest"; }

build_backend() {
  say "Building + pushing the backend image"
  local uri; uri="$(image_uri backend)"
  # The backend image builds from the REPO ROOT (it needs backend/ AND db/baseline/schema.sql in
  # their real relative layout — see backend/Dockerfile). `gcloud builds submit <dir> --tag` would
  # assume a Dockerfile at the context root, so we use an explicit cloudbuild.yaml that points at
  # backend/Dockerfile with the repo root as context.
  local cb; cb="$(mktemp)"
  cat >"${cb}" <<YAML
steps:
  - name: gcr.io/cloud-builders/docker
    args: [build, -f, backend/Dockerfile, -t, ${uri}, .]
images:
  - ${uri}
YAML
  gcloud builds submit "${REPO_ROOT}" --config "${cb}" --project "${PROJECT_ID}"
  rm -f "${cb}"
  info "pushed ${uri}"
}

build_frontend() {
  # NEXT_PUBLIC_API_BASE_URL is inlined at build time, so the frontend image must be built AFTER the
  # backend is deployed (we need its URL). gcloud builds submit can't pass --build-arg directly, so
  # we generate a tiny cloudbuild.yaml that does the docker build with the arg.
  local backend_url="$1"
  say "Building + pushing the frontend image (NEXT_PUBLIC_API_BASE_URL=${backend_url})"
  local uri; uri="$(image_uri frontend)"
  local cb; cb="$(mktemp)"
  cat >"${cb}" <<YAML
steps:
  - name: gcr.io/cloud-builders/docker
    args:
      - build
      - --build-arg
      - NEXT_PUBLIC_API_BASE_URL=${backend_url}
      - -t
      - ${uri}
      - .
images:
  - ${uri}
YAML
  gcloud builds submit "${REPO_ROOT}/frontend" --config "${cb}" --project "${PROJECT_ID}"
  rm -f "${cb}"
  info "pushed ${uri}"
}

# --------------------------------------------------------------------------------------------
# 5. deploy the backend Cloud Run service (Cloud SQL socket + DATABASE_URL + secrets)
# --------------------------------------------------------------------------------------------
deploy_backend() {
  say "Deploying the backend Cloud Run service '${BACKEND_SVC}'"
  local uri; uri="$(image_uri backend)"
  # DATABASE_URL uses the /cloudsql UNIX SOCKET (host=/cloudsql/<connection-name>), the standard
  # Cloud Run -> Cloud SQL path. psycopg accepts the socket dir as `host`. The password is injected
  # from Secret Manager; the rest is plain config. Note %2F-free socket form: host is a dir path.
  local db_url="postgresql+psycopg://${DB_USER}:PASSWORD_PLACEHOLDER@/${DB_NAME}?host=/cloudsql/${SQL_CONNECTION_NAME}"

  # We pass the password via a secret env var and compose DATABASE_URL at runtime would need a shell;
  # instead we inject the password into DATABASE_URL through a secret-backed env and let the app read
  # DB_PASSWORD + DATABASE_URL_TEMPLATE? Simpler + explicit: deploy with the password from the secret
  # substituted at deploy time (the URL still lives only in the service config, not the repo).
  local db_password
  db_password="$(gcloud secrets versions access latest --secret "${SECRET_DB_PASSWORD}" --project "${PROJECT_ID}")"
  db_url="${db_url/PASSWORD_PLACEHOLDER/${db_password}}"

  gcloud run deploy "${BACKEND_SVC}" \
    --image "${uri}" \
    --region "${REGION}" \
    --platform managed \
    --allow-unauthenticated \
    --port 8000 \
    --add-cloudsql-instances "${SQL_CONNECTION_NAME}" \
    --min-instances "${MIN_INSTANCES}" \
    --set-env-vars "ENV=production,DATABASE_URL=${db_url}" \
    --set-secrets "AUTH_SECRET_KEY=${SECRET_APP_KEY}:latest" \
    --project "${PROJECT_ID}"

  BACKEND_URL="$(gcloud run services describe "${BACKEND_SVC}" \
    --region "${REGION}" --project "${PROJECT_ID}" --format='value(status.url)')"
  info "backend URL: ${BACKEND_URL}"
}

# --------------------------------------------------------------------------------------------
# 6. deploy the frontend Cloud Run service (image already baked with the backend URL)
# --------------------------------------------------------------------------------------------
deploy_frontend() {
  say "Deploying the frontend Cloud Run service '${FRONTEND_SVC}'"
  local uri; uri="$(image_uri frontend)"
  gcloud run deploy "${FRONTEND_SVC}" \
    --image "${uri}" \
    --region "${REGION}" \
    --platform managed \
    --allow-unauthenticated \
    --port 3000 \
    --min-instances "${MIN_INSTANCES}" \
    --project "${PROJECT_ID}"

  FRONTEND_URL="$(gcloud run services describe "${FRONTEND_SVC}" \
    --region "${REGION}" --project "${PROJECT_ID}" --format='value(status.url)')"
  info "frontend URL: ${FRONTEND_URL}"
}

# --------------------------------------------------------------------------------------------
# 7. wire the backend CORS allowed-origin to the deployed frontend URL (a cheap env update)
# --------------------------------------------------------------------------------------------
wire_cors() {
  say "Wiring backend CORS_ALLOW_ORIGINS to the frontend URL"
  gcloud run services update "${BACKEND_SVC}" \
    --region "${REGION}" --project "${PROJECT_ID}" \
    --update-env-vars "CORS_ALLOW_ORIGINS=${FRONTEND_URL}"
  info "CORS now allows ${FRONTEND_URL}"
}

# --------------------------------------------------------------------------------------------
# 8. migrations: run `alembic upgrade head` against Cloud SQL via a one-off Cloud Run JOB
#    (the backend image carries alembic + the migrations; a job runs it once with the SQL socket).
# --------------------------------------------------------------------------------------------
run_migrations() {
  say "Running 'alembic upgrade head' against Cloud SQL (Cloud Run job)"
  local uri; uri="$(image_uri backend)"
  local job="${APP_PREFIX}-migrate"
  local db_password db_url
  db_password="$(gcloud secrets versions access latest --secret "${SECRET_DB_PASSWORD}" --project "${PROJECT_ID}")"
  db_url="postgresql+psycopg://${DB_USER}:${db_password}@/${DB_NAME}?host=/cloudsql/${SQL_CONNECTION_NAME}"

  if gcloud run jobs describe "${job}" --region "${REGION}" --project "${PROJECT_ID}" >/dev/null 2>&1; then
    gcloud run jobs update "${job}" \
      --image "${uri}" --region "${REGION}" --project "${PROJECT_ID}" \
      --set-cloudsql-instances "${SQL_CONNECTION_NAME}" \
      --set-env-vars "ENV=production,DATABASE_URL=${db_url}" \
      --command alembic --args "upgrade,head"
  else
    gcloud run jobs create "${job}" \
      --image "${uri}" --region "${REGION}" --project "${PROJECT_ID}" \
      --set-cloudsql-instances "${SQL_CONNECTION_NAME}" \
      --set-env-vars "ENV=production,DATABASE_URL=${db_url}" \
      --command alembic --args "upgrade,head"
  fi
  gcloud run jobs execute "${job}" --region "${REGION}" --project "${PROJECT_ID}" --wait
  info "migrations applied."
}

# --------------------------------------------------------------------------------------------
# 9. seed: admin user + the TOMATO + POTATO cycles, also via a one-off Cloud Run job.
# --------------------------------------------------------------------------------------------
run_seed() {
  [ "${RUN_SEED}" = "1" ] || { info "RUN_SEED=0 — skipping seed."; return; }
  [ -n "${SEED_ADMIN_PASSWORD:-}" ] || die "SEED_ADMIN_PASSWORD is not set (needed to seed the admin). export it or run with --no-seed."
  say "Seeding the database (admin + TOMATO + POTATO) via a Cloud Run job"
  local uri; uri="$(image_uri backend)"
  local job="${APP_PREFIX}-seed"
  local db_password db_url
  db_password="$(gcloud secrets versions access latest --secret "${SECRET_DB_PASSWORD}" --project "${PROJECT_ID}")"
  db_url="postgresql+psycopg://${DB_USER}:${db_password}@/${DB_NAME}?host=/cloudsql/${SQL_CONNECTION_NAME}"

  if gcloud run jobs describe "${job}" --region "${REGION}" --project "${PROJECT_ID}" >/dev/null 2>&1; then
    gcloud run jobs update "${job}" \
      --image "${uri}" --region "${REGION}" --project "${PROJECT_ID}" \
      --set-cloudsql-instances "${SQL_CONNECTION_NAME}" \
      --set-env-vars "ENV=production,DATABASE_URL=${db_url},SEED_ADMIN_PASSWORD=${SEED_ADMIN_PASSWORD}" \
      --command python --args "/app/deploy/gcp/seed.py"
  else
    gcloud run jobs create "${job}" \
      --image "${uri}" --region "${REGION}" --project "${PROJECT_ID}" \
      --set-cloudsql-instances "${SQL_CONNECTION_NAME}" \
      --set-env-vars "ENV=production,DATABASE_URL=${db_url},SEED_ADMIN_PASSWORD=${SEED_ADMIN_PASSWORD}" \
      --command python --args "/app/deploy/gcp/seed.py"
  fi
  gcloud run jobs execute "${job}" --region "${REGION}" --project "${PROJECT_ID}" --wait
  info "seed complete."
}

# --------------------------------------------------------------------------------------------
# orchestration
# --------------------------------------------------------------------------------------------
main() {
  require_tools
  require_project

  case "${1:-}" in
    --print-urls) print_urls; exit 0 ;;
    --no-seed)    RUN_SEED=0 ;;
  esac

  gcloud config set project "${PROJECT_ID}" >/dev/null 2>&1 || true

  enable_apis
  ensure_artifact_registry
  ensure_secrets         # secrets first — Cloud SQL user reads its password from the secret
  ensure_cloud_sql       # sets SQL_CONNECTION_NAME
  grant_runtime_iam

  build_backend
  deploy_backend         # sets BACKEND_URL
  run_migrations         # alembic upgrade head against Cloud SQL

  build_frontend "${BACKEND_URL}"   # bakes NEXT_PUBLIC_API_BASE_URL = backend URL
  deploy_frontend                   # sets FRONTEND_URL
  wire_cors                         # backend CORS -> frontend URL

  run_seed

  say "DONE"
  echo "----------------------------------------------------------------"
  echo "  backend : ${BACKEND_URL}"
  echo "  frontend: ${FRONTEND_URL}      <-- open this and log in as 'admin'"
  echo "----------------------------------------------------------------"
}

main "$@"
