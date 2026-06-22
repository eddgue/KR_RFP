# KR_RFP web console (Next.js 14, app-router) — Cloud Run runtime image.
#
# Multi-stage so the final image carries ONLY the Next "standalone" server output (a minimal node
# server + the deps it actually imports) — not node_modules, not the source, not the build cache.
# The result is a small, STATELESS container (ADR-0018: the console writes zero files) that binds
# the platform-provided $PORT, which is exactly Cloud Run's contract.
#
# NEXT_PUBLIC_API_BASE_URL is INLINED AT BUILD TIME (that is how Next handles NEXT_PUBLIC_* vars),
# so it is a build arg, not a runtime env. deploy/gcp/deploy.sh passes the deployed backend URL as
# --build-arg NEXT_PUBLIC_API_BASE_URL=<backend-url> when it builds this image. Locally,
# docker-compose passes http://localhost:8000.

# ---- deps: install node_modules from the lockfile (cached unless package*.json changes) ----
FROM node:20-slim AS deps
WORKDIR /app
COPY package.json package-lock.json ./
# Reproducible install from the committed lockfile.
RUN npm ci

# ---- build: compile the app to the standalone server output ----
FROM node:20-slim AS build
WORKDIR /app

# NEXT_PUBLIC_* are baked into the client bundle at build time, so the API base URL must be present
# as a build arg here (not at `docker run`). Default to the local backend so a bare `docker build`
# still produces a runnable image; deploy/gcp/deploy.sh overrides it with the real backend URL.
ARG NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_BASE_URL=${NEXT_PUBLIC_API_BASE_URL}
# Don't phone home during CI/Docker builds.
ENV NEXT_TELEMETRY_DISABLED=1

COPY --from=deps /app/node_modules ./node_modules
COPY . .

# `output: "standalone"` in next.config.mjs makes this emit .next/standalone (server + minimal deps)
# plus .next/static (the client assets the server references).
RUN npm run build

# ---- runtime: the slim standalone server only ----
FROM node:20-slim AS runtime
WORKDIR /app

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    # Cloud Run injects PORT; default to 3000 for local/compose. server.js reads process.env.PORT.
    PORT=3000 \
    # Bind all interfaces so the platform's load balancer can reach the container.
    HOSTNAME=0.0.0.0

# Run as the unprivileged node user that the base image ships.
USER node

# The standalone tree contains a self-sufficient server.js + the traced node_modules subset.
COPY --from=build --chown=node:node /app/.next/standalone ./
# The static assets the server serves (/_next/static/*) are NOT inside standalone — copy them in.
COPY --from=build --chown=node:node /app/.next/static ./.next/static
# NOTE: there is no public/ directory in this project; if one is added later, also:
#   COPY --from=build --chown=node:node /app/public ./public

EXPOSE 3000

# server.js is emitted at the root of the standalone tree; it honours PORT + HOSTNAME.
CMD ["node", "server.js"]
