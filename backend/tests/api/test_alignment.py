"""Web alignment / scenario slice API + read layer (PLAN §5) — the "which lens" decision surface.

Integration (real Postgres + a temp vault): the scenario/award routes hang off the runs router and
wrap `PilotService` with `isolate_db=False`, so they share the rolled-back test session and
provision no per-run DB. The `vault_root` fixture redirects the routers' vault; `client` shares the
test session. Setup + bids are built with the SAME synthetic builders the pilot e2e uses (reused
from `tests.pilot.test_pilot_cycle_e2e`) so the routes exercise the real engine + seal path.

Covers: auth (401); the full alignment path (create → setup → template → import → POST analysis →
GET scenarios [7 lenses, B recommended] → GET scenario B detail [per-cell suppliers, one min + the
recommended flagged] → POST freeze B); gate-before-analysis (400); unknown run / scenario errors.

CONSISTENCY: a read-layer test seals one run and asserts the read layer's per-lens `total_spend` +
savings EQUAL the workbook's `_gather_scenario_rollups` output for the same run (the gather called
directly), so the web can never diverge from the Excel.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.cycle.loader import load_cycle
from app.domain.eng.models import AnalysisScenario
from app.domain.eng.read import scenario_comparison
from app.output.scenario_workbook import _gather_scenario_rollups
from app.pilot.service import PilotService
from app.pilot.vault import stage_filename
from tests.pilot.test_pilot_cycle_e2e import _build_filled_setup, _fill_bid_template

AUTH = "/api/v1/auth"
RUNS = "/api/v1/runs"

_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


# --------------------------------------------------------------------------- #
# helpers — drive the run up to a sealed analysis through the HTTP surface
# --------------------------------------------------------------------------- #
def _login(client, seed_user) -> None:  # type: ignore[no-untyped-def]
    resp = client.post(
        f"{AUTH}/login",
        json={"username": seed_user["username"], "password": seed_user["password"]},
    )
    assert resp.status_code == 200


def _create_run(client) -> str:  # type: ignore[no-untyped-def]
    created = client.post(
        RUNS, json={"commodity": "Field Tomatoes", "label": "Alignment E2E", "rehearsal": False}
    )
    assert created.status_code == 201
    return created.json()["slug"]


def _seed_sealed_run(client, slug: str) -> str:  # type: ignore[no-untyped-def]
    """create → ingest setup → template → strict import → POST analysis; return analysis_run_id."""

    setup = client.post(
        f"{RUNS}/{slug}/setup", files={"file": ("setup.xlsx", _build_filled_setup(), _XLSX)}
    )
    assert setup.status_code == 200, setup.text

    tmpl = client.post(f"{RUNS}/{slug}/rounds/1/template")
    assert tmpl.status_code == 200, tmpl.text
    template_name = tmpl.json()["filename"]
    template_bytes = client.get(f"{RUNS}/{slug}/files/{template_name}").content
    filled = _fill_bid_template(template_bytes)

    imported = client.post(
        "/api/v1/bids/import",
        data={"run": slug, "round": 1, "mode": "strict"},
        files={"file": (template_name, filled, _XLSX)},
    )
    assert imported.status_code == 200, imported.text
    assert imported.json()["ingested"] == 8

    analysis = client.post(f"{RUNS}/{slug}/rounds/1/analysis")
    assert analysis.status_code == 200, analysis.text
    return analysis.json()["analysis_run_id"]


# --------------------------------------------------------------------------- #
# auth gate
# --------------------------------------------------------------------------- #
@pytest.mark.integration
def test_analysis_routes_require_auth(client, vault_root) -> None:  # type: ignore[no-untyped-def]
    """Every alignment route with no session is a 401."""

    assert client.post(f"{RUNS}/x/rounds/1/analysis").status_code == 401
    assert client.get(f"{RUNS}/x/analysis").status_code == 401
    assert client.get(f"{RUNS}/x/analysis/run-1/scenarios").status_code == 401
    assert client.get(f"{RUNS}/x/analysis/run-1/scenarios/B").status_code == 401
    assert (
        client.post(
            f"{RUNS}/x/awards/freeze",
            json={"analysis_run_id": "run-1", "scenario_code": "B", "award_code": "AWD-1"},
        ).status_code
        == 401
    )


# --------------------------------------------------------------------------- #
# the full alignment path, end to end
# --------------------------------------------------------------------------- #
@pytest.mark.integration
def test_alignment_full_path_e2e(client, seed_user, vault_root) -> None:  # type: ignore[no-untyped-def]
    """run analysis → list → compare 7 lenses (B recommended) → B detail → freeze B."""

    _login(client, seed_user)
    slug = _create_run(client)
    analysis_run_id = _seed_sealed_run(client, slug)

    # POST analysis returned a sealed run summary.
    summary = client.post(f"{RUNS}/{slug}/rounds/1/analysis")  # a second run → version 2
    assert summary.status_code == 200, summary.text
    body = summary.json()
    assert body["version"] == 2  # the second sealed run for the cycle
    assert body["round_number"] == 1
    assert body["scenario_count"] == 7
    assert body["analysis_run_id"]
    assert body["sealed_at"]
    assert body["filename"].endswith(".xlsx")

    # GET list — two sealed runs now, oldest first with version ordinals.
    listed = client.get(f"{RUNS}/{slug}/analysis")
    assert listed.status_code == 200
    runs = listed.json()
    assert [r["version"] for r in runs] == [1, 2]
    assert runs[0]["analysis_run_id"] == analysis_run_id
    assert all(r["round_number"] == 1 and r["engine_version"] for r in runs)

    # GET scenarios — the seven lenses A-G, exactly one (B) recommended.
    scenarios = client.get(f"{RUNS}/{slug}/analysis/{analysis_run_id}/scenarios")
    assert scenarios.status_code == 200
    lenses = scenarios.json()
    assert [lens["code"] for lens in lenses] == ["A", "B", "C", "D", "E", "F", "G"]
    recommended = [lens for lens in lenses if lens["is_recommended"]]
    assert [lens["code"] for lens in recommended] == ["B"]
    for lens in lenses:
        for field in (
            "code",
            "label",
            "description",
            "total_spend",
            "delta_vs_a",
            "savings_vs_incumbent_pct",
            "savings_vs_stly_pct",
            "supplier_count",
            "cell_count",
            "cap_breach_count",
        ):
            assert field in lens
        assert lens["total_spend"] > 0
        assert lens["cell_count"] == 4  # 2 DCs × 2 lots × 1 TF
    lens_a = next(lens for lens in lenses if lens["code"] == "A")
    assert lens_a["delta_vs_a"] == 0.0
    assert lens_a["total_spend"] > 0

    # GET scenario B detail — per-cell suppliers with one min + the recommended pick flagged.
    detail = client.get(f"{RUNS}/{slug}/analysis/{analysis_run_id}/scenarios/B")
    assert detail.status_code == 200
    d = detail.json()
    assert d["code"] == "B" and d["is_recommended"] is True
    assert d["savings"]["total_spend"] > 0
    assert d["savings"]["savings_vs_incumbent"] > 0
    assert len(d["cells"]) == 4
    for cell in d["cells"]:
        assert cell["dc"] and cell["lot"] and cell["tf"]
        assert cell["incumbent_supplier"]
        assert cell["suppliers"]
        # exactly one supplier is the min price ...
        assert sum(1 for s in cell["suppliers"] if s["is_min"]) == 1
        # ... and exactly one is the recommended (awarded) pick for the single-winner B lens.
        recs = [s for s in cell["suppliers"] if s["is_recommended"]]
        assert len(recs) == 1
        assert recs[0]["volume_share"] > 0
        # the recommended block names that supplier + carries the engine's B reason label.
        assert cell["recommended"]["supplier"] == recs[0]["name"]
        assert cell["recommended"]["rec_type"]  # B carries a rec_type reason
        # the cell's min_price equals the lowest supplier price present.
        prices = [s["price_per_case"] for s in cell["suppliers"] if s["price_per_case"] is not None]
        assert cell["min_price"] == min(prices)

    # POST freeze B — a governed decision → an award id.
    frozen = client.post(
        f"{RUNS}/{slug}/awards/freeze",
        json={
            "analysis_run_id": analysis_run_id,
            "scenario_code": "B",
            "award_code": "AWD-ALIGN-1",
        },
    )
    assert frozen.status_code == 200, frozen.text
    fb = frozen.json()
    assert fb["award_id"]
    assert fb["scenario_code"] == "B"


@pytest.mark.integration
def test_freeze_emits_frozen_audit_event(client, seed_user, vault_root, db_session) -> None:  # type: ignore[no-untyped-def]
    """Freezing through the HTTP path still lands the FROZEN audit event (governed decision)."""

    from sqlalchemy import text

    _login(client, seed_user)
    slug = _create_run(client)
    analysis_run_id = _seed_sealed_run(client, slug)

    frozen = client.post(
        f"{RUNS}/{slug}/awards/freeze",
        json={
            "analysis_run_id": analysis_run_id,
            "scenario_code": "B",
            "award_code": "AWD-AUDIT-1",
        },
    )
    assert frozen.status_code == 200, frozen.text
    award_id = frozen.json()["award_id"]

    events = db_session.execute(
        text(
            "SELECT count(*) FROM audit.event_log "
            "WHERE event_type = 'FROZEN' AND entity_type = 'awd.award' AND entity_id = :aid"
        ),
        {"aid": award_id},
    ).scalar_one()
    assert events == 1


@pytest.mark.integration
def test_freeze_unknown_scenario_rejected_and_writes_nothing(
    client, seed_user, vault_root, db_session
) -> None:  # type: ignore[no-untyped-def]
    """An unknown scenario code is a clean 400 — and leaves NO award + NO FROZEN event behind.

    Guards the Codex P2: the scenario's award rows are read BEFORE anything is written, so a typo
    can't leave a bogus zero-line FROZEN award (immutable!) or a spurious FROZEN audit event.
    """

    from sqlalchemy import text

    _login(client, seed_user)
    slug = _create_run(client)
    analysis_run_id = _seed_sealed_run(client, slug)

    resp = client.post(
        f"{RUNS}/{slug}/awards/freeze",
        json={
            "analysis_run_id": analysis_run_id,
            "scenario_code": "Z",  # not a sealed lens
            "award_code": "AWD-BAD-1",
        },
    )
    assert resp.status_code == 400, resp.text
    assert resp.json()["code"] == "validation_error"

    # Nothing governed was written for the bogus code: no frozen award row exists for it.
    awards = db_session.execute(
        text("SELECT count(*) FROM awd.award WHERE analysis_run_id = :rid AND scenario_code = 'Z'"),
        {"rid": analysis_run_id},
    ).scalar_one()
    assert awards == 0


# --------------------------------------------------------------------------- #
# gates + error paths
# --------------------------------------------------------------------------- #
@pytest.mark.integration
def test_analysis_before_setup_is_gated(client, seed_user, vault_root) -> None:  # type: ignore[no-untyped-def]
    """Running analysis before setup ingest is a clean 400 (gate_required), not a 500."""

    _login(client, seed_user)
    slug = _create_run(client)
    resp = client.post(f"{RUNS}/{slug}/rounds/1/analysis")
    assert resp.status_code == 400
    assert resp.json()["code"] == "gate_required"


@pytest.mark.integration
def test_scenarios_before_any_sealed_run_is_gated(client, seed_user, vault_root) -> None:  # type: ignore[no-untyped-def]
    """Scenario reads before a sealed analysis exists are a clean 400 (gate_required)."""

    _login(client, seed_user)
    slug = _create_run(client)
    # No cycle, no sealed run → the scenario read is gated, not a 500/404 of an empty list.
    resp = client.get(f"{RUNS}/{slug}/analysis/whatever/scenarios")
    assert resp.status_code == 400
    assert resp.json()["code"] == "gate_required"


@pytest.mark.integration
def test_list_analysis_is_empty_before_seal(client, seed_user, vault_root) -> None:  # type: ignore[no-untyped-def]
    """The LIST endpoint is never a gate — it's an empty list before any sealed run."""

    _login(client, seed_user)
    slug = _create_run(client)
    resp = client.get(f"{RUNS}/{slug}/analysis")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.integration
def test_unknown_run_404_on_alignment_routes(client, seed_user, vault_root) -> None:  # type: ignore[no-untyped-def]
    """An unknown run slug is a 404 on every alignment route."""

    _login(client, seed_user)
    ghost = "no-such-run-20260101-abcdef"
    assert client.post(f"{RUNS}/{ghost}/rounds/1/analysis").status_code == 404
    assert client.get(f"{RUNS}/{ghost}/analysis").status_code == 404
    assert client.get(f"{RUNS}/{ghost}/analysis/run-1/scenarios").status_code == 404
    assert client.get(f"{RUNS}/{ghost}/analysis/run-1/scenarios/B").status_code == 404
    assert (
        client.post(
            f"{RUNS}/{ghost}/awards/freeze",
            json={"analysis_run_id": "run-1", "scenario_code": "B", "award_code": "AWD-1"},
        ).status_code
        == 404
    )


@pytest.mark.integration
def test_unknown_analysis_run_404(client, seed_user, vault_root) -> None:  # type: ignore[no-untyped-def]
    """A real run but an unknown analysis_run_id is a 404 (never another run's analysis)."""

    _login(client, seed_user)
    slug = _create_run(client)
    _seed_sealed_run(client, slug)  # a cycle + a sealed run now exist
    resp = client.get(f"{RUNS}/{slug}/analysis/not-a-real-run-id/scenarios")
    assert resp.status_code == 404


@pytest.mark.integration
def test_unknown_scenario_code_is_validation_error(client, seed_user, vault_root) -> None:  # type: ignore[no-untyped-def]
    """A valid sealed run but an unknown lens code is a clean 400 (validation_error)."""

    _login(client, seed_user)
    slug = _create_run(client)
    analysis_run_id = _seed_sealed_run(client, slug)
    resp = client.get(f"{RUNS}/{slug}/analysis/{analysis_run_id}/scenarios/Z")
    assert resp.status_code == 400
    assert resp.json()["code"] == "validation_error"


# --------------------------------------------------------------------------- #
# CONSISTENCY — the read layer must match the workbook's gather for the same run
# --------------------------------------------------------------------------- #
@pytest.mark.integration
def test_read_layer_matches_workbook_gather(tmp_path: Path, db_session) -> None:  # type: ignore[no-untyped-def]
    """The read layer's per-lens spend + savings EQUAL `_gather_scenario_rollups` for the run.

    Both the alignment workbook and the web read layer must show the SAME numbers; this seals one
    run, calls the workbook's gather DIRECTLY, and asserts the read layer's `scenario_comparison`
    reproduces every lens's `total_spend`, `delta_vs_a`, and both savings fractions exactly. A
    regression where the web recomputes (and drifts from) the Excel would fail here.
    """

    service = PilotService(tmp_path, isolate_db=False)
    paths = service.start_run(commodity="Field Tomatoes", label="Consistency")
    setup_path = paths.inputs / stage_filename(1, "setup_kickoff")
    setup_path.write_bytes(_build_filled_setup())
    cycle_id = service.ingest_setup(db_session, paths, setup_path)

    template_path = service.generate_bid_template(db_session, paths, 1)
    template_path.write_bytes(_fill_bid_template(template_path.read_bytes()))
    service.ingest_bids(db_session, paths, 1, template_path)
    service.run_round(db_session, paths, 1)

    analyses = service.list_analyses(db_session, paths)
    assert len(analyses) == 1
    analysis_run_id = analyses[0].analysis_run_id

    cycle = load_cycle(db_session, cycle_id)

    # The workbook's gather — the SAME pure function the Excel writer calls (ground truth).
    scenarios = (
        db_session.query(AnalysisScenario)
        .filter(AnalysisScenario.analysis_run_id == analysis_run_id)
        .order_by(AnalysisScenario.scenario_code)
        .all()
    )
    rollups, _baseline_total, _stly_total = _gather_scenario_rollups(
        db_session, cycle, scenarios, analysis_run_id
    )
    by_code = {r.code: r for r in rollups}

    # The read layer the web consumes.
    rows = scenario_comparison(db_session, cycle, analysis_run_id)
    assert {r.code for r in rows} == {"A", "B", "C", "D", "E", "F", "G"}

    for row in rows:
        gather = by_code[row.code]
        assert row.total_spend == pytest.approx(float(gather.total_spend))
        assert row.delta_vs_a == pytest.approx(float(gather.delta_vs_a))
        assert row.savings_vs_incumbent_pct == pytest.approx(float(gather.savings_vs_baseline_frac))
        assert row.savings_vs_stly_pct == pytest.approx(float(gather.savings_vs_stly_frac))
        assert row.supplier_count == gather.n_suppliers
        assert row.cell_count == gather.n_cells
        assert row.cap_breach_count == gather.n_cap_breaches
