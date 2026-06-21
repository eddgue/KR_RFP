"""Supplier comms (E-37): award-notification email drafts over the HTTP surface.

Integration (real Postgres + temp vault): reuses the alignment HTTP seed helpers (create → setup →
template → import → analysis) + the freeze helper, then exercises the award comms-draft endpoint —
one template-merge draft per awarded supplier, draft-only.
"""

from __future__ import annotations

import pytest

from tests.api.test_alignment import _create_run, _login, _seed_sealed_run
from tests.api.test_post_award import _freeze_b

RUNS = "/api/v1/runs"


@pytest.mark.integration
def test_award_comms_requires_auth(client, vault_root) -> None:  # type: ignore[no-untyped-def]
    assert client.get(f"{RUNS}/x/awards/a-1/comms/award").status_code == 401


@pytest.mark.integration
def test_award_comms_drafts_one_per_awarded_supplier(client, seed_user, vault_root) -> None:  # type: ignore[no-untyped-def]
    """freeze B → an award draft per supplier; machine-tag subject + data-filled body."""

    _login(client, seed_user)
    slug = _create_run(client)
    analysis_run_id = _seed_sealed_run(client, slug)
    award_id = _freeze_b(client, slug, analysis_run_id, code="AWD-COMMS-1")

    resp = client.get(f"{RUNS}/{slug}/awards/{award_id}/comms/award")
    assert resp.status_code == 200, resp.text
    drafts = resp.json()
    assert len(drafts) >= 1

    for draft in drafts:
        assert draft["email_type"] == "Award Notification"
        # Subject: machine-readable routing tags first, then the human-readable type + cycle.
        assert draft["subject"].startswith("[RFP:")
        assert "[SUP:" in draft["subject"]
        assert "Award Notification –" in draft["subject"]
        # Body merged from governed data.
        assert f"Dear {draft['supplier_name']}," in draft["body"]
        assert "selected for award" in draft["body"]
        assert "Awarded Locations:" in draft["body"]
        # Counts are filled (not visible holes).
        assert "[#AwardedDCCount]" not in draft["body"]
        assert "[#AwardedLotCount]" not in draft["body"]
        # Each draft attaches the supplier's OWN individual guide (generated at freeze) — never the
        # combined all-suppliers workbook (which would leak every supplier's awards).
        assert "[#AwardFileName]" not in draft["body"]
        assert "AwardFileName" not in draft["missing"]
        assert "award_guide" in draft["body"]
        assert "supplier_guides" not in draft["body"]
        # The authenticated user is the draft's buyer; the title is left for the buyer to complete.
        assert seed_user["username"] in draft["body"]
        assert "BuyerTitle" in draft["missing"]


@pytest.mark.integration
def test_award_comms_guide_is_not_stale_across_awards(client, seed_user, vault_root) -> None:  # type: ignore[no-untyped-def]
    """Two awards on one run → an earlier award's drafts attach ITS guide, never the later one's.

    The per-supplier guide is award-code-stamped, so freezing a second scenario can't shadow the
    first award's files (the regression Codex flagged: a fixed-name guide overwritten per freeze).
    """

    _login(client, seed_user)
    slug = _create_run(client)
    analysis_run_id = _seed_sealed_run(client, slug)
    award_b = _freeze_b(client, slug, analysis_run_id, code="AWD-B")
    resp_a = client.post(
        f"{RUNS}/{slug}/awards/freeze",
        json={"analysis_run_id": analysis_run_id, "scenario_code": "A", "award_code": "AWD-A"},
    )
    assert resp_a.status_code == 200, resp_a.text

    drafts = client.get(f"{RUNS}/{slug}/awards/{award_b}/comms/award").json()
    assert len(drafts) >= 1
    for draft in drafts:
        body = draft["body"].lower()
        assert "award file: " in body  # a guide is attached
        assert "awd_b" in body  # the EARLIER award's stamped guide
        assert "awd_a" not in body  # never the later award's guide


@pytest.mark.integration
def test_award_comms_unknown_award_404(client, seed_user, vault_root) -> None:  # type: ignore[no-untyped-def]
    _login(client, seed_user)
    slug = _create_run(client)
    _seed_sealed_run(client, slug)
    resp = client.get(f"{RUNS}/{slug}/awards/no-such-award/comms/award")
    assert resp.status_code == 404


@pytest.mark.integration
def test_feedback_comms_requires_auth(client, vault_root) -> None:  # type: ignore[no-untyped-def]
    assert client.get(f"{RUNS}/x/analysis/run-1/comms/feedback").status_code == 401


@pytest.mark.integration
def test_feedback_comms_drafts_above_benchmark_suppliers(client, seed_user, vault_root) -> None:  # type: ignore[no-untyped-def]
    """A sealed round → a round-feedback draft per supplier above the market-low benchmark.

    The synthetic seed splits each DC's two lots across the two suppliers, so on its weaker lot each
    supplier sits above the other's market low — both get a draft with a machine-tag subject and a
    data-filled body (DC summary + hard/soft ask sections, tables expanded, no visible holes).
    """

    _login(client, seed_user)
    slug = _create_run(client)
    analysis_run_id = _seed_sealed_run(client, slug)

    resp = client.get(f"{RUNS}/{slug}/analysis/{analysis_run_id}/comms/feedback")
    assert resp.status_code == 200, resp.text
    drafts = resp.json()
    assert len(drafts) >= 1

    for draft in drafts:
        assert draft["email_type"] == "Round Feedback"
        # Subject: machine-readable routing tags first, then the round-feedback infix + cycle.
        assert draft["subject"].startswith("[RFP:")
        assert "[SUP:" in draft["subject"]
        assert "Feedback –" in draft["subject"]
        assert "[#RoundNumber]" not in draft["subject"]
        # Body merged from governed data: greeting + the three authored sections.
        assert f"Dear {draft['supplier_name']}," in draft["body"]
        assert "DC Summary" in draft["body"]
        assert "Items Requiring Action" in draft["body"]
        assert "Additional Improvement Opportunities" in draft["body"]
        # Every table block expanded (even an empty one renders a header, never a leftover token).
        assert "[#DCSummaryTable]" not in draft["body"]
        assert "[#HardAskTable]" not in draft["body"]
        assert "[#SoftAskTable]" not in draft["body"]
        # The authenticated user is the draft's buyer; the title is left for the buyer to complete.
        assert seed_user["username"] in draft["body"]
        assert "BuyerTitle" in draft["missing"]


@pytest.mark.integration
def test_feedback_comms_unknown_run_404(client, seed_user, vault_root) -> None:  # type: ignore[no-untyped-def]
    _login(client, seed_user)
    slug = _create_run(client)
    _seed_sealed_run(client, slug)
    resp = client.get(f"{RUNS}/{slug}/analysis/no-such-run/comms/feedback")
    assert resp.status_code == 404


@pytest.mark.integration
def test_rejection_comms_requires_auth(client, vault_root) -> None:  # type: ignore[no-untyped-def]
    assert client.get(f"{RUNS}/x/awards/a-1/comms/rejection").status_code == 401


@pytest.mark.integration
def test_rejection_comms_drafts_per_lost_lot(client, seed_user, vault_root) -> None:  # type: ignore[no-untyped-def]
    """freeze B → a non-selection draft per supplier with a lot they did not win.

    The synthetic seed splits each DC's two lots across the two suppliers, so each supplier loses
    its weaker lot — both get a "RFP Results" draft itemizing the lost lots (their price, the
    market-low benchmark, the % gap, a reason), with a machine-tag subject and no visible holes.
    """

    _login(client, seed_user)
    slug = _create_run(client)
    analysis_run_id = _seed_sealed_run(client, slug)
    award_id = _freeze_b(client, slug, analysis_run_id, code="AWD-COMMS-REJ-1")

    resp = client.get(f"{RUNS}/{slug}/awards/{award_id}/comms/rejection")
    assert resp.status_code == 200, resp.text
    drafts = resp.json()
    assert len(drafts) >= 1

    for draft in drafts:
        assert draft["email_type"] == "RFP Results"
        # Subject: machine-readable routing tags first, then the results infix + cycle.
        assert draft["subject"].startswith("[RFP:")
        assert "[SUP:" in draft["subject"]
        assert "RFP Results –" in draft["subject"]
        # Body merged from governed data: greeting + the evaluation summary section.
        assert f"Dear {draft['supplier_name']}," in draft["body"]
        assert "not selected for award" in draft["body"]
        assert "Evaluation Summary" in draft["body"]
        # The reason table expanded (header present, placeholder gone).
        assert "[#RejectionReasonTable]" not in draft["body"]
        assert "Benchmark Price" in draft["body"]
        # The authenticated user is the draft's buyer; the title is left for the buyer to complete.
        assert seed_user["username"] in draft["body"]
        assert "BuyerTitle" in draft["missing"]


@pytest.mark.integration
def test_rejection_comms_unknown_award_404(client, seed_user, vault_root) -> None:  # type: ignore[no-untyped-def]
    _login(client, seed_user)
    slug = _create_run(client)
    _seed_sealed_run(client, slug)
    resp = client.get(f"{RUNS}/{slug}/awards/no-such-award/comms/rejection")
    assert resp.status_code == 404
