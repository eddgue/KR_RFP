---
doc: Milestone Roadmap
id: PM-005
version: 0.1
status: Draft
created: 2026-06-18
depends_on: PM-004, audit/04_RISKS_DECISIONS_ROADMAP
---

# Milestone Roadmap

Phase plan, gates, dependencies, and squad load. **Gates are demonstrated outcomes, not table counts.** Calendar dates are intentionally omitted until D1–D7 and DEP-1 land (they swing sizing materially); sequence and dependencies are firm.

## Phase plan

| Phase | Milestone | Epics | Exit gate (demonstrated) | Lead squads |
|---|---|---|---|---|
| **0 · Reconcile** | Foundation locked | E-00, E-01, E-02, E-03(start), E-04(start), E-27(start) | Decisions D1–D7 ratified · schema migrates clean on real Postgres · Target Spec v1.0 supersedes both packages · source-of-truth obtained (DEP-1) | Architect, Plat&Data, Security, DevOps |
| **A · Spine hardening** | Governed store is enterprise-true | E-03, E-04, E-05, E-06, E-07, E-27 | Live event log proven · "open last cycle" returns full story <2s · RBAC + tenant isolation enforced · CI green | Plat&Data, Security, Engine, DevOps |
| **B · History + Normalization + PILOT** | **Proven on reality (retires R1)** | E-08, E-09, E-10, E-11, E-12, **E-13** | **One real iTrade pull lands; items propose lots; human confirms; scorecard computes; one real cycle runs end-to-end** | Plat&Data, QA, Engine |
| **C · Kickoff keystone + rail** | The in-gate, for real | E-14, E-15(start), E-16, E-17 | A cycle is declared from a real kickoff doc; the console renders its rail from the cycle; Stage-0 in-gate enforced | Product, Plat&Data, Engine, Security |
| **D · The brain** | Right engine, shipped together | E-15, E-18, E-19, **E-20** | A stored round runs and reproduces v3's verified scoring + **split allocation** against a known input | Engine, Plat&Data |
| **E · Outward-facing half** | Close the loop | E-21, E-22, E-23, E-24 | A chosen scenario → frozen awards; **booking guide + sign-off deck generate from records**; savings-vs-STLY computes; draft→sent enforced | Engine, Experience, Security |
| **F · API hardening, then UI** | A view onto the store | E-25, E-26, E-27 | OpenAPI complete + guarded; the **enterprise web app** renders live and historic cycles identically | Engine, Experience, Security, DevOps |

## Dependency graph

```
0 ──▶ A ──▶ B ──▶ D ──▶ E ──▶ F
            │      ▲
            └─▶ C ─┘        (C overlaps B once A is done; D needs B's feeds + C's config)
```
- **B and C overlap** once A is complete.
- **D depends on B** (real cost/history feeds the scorer) **and C** (cycle config drives the run).
- **The UI (F) does not start until E is proven** — a good front end is a view onto the store; on a half-built store it is only a nicer way to forget each run (intake, Session 6).

## Squad load by phase (H/M/L)

| Squad | 0 | A | B | C | D | E | F |
|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| Platform & Data | H | H | H | M | M | M | L |
| Engine & Domain | L | M | M | M | H | H | M |
| Experience (Web) | L | L | L | M | L | M | H |
| Platform Eng / DevOps | M | H | M | L | L | L | M |
| Security & Compliance | M | H | M | M | L | M | M |
| Quality & Assurance | L | M | H | M | M | H | M |

## Value-timing note (from the intake)

The historical payoff begins at **cycle 2** and compounds; cycle 1 *produces* the record, it does not consume one. **Phase B's pilot is the inflection point** — until one full cycle completes on real data, the system's reason-for-being (cure historical blindness) returns zero. Everything before B is necessary scaffolding; B is where value starts.

## What gates the plan starting

DEP-1 (code + ECLS) gates Phase 0 execution. D1/D2/D6/D7 gate how squads plan in detail. The PM will not freeze a calendar until these clear; the **sequence above does not change** regardless of how the decisions land — only the contents of Phase 0 and the frontend stack do.
