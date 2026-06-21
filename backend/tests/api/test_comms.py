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
        # The authenticated user is the draft's buyer; the title is left for the buyer to complete.
        assert seed_user["username"] in draft["body"]
        assert "BuyerTitle" in draft["missing"]


@pytest.mark.integration
def test_award_comms_unknown_award_404(client, seed_user, vault_root) -> None:  # type: ignore[no-untyped-def]
    _login(client, seed_user)
    slug = _create_run(client)
    _seed_sealed_run(client, slug)
    resp = client.get(f"{RUNS}/{slug}/awards/no-such-award/comms/award")
    assert resp.status_code == 404
