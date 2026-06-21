"""The post-award READ layer (`awd.read`): list frozen awards + inspect one award.

Drives the real PilotService pipeline (setup → bids → run_round → freeze_award), then records a
versioned adjustment layer and asserts the read views the web console renders:
  * `list_awards` — the cycle's frozen award(s) with line count + latest layer version;
  * `award_detail` — baseline lines resolved to NAMES (D23) with frozen + effective price + delta,
    plus the version history (v0 FROZEN → vN). The effective price + delta reflect the layer.

Integration (needs a live Postgres at head).
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from app.domain.awd.models import AwardLine
from app.domain.awd.service import add_adjustment
from app.pilot.service import PilotService
from app.pilot.vault import stage_filename
from tests.bid.test_period_import import _fill_template_full_columns
from tests.pilot.test_pilot_cycle_e2e import _build_filled_setup


@pytest.mark.integration
def test_award_read_list_and_detail_reflect_layers(tmp_path: Path, db_session) -> None:  # type: ignore[no-untyped-def]
    """list_awards + award_detail expose the frozen baseline, effective price, and history."""

    service = PilotService(tmp_path, isolate_db=False)
    paths = service.start_run(commodity="Colored Potatoes", label="Award Read")
    setup_path = paths.inputs / stage_filename(1, "setup_kickoff")
    setup_path.write_bytes(_build_filled_setup())
    service.ingest_setup(db_session, paths, setup_path)

    template_path = service.generate_bid_template(db_session, paths, 1)
    template_path.write_bytes(_fill_template_full_columns(template_path.read_bytes(), []))
    service.ingest_bids(db_session, paths, 1, template_path)
    service.run_round(db_session, paths, 1)

    analyses = service.list_analyses(db_session, paths)
    assert analyses, "a sealed analysis exists"
    award_id = service.freeze_award(
        db_session,
        paths,
        analysis_run_id=analyses[-1].analysis_run_id,
        scenario_code="B",
        award_code="AWD-READ-TEST",
    )

    # list_awards: exactly one frozen award, baseline only (latest_version == 0).
    awards = service.list_awards(db_session, paths)
    assert len(awards) == 1
    summary = awards[0]
    assert summary.award_id == award_id
    assert summary.award_code == "AWD-READ-TEST"
    assert summary.scenario_code == "B"
    assert summary.line_count > 0
    assert summary.latest_version == 0

    # award_detail: baseline lines by NAME (D23), frozen == effective, delta 0; history = v0 FROZEN.
    detail = service.award_detail(db_session, paths, award_id)
    assert detail.award_code == "AWD-READ-TEST"
    assert detail.lines, "baseline lines present"
    assert all(line.delta == 0 for line in detail.lines)
    assert all(line.effective_price == line.frozen_price for line in detail.lines)
    assert all(line.dc and line.supplier for line in detail.lines)  # names resolved
    assert [v.version_no for v in detail.versions] == [0]
    assert detail.versions[0].adjustment_type == "FROZEN"
    assert detail.latest_version == 0

    # Record a versioned adjustment on ONE cell (+$5), then re-read.
    row = db_session.query(AwardLine).filter(AwardLine.award_id == award_id).first()
    assert row is not None
    new_price = row.frozen_price + Decimal("5")
    version_no = add_adjustment(
        db_session,
        award_id=award_id,
        adjustment_type="MARKET_HIKE",
        effective_date=date(2026, 4, 1),
        reason="trailing-4wk reset",
        created_by="tester",
        line_changes=[(row.dc_id, row.lot_id, row.tf_id, row.supplier_id, new_price)],
    )
    db_session.flush()
    assert version_no == 1

    detail2 = service.award_detail(db_session, paths, award_id)
    # The adjusted cell now carries a delta == +5; every other cell stays at delta 0.
    adjusted = [line for line in detail2.lines if line.delta != 0]
    assert len(adjusted) == 1
    assert abs(adjusted[0].delta - 5.0) < 1e-6
    assert abs(adjusted[0].effective_price - adjusted[0].frozen_price - 5.0) < 1e-6
    # The history now shows v0 FROZEN + v1 MARKET_HIKE; the summary's latest_version advances.
    assert [v.version_no for v in detail2.versions] == [0, 1]
    assert detail2.versions[1].adjustment_type == "MARKET_HIKE"
    assert detail2.latest_version == 1
    assert service.list_awards(db_session, paths)[0].latest_version == 1
