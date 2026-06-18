---
doc: Team Structure & RACI
id: PM-001
version: 0.1
status: Draft
created: 2026-06-18
depends_on: PM-000
---

# Team Structure & RACI

How the program is organized, who owns what, and how each squad is staffed. Each squad lead is instantiated as a **specialist agent** under the PM's orchestration; the structure is written so it maps cleanly onto a human delivery org if/when staffed with people.

## 1. Org at a glance

```
                              Sponsor / Product Authority — Ed (Sourcing)
                                              │
                                   Program Manager (PM)  ── owns plan, RACI, risk, decisions, cadence
                                              │
        ┌───────────────┬───────────────┬─────┴─────────┬───────────────┬───────────────┐
   Solution         Product Owner /   (delivery squads below report into the PM via their leads)
   Architect           BA
        │                │
   ─────┴──────────────────────────────────────────────────────────────────────────────────
   SQUAD 1            SQUAD 2          SQUAD 3          SQUAD 4          SQUAD 5         SQUAD 6
   Platform & Data    Engine & Domain  Experience (Web) Platform Eng /   Security &      Quality &
                                                        DevOps           Compliance      Assurance
```

## 2. Leadership

| Role | Charter | Staffing |
|---|---|---|
| **Program Manager** | Orchestration, RACI, risk register, decision log, cadence, integration of squad plans, stakeholder comms. | PM (this engagement) |
| **Solution Architect** | Target architecture, ADRs, tech standards, cross-cutting NFR architecture, the reconciled data model, "keep vs change vs build" rulings. | `architect` agent |
| **Product Owner / BA** | Requirements (esp. the kickoff keystone, G5), backlog grooming, acceptance criteria, the discrepancy register, sponsor liaison. | `product` agent |

## 3. Delivery squads

| # | Squad | Owns (primary gaps/capabilities) | Lead staffing |
|---|---|---|---|
| **1** | **Platform & Data** | Reconciled Postgres schema; Alembic migrations from the 63-table baseline; the two breaking migrations (G1 grain, G2 scenario generalization); persistent `norm.lot` + attribute taxonomy (G8); data feeds — iTrade receipt grain, KCMS, scorecard (G6); two-origins + `zip_centroid` distance (G7); demand≠capacity & VSP (KEEP). | Data/Platform Engineer agent |
| **2** | **Engine & Domain** | v3 brain lifted to a library; 5-factor scoring `bid_score` (G2); scenarios A–G; split allocation `scenario_award` + `volume_share` (G1); KEEP the calc-run spine, 5-mode landed cost, 7-gate eligibility; pricing lifted to kickoff + executable safeties (G4); the REST API. | Backend/Domain Engineer agent |
| **3** | **Experience (Web)** | The enterprise web app (stack = D6): cycle setup/kickoff UI, supplier field, intake review, scenario review & override, **open last cycle**, sign-off, generated-doc preview; design system; rail generated from the cycle timeline (G10). Built last (ADR-001) but design starts early. | Frontend/UX Engineer agent |
| **4** | **Platform Engineering / DevOps** | Environments (dev/stage/prod), CI/CD, IaC, secrets, DB migration pipeline, observability/logging/metrics, release management, performance/sizing. | DevOps Engineer agent |
| **5** | **Security & Compliance** | Multi-tenant (`client`) isolation, RBAC/actor model, PII & data classification, retention, the **live** audit hash-chain (G11), draft→sent governance (G9), threat model, access controls on the API, Stage-0 governance in-gate (G12). | Security Engineer agent |
| **6** | **Quality & Assurance** | Test strategy & automation pyramid; migration roundtrip tests; engine reproducibility tests; **the real-data pilot** (retires R1) as Phase B's exit gate; UAT with Sourcing; non-functional/perf testing. | QA Lead agent |

## 4. Squad outputs (first deliverable each, on mobilization)

1. Platform & Data → **Migration & Data-Model Reconciliation Plan** (baseline assessment + ordered migration set + feed-ingestion design).
2. Engine & Domain → **Engine Integration & API Spec** (v3 `run()` contract, scoring/split, service decomposition, OpenAPI skeleton).
3. Experience → **Web App UX Blueprint & Stack Proposal** (information architecture, key flows, design-system choice, frontend stack per D6).
4. DevOps → **Platform & CI/CD Plan** (environments, pipeline, IaC, observability, branching integration).
5. Security & Compliance → **Security & NFR Specification** (tenancy, RBAC, PII, retention, audit, threat model) — the net-new layer.
6. QA → **Test Strategy & Real-Data Pilot Plan** (automation pyramid + the pilot that proves the system on reality).

## 5. RACI (R=Responsible, A=Accountable, C=Consulted, I=Informed)

| Workstream / Decision | PM | Architect | Product | Plat&Data | Engine | Exp | DevOps | Sec | QA | Sponsor |
|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| Target Spec v1.0 (Phase 0) | A | R | C | C | C | C | C | C | C | C |
| Build-path decision (D1) | A | R | C | C | I | I | I | C | I | **A** |
| Engine/brain decision (D2) | A | R | C | I | R | I | I | I | C | **A** |
| Pricing-to-kickoff (D3/G4) | A | C | R | C | R | I | I | I | C | C |
| Frontend stack (D6) | A | C | C | I | I | R | C | C | I | **A** |
| Schema & migrations | I | C | I | **R/A** | C | I | C | C | C | I |
| Engine & API | I | C | I | C | **R/A** | C | I | C | C | I |
| Web app | I | C | C | I | C | **R/A** | C | C | C | C |
| Environments & CI/CD | I | C | I | C | C | C | **R/A** | C | C | I |
| Security / tenancy / NFR | A | C | I | C | C | C | C | **R/A** | C | C |
| Quality & real-data pilot | A | I | C | C | C | I | I | I | **R/A** | C |
| Risk & decision governance | **R/A** | C | C | I | I | I | I | C | C | C |

## 6. Operating principle

**Inheritance rule (from the audit):** for every layer, take the *shape and intent* from the BRIEF and the *constraint discipline + the seven KEEP capabilities* from the AS-BUILT. Never regress to the brief's thinner schema; never carry forward the as-built's wrong brain. The Architect arbitrates each ruling and records it as an ADR.
