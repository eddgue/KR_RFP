# app/engine — the decision-support library

The engine is a **pure library behind a stable interface**, not a service (PLAN §3,
ADR-0006). It takes a frozen input bundle and returns a result bundle; it never touches the
database, the session, HTTP, the clock, or randomness (except via injected config). That
purity is what makes sealed runs reproducible (S2) and lets the library be unit-tested in
isolation.

## The frozen boundary (does not change when D2 resolves)

- `interface.py` — `Engine.run(inputs: EngineInputs) -> EngineResult` plus the pydantic IO
  types (`EngineConfig`, `BidInput`, `BidScore`, `Scenario`, `ScenarioAward`, `ScenarioCode`
  A–G). This contract is fixed now. Consumers (the Engine Runner in `domain/eng/`, the API,
  the tests) bind to these types and to `run`, never to an implementation's math.

- `stub.py` — `DeterministicStubEngine`: a deterministic placeholder (cost-only `rec_score`,
  a single Scenario A, single-winner awards with `volume_share = 1.0`). Tagged
  `engine_version = "stub"` so no stubbed run is mistaken for a validated v3 run.

## D2 is in spike — swap, don't rewrite

`SPIKE_D2_engine.md` recommends **Option A**: adopt v3's 5-factor banded scoring + the
`max_two_per_dc` split allocator as the engine, retiring the as-built min-cost solver to
"Scenario A = lowest-cost reference". When the spike closes (validated against the golden
input/output pair, QA S2), the real scorer + allocator replace the stub **body** behind this
same interface. Because consumers bound to the interface and the sealed records — not the
math — the swap is internal.

Clean-room (ADR-0001): v3's logic is **lifted** (re-expressed as clean code), never imported;
`backend/` never imports from `reference/`.
