# KR_RFP — Kroger Produce RFP / Sourcing Engine

Project workspace for building an enterprise system of record for running Kroger produce sourcing cycles (RFPs) end to end: set up a cycle, release bids, normalize them, score and allocate, choose split awards, sign off, and generate the booking guide / sign-off deck / supplier letters — with every cycle, bid, and award stored so any past cycle reopens as a query.

This repository **starts with an audit**. Two pre-existing spec packages were produced independently and are meant to be diffed; the audit reconciles them into a single target direction.

## Layout

```
specs/
  rfp-engine/          BRIEF — the target spec, from a 6-session structured intake
    BUILD_00..04             against Ed's real artifacts (ground truth on process/intent)
    intake/                  the evidence base: INDEX + SESSION-01..06 + 20-row discrepancy log
  original-engine/     AS-BUILT — descriptive inventory of the inherited codebase
    BUILD_00..04             (63 tables, 14 migrations, 796 tests, synthetic SQLite)

audit/                 THE DELIVERABLE — read in order
  00_EXECUTIVE_SUMMARY.md        2-page read: verdict, scorecard, ranked gaps, decisions
  01_DOCUMENT_AUDIT.md           the two packages as artifacts; defects [D-n]; readiness scorecard
  02_GAP_ANALYSIS.md             the "gaps" deliverable: capability matrix, ADR-by-ADR, G1..G12, keep-list
  03_SCHEMA_DIFF.md              table-level diff (63 vs 36) across the 8 layers; migration crosswalk
  04_RISKS_DECISIONS_ROADMAP.md  risk register, sponsor decisions D1..D5, target architecture, phased roadmap
```

## The one-line conclusion

**Neither package is the product.** The BRIEF has the right brain, target shape, and governance philosophy but a thin, unvalidated data model; the AS-BUILT has a deep, genuinely enterprise-grade spine but the wrong brain (min-cost single-winner solver), pricing at the wrong layer with inert safeties, and no outward-facing half. The target is **the brief's brain and outward-facing half built on the as-built's spine**, with the twelve gaps (`audit/02`) resolved by five sponsor decisions (`audit/04`), then proven on **one real cycle**.

Start at `audit/00_EXECUTIVE_SUMMARY.md`.
