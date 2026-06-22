# Kroger Produce RFP / Sourcing — backend API image (FastAPI on uvicorn).
#
# Cloud Run contract: the container must bind 0.0.0.0:$PORT (Cloud Run injects PORT; default 8000
# for local/compose) and be STATELESS — no disk persistence (ADR-0018: uploads stream to ingest,
# deliverables render on request). Reaches Cloud SQL over the /cloudsql unix socket via DATABASE_URL
# (set by deploy/gcp/deploy.sh); locally it reaches the compose Postgres over the network.
#
# BUILD CONTEXT = THE REPO ROOT (not backend/). The baseline migration (alembic 0001) reads
# `<repo-root>/db/baseline/schema.sql` — the real as-built schema — resolving repo-root as the
# PARENT of backend/. So the image must carry BOTH trees in that same relative layout: backend/ ->
# /app and db/ -> /db (so /app/alembic/versions/0001_baseline.py resolves /db/baseline/schema.sql).
# Build it as:  docker build -f backend/Dockerfile -t kr-rfp-backend .   (from the repo root)
#
# Migrations are NOT run by this image's CMD — the serving container only serves. `alembic upgrade
# head` is a SEPARATE step (a Cloud Run job in deploy.sh, a one-shot `migrate` service in
# docker-compose): N serving instances must not race to migrate, and a migration failure must not
# crash-loop the service. WORKDIR is /app (= backend/), so alembic finds alembic.ini there.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    # Cloud Run overrides PORT; default 8000 so a bare `docker run` and compose still work.
    PORT=8000

WORKDIR /app

# Install dependencies first for better layer caching (only backend/pyproject.toml busts this).
COPY backend/pyproject.toml ./
RUN pip install --upgrade pip && pip install .

# The repo-root baseline SQL the alembic 0001 migration reads at /db/baseline/schema.sql.
COPY db /db

# Backend application source (app/, alembic/, alembic.ini, scripts/, tests/) -> /app.
# tests/ is included on purpose: deploy/gcp/seed.py reuses the TOMATO builders from tests/pilot/.
COPY backend/ /app/

# The seed script lives at repo-root deploy/gcp/seed.py; ship it so the seed job/`docker run` can
# invoke /app/deploy/gcp/seed.py (it adds backend/ to sys.path itself).
COPY deploy/gcp/seed.py /app/deploy/gcp/seed.py

# The ONE reference sample the POTATO seed reads. scripts/potato_legacy_dryrun.py resolves it at
# <repo-root>/reference/samples/potato_2026_rfp_input.xlsx, which inside the image is
# /reference/samples/... (repo-root maps to /). Only this 0.4MB file is shipped — not the 150MB
# reference/ tree. If it is ever absent, deploy/gcp/seed.py skips the POTATO cycle gracefully.
COPY reference/samples/potato_2026_rfp_input.xlsx /reference/samples/potato_2026_rfp_input.xlsx

EXPOSE 8000

# Serve only — bind 0.0.0.0:$PORT (shell form so $PORT expands at runtime). Migrations run
# out-of-band (see the header). uvicorn is the app server; for a higher-concurrency posture this
# can become `gunicorn -k uvicorn.workers.UvicornWorker` without changing the contract.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
