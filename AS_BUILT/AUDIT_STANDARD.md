---
doc: AS-BUILT AUDIT STANDARD — what "full / nothing skipped" actually means (binding spec)
id: ASBUILT-STANDARD
status: BINDING. The file census + 00_INDEX tracker are the SKELETON only. THIS is the substance bar.
for: the fresh session that executes the exhaustive multi-layer audit.
contract: /CLAUDE.md (inject ABSOLUTE REQUIREMENTS into every audit agent).
---

# The audit standard — "if a decimal moves one pixel, it gets mapped"

A file LIST is not an audit. The audit is the **three layers below**, produced to the exhaustiveness
bar, for **every one of the 896 owned files** (`FILE_CENSUS.md`) — and **every process, branch, edge
case, and value transformation between them**. Nothing skipped. Nothing assumed. Detailed **WHY** on
everything. Empty files explained, not skipped.

## LAYER 1 — Architecture · Data · Data-flows  → `LAYER1_ARCHITECTURE_DATA_DATAFLOWS.md`
- **Architecture map:** every module/package/service, what it owns, how the two runtimes (stateless
  console DB vs MCP harness file-vault) relate. Component diagram (mermaid).
- **Data model — exhaustive:** EVERY schema, table, column — name, type, precision/scale, nullability,
  default, every CHECK, every UNIQUE, every FK (all 46 composite-identity keys), every index. Source:
  `db/baseline/schema.sql` + all 20 migrations. The ORM models mapped to each.
- **Data-flows — charted, value-level:** for EVERY flow (setup ingest → cycle; bid ingest → bid_line;
  engine run → scores → scenarios → award; freeze → layers; deliverable render; comms merge; the
  legacy converter; fan-in/fan-out), a **flow chart (mermaid)** AND a step table that maps **every
  transformation and every value/decimal change**: FOB+freight→landed, unit/pack conversion factors,
  rounding & decimal precision at each hop, weight renormalization, force-positive coercions,
  quarantine diversions, period fan-out (flat-13 → timeframe roll-up). **If a number changes shape or
  precision anywhere, that hop is named with the formula and the file:line that does it.**

## LAYER 2 — Code · Process · Decision-points  → `LAYER2_CODE_PROCESS_DECISIONS.md`
- **Per-file (every file):** path · what · **detailed WHY (why it exists, why shaped this way, what
  breaks without it)** · every public function/class — signature, inputs, outputs, side-effects,
  raised errors · dependencies · cross-ref to its census row. Empty file → why it's empty.
- **Every process, every edge case:** trace each process end-to-end and enumerate EVERY branch —
  happy path AND: no-bid/blank vs incomplete line, quarantine + fix-and-retry, key-mismatch reject,
  capacity breach, cap breach (B flags / D enforces), ties, gate-required (freeze/finalize), error
  envelopes (gate_required/validation_error/not_found), seal/immutability rejections. No branch left
  undocumented.
- **Every decision point:** each behavior tied to its decision (D1–D45) / epic (E-xx) and the exact
  file:line that enforces it; flag any decision NOT enforced in code (drift).

## LAYER 3 — UX / UI  → `LAYER3_UX_UI.md`
- **Every screen + every component** (all of `frontend/app/**` + `frontend/components/**`): purpose,
  detailed WHY, props/inputs.
- **Every state:** loading, empty, error, not-found, gated/disabled, rehearsal, post-close/read-only.
- **Every data binding (pixel-level):** which backend field renders in which element, with its
  **format and precision** (currency, %, decimals, tabular-nums) — i.e. the decimal's journey from DB
  to the rendered pixel. Every interaction → its outcome/endpoint. Navigation reachability per surface.

## Exhaustiveness rules (apply to all three layers)
1. **Every file** in `FILE_CENSUS.md` is accounted for in a slice, including the 18 empty ones.
2. **Detailed WHY** on every entry — not just what.
3. **Every value transformation / decimal / unit change is mapped** with formula + file:line.
4. **Every process edge case / branch is mapped.**
5. **Flow charts** (mermaid) for every data flow and the lifecycle.
6. Nothing assumed; if unverifiable, say so and why. Vendored trees: counted, not per-file.

## Method (nitro)
Per `00_INDEX.md` slice tracker: constrained agent per slice (contract injected) → writes its
per-file Layer-2 entries + its Layer-1 data/flow contributions + (frontend) Layer-3 entries to disk →
reviewed, committed, row flipped DONE. When all slices DONE, synthesize the three LAYER docs (with the
mermaid charts) from them. Commit continuously (context clears every ~3 prompts).
