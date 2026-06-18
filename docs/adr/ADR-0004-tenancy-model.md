# ADR-0004 — Tenancy model: multi-tenant-capable, single-tenant-operated

- **Status:** Accepted (PM/Architect decision, 2026-06-18; sponsor confirmed "one org" framing)
- **Deciders:** PM, Solution Architect, Security lead; Sponsor (Ed)
- **Relates:** Decision D8, Security & DevOps plans, the mobilization report §3/§6, intake Session 1 ("Clients" as a reference entity)

## Context

The Security and DevOps squads flagged "tenancy topology" as their single biggest open fork because it shapes the data model and the deployment and is expensive to change late. The sponsor (Sourcing) reasonably did not have a view — this is a Kroger sourcing tool for one organization, not a product sold to multiple external customers. The intake's mention of "Clients" refers to internal stakeholders/categories, not external paying tenants. There is no evidence of a contractual or compliance requirement for physical data separation.

Two axes were in play:
- **Tenant grain** — who is a tenant? (one org vs internal divisions vs external customers)
- **Isolation topology** — shared schema + Row-Level Security (RLS) vs database-per-tenant.

## Decision

**Build multi-tenant-*capable*, operate single-tenant.**

1. **One logical tenant** for the foreseeable product: the organization (Kroger Sourcing). A single seeded `ref.client` row.
2. **Keep `client_id` on every governed row** and **prepended to the composite-identity FKs** (Security plan) — near-zero cost now, structurally future-proof. This is cheap insurance, not active multi-tenancy.
3. **Isolation = shared schema + Postgres RLS** as the backstop pattern, with tenant context taken only from the verified token (never the request body). This is the enterprise-standard default and good security hygiene even with one tenant.
4. **Database-per-tenant is explicitly deferred** — not built. It is only revisited if a trigger below fires.

## Triggers that would revisit this (and only these)

- Internal divisions must be cryptographically/contractually walled off from each other.
- A decision to offer the system to external organizations (SaaS) is taken.
- A Kroger compliance/contractual rule mandates physically separate databases.

If any fires, the `client_id`-everywhere groundwork makes the move to true multi-tenant (more `ref.client` rows + enforced RLS, or per-tenant DBs) an incremental change, not a rebuild.

## Consequences

- Unblocks Security (RBAC/RLS policy set) and DevOps (shared-schema deploy model, one DB to migrate/back up) — their default assumption is now ratified.
- No per-tenant operational overhead now.
- The model stays honest: we do not claim multi-tenancy we have not built, but we do not foreclose it.
