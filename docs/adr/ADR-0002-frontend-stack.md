# ADR-0002 — Front-end stack: React / Next.js + TypeScript SPA

- **Status:** Accepted (sponsor-ratified 2026-06-18)
- **Deciders:** Sponsor (Ed), PM, Solution Architect, Experience lead
- **Relates:** Decision D6

## Context

The mandate is an **enterprise-level web app**. The AS-BUILT front end is **Streamlit**, which the intake itself flagged as "structurally a bad UI on a stateless engine" (Session 6, Addendum 2). An enterprise system of record needs a real authentication/RBAC surface, multi-tenant context, a design system, and a clean separation between the store/API and the view (ADR-001: UI is a view onto the store).

## Decision

**React + Next.js (App Router) + TypeScript**, as a single-page/server-rendered hybrid app that is a pure client of the FastAPI backend.

- TypeScript end-to-end; types generated from the backend OpenAPI contract.
- A component/design system (to be selected by the Experience squad — e.g. a headless library + tokens) so the console is consistent and accessible.
- Auth/RBAC integrated at the edge (provider per Security squad + DEP-4); tenant context threaded through every request.
- **Built last** (ADR-001) — design and the design system start early, implementation begins at Phase F once the store and outward-facing half are proven.

## Consequences

- Clean API boundary; the same store renders live and historic cycles identically.
- Streamlit is retired (not hardened); any throwaway internal demo UI is explicitly non-production.
- The DevOps squad plans a separate frontend build/deploy pipeline and SSR hosting.

## Rejected

- **Harden Streamlit** — faster to a demo but weak on auth, RBAC, UX, and governance; contradicts the enterprise mandate.
