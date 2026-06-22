---
doc: Design feedback — round 2 (on the v2 handoff package)
id: PM-007-DR2-FB
version: 1.0
status: To send — final design tweaks before the UI baseline is locked
created: 2026-06-21
---

# Design feedback — round 2 (v2 handoff)

Auditor reviewed the v2 handoff; verified per our rule (grain of salt). **Updated verdict: this is now
the UI baseline — lock the design language, stop redesigning the core.** The designer preserved the
calm baseline and added control only where the workflow carries consequence; "calm by default,
gravity at exceptions" is now an actual system rule in the handoff (component states, governed-action
pattern, non-happy-path). The run-status strip, capacity-as-control, freeze gravity, intake exception
queue, and post-award formalization all landed correctly.

**Only three items remain before implementation. Everything else → the live-run backlog, not another
design cycle.**

## 1. Compact-width status-strip truncation (real fix)

At narrower desktop widths the status strip truncates its four core values ("Live · Roun…", "Sealed ·
…", "Not yet froz…", "Hash-chain curr…"). These are the four most important status statements in the
system and must never clip. At the compact breakpoint, reduce to short labels — do not clip meaning:

| Run | Analysis | Award | Audit |
|---|---|---|---|
| Live | Sealed v1 | Not frozen | Current |

## 2. Awards "runtime error" — VERIFIED STALE SCREENSHOT, no code fix needed

The bundle ships a screenshot showing `Awards.renderVals(): can't access property "toLocaleString",
c.demand is undefined`. **Verified against the committed prototype: this is a stale screenshot, not a
live defect.** `Awards.dc.html` `CELLS()` (lines 344–349) defines `demand: 5200` on all four cells,
and `renderVals` reads `c.demand` only over `CELLS()` — there is no undefined-demand path; the
prototype renders cleanly. This is the same export-lag we've seen (the `screenshots/` folder lags the
`.dc.html`). **Action: just refresh/replace the stale screenshots** so nobody sees a red error on the
governed-record screen. No prototype change required.

## 3. Audit-state drill-through (real enhancement)

"Hash-chain current" in the status strip should be **clickable** → open/jump to the latest event:
actor · timestamp · event type · affected artifact/version · prior-hash/record reference. Don't make
users hunt through Run Detail to validate what the strip claims. The data already exists — Run Detail
already renders the hash-chained `audit.event_log` events; this is a link + a focused popover/anchor.

## After these three

The design is the **locked UI baseline** (E-26 implementation target). Items 1 and 3 are design
tweaks; item 2 is a screenshot refresh. Nothing here reopens the core experience.
