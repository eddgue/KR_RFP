---
doc: Program Backlog (Epics)
id: PM-004
version: 0.1
status: Draft
created: 2026-06-18
depends_on: PM-000, audit/02_GAP_ANALYSIS, audit/04_RISKS_DECISIONS_ROADMAP
---

# Program Backlog — Epics

The twelve gaps, the seven "keep" capabilities, and the net-new enterprise layer, converted into epics, mapped to phases and owning squads. Priority: **P0** (foundational/blocking) · **P1** · **P2**. Each epic links its gap (`audit/02`).

## Epic map

| Epic | Title | Gap | Phase | Squad | Pri | Acceptance (slice done) |
|---|---|:--:|:--:|---|:--:|---|
| **E-00** | Target Spec v1.0 supersedes both packages | — | 0 | Architect+Product | P0 | One current spec; ADRs renumbered canonically; decision log ratified |
| **E-01** | Validate as-built schema on real Postgres; kill SQLite-isms + no-op CHECK | — | 0 | Plat&Data | P0 | DDL migrates clean on PG15; roundtrip test green; `[D-6]` defects closed |
| **E-02** | Obtain & reconcile source-of-truth (repo, migrations, tests, ECLS) | — | 0 | Architect | P0 | DEP-1 closed; 63 tables/14 migrations/796 tests verified, not asserted |
| **E-03** | Multi-tenant `client` + RBAC/actor model | net-new | 0/A | Security | P0 | Tenant isolation enforced at row + API; roles defined; access tests pass |
| **E-04** | Security & NFR specification (PII, retention, threat model, sizing) | net-new | 0/A | Security | P0 | Signed NFR spec; data classification on every entity; perf targets set |
| **E-05** | Make the audit event log **live** (finish the hash-chain) | G11 | A | Security+Plat&Data | P0 | Every state change emits an event; write-only enforced; tamper-evident |
| **E-06** | KEEP-list hardening (identity FKs, calc-run spine, landed cost, eligibility, VSP) | KEEP | A | Plat&Data+Engine | P1 | Carried forward intact; covered by tests; no regression to thinner model |
| **E-07** | "Open last cycle" query + read model | — | A | Engine | P0 | Any cycle reopens with full story < 2s (S1) |
| **E-08** | iTrade **receipt-grain** feed (`itrade_receipt`) | G6 | B | Plat&Data | P0 | Real pull lands; flag-first validation; impossible-date-span rejection |
| **E-09** | KCMS scan feed (`kcms_movement`) | G6 | B | Plat&Data | P1 | Scan/margin lands; distinct from iTrade |
| **E-10** | Supplier scorecard — two frozen snapshots (derivation) | G6 | B | Plat&Data | P1 | Kickoff + sign-off snapshots compute from receipts |
| **E-11** | Persistent `norm.lot` + attribute taxonomy + sticky map | G8 | B | Plat&Data | P0 | Items propose lots; human confirms; map sticks across cycles; regroup by attribute |
| **E-12** | Two origins + `zip_centroid` distance | G7 | B | Plat&Data | P1 | `grow_origin`/`ship_from_zip` separate; distance derived (lift `calculate_distances`) |
| **E-13** | **REAL-DATA PILOT** (Phase B exit gate; retires R1) | — | B | QA+all | P0 | One real cycle end-to-end on real iTrade + bids; engine reproduces v3 (S2) |
| **E-14** | Kickoff keystone — rich `cyc.*` (objective, pricing+safeties, PBA, working capital, KPM, RFI, narrative) | G5 | C | Product+Plat&Data | P0 | A cycle declared from a real kickoff doc; structured drives system, prose stays prose |
| **E-15** | Pricing model + **safety TERMS** declared & stored at kickoff | G4 | C | Product+Plat&Data | P0 | `cyc.cycle_pricing` + `cyc.cycle_safety` store the declared contract terms/params; **the engine does NOT consume them** (D13/ADR-0014) |
| **E-29** | **Contract execution — safety reprice + market feed + reprice-and-layer** | G4 | E+ | Engine+Plat&Data | P1 | Formulaic safeties (rolling midpoint, tolerance band, collar) compute/visualize; disaster/inverse triggers flag for human reprice (revert-to-contract); every move lands in `awd.award_layer`; needs market-price feed (DEP-6) |
| **E-30** | **Kanban views — RFP portfolio + RFP-by-supplier** | net-new | F | Experience | P1 | Board 1: every RFP as a card across the process-rail stages (the cycle timeline, G10). Board 2 (drill-in): within one RFP, suppliers as cards across their lifecycle (invited → submitted → in-round → shortlisted → awarded/declined). Reads from the store; same render live or historic. Sponsor-requested. |
| **E-31** | **Gate-closure backup export (DR / historic)** | net-new | E | Engine+Experience+Security | P1 | At **every governance gate closure / decision point** (kickoff in-gate G12, each round close, award freeze G3, sign-off out-gate) generate a **downloadable portable snapshot** — full cycle state at that point (structured export, e.g. a zip of JSON/Excel + the generated docs) — the sponsor saves to the drives for historic / emergency recovery. Portable fallback the sponsor controls, on top of the live store + event log + freeze-and-layer. Also a trust/adoption lever. Sponsor-requested. |
| **E-32** | **AI assistant (read-only) — NL data recall + drafting** | net-new | F+ / post-MVP | Experience+Engine+Security | **P3 (wish-list)** | Read-only natural-language layer over the store: answer questions / recall data, and help **draft** emails/letters/summaries. **Never writes to the DB**; never auto-asserts an award (decision-support-only); reads are **RBAC/tenant-scoped** (only what the user may see); drafts pass the human + draft→sent gate (G9); answers are auditable. Built on the latest Claude models. **Lowest priority.** Sponsor wish-list. |
| **E-16** | Process rail generated from the cycle timeline | G10 | C | Experience+Engine | P1 | Console renders the rail from `cycle_timeline_event`, not hardcoded |
| **E-17** | Stage-0 governance **in-gate** | G12 | C | Security | P1 | A cycle cannot open on real data without the in-gate approval |
| **E-18** | v3 brain → `bid_score` 5-factor scoring + eligibility inputs | G2 | D | Engine | P0 | Reproduces v3 banded scoring (Price.35/Cov.25/Hist.20/Z.10/Cont.10) |
| **E-19** | Scenarios A–G (lenses) | G2 | D | Engine | P1 | Seven lenses produced; A = lowest-cost reference, never auto-applied |
| **E-20** | **Split allocation** — `scenario_award` + `volume_share` + cap-breach (ships with E-18) | G1 | D | Engine+Plat&Data | P0 | Cell awards to multiple suppliers, capacity-constrained, permit-not-force (S4) |
| **E-21** | Award object → freeze → `award_layer` | G3 | E | Engine+Plat&Data | P0 | Selection promoted to award; `frozen_at` seals; changes layer; raw recoverable (S6) |
| **E-22** | Portfolio sign-off gate (`signoff`) + savings-vs-STLY | G3 | E | Engine | P0 | Portfolio savings rolls to a sign-off total (S8) |
| **E-23** | Generated outputs — booking guide → deck → letters → email | G3 | E | Engine+Experience | P0 | Generated from records (lift v1.4 generators); booking guide first (S5) |
| **E-24** | Draft→**SENT** governance gate | G9 | E | Security+Engine | P1 | "Sent" = official, approver+timestamp; engine still never auto-asserts |
| **E-25** | REST API hardening (contract-first, authn/authz) | — | F | Engine+Security | P0 | OpenAPI complete; every endpoint guarded |
| **E-26** | Enterprise web app (stack D6) — the console | — | F | Experience | P0 | Live + historic cycles render identically from the store; ADR-001 honored |
| **E-27** | Platform: environments, CI/CD, IaC, observability | net-new | 0→F | DevOps | P0 | 3 envs; pipeline green; migrations automated; metrics/logs live |
| **E-28** | **Supplier behavior — contracted-vs-effective analytics** | net-new | E / post-pilot | Engine+Plat&Data | P1 | Per supplier×DC×lot: **contracted price vs iTrade actual-paid (effective) delta**, plus fill rate / rejection / on-time / supply-continuity from iTrade; merchandiser-facing flags ("priority supplier's effective rate ran above contract", "stopped supplying this DC", off-contract drift). Derivation over `perf.itrade_receipt` + `awd.award` + historical booking guides. Compounds from cycle 2. |
| **E-33** | **PBA / Contract builder — the post-award final step** | net-new | E | Product+Engine+Experience | P0 | The **last step after award**: build the executable **PBA / contract** from the frozen award. Pulls the kickoff-declared PBA + pricing + safety **terms** (E-14/E-15), the awarded supplier×DC×lot×price, volumes and effective dates from `awd.award` (+ layers, E-21) into a structured, reviewable, **versioned + auditable** contract document; draft→approve→**SENT** governance (G9/E-24); exportable. **Sponsor: spec out NOW and prep to go live while the RFPs run** (build in parallel with the pilot). |
| **E-34** | **Supplier master list — importer + per-RFP participant selection** | net-new | B/C | Plat&Data+Experience | P1 | A shared, growing supplier master (`ref.supplier`): an **importer** that ingests an exported supplier list, validates, and **upserts** (adds new rows, updates changed ones), idempotently. Plus per-RFP **selection of participating suppliers by the categories they sell**. Sponsor-described intake. (Groundwork landed: setup-ingest now treats DC + supplier as shared master data, reusing by natural key — D36.) |

## Cross-references

- Gaps → epics: G1→E-20 · G2→E-18/E-19 · G3→E-21/E-22/E-23 · G4→E-15 · G5→E-14 · G6→E-08/E-09/E-10 · G7→E-12 · G8→E-11 · G9→E-24 · G10→E-16 · G11→E-05 · G12→E-17 · KEEP→E-06 · net-new→E-03/E-04/E-27.
- Risk retirement: R1→E-13 · R2→E-18/E-20 (D2) · R3→E-01/E-02 (D1) · R5→E-15 · R7→E-03/E-04.

## Notes

- **E-18 and E-20 are a single increment** (Ed's "ship together" rule): scoring and split both touch the solver core.
- **E-28 is mostly a derivation, not new plumbing:** once awards, iTrade actuals, and booking guides are in the store, it is a read/analytics + merchandiser-reporting layer over data we already model. It rides on the D11 savings-baseline work and the scorecard (E-10). Historical booking guides (DEP-5) backfill prior **contracted** terms so contracted-vs-effective works even before a full cycle has run in-system.
- Epics are phase-anchored but groomed into vertical-slice stories at phase entry (Ways of Working §1).
- Estimates are deliberately omitted until D1–D7 and DEP-1 are resolved (they swing the sizing materially).
