"""The engine runner — orchestrates a sealed decision-support run on the governed store.

This is the service seam between the governed Postgres store and the FROZEN, pure engine library
(`app.engine`, `V3Engine.run(inputs) -> EngineResult`). It is the ONLY place the two meet: the
library is a pure function of frozen inputs (no I/O, no clock, no randomness); the runner owns the
store I/O, the clock, the hashing, and the transaction (PLAN §3, §7).

What `run_analysis` does, in order (ENG-PLAN §3, ADR-0006, D18/D20/D21):
  1. READ BY KEY. Read the cycle's scored bid lines, the strategy config (weights preset +
     max_sup_dc + thresholds), the projected volumes, and the incumbent baselines from the store
     using the system-owned surrogate KEYS (never name-resolution — D21). Everything the engine
     reads is keyed; nothing commodity/strategy-specific is hardcoded (D18 strategy-agnostic).
  2. ASSEMBLE. Build the frozen `EngineInputs` (config + bids + volumes + incumbents). The engine's
     lot-level cell grain is (dc, lot, tf); store volume is DC x item x tf, so item demand is
     aggregated to the lot. The engine's `tf_code` period token is the store's `tf_code`; the
     runner keeps a tf_code -> tf_id map to write awards back on the keyed grain.
  3. RUN. Call the pure `V3Engine.run`. Same inputs always yield the same result (reproducibility
     is a hard requirement for sealed runs).
  4. SEAL. Hash a canonical manifest of the inputs (sha256) and of the outputs (sha256), then write
     an immutable `eng.analysis_run` (engine version pin + is_sealed=True + both manifests) plus the
     per-bid `eng.bid_score`, the A-G `eng.analysis_scenario` headers, and the split
     `eng.analysis_scenario_award` rows (volume_share / is_fallback / cap_breach_flag).

Decision-support ONLY (ADR-0006): the runner NEVER asserts an award. It writes RECOMMENDATIONS
(scenarios + split shares); a human selects a lens and the real award lands later in `awd.*`. The
service follows the unit-of-work discipline (add + flush, never commit — PLAN §7); the caller's
`unit_of_work` owns the transaction so the sealed run and its rows land atomically.

CLEAN-ROOM (ADR-0001): no import from `reference/`; the engine behind the interface is our own
clean-room re-implementation. This module imports only the FROZEN interface + the store ORM.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.bid.models import BidLine
from app.domain.cyc.models import CycleLotItem, CycleProjectedVolume, CycleRound, CycleTimeframe
from app.domain.eng.models import (
    AnalysisRun,
    AnalysisScenario,
    AnalysisScenarioAward,
    BidScore,
)
from app.engine.interface import (
    BidComponents,
    BidInput,
    Engine,
    EngineConfig,
    EngineInputs,
    EngineResult,
    IncumbentBaseline,
    ScenarioCode,
    VolumeRequirement,
)
from app.engine.v3 import V3Engine


@dataclass(frozen=True)
class IncumbentRow:
    """A keyed incumbent baseline for one (dc, lot): the incumbent supplier + routing baseline.

    Synthetic/strategy-agnostic: the runner takes whatever incumbents the caller resolved from the
    store (`perf.historical_award_assignment` in production); it hardcodes nothing.
    """

    dc_id: str
    lot_id: str
    supplier_id: str
    routing_cost_per_case: Decimal | None = None


@dataclass(frozen=True)
class RunResult:
    """The persisted run's identity + a small headline summary for the caller / demo log."""

    analysis_run_id: str
    cycle_id: str
    round_id: str
    engine_version: str
    input_hash: str
    output_hash: str
    score_count: int
    scenario_count: int
    award_count: int


class EngineRunner:
    """Orchestrates a sealed decision-support run: read-by-key -> assemble -> run -> seal."""

    def __init__(self, session: Session, engine: Engine | None = None) -> None:
        self._session = session
        # Bind the real v3 engine by default; an injected engine keeps the runner testable.
        self._engine = engine if engine is not None else V3Engine()

    # ------------------------------------------------------------------ public
    def run_analysis(
        self,
        *,
        cycle_id: str,
        round_id: str,
        config: EngineConfig,
        incumbents: tuple[IncumbentRow, ...] = (),
        run_by: str = "engine-runner",
    ) -> RunResult:
        """Run + seal one analysis for a cycle's round; returns the persisted run's identity.

        Reads the round's bids/volumes/incumbents BY KEY, assembles the frozen inputs, calls the
        pure engine, hashes the canonical input/output manifests, and writes the sealed run + scores
        + scenarios + split awards. Add + flush only — the caller's unit of work commits.
        """

        started_at = datetime.now(UTC).replace(tzinfo=None)  # naive UTC for `timestamp` columns

        # 1) READ BY KEY + 2) ASSEMBLE.
        round_code = self._round_code(cycle_id, round_id)
        tf_code_by_id, tf_id_by_code = self._timeframe_maps(cycle_id)
        lot_by_item = self._lot_by_item(cycle_id)

        bid_lines = self._read_bid_lines(cycle_id, round_id)
        # The incumbent's bid (matched by dc × lot × supplier) carries is_incumbent=True so the
        # §2.5 continuity factor can reward it — without this the continuity weight is inert.
        incumbent_keys = {(inc.dc_id, inc.lot_id, inc.supplier_id) for inc in incumbents}
        bids = self._assemble_bids(bid_lines, tf_code_by_id, lot_by_item, incumbent_keys)
        volumes = self._assemble_volumes(cycle_id, tf_code_by_id, lot_by_item)
        incumbent_inputs = self._assemble_incumbents(incumbents)

        inputs = EngineInputs(
            cycle_id=cycle_id,
            round_code=round_code,
            config=config,
            bids=tuple(bids),
            volumes=tuple(volumes),
            incumbents=tuple(incumbent_inputs),
        )

        # 3) RUN (pure).
        result = self._engine.run(inputs)

        # 4) SEAL.
        input_hash = _canonical_hash(_inputs_manifest(inputs))
        output_hash = _canonical_hash(_outputs_manifest(result))
        finished_at = datetime.now(UTC).replace(tzinfo=None)

        analysis_run_id = _new_id()
        run = AnalysisRun(
            analysis_run_id=analysis_run_id,
            cycle_id=cycle_id,
            round_id=round_id,
            engine_version=result.engine_version,
            config_preset=str(config.preset.value),
            status="SEALED",
            is_sealed=True,
            input_hash_manifest=input_hash,
            output_hash_manifest=output_hash,
            run_started_at=started_at,
            run_finished_at=finished_at,
            run_by=run_by,
        )
        self._session.add(run)
        self._session.flush()

        # Map each bid_id (the BidLine PK) back to its keyed identity for the score rows.
        line_by_id = {line.bid_line_id: line for line in bid_lines}
        self._persist_scores(analysis_run_id, result, line_by_id)
        scenario_id_by_code = self._persist_scenarios(analysis_run_id, result, inputs)
        self._persist_awards(result, scenario_id_by_code, tf_id_by_code)
        self._session.flush()

        return RunResult(
            analysis_run_id=analysis_run_id,
            cycle_id=cycle_id,
            round_id=round_id,
            engine_version=result.engine_version,
            input_hash=input_hash,
            output_hash=output_hash,
            score_count=len(result.scores),
            scenario_count=len(result.scenarios),
            award_count=len(result.awards),
        )

    # ------------------------------------------------------- store reads (key)
    def _round_code(self, cycle_id: str, round_id: str) -> str:
        row = self._session.execute(
            select(CycleRound.round_number).where(
                CycleRound.round_id == round_id, CycleRound.cycle_id == cycle_id
            )
        ).one()
        return f"R{row[0]}"

    def _timeframe_maps(self, cycle_id: str) -> tuple[dict[str, str], dict[str, str]]:
        """(tf_id -> tf_code, tf_code -> tf_id) for the cycle's timeframes."""

        rows = self._session.execute(
            select(CycleTimeframe.tf_id, CycleTimeframe.tf_code).where(
                CycleTimeframe.cycle_id == cycle_id
            )
        ).all()
        tf_code_by_id: dict[str, str] = {tf_id: tf_code for tf_id, tf_code in rows}  # noqa: C416
        tf_id_by_code: dict[str, str] = {tf_code: tf_id for tf_id, tf_code in rows}
        return tf_code_by_id, tf_id_by_code

    def _lot_by_item(self, cycle_id: str) -> dict[str, str]:
        """item_id -> lot_id for the cycle (one lot per item — cyc.cycle_lot_item)."""

        rows = self._session.execute(
            select(CycleLotItem.item_id, CycleLotItem.lot_id).where(
                CycleLotItem.cycle_id == cycle_id
            )
        ).all()
        return {item_id: lot_id for item_id, lot_id in rows}  # noqa: C416

    def _read_bid_lines(self, cycle_id: str, round_id: str) -> list[BidLine]:
        """The round's scoreable bid lines, BY KEY (cycle_id, round_id).

        Only `is_scoreable` lines are returned: a superseded submission (a supplier re-sent a
        corrected file, or sent both an owned template and their own sheet for the same round) has
        its prior lines marked non-scoreable at ingest, so the engine scores ONE submission per
        supplier per round — no double-counting (supersede, never hard-delete; ADR-0006).
        """

        return list(
            self._session.execute(
                select(BidLine)
                .where(
                    BidLine.cycle_id == cycle_id,
                    BidLine.round_id == round_id,
                    BidLine.is_scoreable.is_(True),
                )
                .order_by(BidLine.bid_line_id)
            )
            .scalars()
            .all()
        )

    # ------------------------------------------------------- input assembly
    def _assemble_bids(
        self,
        bid_lines: list[BidLine],
        tf_code_by_id: dict[str, str],
        lot_by_item: dict[str, str],
        incumbent_keys: frozenset[tuple[str, str, str]] | set[tuple[str, str, str]] = frozenset(),
    ) -> list[BidInput]:
        """Map keyed bid lines to the engine's frozen BidInput (lot-level cell grain).

        A bid is flagged `is_incumbent` when its (dc, lot, supplier) is the cycle's incumbent for
        that cell, so the §2.5 continuity factor (incumbent -> 100) actually fires.
        """

        bids: list[BidInput] = []
        for line in bid_lines:
            lot_id = lot_by_item.get(line.item_id, line.lot_id)
            tf_code = tf_code_by_id.get(line.tf_id, line.tf_id)
            components = BidComponents(
                all_in=line.submitted_all_in_case,
                fob=line.fob_case,
                delivery_surcharge=line.delivery_surcharge_case or Decimal("0"),
                vegcool_surcharge=line.vegcool_surcharge_case or Decimal("0"),
                lot_discount=line.lot_discount_case or Decimal("0"),
            )
            landed = line.submitted_all_in_case or line.fob_case or Decimal("0")
            bids.append(
                BidInput(
                    bid_id=line.bid_line_id,
                    supplier_id=line.supplier_id,
                    dc_no=line.dc_id,
                    lot_id=lot_id,
                    tf_code=tf_code,
                    landed_cost_per_case=landed,
                    eligible=line.is_scoreable,
                    is_incumbent=(line.dc_id, lot_id, line.supplier_id) in incumbent_keys,
                    components=components,
                    total_vol_offered=line.volume_minimum_cases,
                )
            )
        return bids

    def _assemble_volumes(
        self,
        cycle_id: str,
        tf_code_by_id: dict[str, str],
        lot_by_item: dict[str, str],
    ) -> list[VolumeRequirement]:
        """Aggregate DC x item x tf projected volume to the engine's (dc, lot, tf) cell grain."""

        rows = self._session.execute(
            select(
                CycleProjectedVolume.dc_id,
                CycleProjectedVolume.item_id,
                CycleProjectedVolume.tf_id,
                CycleProjectedVolume.projected_period_cases,
            ).where(CycleProjectedVolume.cycle_id == cycle_id)
        ).all()

        by_cell: dict[tuple[str, str, str], Decimal] = defaultdict(lambda: Decimal("0"))
        for dc_id, item_id, tf_id, period_cases in rows:
            lot_id = lot_by_item.get(item_id)
            tf_code = tf_code_by_id.get(tf_id)
            if lot_id is None or tf_code is None:
                continue
            by_cell[(dc_id, lot_id, tf_code)] += period_cases or Decimal("0")

        return [
            VolumeRequirement(dc_no=dc, lot_id=lot, tf_code=tf, total_volume=total)
            for (dc, lot, tf), total in by_cell.items()
        ]

    def _assemble_incumbents(self, incumbents: tuple[IncumbentRow, ...]) -> list[IncumbentBaseline]:
        return [
            IncumbentBaseline(
                dc_no=inc.dc_id,
                lot_id=inc.lot_id,
                supplier_id=inc.supplier_id,
                routing_cost_per_case=inc.routing_cost_per_case,
            )
            for inc in incumbents
        ]

    # ------------------------------------------------------- output persistence
    def _persist_scores(
        self,
        analysis_run_id: str,
        result: EngineResult,
        line_by_id: dict[str, BidLine],
    ) -> None:
        for score in result.scores:
            line = line_by_id.get(score.bid_id)
            if line is None:
                continue
            self._session.add(
                BidScore(
                    bid_score_id=_new_id(),
                    analysis_run_id=analysis_run_id,
                    bid_line_id=score.bid_id,
                    supplier_id=line.supplier_id,
                    dc_id=line.dc_id,
                    lot_id=line.lot_id,
                    tf_id=line.tf_id,
                    price_score=score.price_score,
                    coverage_score=score.coverage_score,
                    hist_score=score.hist_score,
                    zrisk_score=score.zrisk_score,
                    continuity_score=score.continuity_score,
                    rec_score=score.rec_score,
                    is_eligible=score.eligible,
                    gate_flags="; ".join(score.gate_flags) if score.gate_flags else None,
                )
            )

    def _persist_scenarios(
        self,
        analysis_run_id: str,
        result: EngineResult,
        inputs: EngineInputs,
    ) -> dict[ScenarioCode, str]:
        """Write the A-G lens headers; return code -> scenario_id for the award rows."""

        # Scenario A objective spend = lowest-cost reference total (sum of A's awarded shares).
        spend_by_code = _scenario_spend(result, inputs)
        out: dict[ScenarioCode, str] = {}
        for scenario in result.scenarios:
            scenario_id = _new_id()
            out[scenario.code] = scenario_id
            self._session.add(
                AnalysisScenario(
                    analysis_scenario_id=scenario_id,
                    analysis_run_id=analysis_run_id,
                    scenario_code=scenario.code.value,
                    label=scenario.label,
                    description=scenario.description or None,
                    objective_total_spend=spend_by_code.get(scenario.code),
                )
            )
        return out

    def _persist_awards(
        self,
        result: EngineResult,
        scenario_id_by_code: dict[ScenarioCode, str],
        tf_id_by_code: dict[str, str],
    ) -> None:
        for award in result.awards:
            scenario_id = scenario_id_by_code.get(award.scenario_code)
            tf_id = tf_id_by_code.get(award.tf_code)
            if scenario_id is None or tf_id is None:
                continue
            if award.awarded_price <= Decimal("0"):
                continue  # the table requires a positive awarded price; skip degenerate rows
            self._session.add(
                AnalysisScenarioAward(
                    award_id=_new_id(),
                    analysis_scenario_id=scenario_id,
                    dc_id=award.dc_no,
                    lot_id=award.lot_id,
                    tf_id=tf_id,
                    supplier_id=award.supplier_id,
                    volume_share=award.volume_share,
                    awarded_price=award.awarded_price,
                    is_recommended=award.is_recommended,
                    is_fallback=award.is_fallback,
                    cap_breach_flag=award.cap_breach_flag,
                    rec_type=award.rec_type,
                )
            )


# ---------------------------------------------------------------------------
# Canonical manifest + hashing (reproducible sha256 of the inputs/outputs)
# ---------------------------------------------------------------------------
def _new_id() -> str:
    return str(uuid.uuid4())


def _canonical_hash(manifest: object) -> str:
    """sha256 of the canonical (sorted-key, str-coerced) JSON of a manifest."""

    payload = json.dumps(manifest, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _inputs_manifest(inputs: EngineInputs) -> dict[str, object]:
    """A stable, hashable view of the frozen inputs (the sealed-run input manifest)."""

    return {
        "cycle_id": inputs.cycle_id,
        "round_code": inputs.round_code,
        "config": {
            "preset": inputs.config.preset.value,
            "weights": [
                str(inputs.config.weight_price),
                str(inputs.config.weight_coverage),
                str(inputs.config.weight_historical),
                str(inputs.config.weight_zrisk),
                str(inputs.config.weight_continuity),
            ],
            "max_sup_dc": inputs.config.max_sup_dc,
            "conc_thresh": str(inputs.config.conc_thresh),
            "global_premium_threshold": str(inputs.config.global_premium_threshold),
            "coverage_floor": str(inputs.config.coverage_floor),
            "lenses": [c.value for c in inputs.config.lenses],
        },
        "bids": sorted(
            [
                [b.bid_id, b.supplier_id, b.dc_no, b.lot_id, b.tf_code, str(b.landed_cost_per_case)]
                for b in inputs.bids
            ]
        ),
        "volumes": sorted(
            [[v.dc_no, v.lot_id, v.tf_code, str(v.total_volume)] for v in inputs.volumes]
        ),
        "incumbents": sorted(
            [
                [i.dc_no, i.lot_id, i.supplier_id, str(i.routing_cost_per_case)]
                for i in inputs.incumbents
            ]
        ),
    }


def _outputs_manifest(result: EngineResult) -> dict[str, object]:
    """A stable, hashable view of the engine result (the sealed-run output manifest)."""

    return {
        "engine_version": result.engine_version,
        "scores": sorted([[s.bid_id, str(s.rec_score), s.eligible] for s in result.scores]),
        "scenarios": sorted([[s.code.value, s.label] for s in result.scenarios]),
        "awards": sorted(
            [
                [
                    a.scenario_code.value,
                    a.dc_no,
                    a.lot_id,
                    a.tf_code,
                    a.supplier_id,
                    str(a.volume_share),
                    str(a.awarded_price),
                    a.is_fallback,
                    a.cap_breach_flag,
                    a.rec_type or "",
                ]
                for a in result.awards
            ]
        ),
    }


def _scenario_spend(result: EngineResult, inputs: EngineInputs) -> dict[ScenarioCode, Decimal]:
    """Per-lens objective spend: sum over the lens's awards of price * cell volume * share.

    A decision-support comparison figure (e.g. Scenario A lowest-cost benchmark vs Scenario B),
    not an assertion. Volume defaults to a per-case weight of 1 when a cell has no projected demand.
    """

    vol_by_cell: dict[tuple[str, str, str], Decimal] = {}
    for v in inputs.volumes:
        vol_by_cell[(v.dc_no, v.lot_id, v.tf_code)] = v.total_volume or Decimal("1")

    spend: dict[ScenarioCode, Decimal] = defaultdict(lambda: Decimal("0"))
    for a in result.awards:
        vol = vol_by_cell.get((a.dc_no, a.lot_id, a.tf_code), Decimal("1"))
        spend[a.scenario_code] += a.awarded_price * vol * a.volume_share
    return dict(spend)
