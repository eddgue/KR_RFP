# ADR-0018 — Storage model: DB is the system of record; deliverables render on request, uploads not persisted (web console, with Cloud Run) — and NO storage change before the live RFPs

- **Status:** Accepted (2026-06-21)
- **Deciders:** Sponsor (Ed), PM, Solution Architect
- **Relates:** ADR-0017 (GCP / Cloud Run — stateless compute); ADR-0003 (two runtimes — web console + MCP harness); D30 (per-run vault + isolated DB); E-39 (canonical formula registry — deterministic renders); E-31 (gate-closure backup export); `norm.source_artifact`; As-Built §16 (persistence); the Awards design ("Postgres is authoritative — generated guides are renders of it")

## Context

Question raised: are output files generated **on request** or **stored server-side**, and should
uploads persist after ingest? **Today:** generated deliverables (alignment workbook, booking/supplier
guides, post-award docs) are **written to the run's `outputs/` folder on disk** at generation time;
uploads are **kept** in `inputs/`; single-file and run-zip downloads **read bytes off disk**; the
whole "vault" is git-committed and (on web) auto-pushed, with a `run_data.json` + a `db/` DB snapshot
alongside. The sponsor's principle: **the DB is the single source of truth — render deliverables on
request, never store them; don't keep uploaded files (re-extract via the standard template + DB).**

**Decisive constraint: two live RFPs start this coming week.** They run on the **MCP harness**
(per-run isolated DB + vault); **GCP is decided (ADR-0017) but not yet provisioned**, so nothing runs
on Cloud Run this week.

## Decision (by the Decision Doctrine, PM-008)

1. **Strategic target — ratified.** The **PostgreSQL database is the system of record.** All
   generated deliverables **render on request and are not persisted**; uploads are **streamed →
   ingested → not retained as derived copies.** This is sound because the generators are already
   **pure, deterministic DB-renders** (E-39 → byte-identical regeneration), so for our own templates
   regeneration is exact and lossless. The sponsor's principle is adopted as the platform direction.

2. **Delivery binding — Category B, with the Cloud Run deployment, AFTER the live RFPs.** The refactor
   is an enhancement **within the existing architecture**, and Cloud Run's statelessness *requires*
   it anyway (local disk doesn't survive across instances / scale-to-zero). It ships **with** the
   GCP web-console deployment — not before.

3. **Pre-live-RFP — Category-NOT-A: change nothing now.** The two live RFPs run on the harness, whose
   **per-run vault (files + git history + DB snapshot) is RETAINED.** That vault is the run's
   **portable, recoverable record across ephemeral boxes (D30)** — a **safety feature** for a live
   run, not tech debt. Refactoring a working, recovery-critical storage layer the week of go-live is
   the highest-margin-for-error move available, so we do not. The current "generate-and-store +
   git/autopush" behavior stands for the live RFPs **unchanged.**

4. **One open sub-decision (resolve at deployment, not now).** When the web console goes stateless,
   the **raw-as-received *flexible* upload** is the only governed input not reconstructable from the
   DB (strict/our-template uploads are reproducible from DB + the standard template). **Recommended
   resolution:** retain **that one artifact class** in **object storage (GCS)** for audit/dispute
   (its `norm.source_artifact` SHA-256 needs something to verify against) and render everything else
   on request. *Sponsor leans pure-discard;* this is the single audit-safety exception — confirm at
   deployment. E-31's gate-closure export is likewise an intentional, user-initiated snapshot → GCS,
   never the request path.

## Consequences

- **This week:** live RFPs proceed on the proven harness/vault model. The in-flight safety net is the
  vault recovery (git push of the DB snapshot); **confirm autopush/rehydrate is working as a
  live-run readiness check** (it is the thing that protects an in-flight RFP if a box dies).
- **At Cloud Run provisioning (the B work):** download endpoints generate-and-stream from Cloud SQL;
  the run-zip builds every deliverable into an in-memory zip on request; `outputs/` persistence is
  removed; uploads stream straight to ingest; the retained raw flexible artifact (if kept) + E-31
  exports go to a GCS bucket. `DATABASE_URL` stays the single connection var; add a bucket + signed
  URL/stream for the retained class only.
- The As-Built persistence section is updated **when implemented** (implemented-reality only, per
  D39) — not now.
- Low risk: because every output is a deterministic DB-render (E-39), generate-on-request yields the
  same bytes the stored files do today — the switch is behavior-preserving for outputs.

## Rejected

- **Refactor storage before the live RFPs** — highest margin for error; strips the harness's
  recovery/portability net the week of go-live, for zero benefit this week (the RFPs don't run on
  Cloud Run).
- **Persist generated outputs on disk under Cloud Run** — doesn't survive statelessness; redundant
  given deterministic renders.
- **Discard the raw-as-received *flexible* upload too** — loses the only irreproducible governed
  input and weakens audit/dispute; held as the open sub-decision above (sponsor may override).
